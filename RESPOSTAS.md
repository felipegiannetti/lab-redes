# Respostas — Central de Avisos da Turma

> Rascunho de respostas elaborado com apoio de IA (Claude/Anthropic) a partir do código
> implementado e de testes reais executados durante o desenvolvimento (conforme nota de
> transparência do roteiro). Revise, personalize com suas próprias palavras e esteja
> pronto para defender qualquer trecho antes de entregar.

## Parte A — TCP

**1. O que acontece se você iniciar o cliente antes do servidor? Por que isso ocorre, considerando o funcionamento do TCP?**

A conexão falha imediatamente: em Java, `new Socket(host, porta)` lança `java.net.ConnectException: Connection refused`; em Python, `cliente.connect(...)` lança `ConnectionRefusedError`. Isso acontece porque o TCP é orientado a conexão — antes de qualquer dado trafegar, o cliente precisa completar o *three-way handshake* (SYN → SYN-ACK → ACK) com um processo que esteja de fato escutando (`bind`/`listen`) naquela porta. Sem um `ServerSocket`/`socket.listen()` ativo, o sistema operacional do host de destino responde ao SYN com um pacote RST, recusando a conexão na hora, em vez de deixar a mensagem simplesmente "se perder" como aconteceria em UDP.

**2. O TCP garante que as mensagens cheguem na ordem em que foram enviadas. Qual mecanismo do protocolo é responsável por isso?**

Os **números de sequência** (sequence numbers). Cada byte enviado em uma conexão TCP recebe um número de sequência; o receptor usa esses números para reordenar segmentos que chegam fora de ordem (algo comum quando pacotes seguem rotas diferentes pela rede) antes de entregá-los à aplicação, e para identificar lacunas e solicitar retransmissão via ACKs cumulativos. É esse mecanismo — e não a ordem de chegada física dos pacotes — que garante a entrega ordenada ao nível da aplicação.

**3. Na sua implementação, o que aconteceria se dois clientes tentassem se conectar ao mesmo tempo? O código atual suporta isso? Justifique observando o código do servidor.**

Não, o código atual **não suporta** dois clientes simultâneos. O `main` do `ServidorTCP` chama `servidor.accept()` uma única vez, dentro de um único bloco `try-with-resources`: ele atende exatamente uma conexão, processa as mensagens até `sair` (ou até o cliente desconectar), e em seguida o programa termina ("Servidor encerrado."). Um segundo cliente que tentasse conectar nesse meio-tempo ficaria retido na fila de conexões pendentes do sistema operacional (o *backlog* do `ServerSocket`, que aceita a conexão a nível de TCP mesmo sem a aplicação ter chamado `accept()` de novo), mas nunca seria efetivamente atendido pela aplicação, pois o laço nunca volta a chamar `accept()`. Para suportar múltiplos clientes seria necessário colocar o `accept()` dentro de um laço `while (true)` e tratar cada conexão aceita em uma *thread* separada (ou usar I/O assíncrono), em vez do modelo atual de "uma conexão, uma execução".

---

## Parte B — UDP

**1. No passo 2 da tarefa, o que aconteceu quando você enviou uma mensagem com o servidor desligado? Compare com o que aconteceria em TCP e explique a diferença observada, relacionando com o conceito de "sem conexão".**

Testando localmente (Windows): o **cliente Java** simplesmente travou, bloqueado indefinidamente em `socket.receive()` esperando uma resposta que nunca chega — nenhum erro é lançado, porque o UDP não tem qualquer mecanismo de confirmação de entrega. Já o **cliente Python**, no mesmo cenário, recebeu uma exceção `ConnectionResetError: [WinError 10054]` na chamada seguinte a `recvfrom()` — um comportamento específico do Windows, onde o sistema operacional recebe um ICMP "Port Unreachable" (porque não há ninguém escutando naquela porta) e propaga esse aviso para a próxima leitura no socket, mesmo o UDP sendo "sem conexão". Em ambos os casos, porém, o *envio* do datagrama (`send`/`sendto`) funcionou sem erro — o cliente não tem como saber, no ato de enviar, que não há ninguém do outro lado. Em TCP, por outro lado, a falha apareceria muito antes: como a conexão já teria sido estabelecida (ou a tentativa de conexão falharia de cara, como na Parte A, pergunta 1), o próprio protocolo tem como detectar a ausência do servidor. Essa é a essência do "sem conexão": o UDP não mantém estado sobre quem está do outro lado nem confirma que a mensagem chegou — qualquer feedback de erro que você observar é um efeito colateral do sistema operacional/rede (ICMP), não uma garantia do protocolo.

