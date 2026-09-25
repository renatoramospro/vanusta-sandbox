import sqlite3
import pickle
import logging
import os

# Configuração do log AOF
logging.basicConfig(filename='aof.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Conexão com o banco de dados em memória
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Função para gravar dados no log AOF
def gravar_dados(chave, valor):
    logging.info(f'Gravando dados: {chave} - {valor}')
    with open('aof.log', 'a') as f:
        f.write(f'{chave} - {valor}\n')

# Função para recuperar dados do log AOF
def recuperar_dados():
    with open('aof.log', 'r') as f:
        linhas = f.readlines()
    dados = {}
    for linha in linhas:
        chave, valor = linha.strip().split(' - ')
        dados[chave] = valor
    return dados

# Função para testar o sistema
def testar_sistema():
    for i in range(10000):
        chave = f'chave_{i}'
        valor = f'valor_{i}'
        gravar_dados(chave, valor)
    dados = recuperar_dados()
    return dados

# Testar o sistema
dados = testar_sistema()
print(dados)