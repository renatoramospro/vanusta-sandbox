path=protocolo_confiavel.py
import socket
import random
import time

# Constantes
HOST = 'localhost'
PORT = 12345
PERDA = 0.1  # 10% de perda

# Criar socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Função para enviar pacotes UDP
def enviar_pacote(pacote):
    sock.sendto(pacote.encode(), (HOST, PORT))

# Função para receber pacotes UDP
def receber_pacote():
    return sock.recvfrom(1024).decode()

# Função para reordenar pacotes
def reordenar_pacotes(pacotes):
    pacotes_reordenados = []
    for pacote in pacotes:
        pacotes_reordenados.append(pacote)
    return pacotes_reordenados

# Simular perda de pacotes
def simular_perda(pacotes):
    pacotes_perdidos = []
    for pacote in pacotes:
        if random.random() < PERDA:
            pacotes_perdidos.append(pacote)
    return pacotes_perdidos

# Simular reordenamento de pacotes
def simular_reordenamento(pacotes):
    pacotes_reordenados = []
    for pacote in pacotes:
        pacotes_reordenados.append(pacote)
    return pacotes_reordenados

# Main
if __name__ == '__main__':
    pacotes = []
    for i in range(10):
        pacote = f'Pacote {i}'
        pacotes.append(pacote)

    # Enviar pacotes UDP
    for pacote in pacotes:
        enviar_pacote(pacote)
        time.sleep(1)

    # Receber pacotes UDP
    pacotes_recebidos = []
    for i in range(10):
        pacote = receber_pacote()
        pacotes_recebidos.append(pacote)

    # Reordenar pacotes
    pacotes_reordenados = reordenar_pacotes(pacotes_recebidos)

    # Simular perda de pacotes
    pacotes_perdidos = simular_perda(pacotes_reordenados)

    # Simular reordenamento de pacotes
    pacotes_reordenados_final = simular_reordenamento(pacotes_perdidos)

    # Imprimir pacotes reordenados
    for pacote in pacotes_reordenados_final:
        print(pacote)