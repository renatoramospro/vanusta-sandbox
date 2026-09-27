import unittest

class PNCounter:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.P = {}  # incrementos por nó
        self.N = {}  # decrementos por nó

    def increment(self, val: int = 1):
        self.P[self.node_id] = self.P.get(self.node_id, 0) + val

    def decrement(self, val: int = 1):
        self.N[self.node_id] = self.N.get(self.node_id, 0) + val

    @property
    def value(self) -> int:
        sum_p = sum(self.P.values())
        sum_n = sum(self.N.values())
        return sum_p - sum_n

    def merge(self, other: 'PNCounter'):
        all_nodes = set(self.P.keys()).union(other.P.keys())
        new_P = {}
        for node in all_nodes:
            new_P[node] = max(self.P.get(node, 0), other.P.get(node, 0))
        
        all_nodes_n = set(self.N.keys()).union(other.N.keys())
        new_N = {}
        for node in all_nodes_n:
            new_N[node] = max(self.N.get(node, 0), other.N.get(node, 0))
            
        self.P = new_P
        self.N = new_N

    def clone(self) -> 'PNCounter':
        c = PNCounter(self.node_id)
        c.P = self.P.copy()
        c.N = self.N.copy()
        return c


class LWWElementSet:
    def __init__(self, node_id: str):
        self.node_id = node_id
        # {element: (timestamp, node_id)}
        self.add_set = {}
        self.remove_set = {}

    def add(self, element, timestamp: int):
        current = self.add_set.get(element, (-1, ""))
        if (timestamp, self.node_id) > current:
            self.add_set[element] = (timestamp, self.node_id)

    def remove(self, element, timestamp: int):
        current = self.remove_set.get(element, (-1, ""))
        if (timestamp, self.node_id) > current:
            self.remove_set[element] = (timestamp, self.node_id)

    @property
    def value(self) -> set:
        elements = set(self.add_set.keys()).union(self.remove_set.keys())
        result = set()
        for elem in elements:
            add_ts = self.add_set.get(elem, (-1, ""))
            rem_ts = self.remove_set.get(elem, (-1, ""))
            # LWW: Se remove_ts > add_ts, o elemento foi removido.
            # Em caso de empate de timestamp, o tie-breaker padrão pode ser aplicado (aqui usamos o par completo (ts, node_id)).
            if add_ts > rem_ts:
                result.add(elem)
        return result

    def merge(self, other: 'LWWElementSet'):
        for elem, ts_node in other.add_set.items():
            current = self.add_set.get(elem, (-1, ""))
            if ts_node > current:
                self.add_set[elem] = ts_node

        for elem, ts_node in other.remove_set.items():
            current = self.remove_set.get(elem, (-1, ""))
            if ts_node > current:
                self.remove_set[elem] = ts_node

    def clone(self) -> 'LWWElementSet':
        s = LWWElementSet(self.node_id)
        s.add_set = self.add_set.copy()
        s.remove_set = self.remove_set.copy()
        return s


class TestCRDTConvergence(unittest.TestCase):

    def test_pn_counter_convergence_and_properties(self):
        # 3 nós simulados
        nodeA = PNCounter("A")
        nodeB = PNCounter("B")
        nodeC = PNCounter("C")

        # Operações concorrentes
        nodeA.increment(5)
        nodeB.increment(3)
        nodeB.decrement(1)
        nodeC.decrement(2)
        nodeC.increment(10)

        # Simulação de entrega de mensagens fora de ordem
        # Nó A recebe C, depois B
        nodeA.merge(nodeC)
        nodeA.merge(nodeB)

        # Nó B recebe A, depois C
        nodeB.merge(nodeA)
        nodeB.merge(nodeC)

        # Nó C recebe B, depois A
        nodeC.merge(nodeB)
        nodeC.merge(nodeA)

        # Convergência estrita
        self.assertEqual(nodeA.value, nodeB.value)
        self.assertEqual(nodeB.value, nodeC.value)
        # 5 (A.P) + 3 (B.P) + 10 (C.P) = 18. 1 (B.N) + 2 (C.N) = 3. Total = 15
        self.assertEqual(nodeA.value, 15)

        # Validação de Idempotência: merge(A, A) == A
        clone_A = nodeA.clone()
        nodeA.merge(clone_A)
        self.assertEqual(nodeA.P, clone_A.P)
        self.assertEqual(nodeA.N, clone_A.N)

        # Validação de Associatividade e Comutatividade
        x = PNCounter("X")
        x.increment(2)
        y = PNCounter("Y")
        y.decrement(1)
        z = PNCounter("Z")
        z.increment(5)

        xy = x.clone(); xy.merge(y)
        xy_z = xy.clone(); xy_z.merge(z)

        yz = y.clone(); yz.merge(z)
        x_yz = x.clone(); x_yz.merge(yz)

        self.assertEqual(xy_z.P, x_yz.P)
        self.assertEqual(xy_z.N, x_yz.N)

    def test_lww_element_set_convergence_and_properties(self):
        setA = LWWElementSet("A")
        setB = LWWElementSet("B")
        setC = LWWElementSet("C")

        # Operações concorrentes com timestamps
        setA.add("apple", timestamp=10)
        setA.add("banana", timestamp=10)

        setB.add("apple", timestamp=5)  # timestamp menor, deve perder para o add de A
        setB.remove("apple", timestamp=12) # remoção com timestamp maior que add de A ("apple" deve sumir)
        setB.add("cherry", timestamp=11)

        setC.remove("banana", timestamp=8) # remove banana (timestamp 8 < add 10, banana continua)
        setC.add("date", timestamp=15)

        # Entrega fora de ordem entre os nós
        setA.merge(setC)
        setA.merge(setB)

        setB.merge(setA)
        setB.merge(setC)

        setC.merge(setB)
        setC.merge(setA)

        # Convergência estrita de estados finais
        self.assertEqual(setA.value, setB.value)
        self.assertEqual(setB.value, setC.value)

        # Análise do estado esperado:
        # - "apple": add(10, A) vs remove(12, B) -> remove vence -> ausente
        # - "banana": add(10, A) vs remove(8, C) -> add vence -> presente
        # - "cherry": add(11, B) -> presente
        # - "date": add(15, C) -> presente
        expected_values = {"banana", "cherry", "date"}
        self.assertEqual(setA.value, expected_values)

        # Idempotência
        clone_setA = setA.clone()
        setA.merge(clone_setA)
        self.assertEqual(setA.add_set, clone_setA.add_set)
        self.assertEqual(setA.remove_set, clone_setA.remove_set)


if __name__ == "__main__":
    unittest.main()