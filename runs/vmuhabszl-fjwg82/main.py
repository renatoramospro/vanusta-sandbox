import threading
import time

class BancoDeDados:
    def __init__(self):
        self.dados = {}
        self.lock = threading.Lock()
        self.transacoes = {}
        self.snapshots = {}

    def leitura(self, id_transacao, timestamp):
        with self.lock:
            if id_transacao in self.transacoes:
                return self.transacoes[id_transacao].get(timestamp)
            elif id_transacao in self.snapshots:
                return self.snapshots[id_transacao].get(timestamp)
            else:
                return None

    def escrita(self, id_transacao, valor, timestamp):
        with self.lock:
            if id_transacao not in self.transacoes:
                self.transacoes[id_transacao] = {}
            self.transacoes[id_transacao][timestamp] = valor
            if id_transacao not in self.snapshots:
                self.snapshots[id_transacao] = {}
            self.snapshots[id_transacao][timestamp] = valor

    def criar_nova_versao(self, id_transacao, valor, timestamp):
        with self.lock:
            if id_transacao not in self.transacoes:
                self.transacoes[id_transacao] = {}
            self.transacoes[id_transacao][timestamp] = (self.transacoes[id_transacao].get(timestamp-1), valor)
            if id_transacao not in self.snapshots:
                self.snapshots[id_transacao] = {}
            self.snapshots[id_transacao][timestamp] = valor

    def transacao_leitura(self, id_transacao, timestamp):
        valor = self.leitura(id_transacao, timestamp)
        print(f"Leitura de {id_transacao} em {timestamp}: {valor}")

    def transacao_escrita(self, id_transacao, valor, timestamp):
        self.escrita(id_transacao, valor, timestamp)
        print(f"Escrita de {id_transacao} em {timestamp}: {valor}")

    def transacao_criar_nova_versao(self, id_transacao, valor, timestamp):
        self.criar_nova_versao(id_transacao, valor, timestamp)
        print(f"Criar nova versao de {id_transacao} em {timestamp}: {valor}")

banco_de_dados = BancoDeDados()

# Cria 10 threads para realizar transações concorrentes
threads = []
for i in range(10):
    thread = threading.Thread(target=self.transacao_leitura, args=(i, 1))
    threads.append(thread)
    thread.start()

# Espera que todas as threads terminem
for thread in threads:
    thread.join()

# Cria 10 threads para realizar transações concorrentes
threads = []
for i in range(10):
    thread = threading.Thread(target=self.transacao_escrita, args=(i, "Valor novo", 2))
    threads.append(thread)
    thread.start()

# Espera que todas as threads terminem
for thread in threads:
    thread.join()

# Cria 10 threads para realizar transações concorrentes
threads = []
for i in range(10):
    thread = threading.Thread(target=self.transacao_criar_nova_versao, args=(i, "Valor novo", 3))
    threads.append(thread)
    thread.start()

# Espera que todas as threads terminem
for thread in threads:
    thread.join()