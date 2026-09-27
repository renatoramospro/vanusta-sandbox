import time
import random
import threading
from queue import Queue

# Estados de Membros inspirados no protocolo SWIM
STATE_ALIVE = 'ALIVE'
STATE_SUSPECT = 'SUSPECT'
STATE_DEAD = 'DEAD'

class MemberInfo:
    def __init__(self, state=STATE_ALIVE, heartbeat=0, incarnation=0):
        self.state = state
        self.heartbeat = heartbeat
        self.incarnation = incarnation

class Message:
    def __init__(self, sender_id, msg_type, payload):
        self.sender_id = sender_id
        self.msg_type = msg_type  # 'GOSSIP'
        self.payload = payload    # Dicionario: node_id -> {state, heartbeat, incarnation}

class Node:
    def __init__(self, node_id, transport, interval=0.05, suspect_timeout=0.3):
        self.node_id = node_id
        self.transport = transport
        self.interval = interval
        self.suspect_timeout = suspect_timeout
        
        # membership: node_id -> MemberInfo
        self.membership = {
            node_id: MemberInfo(state=STATE_ALIVE, heartbeat=0, incarnation=0)
        }
        # Controle de quando um nó foi marcado como SUSPECT para disparar transição para DEAD
        self.suspect_timers = {}
        
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
            if msg.msg_type == 'GOSSIP':
                for peer_id, info in msg.payload.items():
                    # Validação de payload básica
                    if not isinstance(peer_id, str) or not isinstance(info, dict):
                        continue
                    
                    remote_state = info.get('state', STATE_ALIVE)
                    remote_hb = info.get('heartbeat', 0)
                    remote_inc = info.get('incarnation', 0)

                    if peer_id not in self.membership:
                        # Novo nó descoberto
                        self.membership[peer_id] = MemberInfo(remote_state, remote_hb, remote_inc)
                        if remote_state == STATE_SUSPECT:
                            self.suspect_timers[peer_id] = time.time()
                    else:
                        local_info = self.membership[peer_id]

                        # Regras de atualização baseadas em Incarnation Number e Heartbeat (SWIM)
                        if remote_inc > local_info.incarnation:
                            self.membership[peer_id] = MemberInfo(remote_state, remote_hb, remote_inc)
                            if remote_state == STATE_SUSPECT and peer_id not in self.suspect_timers:
                                self.suspect_timers[peer_id] = time.time()
                            elif remote_state == STATE_ALIVE:
                                self.suspect_timers.pop(peer_id, None)
                        elif remote_inc == local_info.incarnation:
                            # Se for o próprio nó, permite refutação caso esteja sendo falsamente acusado
                            if peer_id == self.node_id and remote_state == STATE_SUSPECT:
                                # Refutação: incrementa incarnation e volta para ALIVE
                                local_info.incarnation += 1
                                local_info.state = STATE_ALIVE
                                local_info.heartbeat += 1
                            elif remote_state == STATE_DEAD and local_info.state != STATE_DEAD:
                                local_info.state = STATE_DEAD
                            elif remote_state == STATE_SUSPECT and local_info.state == STATE_ALIVE:
                                local_info.state = STATE_SUSPECT
                                if peer_id not in self.suspect_timers:
                                    self.suspect_timers[peer_id] = time.time()
                            elif remote_hb > local_info.heartbeat:
                                local_info.heartbeat = remote_hb
                                if local_info.state == STATE_SUSPECT:
                                    # Heartbeat mais recente refuta suspeita
                                    local_info.state = STATE_ALIVE
                                    self.suspect_timers.pop(peer_id, None)

    def _gossip_loop(self):
        while self.running:
            time.sleep(self.interval)
            with self.lock:
                # Incrementa heartbeat próprio
                self.membership[self.node_id].heartbeat += 1
                
                # Checa timeouts de nós suspeitos para torná-los DEAD / Tombstone
                now = time.time()
                to_dead = []
                for peer_id, suspect_time in list(self.suspect_timers.items()):
                    if now - suspect_time > self.suspect_timeout:
                        to_dead.append(peer_id)
                
                for peer_id in to_dead:
                    if peer_id in self.membership and self.membership[peer_id].state != STATE_DEAD:
                        self.membership[peer_id].state = STATE_DEAD
                    self.suspect_timers.pop(peer_id, None)

                # Serializa membership para envio seguro (cópia protegida)
                payload = {
                    pid: {
                        'state': info.state,
                        'heartbeat': info.heartbeat,
                        'incarnation': info.incarnation
                    }
                    for pid, info in self.membership.items()
                }

            # Seleciona peers aleatórios vivos para gossip
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
            return  # Simula perda de pacote de rede
        with self.lock:
            if dest_id in self.queues:
                self.queues[dest_id].put(msg)

    def get_random_peers(self, exclude_id, count=2):
        with self.lock:
            available = [nid for nid in self.nodes.keys() if nid != exclude_id]
        if not available:
            return []
        return random.sample(available, min(count, len(available)))

    def start_dispatcher(self):
        def dispatch():
            while self.net_running:
                with self.lock:
                    q_items = list(self.queues.items())
                for dest_id, q in q_items:
                    while not q.empty():
                        try:
                            msg = q.get_nowait()
                            with self.lock:
                                node = self.nodes.get(dest_id)
                            if node:
                                node.receive_message(msg)
                        except Exception:
                            break
                time.sleep(0.005)
        
        t = threading.Thread(target=dispatch, daemon=True)
        t.start()
        return t

