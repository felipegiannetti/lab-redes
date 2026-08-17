import socket

HOST = "0.0.0.0"
PORTA = 5001

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidor:
    servidor.bind((HOST, PORTA))
    print(f"[UDP] Servidor aguardando datagramas na porta {PORTA}...")

    while True:
        dados, endereco_cliente = servidor.recvfrom(1024)
        mensagem = dados.decode("utf-8")
        print(f"[UDP] Recebido de {endereco_cliente}: {mensagem}")

        resposta = f'Monitor responde: recebi sua mensagem -> "{mensagem}"'
        servidor.sendto(resposta.encode("utf-8"), endereco_cliente)
