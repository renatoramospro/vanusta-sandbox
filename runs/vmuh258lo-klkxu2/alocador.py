class OutOfMemoryError(Exception):
    pass

class DoubleFreeError(Exception):
    pass

class BlocoHeap:
    def __init__(self, endereco, tamanho, livre=True):
        self.endereco = endereco
        self.tamanho = tamanho
        self.livre = livre
        self.anterior = None
        self.posterior = None

class AlocadorMemoria:
    def __init__(self, tamanho_total):
        self.tamanho_total = tamanho_total
        # Inicializa o heap com um único bloco livre cobrindo todo o espaço
        self.primeiro_bloco = BlocoHeap(endereco=0, tamanho=tamanho_total, livre=True)

    def alocar(self, tamanho):
        if tamanho <= 0:
            raise ValueError("Tamanho de alocação deve ser maior que zero.")
        
        # Estratégia First-Fit: busca o primeiro bloco livre com tamanho suficiente
        atual = self.primeiro_bloco
        while atual is not None:
            if atual.livre and atual.tamanho >= tamanho:
                # Se o bloco for maior que o necessário, faz o split
                if atual.tamanho > tamanho:
                    resto = BlocoHeap(
                        endereco=atual.endereco + tamanho,
                        tamanho=atual.tamanho - tamanho,
                        livre=True
                    )
                    resto.posterior = atual.posterior
                    resto.anterior = atual
                    if atual.posterior:
                        atual.posterior.anterior = resto
                    atual.posterior = resto
                    atual.tamanho = tamanho
                
                atual.livre = False
                return atual.endereco
            atual = atual.posterior
        raise OutOfMemoryError("Sem memória suficiente para alocação.")

    def liberar(self, endereco):
        # Encontra o bloco pelo endereço físico
        atual = self.primeiro_bloco
        while atual is not None:
            if atual.endereco == endereco:
                if atual.livre:
                    raise DoubleFreeError(f"Erro: Tentativa de liberar um bloco já livre no endereço {endereco}.")
                
                # Marca o bloco como livre
                atual.livre = True
                
                # Coalescência com o bloco posterior (se adjacente e livre)
                if atual.posterior and atual.posterior.livre:
                    proximo = atual.posterior
                    atual.tamanho += proximo.tamanho
                    atual.posterior = proximo.posterior
                    if proximo.posterior:
                        proximo.posterior.anterior = atual
                
                # Coalescência com o bloco anterior (se adjacente e livre)
                if atual.anterior and atual.anterior.livre:
                    anterior = atual.anterior
                    anterior.tamanho += atual.tamanho
                    anterior.posterior = atual.posterior
                    if atual.posterior:
                        atual.posterior.anterior = anterior
                
                return
            atual = atual.posterior
        
        raise ValueError(f"Endereço inválido para liberação: {endereco}")

if __name__ == "__main__":
    heap = AlocadorMemoria(1024)
    print("Heap inicializado com 1024 bytes.")

    # Aloca um bloco
    p1 = heap.alocar(200)
    print(ufa := f"Bloco alocado em p1={p1}")

    # Libera p1 corretamente
    heap.liberar(p1)
    print("Bloco p1 liberado com sucesso pela primeira vez.")

    # Testa a proteção contra Double Free
    try:
        heap.liberar(p1)
        assert False, "Deveria ter lançado DoubleFreeError!"
    except DoubleFreeError as e:
        print(f"Proteção ativada com sucesso: {e}")

    print("Teste executado com sucesso: Double Free interceptado e evitado!")