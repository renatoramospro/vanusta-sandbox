import networkx as nx
import threading
import time
import random

class CRDT:
    def __init__(self):
        self.graph = nx.Graph()
        self.lock = threading.Lock()

    def add_node(self, node):
        with self.lock:
            self.graph.add_node(node)

    def add_edge(self, node1, node2):
        with self.lock:
            self.graph.add_edge(node1, node2)

    def remove_node(self, node):
        with self.lock:
            self.graph.remove_node(node)

    def remove_edge(self, node1, node2):
        with self.lock:
            self.graph.remove_edge(node1, node2)

    def get_graph(self):
        return self.graph

def simulate_operations(crdt, num_operations):
    threads = []
    for _ in range(num_operations):
        thread = threading.Thread(target=crdt.add_node, args=(random.randint(1, 10),))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return crdt.get_graph()

def test_fusion(crdt1, crdt2):
    graph1 = crdt1.get_graph()
    graph2 = crdt2.get_graph()

    # Verificar se os grafos são iguais
    if graph1.nodes() != graph2.nodes() or graph1.edges() != graph2.edges():
        return False

    return True

# Testar a implementação
crdt = CRDT()
graph = simulate_operations(crdt, 15)

# Testar a fusão
crdt2 = CRDT()
graph2 = simulate_operations(crdt2, 15)

if test_fusion(crdt, crdt2):
    print("Convergência de estado idêntica alcançada!")
else:
    print("Convergência de estado idêntica não alcançada.")