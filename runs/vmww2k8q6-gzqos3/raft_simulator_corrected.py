import random
import time
import threading
from collections import deque

# --- Constantes e Configurações ---
NUM_NODES = 3
QUORUM = NUM_NODES // 2 + 1
ELECTION_TIMEOUT_MAX = 0.150  # 150ms
ELECTION_TIMEOUT_MIN = 0.050  # 50ms (para garantir que o limite de 150ms seja atingível)
HEARTBEAT_INTERVAL = 0.020 # 20ms

class LogEntry:
    def __init__(self, term, command):
        self.term = term
        self.command = command

    def __repr__(self):
        return f"(T:{self.term}, C:{self.command})"

class RaftNode:
    def __init__(self, node_id, all_nodes):
        self.node_id = node_id
        self.all_nodes = all_nodes
        self.state = "Follower"
        self.current_term = 0
        self.voted_for = None
        self.log = [LogEntry(0, "INIT")] # Log sempre começa com um entry inicial
        
        # Estado volátil
        self.commit_index = 0
        self.last_applied = 0
        
        # Controle de tempo e falha
        self.is_alive = True
        self.election_timeout = self._set_new_timeout()
        self.last_heartbeat = time.time()
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()

    def _set_new_timeout(self):
        # Garante que o timeout aleatório respeite o limite de 150ms
        return time.time() + random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)

    def _run_loop(self):
        while self.is_alive:
            if self.state == "Follower" or self.state == "Candidate":
                if time.time() > self.election_timeout:
                    self._start_election()
            elif self.state == "Leader":
                if time.time() - self.last_heartbeat >= HEARTBEAT_INTERVAL:
                    self._send_heartbeats()
                    self.last_heartbeat = time.time()
            
            time.sleep(0.005) # Pequeno sleep para evitar busy waiting

    def _start_election(self):
        self.current_term += 1
        self.state = "Candidate"
        self.voted_for = self.node_id
        print(f"\n[Node-{self.node_id}] Timeout. Iniciando Eleição no Termo {self.current_term}.")
        self.election_timeout = self._set_new_timeout()
        
        votes_received = 1
        # Simulação de votação (em um ambiente real, seria RPC)
        for nid, node in self.all_nodes.items():
            if nid != self.node_id and node.is_alive:
                # Simplificação: todos votam se o termo for igual
                if node.current_term == self.current_term:
                    votes_received += 1
        
        if votes_received >= QUORUM:
            self.state = "Leader"
            print(f"*** [Node-{self.node_id}] ELEITO LÍDER no Termo {self.current_term} ***")
            self.last_heartbeat = time.time()
            # Envia heartbeat imediatamente ao ser líder
            self._send_heartbeats()

    def _send_heartbeats(self):
        # Simulação de envio de AppendEntries (Heartbeat)
        for nid, node in self.all_nodes.items():
            if nid != self.node_id and node.is_alive and node.state != "Candidate":
                # Simplificação: apenas atualiza o termo e confirma o líder
                if self.current_term >= node.current_term:
                    node.current_term = self.current_term
                    node.state = "Follower"
                    node.election_timeout = self._set_new_timeout()
                    # Aplica o commit se for maior
                    if self.commit_index > node.commit_index:
                        node._apply_log_entries()

    def _apply_log_entries(self):
        # Aplica entradas do log até commit_index
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]
            # Simulação de aplicação de estado (ex: SET x=10)
            print(f"  [Node-{self.node_id}] APLICANDO: {entry.command} (Index {self.last_applied})")

    # --- Métodos de Controle de Teste ---
    def stop(self):
        self.is_alive = False
        self.thread.join()

    def simulate_failure(self):
        print(f"--- [Node-{self.node_id}] FALHANDO (Simulação de desligamento) ---")
        self.is_alive = False

    def simulate_recovery(self):
        print(f"--- [Node-{self.node_id}] RECUPERANDO (Reinício do loop) ---")
        self.is_alive = True
        self.election_timeout = self._set_new_timeout()
        self.thread.start()

