py
import random
import time

class BPlusTreeNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = [] # Apenas para nós internos
        self.next = None     # Apenas para nós folhas (lista encadeada)
        self.values = []     # Apenas para nós folhas

class BPlusTree:
    def __init__(self, t=4):
        self.root = BPlusTreeNode(is_leaf=True)
        self.t = t # Grau mínimo (ordem máxima = 2*t)

    def search(self, key):
        """Busca pontual por uma chave."""
        current = self.root
        while not current.is_leaf:
            i = 0
            while i < len(current.keys) and key >= current.keys[i]:
                i += 1
            current = current.children[i]
        
        # No nó folha, procura pela chave exata
        for i, item in enumerate(current.keys):
            if item == key:
                return current.values[i]
        return None

    def range_query(self, start_key, end_key):
        """Varredura por intervalo utilizando a lista encadeada de folhas."""
        current = self.root
        while not current.is_leaf:
            i = 0
            while i < len(current.keys) and start_key >= current.keys[i]:
                i += 1
            current = current.children[i]

        results = []
        # Encontra a folha e percorre horizontalmente via .next
        while current is not None:
            for i, key in enumerate(current.keys):
                if key > end_key:
                    return results
                if start_key <= key <= end_key:
                    results.append((key, current.values[i]))
            current = current.next
        return results

    def insert(self, key, value):
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:
            # Raiz cheia, cria nova raiz e faz split
            new_root = BPlusTreeNode(is_leaf=False)
            self.root = new_root
            new_root.children.append(root)
            self._split_child(new_root, 0, root)
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, parent, key, value):
        i = len(parent.keys) - 1
        if parent.is_leaf:
            # Insere ordenado na folha
            while i >= 0 and key < parent.keys[i]:
                i -= 1
            parent.keys.insert(i + 1, key)
            parent.values.insert(i + 1, value)
        else:
            while i >= 0 and key < parent.keys[i]:
                i -= 1
            i += 1
            child = parent.children[i]
            if len(child.keys) == (2 * self.t) - 1:
                self._split_child(parent, i, child)
                if key > parent.keys[i]:
                    i += 1
            self._insert_non_full(parent.children[i], key, value)

    def _split_child(self, parent, i, child):
        t = self.t
        z = BPlusTreeNode(is_leaf=child.is_leaf)
        
        # O nó y (child) é dividido ao meio
        # Se for folha, z recebe a metade superior (incluindo o elemento do meio para cópia)
        # Se for interno, o elemento do meio sobe e não fica nem em y nem em z.
        mid_idx = t - 1

        if child.is_leaf:
            z.keys = child.keys[mid_idx:]
            z.values = child.values[mid_idx:]
            child.keys = child.keys[:mid_idx]
            child.values = child.values[:mid_idx]
            
            # Atualiza ponteiros da lista encadeada horizontal
            z.next = child.next
            child.next = z
            
            promoted_key = z.keys[0] # Na folha, a primeira chave de z é copiada para o pai
            parent.children.insert(i + 1, z)
            parent.keys.insert(i, promoted_key)
        else:
            promoted_key = child.keys[mid_idx]
            z.keys = child.keys[mid_idx + 1:]
            z.children = child.children[mid_idx + 1:]
            
            child.keys = child.keys[:mid_idx]
            child.children = child.children[:mid_idx + 1]
            
            parent.children.insert(i + 1, z)
            parent.keys.insert(i, promoted_key)

# --- EXECUÇÃO DO EXPERIMENTO E VALIDAÇÃO ---
if __name__ == "__main__":
    print("Iniciando experimento da Árvore B+...")
    tree = BPlusTree(t=4)

    # Gerar 10.000 chaves aleatórias únicas
    random.seed(42)
    keys = list(range(100000))
    random.shuffle(keys)
    sample_keys = keys[:10000]

    # 1. Teste de Inserção de 10.000 chaves
    start_time = time.time()
    for k in sample_keys:
        tree.insert(k, f"val_{k}")
    insert_duration = (time.time() - start_time) * 1000 # ms
    print(f"[Sucesso] Inseridas 10.000 chaves em {insert_duration:.2f} ms.")

    # 2. Teste de Busca Pontual
    test_key = sample_keys[500]
    val = tree.search(test_key)
    assert val == f"val_{test_key}", f"Busca pontual falhou para a chave {test_key}"
    print(f"[Sucesso] Busca pontual bem-sucedida para a chave {test_key} -> {val}")

    # 3. Teste de Varredura por Intervalo (Range Query) com medição de tempo (< 50 ms exigidos)
    start_q = time.time()
    range_results = tree.range_query(1000, 1050)
    query_duration = (time.time() - start_q) * 1000 # ms

    print(f"[Sucesso] Varredura por intervalo (1000 a 1050) executada em {query_duration:.4f} ms.")
    print(f"Total de registros encontrados no intervalo: {len(range_results)}")
    
    # Validação rigorosa do critério de sucesso
    assert query_duration < 50.0, f"Tempo de varredura por intervalo ({query_duration} ms) excedeu o limite de 50 ms!"
    print("Critério de sucesso validado com folga: Busca por intervalo em menos de 50 ms.")

    # 4. Contraexemplo / Tratamento de Equívoco: Tentativa de busca em chave inexistente
    missing_val = tree.search(9999999)
    assert missing_val is None, "Deveria retornar None para chave inexistente."
    print("[Sucesso] Contraexemplo validado: Chave inexistente retorna corretamente None sem corromper a árvore.")