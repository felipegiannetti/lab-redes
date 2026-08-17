import asyncio
import websockets

clientes_conectados = set()

async def tratar_conexao(websocket):
    clientes_conectados.add(websocket)
    print(f"[WebSocket] Novo aluno conectado. Total: {len(clientes_conectados)}")
    await websocket.send("Bem-vindo(a) ao mural de avisos da turma!")
    try:
        async for mensagem in websocket:
            print(f"[WebSocket] Recebido: {mensagem}")
            aviso_formatado = f"Aviso da turma: {mensagem}"
            websockets.broadcast(clientes_conectados, aviso_formatado)
    finally:
        clientes_conectados.remove(websocket)
        print(f"[WebSocket] Aluno desconectado. Total: {len(clientes_conectados)}")

async def main():
    print("[WebSocket] Servidor do mural iniciado na porta 8888.")
    async with websockets.serve(tratar_conexao, "0.0.0.0", 8888):
        await asyncio.Future()  # mantém o servidor rodando indefinidamente

asyncio.run(main())
