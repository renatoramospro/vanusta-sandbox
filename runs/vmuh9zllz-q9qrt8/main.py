import threading
import time

class BancoDeDados:
    def __init__(self):
        self.dados = {}
        self.lock = threading.Lock()

    def leitura(self, id_transacao):
        with self.lock:
            return self.dados.get(id_transacao)

    def escrita(self, id_transacao, valor):
        with self.lock:
            self.dados[id_transacao] = valor

    def criar_nova_versao(self, id_transacao, valor):
        with self.lock:
            self.dados[id_transacao] = (self.dados.get(id_transacao), valor)

def transacao_leitura(id_transacao, banco_de_dados):
    valor = banco_de_dados.leitura(id_transacao)
    print(f"Leitura de {id_transacao}: {valor}")

def transacao_escrita(id_transacao, banco_de_dados):
    valor = banco_de_dados.escrita(id_transacao, "Valor novo")
    print(f"Escrita de {id_transacao}: {valor}")

def transacao_criar_nova_versao(id_transacao, banco_de_dados):
    valor = banco_de_dados.criar_nova_versao(id_transacao, "Valor novo")
    print(f"Criar nova versao de {id_transacao}: {valor}")

banco_de_dados = BancoDeDados()

# Cria 10 threads para realizar transações concorrentes
threads = []
for i in range(10):
    thread = threading.Thread(target=transacao_leitura, args=(i, banco_de_dados))
    threads.append(thread)
    thread.start()

# Espera que todas as threads terminem
for thread in threads:
    thread.join()

# Cria 10 threads para realizar transações concorrentes
threads = []
for i in range(10):
    thread = threading.Thread(target=transacao_escrita, args=(i, banco_de_dados))
    threads.append(thread)
    thread.start()

# Espera que todas as threads terminem
for thread in threads:
    thread.join()

# Cria 10 threads para realizar transações concorrentes
threads = []
for i in range(10):
    thread = threading.Thread(target=transacao_criar_nova_versao, args=(i, banco_de_dados))
    threads.append(thread)
    thread.start()

# Espera que todas as threads terminem
for thread in threads:
    thread.join()