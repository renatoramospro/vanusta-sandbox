import random
import unittest

class BPlusNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []  # Para nós internos: ponteiros para BPlusNode. Para folhas: valores (ou lista de valores se duplicados).
        self.next = None    # Apenas para folhas: ponteiro para o próximo nó folha
        self.prev = None    # Apenas para folhas: ponteiro para o nó folha anterior

class BPlusTree:
    def __init__(self, t=3):
        """
        t: grau mínimo. Um nó interno (exceto raiz) tem entre t-1 e 2t-1 chaves.
        """
        self.root = BPlusNode(is_leaf=True)
        self.t = t

    def search(self, key):
        """Busca uma chave na árvore B+. Retorna o valor ou None se não existir."""
        node = self.root
        while not node.is_leaf:
            # Encontra o primeiro índice onde a chave do nó é maior que a chave buscada
            idx = 0
            while idx < len(node.keys) and key >= node.keys[idx]:
                idx += 1
            node = node.children[idx]
        
        # Na folha, procura a chave exata
        for i, k in enumerate(node.keys):
            if k == key:
                return node.children[i]
            if k > key:
                break
        return None

    def insert(self, key, value):
        """Insere uma chave e valor na árvore B+."""
        root = self.root
        if len(root.keys) == (2 * self.t - 1):
            # Se a raiz estiver cheia, a árvore cresce em altura
            new_root = BPlusNode(is_leaf=False)
            self.root = new_root
            new_root.children.append(root)
            self._split_child(new_root, 0, root)
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, node, key, value):
        idx = len(node.keys) - 1
        if node.is_leaf:
            # Encontra a posição correta na folha mantendo ordenação
            while idx >= 0 and key < node.keys[idx]:
                idx -= 1
            
            # Tratamento de chave duplicada (atualiza valor ou insere)
            if idx >= 0 and node.keys[idx] == key:
                node.children[idx] = value  # Atualiza valor
                return

            node.keys.insert(idx + 1, key)
            node.children.insert(idx + 1, value)
        else:
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
        
        # z recebe a metade superior das chaves de child
        z.keys = child.keys[t:]
        child.keys = child.keys[:t-1 if not child.is_leaf else t:] # Na folha, t chaves ficam na esquerda, t na direita (se 2t)

        if not child.is_leaf:
            z.children = child.children[t:]
            child.children = child.children[:t]
        else:
            # Reajusta para folhas: child mantém t chaves, z fica com o resto
            # Corrigindo divisão exata para 2*t-1 chaves:
            # Ex: t=3 -> 5 chaves. Esquerda: 2, Direita: 3.
            # Vamos padronizar: split exato em t.
            child.keys = child.keys[:t]
            z.keys = child.keys[t:] # cuidado: recalculando corretamente abaixo
            
        # Refazendo divisão limpa baseada em t:
        # Se child tem 2*t - 1 chaves:
        # Meio é t - 1 (indexado em 0)
        mid = len(child.keys) // 2
        
        if child.is_leaf:
            z.keys = child.keys[mid:]
            child.keys = child.keys[:mid]
            z.children = child.children[mid:]
            child.children = child.children[:mid]
            
            # Atualiza ponteiros encadeados das folhas
            z.next = child.next
            z.prev = child
            if child.next:
                child.next.prev = z
            child.next = z
            
            # Sobe a primeira chave do nó direito (z) para o pai (B+ tree clássica)
            parent.keys.insert(i, z.keys[0])
            parent.children.insert(i + 1, z)
        else:
            # Nó interno: a chave mediana sobe e sai do filho
            p_key = child.keys[mid]
            z.keys = child.keys[mid + 1:]
            child.keys = child.keys[:mid]
            
            z.children = child.children[mid + 1:]
            child.children = child.children[:mid + 1]
            
            parent.keys.insert(i, p_key)
            parent.children.insert(i + 1, z)

    def delete(self, key):
        """Remove uma chave da árvore B+."""
        self._delete_internal(self.root, key)
        # Se a raiz ficou vazia e não é folha, seu único filho passa a ser a nova raiz
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]

    def _delete_internal(self, node, key):
        t = self.t
        idx = 0
        while idx < len(node.keys) and key > node.keys[idx]:
            idx += 1

        if node.is_leaf:
            if idx < len(node.keys) and node.keys[idx] == key:
                node.keys.pop(idx)
                node.children.pop(idx)
            return

        # Nó interno
        if idx < len(node.keys) and node.keys[idx] == key:
            # Chave encontrada no nó interno
            # Para simplificar na B+, idealmente removemos na folha, mas podemos tratar aqui ou delegar
            # Vamos buscar o predecessor na folha ou tratar via descendentes
            pass

        child = node.children[idx]
        if len(child.keys) < t:
            # O filho tem menos que t chaves, precisamos garantir propriedades antes de descer
            self._fill_child(node, idx)
            # Após _fill_child, o índice pode ter mudado
            if idx > len(node.keys):
                idx = len(node.keys)
            child = node.children[idx]

        self._delete_internal(child, key)

    def _fill_child(self, node, idx):
        t = self.t
        if idx > 0 and len(node.children[idx - 1].keys) >= t:
            self._borrow_from_prev(node, idx)
        elif idx < len(node.keys) and len(node.children[idx + 1].keys) >= t:
            self._borrow_from_next(node, idx)
        else:
            if idx < len(node.keys):
                self._merge(node, idx)
            else:
                self._merge(node, idx - 1)

    def _borrow_from_prev(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx - 1]
        
        if child.is_leaf:
            child.keys.insert(0, sibling.keys.pop())
            child.children.insert(0, sibling.children.pop())
            node.keys[idx - 1] = child.keys[0]
        else:
            child.keys.insert(0, node.keys[idx - 1])
            node.keys[idx - 1] = sibling.keys.pop()
            child.children.insert(0, sibling.children.pop())

    def _borrow_from_next(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx + 1]
        
        if child.is_leaf:
            child.keys.append(sibling.keys.pop(0))
            child.children.append(sibling.children.pop(0))
            node.keys[idx] = sibling.keys[0]
        else:
            child.keys.append(node.keys[idx])
            node.keys[idx] = sibling.keys.pop(0)
            child.children.append(sibling.children.pop(0))

    def _merge(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx + 1]
        
        if child.is_leaf:
            child.keys.extend(sibling.keys)
            child.children.extend(sibling.children)
            child.next = sibling.next
            if sibling.next:
                sibling.next.prev = child
            node.keys.pop(idx)
            node.children.pop(idx + 1)
        else:
            child.keys.append(node.keys[idx])
            child.keys.extend(sibling.keys)
            child.children.extend(sibling.children)
            node.keys.pop(idx)
            node.children.pop(idx + 1)


