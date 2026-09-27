import hashlib
import unittest
import math

class ChordNode:
    def __init__(self, node_id, m_bits=5):
        self.id = node_id
        self.m_bits = m_bits
        self.m_size = 2 ** m_bits
        self.successor = self
        self.predecessor = None
        self.finger = [self] * m_bits
        self.store = {}

    def _in_range(self, val, start, end, inclusive_end=False):
        """Verifica se val está no intervalo circular (start, end) ou (start, end]."""
        start = start % self.m_size
        end = end % self.m_size
        val = val % self.m_size

        if start < end:
            if inclusive_end:
                return start < val <= end
            return start < val < end
        else:  # Atravessa o zero
            if inclusive_end:
                return val > start or val <= end
            return val > start or val < end

    def find_successor(self, key_id):
        """Encontra o sucessor responsável por key_id."""
        if self._in_range(key_id, self.id, self.successor.id, inclusive_end=True):
            return self.successor
        
        # Caso contrário, usa a finger table para saltar o mais próximo possível
        nprime = self.closest_preceding_node(key_id)
        if nprime == self:
            return self.successor
        return nprime.find_successor(key_id)

    def closest_preceding_node(self, key_id):
        """Retorna o nó na finger table mais próximo (antes) de key_id."""
        for i in range(self.m_bits - 1, -1, -1):
            f = self.finger[i]
            if f and self._in_range(f.id, self.id, key_id, inclusive_end=False):
                return f
        return self

    def put(self, key, value):
        """Armazena uma chave na DHT."""
        key_id = int(hashlib.sha1(key.encode()).hexdigest(), 16) % self.m_size
        succ = self.find_successor(key_id)
        succ.store[key] = value
        return succ.id

    def get(self, key):
        """Busca uma chave na DHT e retorna o valor junto com o número de saltos."""
        key_id = int(hashlib.sha1(key.encode()).hexdigest(), 16) % self.m_size
        curr = self
        hops = 0
        
        # Limite de segurança para evitar loops em redes simuladas pequenas
        max_hops = self.m_size 

        while hops < max_hops:
            if curr._in_range(key_id, curr.predecessor.id if curr.predecessor else curr.id, curr.id, inclusive_end=True):
                return curr.store.get(key, None), hops
            
            next_node = curr.find_successor(key_id)
            if next_node == curr:
                return curr.store.get(key, None), hops
            
            curr = next_node
            hops += 1

        return None, hops

def hash_key(k, m_bits=5):
    return int(hashlib.sha1(k.encode()).hexdigest(), 16) % (2 ** m_bits)

class TestChordProtocol(unittest.TestCase):
    def test_chord_ring_and_routing(self):
        m_bits = 5
        m_size = 2 ** m_bits
        
        # Criação de nós distribuídos no anel
        node_ids = [1, 4, 12, 19, 25]
        nodes = [ChordNode(nid, m_bits) for nid in node_ids]

        # Configura sucessores e predecessores estaticamente para simular o anel estabilizado
        num_nodes = len(nodes)
        for i in range(num_nodes):
            nodes[i].successor = nodes[(i + 1) % num_nodes]
            nodes[(i + 1) % num_nodes].predecessor = nodes[i]
            
            # Preenche finger tables básicas para roteamento O(log N)
            for j in range(m_bits):
                target = (nodes[i].id + (2 ** j)) % m_size
                # Encontra o sucessor para o target na lista de nós
                succ = nodes[i]
                for n in nodes:
                    if nodes[i]._in_range(target, nodes[i].id, n.id, inclusive_end=True):
                        succ = n
                        break
                nodes[i].finger[j] = succ

        # Inserção de chaves de teste
        test_keys = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
        n0 = nodes[0]

        print("\n[Simulação] Inserindo chaves na DHT...")
        for k in test_keys:
            stored_at = n0.put(k, f"valor_{k}")
            print(f"  Chave '{k}' (hash {hash_key(k, m_bits)}) mapeada para o nó {stored_at}")

        # Validação de busca e limite de saltos O(log N)
        max_allowed_hops = math.ceil(math.log2(num_nodes)) + 1
        print(f"[Validação] Número de nós ativos (N): {num_nodes}. Limite máximo teórico de saltos: {max_allowed_hops}")

        for k in test_keys:
            val, hops = n0.get(k)
            self.assertEqual(val, f"valor_{k}", f"Chave {k} foi perdida ou corrompida!")
            print(f"  Busca pela chave '{k}': Encontrada em {hops} salto(s).")
            self.assertLessEqual(hops, max_allowed_hops + 2, f"Número excessivo de saltos ({hops}) para a chave {k}")

        # Simulação de Saída de Nó (Leave / Failure) com indentação corrigida
        leaving_node = nodes.pop()
        print(f"[Simulação] Removendo o nó com ID {leaving_node.id} do anel.")
        
        # Reorganiza o anel após a remoção
        num_nodes = len(nodes)
        for i in range(num_nodes):
            nodes[i].successor = nodes[(i + 1) % num_nodes]
            nodes[(i + 1) % num_nodes].predecessor = nodes[i]

        # Valida que nenhuma chave foi perdida após a saída do nó
        print("[Validação] Verificando integridade das chaves após a remoção do nó...")
        lost_keys = 0
        for k in test_keys:
            val, hops = nodes[0].get(k)
            if val is None:
                lost_keys += 1
            else:
                self.assertEqual(val, f"valor_{k}")

        self.assertEqual(lost_keys, 0, "Erro: Chaves foram perdidas após a saída do nó!")
        print("[Sucesso] Todas as chaves foram preservadas e recuperadas com sucesso após a reorganização da rede.")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)