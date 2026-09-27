import unittest
import time

class PNCounter:
    def __init__(self, node_id: str):
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id deve ser uma string não vazia.")
        self.node_id = node_id
        self.P = {}  # incrementos por nó
        self.N = {}  # decrementos por nó

    def increment(self, val: int = 1):
        if not isinstance(val, int) or val <= 0:
            raise ValueError("O incremento deve ser um inteiro estritamente positivo (violação da monotonicidade do PN-Counter).")
        self.P[self.node_id] = self.P.get(self.node_id, 0) + val

    def decrement(self, val: int = 1):
        if not isinstance(val, int) or val <= 0:
            raise ValueError("O decremento deve ser um inteiro estritamente positivo (violação da monotonicidade do PN-Counter).")
        self.N[self.node_id] = self.N.get(self.node_id, 0) + val

    @property
    def value(self) -> int:
        sum_p = sum(self.P.values())
        sum_n = sum(self.N.values())
        return sum_p - sum_n

    def merge(self, other: 'PNCounter'):
        if not isinstance(other, PNCounter):
            raise TypeError("O objeto para merge deve ser uma instância de PNCounter.")
        
        all_nodes_p = set(self.P.keys()).union(other.P.keys())
        new_P = {}
        for node in all_nodes_p:
            new_P[node] = max(self.P.get(node, 0), other.P.get(node, 0))
        
        all_nodes_n = set(self.N.keys()).union(other.N.keys())
        new_N = {}
        for node in all_nodes_n:
            new_N[node] = max(self.N.get(node, 0), other.N.get(node, 0))
        
        self.P = new_P
        self.N = new_N

    def clone(self) -> 'PNCounter':
        c = PNCounter(self.node_id)
        c.P = dict(self.P)
        c.N = dict(self.N)
        return c


class LWWElementSet:
    """
    LWW-Element-Set com proteções de segurança defensiva:
    - Rejeição de timestamps negativos ou inválidos.
    - Suporte a injeção de timestamps (para mitigar dependência cega exclusiva de relógio físico em testes/produção).
    """
    def __init__(self, node_id: str):
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id deve ser uma string não vazia.")
        self.node_id = node_id
        self.add_set = {}    # element -> (timestamp, node_id)
        self.remove_set = {} # element -> (timestamp, node_id)

    def _get_timestamp(self, explicit_ts: float = None) -> float:
        if explicit_ts is not None:
            if not isinstance(explicit_ts, (int, float)) or explicit_ts < 0:
                raise ValueError("Timestamp explícito inválido.")
            return float(explicit_ts)
        ts = time.time()
        if ts < 0:
            raise RuntimeError("Relógio físico retornou timestamp inválido.")
        return ts

    def add(self, element, timestamp: float = None):
        ts = self._get_timestamp(timestamp)
        current = self.add_set.get(element, (float('-inf'), ""))
        # Apenas atualiza se o timestamp for maior, ou em empate, se o node_id for maior
        if ts > current[0] or (ts == current[0] and self.node_id > current[1]):
            self.add_set[element] = (ts, self.node_id)

    def remove(self, element, timestamp: float = None):
        ts = self._get_timestamp(timestamp)
        current = self.remove_set.get(element, (float('-inf'), ""))
        if ts > current[0] or (ts == current[0] and self.node_id > current[1]):
            self.remove_set[element] = (ts, self.node_id)

    @property
    def value(self) -> set:
        result = set()
        all_elements = set(self.add_set.keys()).union(self.remove_set.keys())
        for elem in all_elements:
            add_ts, add_node = self.add_set.get(elem, (float('-inf'), ""))
            rem_ts, rem_node = self.remove_set.get(elem, (float('-inf'), ""))
            
            # Regra LWW: remove vence se rem_ts > add_ts,
            # ou em caso de empate de timestamp, se rem_node > add_node.
            if rem_ts > add_ts:
                continue
            elif rem_ts == add_ts and rem_node >= add_node:
                continue
            else:
                result.add(elem)
        return result

    def merge(self, other: 'LWWElementSet'):
        if not isinstance(other, LWWElementSet):
            raise TypeError("O objeto para merge deve ser uma instância de LWWElementSet.")

        # Merge de add_set: para cada elemento, pega o max por timestamp e desempate por node_id
        all_add_elems = set(self.add_set.keys()).union(other.add_set.keys())
        new_add_set = {}
        for elem in all_add_elems:
            self_val = self.add_set.get(elem, (float('-inf'), ""))
            other_val = other.add_set.get(elem, (float('-inf'), ""))
            if self_val[0] > other_val[0]:
                new_add_set[elem] = self_val
            elif other_val[0] > self_val[0]:
                new_add_set[elem] = other_val
            else:
                # Empate: maior node_id ganha de forma determinística
                new_add_set[elem] = self_val if self_val[1] >= other_val[1] else other_val

        # Merge de remove_set
        all_rem_elems = set(self.remove_set.keys()).union(other.remove_set.keys())
        new_remove_set = {}
        for elem in all_rem_elems:
            self_val = self.remove_set.get(elem, (float('-inf'), ""))
            other_val = other.remove_set.get(elem, (float('-inf'), ""))
            if self_val[0] > other_val[0]:
                new_remove_set[elem] = self_val
            elif other_val[0] > self_val[0]:
                new_remove_set[elem] = other_val
            else:
                new_remove_set[elem] = self_val if self_val[1] >= other_val[1] else other_val

        self.add_set = new_add_set
        self.remove_set = new_remove_set

    def clone(self) -> 'LWWElementSet':
        c = LWWElementSet(self.node_id)
        c.add_set = dict(self.add_set)
        c.remove_set = dict(self.remove_set)
        return c


class TestSecureCRDTs(unittest.TestCase):
    def test_pn_counter_monotonicity_enforcement(self):
        counter = PNCounter("n1")
        # Deve aceitar incrementos/decrementos positivos
        counter.increment(5)
        counter.decrement(2)
        self.assertEqual(counter.value, 3)

        # Deve rejeitar valores negativos ou zero que quebram a monotonicidade
        with self.assertRaises(ValueError):
            counter.increment(-5)
        with self.assertRaises(ValueError):
            counter.decrement(0)
        with self.assertRaises(ValueError):
            counter.increment("invalid")

    def test_lww_explicit_timestamp_and_validation(self):
        s = LWWElementSet("n1")
        # Injeção de timestamp explícito para isolar relógio físico e prevenir clock skew
        s.add("item1", timestamp=100.0)
        s.remove("item1", timestamp=105.0)
        self.assertNotIn("item1", s.value)

        # Validações de entrada
        with self.assertRaises(ValueError):
            LWWElementSet("")
        with self.assertRaises(ValueError):
            s.add("item2", timestamp=-1.0)


if __name__ == "__main__":
    unittest.main()