import asyncio
import websockets

async def escutar(websocket):
    async for mensagem in websocket:
        print(f"\n{mensagem}")
        print("> ", end="", flush=True)

async def main():
    uri = "ws://localhost:8888"
    async with websockets.connect(uri) as websocket:
        print("[WebSocket] Conectado ao mural. Digite 'sair' para encerrar.")
        tarefa_escuta = asyncio.create_task(escutar(websocket))

        loop = asyncio.get_event_loop()
        while True:
            mensagem = await loop.run_in_executor(None, input, "> ")
            if mensagem.lower() == "sair":
                break
            await websocket.send(mensagem)

        tarefa_escuta.cancel()

asyncio.run(main())
