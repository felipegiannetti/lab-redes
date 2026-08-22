import grpc
import central_pb2
import central_pb2_grpc

OFFSET = 0
PORTA = 50061 + OFFSET


def main():
    canal = grpc.insecure_channel(f"localhost:{PORTA}")
    stub = central_pb2_grpc.CentralAtendimentoStub(canal)

    nome = input("Digite seu nome: ")

    # Chamada unária: parece uma chamada de função local, mas atravessa a rede
    resposta = stub.ConsultarHorario(central_pb2.PerguntaHorario(nome_aluno=nome))
    print(f"[gRPC] {resposta.mensagem}")

    # Chamada com streaming: o servidor envia vários Avisos ao longo do tempo
    print("[gRPC] Inscrevendo-se para acompanhar avisos...")
    for aviso in stub.AcompanharAvisos(central_pb2.InscricaoAvisos(nome_aluno=nome)):
        print(f"[gRPC] Recebido: {aviso.texto}")


if __name__ == "__main__":
    main()
