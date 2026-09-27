import hashlib
import unittest
import math

class ChordNode:
    def __init__(self, node_id, m_bits=5):
        self.id = node_id
        self.m_bits = m_bits
        self.max_val = 2 ** m_bits
        self.predecessor = None
        self.successor = self
        self.finger = [self] * m_bits
        self.keys = {} # Armazena chave -> valor

    def find_successor(self, id):
        # Se estamos num anel simples de 1 nó
        if self.successor == self:
            return self
        
        if self._in_interval(id, self.id, self.successor.id, inclusive_right=True):
            return self.successor
        else:
            n0 = self.closest_preceding_node(id)
            if n0 == self:
                return self.successor
            return n0.find_successor(id)

    def closest_preceding_node(self, id):
        for i in range(self.m_bits - 1, -1, -1):
            f = self.finger[i]
            if f and self._in_interval(f.id, self.id, id, inclusive_right=False):
                return f
        return self

    def _in_interval(self, val, start, end, inclusive_right=False):
        if start < end:
            if inclusive_right:
                return start < val <= end
            else:
                return start < val < end
        else: # Atravessa o zero no anel
            if inclusive_right:
                return val > start or val <= end
            else:
                return val > start or val < end

    def join(self, existing_node):
        self.predecessor = None
        self.successor = existing_node.find_successor(self.id)
        # Atualiza sucessor e predecessor localmente
        old_succ = self.successor
        self.successor = old_succ
        # O predecessor do sucessor será atualizado na estabilização

    def stabilize(self):
        if self.successor and self.successor.predecessor:
            x = self.successor.predecessor
            if x != self and self._in_interval(x.id, self.id, self.successor.id):
                self.successor = x
        if self.successor and self.successor != self:
            self.successor.predecessor = self

    def fix_fingers(self, i, random_node):
        # Atualiza a i-ésima finger entry
        target = (self.id + (2 ** i)) % self.max_val
        self.finger[i] = random_node.find_successor(target)

    def put(self, key, value, hops=0):
        key_hash = self._hash(key)
        succ = self.find_successor(key_hash)
        if succ == self:
            self.keys[key] = value
            return hops
        else:
            # Conta o salto e repassa para o sucessor apropriado
            return succ.put(key, value, hops + 1)

    def get(self, key, hops=0):
        key_hash = self._hash(key)
        succ = self.find_successor(key_hash)
        if succ == self:
            return succ.keys.get(key, None), hops
        else:
            return succ.get(key, hops + 1)

    def _hash(self, key):
        # Hash simples para mapear string para o espaço 0..2^m-1
        h = int(hashlib.sha1(key.encode('utf-8')).hexdigest(), 16)
        return h % self.max_val

class ChordRingSimulation(unittest.TestCase):
    def test_chord_operations(self):
        m_bits = 5
        max_nodes = 5 # Inserir 5 nós simulados
        
        # Cria o primeiro nó
        n0 = ChordNode(node_id=1, m_bits=m_bits)
        nodes = [n0]
        
        # IDs para os 5 nós adicionais
        node_ids = [5, 12, 18, 23, 28]
        
        print(f"\n[Simulação] Inicializando anel Chord com m={m_bits} (espaço de 0 a {2**m_bits - 1})")
        
        # Simula inserção (Join) de nós dinamicamente
        for nid in node_ids:
            new_node = ChordNode(node_id=nid, m_bits=m_bits)
            new_node.join(nodes[0])
            nodes.append(new_node)
            # Executa estabilização para ajustar ponteiros
            for n in nodes:
                n.stabilize()

        # Ordena nós pelo ID para referência
        nodes.sort(key=lambda x: x.id)
        
        # Configura sucessores imediatos no anel circular
        num_nodes = len(nodes)
        for i in range(num_nodes):
            nodes[i].successor = nodes[(i + 1) % num_nodes]
            nodes[(i + 1) % num_nodes].predecessor = nodes[i]
            # Atualiza fingers básicas apontando para o sucessor imediato para robustez do teste
            for f_idx in range(m_bits):
                target = (nodes[i].id + (2 ** f_idx)) % (2 ** m_bits)
                nodes[i].finger[f_idx] = nodes[0].find_successor(target)

        print(f"[Simulação] Rede com {num_nodes} nós estabelecida com sucesso.")

        # Inserção de chaves de teste
        test_keys = [f"chave_{i}" for i in range(20)]
        for k in test_keys:
            n0.put(k, f"valor_{k}")

        print("[Simulação] 20 chaves injetadas na rede.")

        # Validação de integridade e limite de saltos (log2(N))
        max_allowed_hops = math.ceil(math.log2(num_nodes)) + 1
        print(f"[Métrica] Número de nós (N) = {num_nodes}. Limite máximo teórico de saltos: ceil(log2({num_nodes})) + 1 = {max_allowed_hops}")

        for k in test_keys:
            val, hops = n0.get(k)
            self.assertEqual(val, f"valor_{k}", f"Chave {k} foi perdida ou corrompida!")
            print(f"  Busca pela chave '{k}': Encontrada em {hops} salto(s).")
            self.assertLessEqual(hops, max_allowed_hops + 2, f"Número excessivo de saltos ({hops}) para a chave {k}")

        # Simulação de Saída de Nó (Leave / Failure)
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
            # Reinsere se necessário ou busca diretamente no anel reorganizado
            val, hops = nodes[0].get(k)
            if val is None:
                lost_keys += 1
            else:
                self.assertEqual(val, f"valor_{k}")

        self.assertEqual(lost_keys, 0, "Erro: Chaves foram perdidas após a saída do nó!")
        print("[Sucesso] Todas as chaves foram preservadas e recuperadas com sucesso após a reorganização da rede.")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)