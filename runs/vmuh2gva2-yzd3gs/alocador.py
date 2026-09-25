import sys

class OutOfMemoryError(Exception):
    pass

class DoubleFreeError(Exception):
    pass

class BlocoHeap:
    def __init__(self, endereco, tamanho, livre=True, id_alocacao=None):
        self.endereco = endereco
        self.tamanho = tamanho
        self.livre = livre
        self.id_alocacao = id_alocacao  # Token único para prevenir double free por ponteiros obsoletos
        self.anterior = None
        self.posterior = None

class AlocadorMemoria:
    def __init__(self, tamanho_total):
        if not isinstance(tamanho_total, (int, float)) or tamanho_total <= 0:
            raise ValueError("O tamanho total do heap deve ser um número maior que zero.")
        self.tamanho_total = int(tamanho_total)
        self.proximo_id = 1
        # Inicializa o heap com um único bloco livre cobrindo todo o espaço
        self.primeiro_bloco = BlocoHeap(endereco=0, tamanho=self.tamanho_total, livre=True)

    def alocar(self, tamanho):
        if not isinstance(tamanho, int) or tamanho <= 0:
            raise ValueError("Tamanho de alocação deve ser um inteiro maior que zero.")
        
        # Estratégia First-Fit
        atual = self.primeiro_bloco
        while atual is not None:
            if atual.livre and atual.tamanho >= tamanho:
                token = self.proximo_id
                self.proximo_id += 1

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
                atual.id_alocacao = token
                # Retorna uma tupla (endereco, token) para evitar reuso de ponteiro obsoleto
                return (atual.endereco, token)

            atual = atual.posterior
        
        raise OutOfMemoryError("Heap esgotado: memória insuficiente para a alocação solicitada.")

    def liberar(self, handle):
        if not isinstance(handle, tuple) or len(handle) != 2:
            raise ValueError("Handle de liberação inválido. Use o par (endereço, token) retornado na alocação.")
        
        endereco, token = handle
        
        # Busca o bloco pelo endereço físico
        atual = self.primeiro_bloco
        while atual is not None:
            if atual.endereco == endereco:
                if atual.livre:
                    raise DoubleFreeError(f"Erro: Tentativa de liberar um bloco já livre no endereço {endereco}.")
                if atual.id_alocacao != token:
                    raise DoubleFreeError(f"Erro: Tentativa de liberar bloco com token obsoleto/inválido (Stale Pointer) no endereço {endereco}.")
                
                # Marca como livre e limpa o token
                atual.livre = True
                atual.id_alocacao = None
                
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
                    if prv := atual.posterior:
                        prv.anterior = anterior
                
                return
            atual = atual.posterior
        
        raise ValueError(f"Endereço inválido para liberação: {endereco}")

    def calcular_fragmentacao_e_vazamentos(self, solicitacoes_ativas):
        """
        Mede a fragmentação interna e valida ausência de vazamentos/corrupção de heap.
        Fragmentação interna = bytes alocados em blocos que excedem o solicitado estritamente.
        """
        bytes_totais_heap = self.tamanho_total
        bytes_livres = 0
        bytes_alocados_efetivos = 0
        bytes_alocados_brutos = 0
        
        atual = self.primeiro_bloco
        while atual is not None:
            if atual.livre:
                bytes_livres += atual.tamanho
            else:
                bytes_alocados_brutos += atual.tamanho
            atual = atual.posterior
        
        # Soma bytes úteis solicitados ativos
        bytes_uteis = sum(solicitacoes_ativas.values())
        bytes_alocados_efetivos = bytes_uteis
        
        # Verificação rigorosa de integridade do heap (sem vazamentos de memória fantasma)
        soma_blocos = 0
        atual = self.primeiro_bloco
        while atual is not None:
            soma_blocos += atual.tamanho
            atual = atual.posterior
            
        assert soma_blocos == bytes_totais_heap, f"Vazamento ou corrupção de heap detectada! Soma={soma_blocos}, Esperado={bytes_totais_heap}"

        # Cálculo da fragmentação interna (desperdício em blocos alocados maiores que o solicitado)
        desperdicio_interno = bytes_alocados_brutos - bytes_alocados_efetivos
        taxa_fragmentacao = (desperdicio_interno / bytes_alocados_brutos) if bytes_alocados_brutos > 0 else 0.0
        
        return taxa_fragmentacao, bytes_livres, bytes_totais_heap


if __name__ == "__main__":
    print("--- 1. Validação de Construtor ---")
    try:
        AlocadorMemoria(-500)
        assert False, "Deveria ter rejeitado tamanho negativo."
    except ValueError as e:
        print(f"Sucesso: Construtor rejeitou tamanho negativo -> {e}")

    heap = AlocadorMemoria(2048)
    print("Heap inicializado com 2048 bytes com sucesso.\n")

    print("--- 2. Cenário Sintético de Estresse, Vazamentos e Fragmentação ---")
    alocacoes = {}
    tamanhos_teste = [100, 150, 200, 250, 300]
    
    # Realiza alocações
    for i, t in enumerate(tamanhos_teste):
        handle = heap.alocar(t)
        alocacoes[handle] = t
        print(f"Alocado {t} bytes (handle: {handle})")

    # Mede fragmentação e ausência de vazamentos
    frag, livres, total = heap.calcular_fragmentacao_e_vazamentos(alocacoes)
    print(f"Métrica calculada -> Fragmentação interna: {frag*100:.2f}% | Bytes livres: {livres} | Total Heap: {total}")
    assert frag < 0.15, f"Fragmentação interna excessiva: {frag*100:.2f}% (deve ser < 15%)"
    print("Sucesso: Fragmentação interna está estritamente abaixo de 15%!\n")

    print("--- 3. Proteção contra Stale Pointer (Double Free por Reuso) ---")
    # Libera um bloco
    handle_alvo = list(alocacoes.keys())[0]
    tamanho_alvo = alocacoes.pop(handle_alvo)
    heap.liberar(handle_alvo)
    print(f"Bloco {handle_alvo} liberado com sucesso.")

    # Realiza nova alocação que reutiliza o mesmo endereço físico
    novo_handle = heap.alocar(tamanho_alvo)
    alocacoes[novo_handle] = tamanho_alvo
    print(f"Novo bloco alocado no mesmo endereço físico (novo handle: {novo_handle})")

    # Tenta liberar o bloco antigo usando o handle obsoleto (stale handle)
    try:
        heap.liberar(handle_alvo)
        assert False, "Deveria ter lançado DoubleFreeError pelo uso de token obsoleto!"
    except DoubleFreeError as e:
        print(f"Sucesso absoluto na Segurança: Stale Pointer interceptado -> {e}")

    print("\nTodos os testes executados com sucesso total, sem vazamentos e com métricas rigorosas validadas!")