# Respostas — Central de Atendimento da Turma via gRPC

> Rascunho de respostas elaborado com apoio de IA (Claude/Anthropic) a partir do código
> implementado e de testes reais executados durante o desenvolvimento (conforme nota de
> transparência do roteiro). Revise, personalize com suas próprias palavras e esteja
> pronto para defender qualquer trecho antes de entregar.

## Parte A — Transparências em Sistemas Distribuídos

### 4.1 Tarefa — revisão do laboratório anterior (`lab-redes`)

**TCP**

1. O endereço do servidor está escrito diretamente no código do cliente: `HOST = "localhost"` (Python) / `String host = "localhost"` (Java), uma constante fixa. Isso **prejudica** a transparência de localização — o cliente só funciona porque "sabe", em tempo de compilação, exatamente onde o servidor está.
2. Sim: o cliente monta a mensagem como uma string de texto crua (`saida.println(linha)` / `cliente.sendall((mensagem + "\n").encode(...))`) e o servidor faz o "parsing" comparando a string recebida (`equalsIgnoreCase("hora")`, `dados.lower() == "hora"`). Isso é **ausência** de transparência de acesso — não existe nenhuma abstração escondendo que se trata de bytes trafegando por um socket; o "formato da mensagem" é uma convenção informal entre quem escreveu o cliente e quem escreveu o servidor.
3. O cliente pararia de funcionar (`ConnectException`/`ConnectionRefusedError`) e exigiria alterar o código-fonte (`HOST`) para apontar para o novo endereço. Não sobrevive à mudança.

**UDP**

1. Mesma situação do TCP: `HOST = "localhost"` fixo no cliente. Prejudica a transparência de localização.
2. Sim, mesma resposta do TCP — mensagens de texto cru, parsing manual por comparação de string. Ausência de transparência de acesso.
3. Mesma resposta do TCP: quebra, exige editar o código-fonte do cliente.

**Multicast**

1. Aqui é diferente: o cliente não aponta para uma *máquina*, e sim para um **grupo lógico** (`GRUPO_MULTICAST = "230.0.0.1"`). Isso ainda é um endereço fixo no código (não é automaticamente descoberto), mas é qualitativamente diferente — o cliente nunca precisa saber em qual máquina o servidor está rodando, só precisa saber o grupo. É a solução das quatro que mais se aproxima de transparência de localização, mesmo sem alcançá-la totalmente.
2. Sim — as mensagens continuam sendo texto cru (`mensagem.getBytes()` / `.encode("utf-8")`), sem nenhuma estrutura imposta pelo protocolo. Ausência de transparência de acesso, igual às anteriores.
3. Esta é a **única das quatro** que sobreviveria parcialmente: se o servidor mudasse de máquina física mas continuasse enviando para o mesmo grupo/porta multicast, os clientes inscritos continuariam recebendo os avisos sem qualquer alteração de código — porque o que importa para o cliente é o grupo, não o host de origem.

**WebSocket**

1. `uri = "ws://localhost:8888"` — também fixo no cliente, e aqui já formalizado como uma URL com protocolo (`ws://`), mas ainda assim hardcoded. Prejudica a transparência de localização, na mesma medida do TCP/UDP.
2. Sim — as mensagens trocadas continuam sendo strings de texto simples (`"Aviso da turma: " + mensagem`), sem serialização estruturada; o cliente e o servidor concordam informalmente sobre o que cada string representa. Ausência de transparência de acesso.
3. Quebra, exige editar o código-fonte do cliente — mesma situação do TCP/UDP.

**Conclusão da tarefa 4.1:** das quatro soluções "na mão", nenhuma esconde completamente a localização do servidor, e nenhuma esconde que a comunicação é uma troca de texto interpretada manualmente. O Multicast é a exceção parcial em transparência de localização (por usar um grupo, não uma máquina), mas mesmo ele não tem transparência de acesso — nas quatro, o programador está o tempo todo "pensando em rede" (sockets, `send`/`receive`, parsing de string).

## 4.3 Perguntas — Parte A

