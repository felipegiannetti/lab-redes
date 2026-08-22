from concurrent import futures
from datetime import datetime
import time

import grpc
import central_pb2
import central_pb2_grpc

OFFSET = 0
PORTA = 50061 + OFFSET


class CentralAtendimentoServicer(central_pb2_grpc.CentralAtendimentoServicer):
    def ConsultarHorario(self, request, context):
        horario = datetime.now().strftime("%H:%M:%S")
        print(f"[gRPC] ConsultarHorario chamado por: {request.nome_aluno}")
        return central_pb2.RespostaHorario(
            horario_atual=horario,
            mensagem=f"Olá, {request.nome_aluno}! Agora são {horario}.",
        )

    def AcompanharAvisos(self, request, context):
        print(f"[gRPC] AcompanharAvisos: {request.nome_aluno} se inscreveu.")
        for i in range(1, 6):
            yield central_pb2.Aviso(
                numero=i,
                texto=f"Aviso #{i}: a aula começa em {5 - i} minuto(s)!",
            )
            time.sleep(2)


def main():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    central_pb2_grpc.add_CentralAtendimentoServicer_to_server(CentralAtendimentoServicer(), servidor)
    servidor.add_insecure_port(f"[::]:{PORTA}")
    servidor.start()
    print(f"[gRPC] Servidor da Central ouvindo na porta {PORTA}")
    servidor.wait_for_termination()


if __name__ == "__main__":
    main()
