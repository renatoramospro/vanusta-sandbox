import threading
import time

class Participante:
    def __init__(self, nome):
        self.nome = nome
        self.preparado = False

    def preparar(self):
        print(f"{self.nome} está preparando...")
        self.preparado = True

    def comitar(self):
        print(f"{self.nome} está comitando...")
        # Simule a comitação da transação
        time.sleep(1)
        print(f"{self.nome} comitou com sucesso!")

    def abortar(self):
        print(f"{self.nome} está abortando...")
        # Simule a abortação da transação
        time.sleep(1)
        print(f"{self.nome} abortou com sucesso!")

class Coordenador:
    def __init__(self, participantes):
        self.participantes = participantes

    def preparar(self):
        print("Coordenador está preparando...")
        for participante in self.participantes:
            participante.preparar()
        print("Todos os participantes estão preparados!")

    def comitar(self):
        print("Coordenador está comitando...")
        for participante in self.participantes:
            participante.comitar()
        print("Todas as transações foram comitadas com sucesso!")

    def abortar(self):
        print("Coordenador está abortando...")
        for participante in self.participantes:
            participante.abortar()
        print("Todas as transações foram abortadas com sucesso!")

# Crie um coordenador e dois participantes
coordenador = Coordenador([Participante("Participante 1"), Participante("Participante 2")])

# Prepare os participantes
coordenador.preparar()

# Comita as transações
coordenador.comitar()

# Aborta as transações
coordenador.abortar()