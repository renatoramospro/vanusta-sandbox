import random
import unittest

class BPlusNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []  # Ponteiros para BPlusNode (se interno) ou valores (se folha)
        self.next = None    # Apenas para folhas
        self.prev = None    # Apenas para folhas

class BPlusTree:
    def __init__(self, t=3):
        """
        t: grau mínimo. Cada nó (exceto raiz) tem entre t-1 e 2t-1 chaves.
        Capacidade máxima de chaves por nó = 2 * t - 1.
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
        if node.is_leaf:
            # Verifica se a chave já existe para atualizar o valor (idempotência / chave duplicada)
            for i, k in enumerate(node.keys):
                if k == key:
                    node.children[i] = value
                    return
            
            # Insere mantendo a ordenação na folha
            idx = len(node.keys) - 1
            while idx >= 0 and node.keys[idx] > key:
                idx -= 1
            
            node.keys.insert(idx + 1, key)
            node.children.insert(idx + 1, value)
        else:
            # Nó interno: encontra o filho correto para descer
            idx = len(node.keys) - 1
            while idx >= 0 and key < node.keys[idx]:
                idx -= 1
            idx += 1

            child = node.children[idx]
            if len(child.keys) == (2 * self.t - 1):
                self._split_child(node, idx, child)
                if key > node.keys[idx]:
                    idx += 1
            self._insert_non_full(node.children[idx], key, value)

    def _split_child(self, parent, i, child):
        t = self.t
        z = BPlusNode(is_leaf=child.is_leaf)
        
        if child.is_leaf:
            # Para nós folhas: move a metade superior para z. 
            # A chave mediana permanece na folha à esquerda (child).
            z.keys = child.keys[t-1:]
            z.children = child.children[t-1:]
            
            child.keys = child.keys[:t-1]
            child.children = child.children[:t-1]
            
            # Atualiza o encadeamento bidirecional das folhas
            z.next = child.next
            z.prev = child
            if child.next:
                child.next.prev = z
            child.next = z
            
            median_key = z.keys[0]
            
            parent.children.insert(i + 1, z)
            parent.keys.insert(i, median_key)
        else:
            # Para nós internos: a chave mediana sobe e é removida do filho.
            z.keys = child.keys[t:]
            z.children = child.children[t:]
            
            median_key = child.keys[t - 1]
            
            child.keys = child.keys[:t - 1]
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
        keys = list(range(2000))  # Escala robusta e rápida para validação contínua
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