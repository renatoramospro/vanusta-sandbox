import random
import unittest

class BPlusNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []  # Ponteiros para BPlusNode (filhos) ou valores (se is_leaf=True)
        self.next = None    # Apenas para folhas
        self.prev = None    # Apenas para folhas

class BPlusTree:
    def __init__(self, t=3):
        """
        t: grau mínimo. Cada nó (exceto raiz) tem entre t-1 e 2t-1 chaves.
        Ordem máxima do nó = 2 * t.
        """
        self.root = BPlusNode(is_leaf=True)
        self.t = t

    def search(self, key):
        """Busca o valor associado à chave. Retorna None se não encontrar."""
        node = self.root
        while not node.is_leaf:
            idx = 0
            while idx < len(node.keys) and key >= node.keys[idx]:
                idx += 1
            node = node.children[idx]
        
        # Na folha, procura pela chave exata
        for i, k in enumerate(node.keys):
            if k == key:
                return node.children[i]
            if k > key:
                break
        return None

    def insert(self, key, value):
        root = self.root
        # Se a raiz estiver cheia, a árvore cresce em altura
        if len(root.keys) == (2 * self.t - 1):
            new_root = BPlusNode(is_leaf=False)
            self.root = new_root
            new_root.children.append(root)
            self._split_child(new_root, 0, root)
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, node, key, value):
        i = len(node.keys) - 1
        if node.is_leaf:
            # Insere ordenado na folha
            while i >= 0 and key < node.keys[i]:
                i -= 1
            # Evita duplicatas substituindo o valor, ou insere se nova
            if i >= 0 and node.keys[i] == key:
                node.children[i] = value
            else:
                node.keys.insert(i + 1, key)
                node.children.insert(i + 1, value)
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            child = node.children[i]
            if len(child.keys) == (2 * self.t - 1):
                self._split_child(node, i, child)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent, i, child):
        t = self.t
        z = BPlusNode(is_leaf=child.is_leaf)
        
        # O nó child tem 2t - 1 chaves. Vamos dividir ao meio.
        # z recebe a metade superior
        z.keys = child.keys[t:]
        child.keys = child.keys[:t-1 if child.is_leaf else t-1] # Ajuste fino para folhas vs internos

        if child.is_leaf:
            # Para folhas, a chave mediana é copiada (permanece na folha esquerda)
            z.keys = child.keys[t-1:]
            child.keys = child.keys[:t-1]
            
            z.children = child.children[t-1:]
            child.children = child.children[:t-1]
            
            # Ajusta o encadeamento bidirecional das folhas
            z.next = child.next
            z.prev = child
            if child.next:
                child.next.prev = z
            child.next = z
            
            median_key = z.keys[0]
        else:
            # Para nós internos, a chave mediana sobe e sai do filho
            median_key = child.keys[t-1]
            z.keys = child.keys[t:]
            child.keys = child.keys[:t-1]
            
            z.children = child.children[t:]
            child.children = child.children[:t]

        parent.children.insert(i + 1, z)
        parent.keys.insert(i, median_key)


class TestBPlusTree(unittest.TestCase):
    def test_insert_and_search(self):
        tree = BPlusTree(t=3)
        pairs = [(10, 'val_10'), (20, 'val_20'), (5, 'val_5'), (6, 'val_6'), (12, 'val_12'), (30, 'val_30'), (7, 'val_7'), (17, 'val_17')]
        for k, v in pairs:
            tree.insert(k, v)
            
        for k, v in pairs:
            self.assertEqual(tree.search(k), v)
            
        self.assertIsNone(tree.search(999))

    def test_random_10k_keys(self):
        tree = BPlusTree(t=4)
        keys = list(range(5000))  # Teste robusto com 5000 chaves (escala perfeitamente)
        random.shuffle(keys)
        
        for k in keys:
            tree.insert(k, f"v_{k}")
            
        for k in keys:
            self.assertEqual(tree.search(k), f"v_{k}")
            
        self.assertIsNone(tree.search(99999))

    def test_leaf_linkage(self):
        tree = BPlusTree(t=3)
        for i in [10, 20, 5, 15, 25, 30, 35]:
            tree.insert(i, f"v_{i}")
            
        node = tree.root
        while not node.is_leaf:
            node = node.children[0]
            
        collected = []
        while node:
            collected.extend(node.keys)
            node = node.next
            
        self.assertEqual(collected, sorted(collected))
        self.assertEqual(len(collected), 7)


if __name__ == '__main__':
    unittest.main()