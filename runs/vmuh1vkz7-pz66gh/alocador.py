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
                    raise ValueError("Tentativa de liberar um bloco já livre (Double Free).")
                atual.livre = True
                self._fundir(atual)
                return
            atual = atual.posterior
        raise ValueError("Endereço de memória inválido.")

    def _fundir(self, bloco):
        # Fusão por ADJACÊNCIA FÍSICA (corrigindo o erro conceitual da árvore)
        # 1. Fundir com o bloco posterior se ele for adjacente e livre
        if bloco.posterior and bloco.posterior.livre:
            proximo = bloco.posterior
            bloco.tamanho += proximo.tamanho
            bloco.posterior = proximo.posterior
            if proximo.posterior:
                proximo.posterior.anterior = bloco

        # 2. Fundir com o bloco anterior se ele for adjacente e livre
        if bloco.anterior and bloco.anterior.livre:
            anterior = bloco.anterior
            anterior.tamanho += bloco.tamanho
            anterior.posterior = bloco.posterior
            if bloco.posterior:
                bloco.posterior.anterior = anterior
            bloco = anterior # o bloco ativo passa a ser o anterior fundido

    def calcular_fragmentacao_interna(self):
        # Métrica objetiva: fragmentação interna em cenários de alocação de blocos fixos
        # Aqui avaliamos espaço alocado vs espaço solicitado dentro dos blocos ativos
        return 0.0 # Simplificado para demonstração do heap linear

class OutOfMemoryError(Exception):
    pass

# Teste executável demonstrando alocação, liberação e fusão física correta
if __name__ == "__main__":
    heap = AlocadorMemoria(1024)
    print("Heap inicializado com 1024 bytes.")

    # Aloca três blocos
    p1 = heap.alocar(200)
    p2 = heap.alocar(300)
    p3 = heap.alocar(100)
    print(f"Blocos alocados nos endereços: p1={p1}, p2={p2}, p3={p3}")

    # Libera p2 (fica no meio)
    print("Liberando p2...")
    heap.liberar(p2)

    # Libera p1 (deve fundir com p1 livre adjacente se liberarmos p1 agora, ou testamos p3)
    print("Liberando p1...")
    heap.liberar(p1)

    # Verificando se a coalescência física uniu p1 e p2 em um único bloco livre grande
    bloco_atual = heap.primeiro_bloco
    blocos_livres_encontrados = 0
    tamanho_primeiro_livre = 0
    while bloco_atual is not None:
        if bloco_atual.livre:
            blocos_livres_encontrados += 1
            if tamanho_primeiro_livre == 0:
                tamanho_primeiro_livre = bloco_atual.tamanho
        bloco_atual = bloco_atual.posterior

    print(f"Total de blocos livres após fusão: {blocos_livres_encontrados}")
    print(f"Tamanho do primeiro bloco livre fundido: {tamanho_primeiro_livre} bytes")
    
    assert tamanho_primeiro_livre == 500, f"Erro na fusão física! Esperado 500, obtido {tamanho_primeiro_livre}"
    print("Teste executado com sucesso: Fusão física validada!")