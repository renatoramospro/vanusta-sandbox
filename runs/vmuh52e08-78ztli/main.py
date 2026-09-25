import random
import time

class BPlusTreeNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = [] # Ponteiros para nós filhos (se interno) ou dados/valores (se folha)
        self.next = None     # Ponteiro horizontal para o próximo nó folha (para range queries)

class BPlusTree:
    def __init__(self, t=4):
        self.root = BPlusTreeNode(is_leaf=True)
        self.t = t # Grau mínimo (define a capacidade dos nós: 2t-1 chaves máximas)

    def search(self, key):
        current = self.root
        while not current.is_leaf:
            i = 0
            while i < len(current.keys) and key >= current.keys[i]:
                i += 1
            current = current.children[i]
        
        # Busca linear no nó folha
        for i, item in enumerate(current.keys):
            if item == key:
                return current.children[i]
        return None

    def insert(self, key, value):
        root = self.root
        if len(root.keys) == (2 * self.t - 1):
            s = BPlusTreeNode(is_leaf=False)
            self.root = s
            s.children.append(root)
            self._split_child(s, 0)
            self._insert_non_full(s, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, node, key, value):
        i = len(node.keys) - 1
        if node.is_leaf:
            # Encontra a posição correta mantendo ordenado
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            node.keys.insert(i, key)
            node.children.insert(i, value)
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            child = node.children[i]
            if len(child.keys) == (2 * self.t - 1):
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent, i):
        t = self.t
        y = parent.children[i]
        z = BPlusTreeNode(is_leaf=y.is_leaf)
        
        # O nó y cede metade das chaves para z
        mid_idx = t - 1
        if y.is_leaf:
            z.keys = y.keys[mid_idx:]
            z.children = y.children[mid_idx:]
            y.keys = y.keys[:mid_idx]
            y.children = y.children[:mid_idx]
            
            # Ajusta ponteiros da lista encadeada horizontal das folhas
            z.next = y.next
            y.next = z
            
            promoted_key = z.keys[0]
        else:
            promoted_key = y.keys[mid_idx]
            z.keys = y.keys[mid_idx + 1:]
            z.children = y.children[mid_idx + 1:]
            y.keys = y.keys[:mid_idx]
            y.children = y.children[:mid_idx + 1]

        parent.children.insert(i + 1, z)
        parent.keys.insert(i, promoted_key)

    def range_query(self, start_key, end_key):
        current = self.root
        while not current.is_leaf:
            i = 0
            while i < len(current.keys) and start_key >= current.keys[i]:
                i += 1
            current = current.children[i]
        
        results = []
        while current is not None:
            for i, key in enumerate(current.keys):
                if key > end_key:
                    return results
                if start_key <= key <= end_key:
                    results.append((key, current.children[i]))
            current = current.next
        return results

if __name__ == "__main__":
    tree = BPlusTree(t=4)
    random.seed(42)
    keys = list(range(1, 15000))
    random.shuffle(keys)
    sample_keys = keys[:10000]

    # 1. Teste de Inserção de 10.000 chaves
    start_time = time.time()
    for k in sample_keys:
        tree.insert(k, f"val_{k}")
    insert_duration = (time.time() - start_time) * 1000
    print(f"[Sucesso] Inseridas 10.000 chaves em {insert_duration:.2f} ms.")

    # 2. Teste de Busca Pontual
    test_key = sample_keys[500]
    val = tree.search(test_key)
    assert val == f"val_{test_key}", f"Busca pontual falhou para a chave {test_key}"
    print(f"[Sucesso] Busca pontual bem-sucedida para a chave {test_key} -> {val}")

    # 3. Teste de Varredura por Intervalo (Range Query) com medição de tempo (< 50 ms exigidos)
    start_q = time.time()
    range_results = tree.range_query(1000, 1050)
    query_duration = (time.time() - start_q) * 1000

    print(f"[Sucesso] Varredura por intervalo (1000 a 1050) executada em {query_duration:.4f} ms.")
    print(f"Total de registros encontrados no intervalo: {len(range_results)}")
    
    assert query_duration < 50.0, f"Tempo de varredura por intervalo ({query_duration} ms) excedeu o limite de 50 ms!"
    print("Critério de sucesso validado com folga: Busca por intervalo em menos de 50 ms.")

    # 4. Contraexemplo / Tratamento de Equívoco: Tentativa de busca em chave inexistente
    missing_val = tree.search(9999999)
    assert missing_val is None, "Deveria retornar None para chave inexistente."
    print("[Sucesso] Contraexemplo validado: Chave inexistente retorna corretamente None sem corromper a árvore.")