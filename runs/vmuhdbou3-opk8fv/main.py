import asyncio
import random

class Actor:
    def __init__(self, name):
        self.name = name
        self.state = None

    async def process_message(self, message):
        # Processa a mensagem e atualiza o estado do ator
        print(f"Autor {self.name} processou a mensagem {message}")

class Message:
    def __init__(self, type, content):
        self.type = type
        self.content = content

class GerenciadorDeConcorrência:
    def __init__(self):
        self.atores = []

    async def criar_atore(self, name):
        # Cria um novo ator e adiciona à lista de atores
        ator = Actor(name)
        self.atores.append(ator)
        return ator

    async def enviar_mensagem(self, ator, message):
        # Envia a mensagem para o ator
        print(f"Enviando mensagem {message} para o autor {ator.name}")
        await ator.process_message(message)

async def main():
    gerenciador = GerenciadorDeConcorrência()
    ator1 = await gerenciador.criar_atore("A1")
    ator2 = await gerenciador.criar_atore("A2")

    mensagens = [Message("Tipo1", "Conteúdo1"), Message("Tipo2", "Conteúdo2")]
    for mensagem in mensagens:
        await gerenciador.enviar_mensagem(ator1, mensagem)
        await gerenciador.enviar_mensagem(ator2, mensagem)

    # Simula falha crítica
    ator1.state = None

    # Recupera o ator
    ator1.state = "Recuperado"

    await asyncio.sleep(1)

    print("Fim do programa")

asyncio.run(main())