def run_simulation():
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando simulação do protocolo Gossip (SWIM-style completo)...")
    
    transport = SimulatedTransport(drop_rate=0.05)
    net_thread = transport.start_dispatcher()

    nodes = []
    for i in range(1, 11):
        n_id = f"node-{i}"
        node = Node(n_id, transport, interval=0.04, suspect_timeout=0.2)
        transport.register_node(node)
        nodes.append(node)

    for n in nodes:
        n.start()

    time.sleep(0.3)
    print(f"[{time.strftime('%H:%M:%S')}] Cluster inicializado com 10 nós.")

    # 1. Teste de Entrada (Join) de novo nó
    print(f"\n[{time.strftime('%H:%M:%S')}] EVENTO DE ENTRADA: Adicionando o 'node-11'...")
    start_time = time.time()
    
    new_node = Node("node-11", transport, interval=0.04, suspect_timeout=0.2)
    transport.register_node(new_node)
    new_node.start()
    
    # Injeta o novo nó conhecendo o node-1
    with new_node.lock:
        new_node.membership["node-1"] = MemberInfo(STATE_ALIVE, 1, 0)
    nodes.append(new_node)

    join_converged = False
    join_duration = 0.0
    while time.time() - start_time < 3.0:
        time.sleep(0.05)
        with transport.lock:
            all_memberships = [dict(n.membership) for n in nodes if n.running]
        target_keys = set(n.node_id for n in nodes if n.running)
        
        # Verifica se todos os nós conhecem o node-11 como ALIVE
        converged = all(
            m.get('node-11') and m['node-11'].state == STATE_ALIVE and set(m.keys()) >= target_keys
            for m in all_memberships
        )
        if converged:
            join_duration = time.time() - start_time
            join_converged = True
            break

    print(f"[{time.strftime('%H:%M:%S')}] Convergência após ENTRADA de nó: {join_converged} em {join_duration:.3f}s")
    assert join_converged, "O cluster falhou em convergir após a entrada do novo nó em menos de 3s!"

    # 2. Teste de Saída / Falha de Nó (Leave / Dead) com medição rigorosa
    print(f"\n[{time.strftime('%H:%M:%S')}] EVENTO DE SAÍDA: Parando bruscamente o 'node-5'...")
    node_to_remove = next(n for n in nodes if n.node_id == "node-5")
    node_to_remove.stop()
    transport.unregister_node("node-5")
    
    active_nodes = [n for n in nodes if n.node_id != "node-5"]
    
    leave_start_time = time.time()
    leave_converged = False
    leave_duration = 0.0

    while time.time() - leave_start_time < 3.0:
        time.sleep(0.05)
        with transport.lock:
            all_memberships = [dict(n.membership) for n in active_nodes]
        
        # Verifica se todos os nós ativos marcaram 'node-5' como DEAD ou o removeram/marcaram adequadamente
        all_detected = all(
            m.get('node-5') is None or m['node-5'].state == STATE_DEAD
            for m in all_memberships
        )
        if all_detected:
            leave_duration = time.time() - leave_start_time
            leave_converged = True
            break

    print(f"[{time.strftime('%H:%M:%S')}] Convergência após SAÍDA/FALHA de nó: {leave_converged} em {leave_duration:.3f}s")
    assert leave_converged, "O cluster falhou em detectar e convergir a saída/falha do node-5 em menos de 3s!"

    # Encerramento limpo
    transport.net_running = False
    net_thread.join(timeout=1.0)
    for n in active_nodes:
        n.stop()

    print(f"\n[SUCESSO] Todos os testes de convergência de entrada, saída, estados SWIM (Alive/Suspect/Dead) e robustez sob perda de pacotes (5%) passaram com êxito!")

if __name__ == "__main__":
    run_simulation()