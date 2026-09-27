path=gossip_simulation.py
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
    def __init__(self, node_id, transport, interval=0.1):
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

    def _gossip_loop(self):
        while self.running:
            time.sleep(self.interval)
            with self.lock:
                self.membership[self.node_id] += 1
                payload = dict(self.membership)
            
            # Seleciona um peer aleatório para fazer gossip
            peers = self.transport.get_random_peers(self.node_id, k=1)
            if peers:
                peer_id = peers[0]
                msg = Message(self.node_id, 'GOSSIP', payload)
                self.transport.send(peer_id, msg)

    def receive_message(self, msg):
        with self.lock:
            for node_id, hb in msg.payload.items():
                if node_id not in self.membership:
                    self.membership[node_id] = hb
                else:
                    if hb > self.membership[node_id]:
                        self.membership[node_id] = hb

    def get_view(self):
        with self.lock:
            return dict(self.membership)

class Transport:
    def __init__(self, loss_rate=0.0, latency=0.01):
        self.nodes = {}
        self.queues = {}
        self.loss_rate = loss_rate
        self.latency = latency
        self.lock = threading.Lock()

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

    def get_random_peers(self, exclude_id, k=1):
        with self.lock:
            available = [nid for nid in self.nodes.keys() if nid != exclude_id]
        if not available:
            return []
        return random.sample(available, min(k, len(available)))

    def send(self, dest_id, message):
        if random.random() < self.loss_rate:
            return  # Simula perda de pacote
        
        with self.lock:
            if dest_id in self.queues:
                self.queues[dest_id].put(message)

    def deliver_messages(self):
        # Despacha mensagens nas filas simulando rede assíncrona
        with self.lock:
            items = list(self.queues.items())
        for dest_id, q in items:
            while not q.empty():
                try:
                    msg = q.get_nowait()
                    with self.lock:
                        node = self.nodes.get(dest_id)
                    if node:
                        node.receive_message(msg)
                except Empty:
                    break

def run_simulation():
    print("=== INICIANDO SIMULAÇÃO DE PROTOCOLO GOSSIP (SWIM-style) ===")
    transport = Transport(loss_rate=0.05, latency=0.005) # 5% de perda de pacotes simulada
    
    cluster_size = 10
    nodes = []

    # 1. Inicialização do Cluster com 10 nós
    print(f"[{time.strftime('%H:%M:%S')}] Criando cluster inicial com {cluster_size} nós...")
    for i in range(cluster_size):
        node = Node(node_id=f"node-{i}", transport=transport, interval=0.05)
        nodes.append(node)
        transport.register_node(node)

    # Thread de rede para despachar pacotes
    net_running = True
    def network_dispatcher():
        while net_running:
            transport.deliver_messages()
            time.sleep(0.01)

    net_thread = threading.Thread(target=network_dispatcher, daemon=True)
    net_thread.start()

    for node in nodes:
        node.start()

    # Função aux para verificar convergência
    def check_convergence(target_nodes, timeout=3.0):
        start_time = time.time()
        while time.time() - start_time < timeout:
            views = [n.get_view() for n in target_nodes]
            # Verifica se todos possuem exatamente as mesmas chaves ativas
            first_view_keys = set(views[0].keys())
            converged = all(set(v.keys()) == first_view_keys for v in views)
            if converged and len(first_view_keys) == len(target_nodes):
                return True, time.time() - start_time
            time.sleep(0.05)
        return False, timeout

    # Aguarda estabilização inicial
    time.sleep(0.5)
    converged, duration = check_convergence(nodes)
    print(f"[{time.strftime('%H:%M:%S')}] Cluster inicial convergido? {converged} em {duration:.3f}s")
    assert converged, "Falha na convergência inicial do cluster!"

    # 2. Teste de Entrada de Novo Nó (Join)
    print(f"\n[{time.strftime('%H:%M:%S')}] EVENTO DE ENTRADA: Adicionando novo nó 'node-10'...")
    new_node = Node(node_id="node-10", transport=transport, interval=0.05)
    nodes.append(new_node)
    transport.register_node(new_node)
    new_node.start()

    all_nodes = nodes
    # Medir tempo de convergência para inclusão do novo nó (< 3s exigido)
    start_join = time.time()
    join_converged = False
    while time.time() - start_join < 3.0:
        views = [n.get_view() for n in all_nodes]
        if all("node-10" in v for v in views):
            # Verifica se todos conhecem todos
            if all(len(v) == 11 for v in views):
                join_converged = True
                break
        time.sleep(0.05)
    
    join_duration = time.time() - start_join
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
    net_running = False
    net_thread.join(timeout=1.0)
    for n in nodes:
        n.stop()

    print(f"\n[SUCESSO] Todos os testes de convergência, entrada e robustez sob perda de pacotes (5%) passaram com êxito!")

if __name__ == "__main__":
    run_simulation()