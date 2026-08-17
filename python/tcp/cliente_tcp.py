import socket

HOST = "localhost"
PORTA = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
    cliente.connect((HOST, PORTA))
    print("[TCP] Conectado ao servidor. Digite 'sair' para encerrar.")
    arquivo = cliente.makefile("r")

    while True:
        mensagem = input("> ")
        cliente.sendall((mensagem + "\n").encode("utf-8"))
        print(arquivo.readline().strip())
        if mensagem.lower() == "sair":
            break
