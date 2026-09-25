import pandas as pd
import nltk
from nltk.tokenize import word_tokenize

# Carregar documentos
documentos = pd.read_csv('documentos.csv')

# Tokenizar documentos
tokens = []
for documento in documentos['texto']:
    tokens.extend(word_tokenize(documento))

# Construir índice invertido
índice_invertido = {}
for token in tokens:
    if token not in índice_invertido:
        índice_invertido[token] = []
    índice_invertido[token].append(documentos['id'][tokens.index(token)])

# Executar consulta de busca
def buscar(consulta):
    tokens_consulta = word_tokenize(consulta)
    resultados = set()
    for token in tokens_consulta:
        if token in índice_invertido:
            resultados.update(índice_invertido[token])
    return resultados

# Testar consulta de busca
consulta = 'palavra1 palavra2'
resultados = buscar(consulta)
print(resultados)