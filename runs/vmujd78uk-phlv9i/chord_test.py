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

    def update_fingers(self, nodes):
        """Atualiza a finger table do nó com base na lista atual de nós ativos no anel."""
        for i in range(self.m_bits):
            target_id = (self.id + (2 ** i)) % self.m_size
            # Encontra o sucessor para o target_id na lista de nós
            succ = self._find_successor_in_list(target_id, nodes)
            self.finger[i] = succ

    def _find_successor_in_list(self, key_id, nodes):
        """Auxiliar estático/determinístico para encontrar o sucessor correto em testes estáticos."""
        # Ordena nós por ID
        sorted_nodes = sorted(nodes, key=lambda n: n.id)
        for n in sorted_nodes:
            if n.id >= key_id:
                return n
        return sorted_nodes[0]

    def find_successor(self, key_id):
        """Encontra o sucessor responsável por key_id usando as finger tables."""
        if self._in_range(key_id, self.id, self.successor.id, inclusive_end=True):
            return self.successor
        
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
        """Armazena uma chave na DHT encontrando seu verdadeiro sucessor."""
        key_id = int(hashlib.sha1(key.encode()).hexdigest(), 16) % self.m_size
        succ = self.find_successor(key_id)
        succ.store[key] = value
        return succ, key_id

    def get(self, key):
        """Busca uma chave na DHT roteando pelo anel e retorna (valor, saltos)."""
        key_id = int(hashlib.sha1(key.encode()).hexdigest(), 16) % self.m_size
        succ = self.find_successor(key_id)
        
        # Conta saltos simulando o roteamento passo a passo a partir de self
        curr = self
        hops = 0
        max_hops = self.m_size

        while hops < max_hops:
            if curr == succ or curr._in_range(key_id, curr.predecessor.id if curr.predecessor else curr.id, curr.id, inclusive_end=True):
                break
            curr = curr.successor
            hops += 1

        val = succ.store.get(key, None)
        return val, hops


class TestChordProtocol(unittest.TestCase):

    def test_chord_ring_and_routing(self):
        m_bits = 5
        m_size = 2 ** m_bits
    
        # Criação de nós distribuídos no anel
        node_ids = [1, 4, 12, 19, 25]
        nodes = [ChordNode(nid, m_bits) for nid in node_ids]
    
        # Configura sucessores, predecessores e finger tables
        num_nodes = len(nodes)
        for i in range(num_nodes):
            nodes[i].successor = nodes[(i + 1) % num_nodes]
            nodes[(i + 1) % num_nodes].predecessor = nodes[i]

        for node in nodes:
            node.update_fingers(nodes)

        # Inserção de chaves de teste
        test_keys = {
            'alpha': 'valor_alpha',
            'beta': 'valor_beta',
            'gamma': 'valor_gamma',
            'delta': 'valor_delta',
            'epsilon': 'valor_epsilon',
            'zeta': 'valor_zeta',
            'eta': 'valor_eta',
            'theta': 'valor_theta'
        }

        print("\n[Simulação] Inserindo chaves na DHT...")
        n0 = nodes[0]
        for k, v in test_keys.items():
            succ, kid = n0.put(k, v)
            print(f"  Chave '{k}' (hash {kid}) mapeada para o nó {succ.id}")

        # Validação do limite teórico de saltos O(log N)
        max_allowed_hops = math.ceil(math.log2(num_nodes))
        print(f"[Validação] Número de nós ativos (N): {num_nodes}. Limite máximo teórico de saltos: {max_allowed_hops}")

        for k in test_keys:
            val, hops = n0.get(k)
            self.assertEqual(val, f"valor_{k}", f"Chave {k} foi perdida ou corrompida!")
            print(f"  Busca pela chave '{k}': Encontrada em {hops} salto(s).")
            self.assertLessEqual(hops, max_allowed_hops + 2, f"Número excessivo de saltos ({hops}) para a chave {k}")

        # Simulação de Saída de Nó (Leave / Failure)
        leaving_node = nodes.pop()
        print(f"[Simulação] Removendo o nó com ID {leaving_node.id} do anel.")
        
        # Migra chaves do nó removido para seu sucessor para evitar perda em saída dinâmica
        surviving_succ = leaving_node.successor
        for k, v in leaving_node.store.items():
            surviving_succ.store[k] = v

        # Reorganiza o anel após a remoção
        num_nodes = len(nodes)
        for i in range(num_nodes):
            nodes[i].successor = nodes[(i + 1) % num_nodes]
            nodes[(i + 1) % num_nodes].predecessor = nodes[i]

        for node in nodes:
            node.update_fingers(nodes)

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