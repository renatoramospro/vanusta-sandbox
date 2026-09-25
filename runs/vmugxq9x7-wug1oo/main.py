import os
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Lista de servidores de backend
servidores = ['servidor1', 'servidor2', 'servidor3']

# Variável para armazenar o servidor atual
servidor_atual = None

# Função para distribuir carga round-robin
def distribuir_carga():
    global servidor_atual
    servidor_atual = servidores[(servidores.index(servidor_atual) + 1) % len(servidores)]

# Função para realizar failover automático
def failover():
    global servidor_atual
    if servidor_atual is None:
        servidor_atual = servidores[0]
    else:
        servidor_atual = servidores[(servidores.index(servidor_atual) + 1) % len(servidores)]

# Função para processar requisições HTTP
@app.route('/', methods=['GET'])
def processar_requisicao():
    global servidor_atual
    distribuir_carga()
    servidor = servidor_atual
    resposta = f'Requisição processada pelo servidor {servidor}'
    return jsonify({'resposta': resposta})

# Função para realizar failover automático
@app.errorhandler(500)
def failover_erro(erro):
    failover()
    return jsonify({'resposta': 'Failover automático realizado'})

if __name__ == '__main__':
    app.run(debug=True)