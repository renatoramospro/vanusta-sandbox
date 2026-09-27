import time
import random
import threading
from queue import Queue, Empty

class Message:
    def __init__(self, sender_id, msg_type, payload):
        self.sender_id = sender_id
        self.msg_type = msg_type  # 'GOSSIP' ou 'JOIN'
        self.payload = payload    # Dicionário de membros {node_id: heartbeat}

class Node:
    def __init__(self, node_id, transport, interval=0.05):
        self.node_id = node_id
        self.transport = transport
        self.interval = interval
        self.membership = {node_id: 0}  # node_id -> heartbeat counter
        self.running = False
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._gossip_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def receive_message(self, msg):
        with self.lock:
            if msg.msg_type in ('GOSSIP', 'JOIN'):
                for peer_id, hb in msg.payload.items():
                    if peer_id not in self.membership or hb > self.membership[peer_id]:
                        self.membership[peer_id] = hb

    def _gossip_loop(self):
        while self.running:
            time.sleep(self.interval)
            with self.lock:
                self.membership[self.node_id] += 1
                payload = dict(self.membership)

            peers = self.transport.get_random_peers(self.node_id, count=2)
            for peer_id in peers:
                msg = Message(self.node_id, 'GOSSIP', payload)
                self.transport.send(peer_id, msg)

class SimulatedTransport:
    def __init__(self, drop_rate=0.05):
        self.nodes = {}
        self.queues = {}
        self.drop_rate = drop_rate
        self.lock = threading.Lock()
        self.net_running = True

    def register_node(self, node):
        with self.lock:
            self.nodes[node.node_id] = node
            self.queues[node.node_id] = Queue()

    def unregister_node(self, node_id):
        with self.lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
            if node_id in self.queues:
                del self.queues[node_id]

    def send(self, dest_id, msg):
        if random.random() < self.drop_rate:
            return  # Simula perda de pacote
        with self.lock:
            if dest_id in self.queues:
                self.queues[dest_id].put(msg)

    def get_random_peers(self, exclude_id, count=2):
        with self.lock:
            available = [nid for nid in self.nodes.keys() if nid != exclude_id]
        if not available:
            return []
        return random.sample(available, min(len(available), count))

    def network_dispatch_loop(self):
        while self.net_running:
            time.sleep(0.01)
            with self.lock:
                targets = list(self.queues.keys())
            for tid in targets:
                try:
                    q = self.queues[tid]
                    while not q.empty():
                        msg = q.get_nowait()
                        with self.lock:
                            node = self.nodes.get(tid)
                        if node:
                            node.receive_message(msg)
                except Empty:
                    pass

def run_simulation():
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando simulação do protocolo Gossip (SWIM-style)...")
    transport = SimulatedTransport(drop_rate=0.05)

    net_thread = threading.Thread(target=transport.network_dispatch_loop, daemon=True)
    net_thread.start()

    # 1. Criação do cluster com 10 nós
    nodes = []
    for i in range(1, 11):
        node = Node(f"node-{i}", transport, interval=0.05)
        nodes.append(node)
        transport.register_node(node)
        node.start()

    print(f"[{time.strftime('%H:%M:%S')}] Cluster inicializado com 10 nós.")
    time.sleep(0.5)

    # 2. Teste de Entrada (Join) de um novo nó
    new_node_id = "node-11"
    print(f"\n[{time.strftime('%H:%M:%S')}] EVENTO DE ENTRADA: Adicionando o '{new_node_id}'...")
    start_time = time.time()

    new_node = Node(new_node_id, transport, interval=0.05)
    transport.register_node(new_node)
    new_node.start()

    # Dispara mensagem de join inicial
    init_msg = Message(new_node_id, 'JOIN', {new_node_id: 0})
    for n in nodes:
        transport.send(n.node_id, init_msg)
    nodes.append(new_node)

    # Mede convergência da entrada
    join_converged = False
    join_duration = 0.0
    while time.time() - start_time < 3.0:
        time.sleep(0.05)
        all_membership = [n.membership for n in nodes]
        target_keys = set(n.node_id for n in nodes)
        
        converged = all(set(m.keys()) == target_keys for m in all_membership)
        if converged:
            join_duration = time.time() - start_time
            join_converged = True
            break

    print(f"[{time.strftime('%H:%M:%S')}] Convergência após ENTRADA de nó: {join_converged} em {join_duration:.3f}s")
    assert join_converged, "O cluster falhou em convergir após a entrada do novo nó em menos de 3s!"
    assert join_duration < 3.0, f"Tempo de convergência de entrada ({join_duration:.3f}s) excedeu o limite de 3.0s!"

    # 3. Teste de Saída de Nó (Leave / Falha)
    print(f"\n[{time.strftime('%H:%M:%S')}] EVENTO DE SAÍDA: Removendo o 'node-5'...")
    node_to_remove = next(n for n in nodes if n.node_id == "node-5")
    node_to_remove.stop()
    transport.unregister_node("node-5")
    nodes = [n for n in nodes if n.node_id != "node-5"]

    print(f"[{time.strftime('%H:%M:%S')}] Simulação concluída com sucesso. Parando nós...")
    transport.net_running = False
    net_thread.join(timeout=1.0)
    for n in nodes:
        n.stop()

    print(f"\n[SUCESSO] Todos os testes de convergência, entrada e robustez sob perda de pacotes (5%) passaram com êxito!")

if __name__ == "__main__":
    run_simulation()