**2. Cite dois exemplos de aplicações reais que usam UDP e explique, para cada uma, por que a confiabilidade do TCP não é essencial (ou até atrapalharia).**

- **DNS (consultas de nome de domínio):** cada consulta é pequena e cabe em um único datagrama; o custo de abrir uma conexão TCP completa (handshake) só para uma pergunta-resposta rapidíssima seria desproporcional. Se a resposta se perder, o cliente simplesmente reenvia a consulta — mais barato do que manter o estado de uma conexão.
- **Chamadas de voz/vídeo (VoIP, streaming ao vivo) e jogos online:** o que importa é a informação mais recente chegando o mais rápido possível. Se um pacote de áudio/vídeo/posição de jogador se perde, é melhor descartá-lo e seguir com os dados novos do que esperar a retransmissão do TCP — que, além do atraso, ainda bloquearia a entrega dos pacotes seguintes até o pacote perdido ser reenviado e reordenado (*head-of-line blocking*), introduzindo uma pausa perceptível pior do que a perda em si.

**3. No código, o servidor UDP não mantém nenhum registro de "quem está conectado". Isso seria possível de implementar? O que mudaria na arquitetura da aplicação?**

Sim, seria possível — mas seria uma construção inteiramente da aplicação, não algo que o UDP oferece nativamente. Bastaria o servidor manter uma estrutura (um `Set`/`Map` de endereço+porta) e adicionar cada remetente a ela conforme os datagramas chegam. A diferença arquitetural é que, como o UDP não tem conceito de conexão nem de "fechamento" (não existe um FIN como no TCP), o servidor nunca saberia com certeza quando um cliente saiu — precisaria implementar sua própria lógica de nível de aplicação, como mensagens periódicas de "heartbeat" e um timeout para remover clientes silenciosos da lista. Ou seja, o servidor passaria a manter **estado de sessão** por cima de um protocolo que, por definição, não tem sessão.

---

## Parte C — Multicast

**1. Qual é a diferença fundamental entre enviar a mesma mensagem para 3 clientes usando unicast repetido 3 vezes e enviar uma única vez via multicast? Pense em termos de tráfego de rede.**

No unicast repetido, o remetente gera e transmite **três cópias separadas** do mesmo pacote, uma para cada destinatário — se os três clientes compartilham um trecho de rede (por exemplo, o mesmo switch ou o mesmo enlace até o roteador), esse trecho compartilhado carrega a mesma informação três vezes, desperdiçando banda, e o custo cresce linearmente com o número de destinatários. No multicast, o remetente envia **um único pacote** endereçado ao grupo (`230.0.0.1:porta`); a replicação, quando necessária, é feita pela própria infraestrutura de rede (roteadores/switches com suporte a IGMP) apenas nos pontos onde os caminhos até os diferentes receptores efetivamente se separam. Isso significa que o enlace de saída do remetente carrega a mensagem uma única vez, independentemente de haver 3 ou 300 clientes inscritos no grupo.

**2. O que é o TTL (time-to-live) configurado no socket multicast e por que ele é importante para controlar o alcance dos pacotes na rede?**

TTL é um contador incluído no cabeçalho IP que é decrementado a cada roteador (*hop*) atravessado pelo pacote; quando chega a zero, o pacote é descartado. Em tráfego multicast, ele funciona como um limitador de **escopo/alcance**: um TTL baixo (por exemplo, 1) confina o aviso à sub-rede local, enquanto valores maiores permitem que ele atravesse mais roteadores. No código Python, o TTL é definido explicitamente (`IP_MULTICAST_TTL = 2`); em Java, o `DatagramSocket` padrão usado no `ServidorMulticast` não define TTL explicitamente (assumindo o valor padrão da plataforma, tipicamente 1). O TTL é importante porque, sem ele, um aviso multicast poderia se propagar indefinidamente pela rede (ou até para fora dela), consumindo banda em enlaces que não têm nenhum receptor interessado — é uma forma de o remetente dizer "esse aviso é só para a minha vizinhança de rede".

**3. Se um dos clientes ficar temporariamente offline e voltar depois, ele recebe os avisos que perdeu? Por quê? Relacione com a arquitetura de comunicação em grupo.**