**1. Dentre os 8 tipos de transparência, qual é a mais visível para o programador que está *usando* um serviço remoto (não construindo a infraestrutura)? Justifique.**

Eu diria a **transparência de acesso**. É a que o programador sente a cada linha de código que escreve: ao chamar `stub.consultarHorario(pergunta)`, a pergunta "isso é uma chamada local ou remota?" desaparece da sintaxe — parece uma chamada de método comum, com parâmetros e retorno tipados. É a transparência que mais afeta diretamente a experiência de programar contra o serviço, porque está presente em toda chamada, não só em situações excepcionais (diferente de, por exemplo, a transparência de falha, que só "aparece" quando algo dá errado).

**2. Transparência total é sempre desejável? Dê um exemplo em que esconder completamente que uma operação é remota atrapalharia mais do que ajudaria.**

Não. Um exemplo clássico: imagine um `stub.transferirSaldo(contaOrigem, contaDestino, valor)` de um sistema bancário, projetado para parecer *exatamente* uma chamada de função local — ou seja, sob a premissa de que ela "sempre executa por completo, ou não executa nada" (a mesma garantia que uma chamada local tem, já que não há rede no meio). Só que chamadas remotas podem falhar de formas que uma chamada local nunca falha: o pacote de requisição pode se perder (nada aconteceu), ou a requisição pode ter sido processada com sucesso no servidor mas a *resposta* se perder no caminho de volta (o cliente não tem como distinguir os dois casos). Se a transparência de falha for total — o cliente é levado a acreditar que só existem os desfechos "sucesso" ou "erro claro", como numa chamada local — o programador nunca vai escrever a lógica de idempotência/reconciliação necessária para não transferir o valor duas vezes numa política de retry. Esconder bem demais que a chamada é remota, aqui, esconde justamente a informação que o programador mais precisa para lidar com falha parcial. O mesmo vale, de forma mais branda, para desempenho: se uma chamada remota "parece" tão barata quanto uma local, é fácil cair em padrões como chamar o serviço em loop (o equivalente distribuído do problema N+1) sem perceber o custo de rede embutido em cada chamada.

**3. (Responder depois de C e D) Comparando o `ClienteTCP` do laboratório anterior com o `ClienteCentral` (gRPC): qual exige "pensar em rede" e qual permite "pensar no problema"? A que transparência isso se relaciona?**

O `ClienteTCP` exige pensar em rede o tempo todo: abrir um `Socket`, criar um `PrintWriter`/`BufferedReader`, montar a mensagem concatenando strings (`saida.println(linha)`), e depois interpretar manualmente a resposta lendo uma linha de texto (`entrada.readLine()`) e decidindo, por comparação de string, o que ela significa. O `ClienteCentral` (gRPC) permite pensar no problema: `PerguntaHorario pergunta = PerguntaHorario.newBuilder().setNomeAluno(nome).build(); RespostaHorario resposta = stub.consultarHorario(pergunta);` — o programador preenche um objeto tipado e recebe outro objeto tipado de volta; a existência de uma rede, de uma serialização binária e de uma conexão HTTP/2 por baixo é irrelevante para escrever essa linha. Isso se relaciona diretamente com a **transparência de acesso**: no TCP cru ela é praticamente ausente (o programador manipula a representação/o protocolo diretamente); no gRPC ela é alta (a chamada remota tem a mesma "forma" de uma chamada de método local, com o protobuf cuidando de toda a representação/serialização por trás dela).

---

## Parte B — Protocol Buffers e o contrato do serviço

**1. Qual a vantagem de ter o contrato explícito em `central.proto`, gerado automaticamente, em vez de combinado apenas "de boca" (como no laboratório anterior)?**

No laboratório anterior, se um dos dois lados (cliente ou servidor) mudasse o formato da mensagem — por exemplo, o nome de um campo ou a ordem dos dados numa string — nada impedia isso de acontecer silenciosamente; o erro só apareceria em tempo de execução, como uma mensagem mal interpretada ou um `NullPointerException`. Com o `.proto`, o formato das mensagens é definido uma única vez e o código de cliente e servidor é *gerado* a partir dele — ou seja, é literalmente impossível que cliente e servidor divirjam sobre o formato dos dados, porque os dois nascem do mesmo arquivo-fonte. Além disso, o gerador já resolve toda a serialização/desserialização (que no roteiro anterior foi escrita manualmente com `getBytes()`/`decode("utf-8")`, fonte comum de bugs de codificação), e o `.proto` funciona como documentação viva da interface — não depende de comentários no código ou de "perguntar pro colega como o servidor espera a mensagem".

