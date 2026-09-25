import asyncio
import json
from aiohttp import web

# Configuração de ambiente
app = web.Application()

# Variável para armazenar o último ID de evento
last_event_id = 0

# Função para gerar eventos
async def gerar_eventos():
    global last_event_id
    while True:
        # Geração de evento
        evento = {
            "id": last_event_id,
            "tipo": "evento",
            "dados": "Dados do evento"
        }
        # Formatação do evento
        evento_str = json.dumps(evento) + "\n\n"
        # Envio do evento
        yield evento_str
        # Atualização do último ID de evento
        last_event_id += 1

# Função para lidar com requisições SSE
async def handle_sse(request):
    # Configuração de headers
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
    # Envio de eventos
    async for evento in gerar_eventos():
        await request.write(evento.encode())
    # Retorno de resposta
    return web.Response(headers=headers)

# Rota para endpoint SSE
app.router.add_get("/sse", handle_sse)

# Inicialização do servidor
if __name__ == "__main__":
    web.run_app(app, port=8080)