class TestBPlusTree(unittest.TestCase):
    def test_insert_and_search(self):
        tree = BPlusTree(t=3)
        data = [(i, f"val_{i}") for i in range(1, 100)]
        for k, v in data:
            tree.insert(k, v)
        
        for k, v in data:
            self.assertEqual(tree.search(k), v)
        
        self.assertIsNone(tree.search(999))

    def test_random_10k_keys(self):
        tree = BPlusTree(t=4)
        keys = list(range(10000))
        random.shuffle(keys)
        
        # Inserção
        for k in keys:
            tree.insert(k, f"v_{k}")
            
        # Busca
        for k in keys:
            self.assertEqual(tree.search(k), f"v_{k}")
            
        self.assertIsNone(tree.search(10005))

    def test_leaf_linkage(self):
        tree = BPlusTree(t=3)
        for i in [10, 20, 5, 15, 25, 30, 35]:
            tree.insert(i, f"v_{i}")
            
        # Percorre pelas folhas usando o ponteiro 'next'
        node = tree.root
        while not node.is_leaf:
            node = node.children[0]
            
        collected = []
        while node:
            collected.extend(node.keys)
            node = node.next
            
        self.assertEqual(collected, sorted(collected))
        self.assertEqual(len(collected), 7)


if __name__ == "__main__":
    unittest.main()