**2. O mesmo `central.proto` gerou código para Java e para Python. O que isso sugere sobre como equipes que usam linguagens diferentes podem se comunicar em um sistema distribuído real?**

Sugere que a linguagem de implementação deixa de ser uma barreira de integração: cada equipe (ou cada serviço, num cenário de microsserviços) pode escolher a linguagem mais adequada ao seu contexto, desde que todos gerem seu código a partir do mesmo contrato compartilhado. É exatamente o modelo usado em arquiteturas poliglotas reais — um serviço em Go conversando com um serviço em Python e um cliente mobile em Kotlin, todos gerados a partir da mesma definição `.proto`, sem que nenhum deles precise conhecer detalhes de implementação dos outros.

**3. Nos arquivos gerados, onde ficam definidas as operações `ConsultarHorario` e `AcompanharAvisos`? Cite ao menos uma classe/método reconhecido.**

Em Java, a classe **`CentralAtendimentoGrpc`** (gerada em `target/generated-sources/protobuf/grpc-java/.../CentralAtendimentoGrpc.java`) contém a classe aninhada **`CentralAtendimentoImplBase`**, que o servidor estende e sobrescreve com os métodos `consultarHorario(...)` e `acompanharAvisos(...)`, e as classes **`CentralAtendimentoBlockingStub`**/**`CentralAtendimentoStub`**, usadas pelo cliente para chamar essas mesmas operações. Em Python, o arquivo **`central_pb2_grpc.py`** define a classe **`CentralAtendimentoServicer`** (com os métodos `ConsultarHorario` e `AcompanharAvisos` que o servidor implementa), a classe **`CentralAtendimentoStub`** (usada pelo cliente) e a função **`add_CentralAtendimentoServicer_to_server`**, que registra o serviço no servidor gRPC.

---

## Parte C — RPC unário: ConsultarHorario

**1. `stub.consultarHorario(pergunta)` parece uma chamada de método comum. Cite pelo menos três coisas que acontecem "por baixo dos panos" entre essa chamada e o `return` no servidor.**

- A mensagem `PerguntaHorario` é **serializada** para um formato binário compacto (Protocol Buffers), não trafega como objeto Java/Python.
- Os bytes serializados são enviados através de uma conexão **HTTP/2** já estabelecida entre cliente e servidor (o `ManagedChannel`/`grpc.insecure_channel`), que multiplexa múltiplas chamadas na mesma conexão TCP.
- No lado do servidor, a requisição é **roteada** até o método correto (`consultarHorario`) com base no nome do serviço/RPC identificado no cabeçalho da chamada — é o gRPC "despachando" a chamada para a implementação registrada.
- O método roda numa **thread do pool de execução** do servidor (o `ThreadPoolExecutor` em Python; um executor interno equivalente em Java), não na thread principal.
- A resposta `RespostaHorario` é serializada de volta e enviada pela mesma conexão, e o cliente a **desserializa** de volta para um objeto tipado antes de retornar da chamada `stub.consultarHorario(...)`.

**2. Onde estava, no TCP, o equivalente a "montar a mensagem" e "interpretar a resposta"? Quem faz esse trabalho agora, no gRPC?**

No `ClienteTCP`, "montar a mensagem" era a linha `saida.println(linha)` (uma string concatenada manualmente) e "interpretar a resposta" era `System.out.println(entrada.readLine())` combinado com a lógica de decidir o que aquele texto significava — tudo escrito à mão pelo programador. No gRPC, esse trabalho é feito pelo **código gerado** a partir do `.proto`: o programador só preenche um builder tipado (`PerguntaHorario.newBuilder().setNomeAluno(nome).build()`) e lê campos tipados da resposta (`resposta.getMensagem()`); toda a serialização/desserialização real fica a cargo do runtime do Protocol Buffers e do gRPC, não do código da aplicação.

**3. O que aconteceria se você chamasse `stub.consultarHorario(pergunta)` com o servidor desligado? Teste e descreva.**

Testei em Java: a chamada falha **imediatamente** com uma exceção `StatusRuntimeException: UNAVAILABLE: io exception: Connection refused: getsockopt: localhost/[0:0:0:0:0:0:0:1]:50051`. Diferente do UDP cru do laboratório anterior (onde o cliente Java simplesmente travava esperando uma resposta que nunca chegaria), o gRPC detecta a falha de conexão rapidamente e a propaga como um **status estruturado e padronizado** (`UNAVAILABLE`), que o código do cliente pode capturar explicitamente com um `try/catch` — um comportamento muito mais previsível e tratável do que o silêncio do UDP.

---

## Parte D — RPC com streaming de servidor: AcompanharAvisos

**1. Se você quisesse que vários clientes gRPC recebessem os mesmos avisos ao mesmo tempo, o que precisaria mudar na implementação do servidor?**

Do jeito que está implementado, cada chamada a `acompanharAvisos`/`AcompanharAvisos` gera sua *própria* sequência de 5 avisos, independente para cada cliente (uma conexão HTTP/2 por chamada, sem relação entre clientes diferentes) — não é broadcast, é um stream individual repetido para quem quer que chame. Para que vários clientes recebessem exatamente os **mesmos** avisos, ao mesmo tempo, seria preciso desacoplar a *origem* dos avisos do *envio* a cada cliente: o servidor manteria uma lista de `StreamObserver`s (Java) / contextos (Python) ativos — exatamente como fizemos "na mão" no `MuralServidor` de WebSocket do laboratório anterior, com `getConnections()` — e, quando um novo aviso fosse gerado (por exemplo, por um publicador central ou uma fila), o servidor percorreria essa lista chamando `onNext()` em cada uma. O gRPC streaming, por padrão, é 1 chamada : 1 stream; broadcast é responsabilidade da aplicação, não algo que o framework dá de graça.

**2. Compare o `StreamObserver`/`onNext()` (Java) com a função geradora `yield` (Python). Qual abordagem você achou mais natural? Justifique.**

A versão em Python (`yield`) pareceu mais natural: ela usa uma abstração que já existe na linguagem para "produzir uma sequência de valores ao longo do tempo" (um gerador comum), então o método de streaming se lê quase como uma função síncrona normal que "pausa" a cada `yield`, sem precisar de nenhum objeto/callback explícito. A versão em Java, com `StreamObserver` e chamadas explícitas a `onNext()`/`onCompleted()`/`onError()`, é mais verbosa, mas também deixa mais explícito o ciclo de vida da chamada (é fácil ver, no código, os três desfechos possíveis de cada evento enviado) — algo que pode ajudar em cenários que exigem tratamento de erro mais granular. Para um primeiro contato com streaming, porém, o `yield` do Python exige menos conceitos novos.

**3. O que aconteceria se o cliente fechasse a conexão no meio do envio dos 5 avisos? Testei o comportamento em Python.**

Testei: derrubei o processo do cliente Python à força depois de ele receber apenas 2 dos 5 avisos (`timeout 3 python cliente_central.py`). No log do servidor, **nada de anormal apareceu** — nenhuma exceção, nenhum erro impresso — o método `AcompanharAvisos` simplesmente parou de ser "puxado" pelo framework: o `yield` seguinte nunca é retomado, porque o gRPC detecta que o contexto da chamada foi cancelado (a conexão HTTP/2 daquele stream específico caiu) e encerra a execução do generator silenciosamente, sem propagar nada para o código da aplicação (que não tinha nenhum `try/except` em volta do `yield`). Confirmei também que o **servidor continuou saudável**: uma nova chamada de um cliente diferente, logo em seguida, funcionou normalmente. Ou seja, o gRPC isola bem a falha de um stream individual — ela não derruba o servidor nem afeta outras chamadas.
