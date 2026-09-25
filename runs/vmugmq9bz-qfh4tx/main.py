import threading
import time

class Participante:
    def __init__(self, nome):
        self.nome = nome
        self.preparado = False
        self.comitado = False

    def preparar(self):
        print(f"{self.nome} está preparando...")
        self.preparado = True

    def comitar(self):
        print(f"{self.nome} está comitando...")
        self.comitado = True

    def abortar(self):
        print(f"{self.nome} está abortando...")
        self.comitado = False

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

    def falhar_participante(self):
        print("Falha de um participante durante o prepare...")
        for participante in self.participantes:
            if participante.preparado:
                participante.abortar()
        print("Reversão automática realizada com sucesso!")

# Crie um coordenador e dois participantes
coordenador = Coordenador([Participante("Participante 1"), Participante("Participante 2")])

# Prepare os participantes
coordenador.preparar()

# Simule a falha de um participante durante o prepare
coordenador.falhar_participante()

# Verifique se a reversão automática foi realizada com sucesso
for participante in coordenador.participantes:
    print(f"{participante.nome} está preparado: {participante.preparado}")
    print(f"{participante.nome} está comitado: {participante.comitado}")