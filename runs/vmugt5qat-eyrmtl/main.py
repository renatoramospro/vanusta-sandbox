import threading
import time
import random

class Conexao:
    def __init__(self):
        self.disponivel = True
        self.lock = threading.Lock()

    def conectar(self):
        with self.lock:
            if self.disponivel:
                self.disponivel = False
                return True
            else:
                return False

    def desconectar(self):
        with self.lock:
            self.disponivel = True

class PoolConexoes:
    def __init__(self, max_conexoes):
        self.max_conexoes = max_conexoes
        self.conexoes = [Conexao() for _ in range(max_conexoes)]
        self.lock = threading.Lock()

    def obter_conexao(self):
        with self.lock:
            for conexao in self.conexoes:
                if conexao.conectar():
                    return conexao
            return None

    def liberar_conexao(self, conexao):
        with self.lock:
            conexao.desconectar()

def teste_conexao(pool, conexao):
    if conexao is None:
        print("Não foi possível obter uma conexão")
    else:
        print("Conexão obtida com sucesso")
        time.sleep(random.randint(1, 5))
        pool.liberar_conexao(conexao)

def teste_estresse(pool, num_threads):
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=teste_conexao, args=(pool, pool.obter_conexao()))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

pool = PoolConexoes(10)
teste_estresse(pool, 100)