import threading
import random
import time

# Variáveis compartilhadas
saldo = 0
lock_pessimista = threading.Lock()
lock_otimista = threading.Lock()
versao = 0

def atualizar_saldo_pessimista():
    global saldo
    global lock_pessimista
    with lock_pessimista:
        saldo += 1

def atualizar_saldo_otimista():
    global saldo
    global lock_otimista
    global versao
    while True:
        try:
            with lock_otimista:
                if versao != get_version():
                    versao = get_version()
                    saldo += 1
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(1)

def get_version():
    return random.randint(1, 100)

def main():
    threads_pessimista = []
    threads_otimista = []

    for _ in range(50):
        thread_pessimista = threading.Thread(target=atualizar_saldo_pessimista)
        thread_pessimista.start()
        threads_pessimista.append(thread_pessimista)

        thread_otimista = threading.Thread(target=atualizar_saldo_otimista)
        thread_otimista.start()
        threads_otimista.append(thread_otimista)

    for thread in threads_pessimista:
        thread.join()

    for thread in threads_otimista:
        thread.join()

    print(f"Saldo final: {saldo}")

if __name__ == "__main__":
    main()