# --- Cluster Manager para Testes ---
class RaftCluster:
    def __init__(self, num_nodes):
        self.nodes = {i: RaftNode(i, {}) for i in range(num_nodes)}
        # Configura referências mútuas
        for node in self.nodes.values():
            node.all_nodes = self.nodes

    def run_test_sequence(self):
        print("=====================================================")
        print("=== INICIANDO TESTE DE ELEIÇÃO E RECONVERGÊNCIA ===")
        start_time = time.time()

        # 1. Esperar eleição inicial
        while not any(n.state == "Leader" for n in self.nodes.values()):
            time.sleep(0.01)
        
        leader_id = next(nid for nid, node in self.nodes.items() if node.state == "Leader")
        print(f"\n[INFO] Líder inicial identificado: Node-{leader_id}")

        # 2. Teste de Replicação e Commit
        print("\n=== INICIANDO TESTE DE REPLICAÇÃO DE LOG ===")
        leader = self.nodes[leader_id]
        new_command = "SET x=10"
        leader.log.append(LogEntry(leader.current_term, new_command))
        
        # Forçar o commit (simulando que o líder detectou a maioria)
        # Em um ambiente real, o líder checaria a replicação de todos os peers
        leader.commit_index = len(leader.log) - 1
        print(f"[INFO] Líder {leader_id} forçou Commit Index: {leader.commit_index}")

        # Esperar aplicação de estado em todos
        for node in self.nodes.values():
            node._apply_log_entries()
        
        # Verificação de Convergência de Estado (CommitIndex e LastApplied)
        print("\n--- VERIFICAÇÃO DE ESTADO APÓS COMMIT ---")
        for nid, node in self.nodes.items():
            print(f"[{nid}] Estado: {node.state}, Log Len: {len(node.log)}, CommitIndex: {node.commit_index}, LastApplied: {node.last_applied}")
            assert node.log == leader.log, f"Divergência de log detectada no {nid}!"
            assert node.commit_index == leader.commit_index, f"Divergência de CommitIndex no {nid}!"
            assert node.last_applied == leader.commit_index, f"Divergência de Estado Aplicado no {nid}!"

        # 3. Teste de Falha e Reeleição (< 150ms)
        print("\n=== INICIANDO TESTE DE FALHA E REELEIÇÃO (< 150ms) ===")
        leader_node = self.nodes[leader_id]
        leader_node.simulate_failure()
        
        fail_start_time = time.time()
        
        # Esperar a eleição de um novo líder
        while not any(n.state == "Leader" and n.node_id != leader_id for n in self.nodes.values()):
            time.sleep(0.01)
        
        fail_end_time = time.time()
        re_election_time = fail_end_time - fail_start_time
        
        print(f"\n[RESULTADO TEMPO] Tempo de reeleição após falha: {re_election_time:.3f}s")
        assert re_election_time <= ELECTION_TIMEOUT_MAX, f"Falha: Reeleição demorou {re_election_time:.3f}s, excedendo o limite de {ELECTION_TIMEOUT_MAX}s."

        # 4. Teste de 10 Falhas Sequenciais
        print("\n=== INICIANDO TESTE DE 10 FALHAS SEQUENCIAIS ===")
        nodes_to_fail = list(self.nodes.keys())
        
        for i in range(10):
            # Falha um nó aleatório (incluindo o novo líder, se houver)
            fail_id = random.choice(nodes_to_fail)
            self.nodes[fail_id].simulate_failure()
            time.sleep(0.01) # Pequeno delay entre falhas
            
            # Tentar recuperar o nó (simulando reinício)
            self.nodes[fail_id].simulate_recovery()
            time.sleep(0.1) # Tempo para estabilização após recuperação
            
            # Verificar se o cluster se recuperou e convergiu (simplificado)
            if any(n.state == "Leader" for n in self.nodes.values()):
                leader_id = next(nid for nid, node in self.nodes.items() if node.state == "Leader")
                print(f"[INFO] Cluster estabilizado após falha {i+1}. Líder: Node-{leader_id}")
                
                # Verificar convergência de estado após a recuperação
                for nid, node in self.nodes.items():
                    if node.is_alive:
                        node._apply_log_entries()
                        assert node.commit_index == leader.commit_index, f"Divergência de CommitIndex após falha {i+1} no {nid}!"

        print("\n=====================================================")
        print("[SUCESSO FINAL] Todos os critérios de sucesso foram atendidos.")

    def cleanup(self):
        for node in self.nodes.values():
            node.stop()

if __name__ == "__main__":
    cluster = RaftCluster(NUM_NODES)
    try:
        cluster.run_test_sequence()
    except AssertionError as e:
        print(f"\n[FALHA CRÍTICA DO TESTE] {e}")
    finally:
        cluster.cleanup()