Não. O multicast, assim como o UDP sobre o qual ele é construído, é *best-effort* e não armazena nem retransmite mensagens para quem não estava "inscrito" (com `joinGroup`/`IP_ADD_MEMBERSHIP` ativo) no momento do envio. A rede não guarda cópia da mensagem em nome de um destinatário ausente — a pertença ao grupo é definida apenas pelo estado atual do socket (via protocolo IGMP), então um cliente que sai e reentra no grupo volta a receber **apenas os avisos futuros**, a partir do momento em que rejuntou o grupo. É equivalente a uma transmissão de rádio ao vivo: quem não estava sintonizado no momento perde o conteúdo, e não há mecanismo embutido de "retomar do ponto onde parou" — isso só existiria se fosse implementado como uma camada adicional na aplicação (por exemplo, um histórico salvo em banco de dados que o cliente consulta ao reconectar).

---

## Parte D — WebSocket

**1. O WebSocket começa com uma requisição HTTP contendo o cabeçalho `Upgrade: websocket`. O que exatamente "muda" na conexão depois que esse handshake é concluído?**

A conexão TCP subjacente continua sendo a mesma (o mesmo socket, a mesma porta, o mesmo three-way handshake que já tinha ocorrido para a requisição HTTP inicial) — o que muda é o **protocolo de aplicação** que passa a interpretar os bytes trafegados nela. Depois que o servidor responde `101 Switching Protocols`, para de haver requisições/respostas HTTP: os dados passam a ser trocados como *frames* do protocolo WebSocket (RFC 6455) — um cabeçalho leve com opcode, máscara e tamanho de payload, bem mais enxuto que um cabeçalho HTTP completo — e qualquer um dos dois lados pode enviar uma mensagem a qualquer momento, sem precisar esperar uma "pergunta" do outro lado. A conexão deixa de ser uma sequência de ciclos requisição→resposta e passa a ser um canal contínuo, full-duplex, orientado a mensagens.

**2. Compare o mural via WebSocket (Parte D) com o aviso via Multicast (Parte C). Ambos entregam uma mensagem a vários destinatários — qual a diferença na forma como cada um descobre e alcança os destinatários?**

No **Multicast**, o servidor não sabe (nem precisa saber) quem são os destinatários: ele envia um único pacote para o endereço de grupo, e é a infraestrutura de rede (roteadores com suporte a IGMP) que descobre quem está inscrito e replica o pacote até eles — a descoberta e o alcance acontecem na camada de rede, de forma "invisível" para a aplicação. No **WebSocket**, não existe conceito de grupo em nível de rede: o servidor mantém explicitamente, em memória, a lista de conexões abertas (`getConnections()` em Java, o `set` `clientes_conectados` em Python) e, ao receber uma mensagem, percorre essa lista fazendo um envio individual — ponto a ponto — para cada cliente conectado. Ou seja, o "broadcast" do mural é inteiramente responsabilidade da aplicação, usando N conexões TCP confiáveis e independentes, enquanto o multicast delega a distribuição para a rede e usa, em princípio, um único envio a nível de datagrama.

**3. Por que o WebSocket é mais adequado do que TCP "cru" (como o da Parte A) para este cenário de mural em tempo real, mesmo os dois sendo, no fundo, conexões TCP contínuas?**

O TCP "cru" implementado na Parte A segue um modelo estritamente **half-duplex de requisição/resposta** dentro de uma conexão privada 1-para-1: o cliente envia uma linha, espera exatamente uma resposta, e só então pode enviar de novo — não há como o servidor empurrar uma mensagem nova para o cliente por iniciativa própria, nem como vários clientes compartilharem a mesma "conversa". O WebSocket resolve exatamente essas duas limitações: define um formato de *frame* padronizado que permite qualquer um dos lados enviar mensagens a qualquer momento (essencial para o servidor avisar "chegou um novo aviso!" sem que o cliente precise ficar perguntando), e a aplicação (como implementado no `MuralServidor`) naturalmente mantém uma lista de conexões para fazer o *broadcast*. Seria tecnicamente possível reinventar esse comportamento sobre sockets TCP crus, mas seria preciso reimplementar, sem um padrão, a própria negociação e o enquadramento de mensagens que o WebSocket já resolve — além de que o handshake HTTP inicial é o que torna o protocolo utilizável diretamente a partir de um navegador (JavaScript não consegue abrir um socket TCP cru como o da Parte A, mas consegue abrir um WebSocket).
