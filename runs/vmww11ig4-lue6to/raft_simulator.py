import random
import time

class LogEntry:
    def __init__(self, term, command):
        self.term = term
        self.command = command

    def __repr__(self):
        return f"(Term:{self.term}, Cmd:{self.command})"

class RaftNode:
    def __init__(self, node_id, peer_ids):
        self.node_id = node_id
        self.peer_ids = peer_ids
        
        # Estado persistente
        self.current_term = 0
        self.voted_for = None
        self.log = [] # Lista de LogEntry
        
        # Estado volátil em todos os nós
        self.commit_index = -1
        self.last_applied = -1
        self.state = "Follower" # Follower, Candidate, Leader
        
        # Controle de tempo para timeout de eleição
        self.reset_election_timeout()
        self.heartbeat_interval = 0.05 # 50ms

    def reset_election_timeout(self):
        # Timeout randômico entre 150ms e 300ms para evitar split votes
        self.election_timeout = time.time() + random.uniform(0.15, 0.30)

    def handle_request_vote(self, term, candidate_id, last_log_index, last_log_term):
        # Regra de segurança de eleição do Raft
        if term > self.current_term:
            self.current_term = term
            self.state = "Follower"
            self.voted_for = None

        if term == self.current_term and (self.voted_for is None or self.voted_for == candidate_id):
            # Verifica se o log do candidato é pelo menos tão atualizado quanto o próprio log
            my_last_term = self.log[-1].term if self.log else -1
            my_last_index = len(self.log) - 1

            up_to_date = (last_log_term > my_last_term) or \
                         (last_log_term == my_last_term and last_log_index >= my_last_index)
            
            if up_to_date:
                self.voted_for = candidate_id
                self.reset_election_timeout()
                return True
        return False

    def handle_append_entries(self, term, leader_id, prev_log_index, prev_log_term, entries, leader_commit):
        if term < self.current_term:
            return False, self.current_term

        # Se o termo RPC for maior ou igual, atualiza estado e vira/mantém Follower
        if term > self.current_term:
            self.current_term = term
            self.state = "Follower"
            self.voted_for = None

        self.reset_election_timeout()

        # Verificação de consistência do log (prevLogIndex e prevLogTerm)
        if prev_log_index >= 0:
            if len(self.log) <= prev_log_index or self.log[prev_log_index].term != prev_log_term:
                return False, self.current_term

        # Processa novas entradas (sobrescreve conflitos se houver)
        self.log = self.log[:prev_log_index + 1] + entries

        # Atualiza commit_index
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log) - 1)

        return True, self.current_term

class RaftCluster:
    def __init__(self, num_nodes=3):
        self.nodes = {}
        node_ids = [f"Node-{i}" for i in range(num_nodes)]
        for nid in node_ids:
            peers = [p for p in node_ids if p != nid]
            self.nodes[nid] = RaftNode(nid, peers)

    def run_election_test(self):
        print("=== INICIANDO TESTE DE ELEIÇÃO DE LÍDER ===")
        # Simula passagem do tempo para forçar timeout no Node-0
        self.nodes["Node-0"].election_timeout = time.time() - 0.01
        
        time.sleep(0.05)
        # Processa timeout e simula votação
        node = self.nodes["Node-0"]
        if time.time() > node.election_timeout and node.state == "Follower":
            node.state = "Candidate"
            node.current_term += 1
            node.voted_for = node.node_id
            votes = 1
            
            last_idx = len(node.log) - 1
            last_term = node.log[-1].term if node.log else -1

            for peer_id in node.peer_ids:
                peer = self.nodes[peer_id]
                granted = peer.handle_request_vote(node.current_term, node.node_id, last_idx, last_term)
                if granted:
                    votes += 1

            if votes > (len(self.nodes) // 2):
                node.state = "Leader"
                print(f"Sucesso: {node.node_id} eleito líder no Termo {node.current_term} com {votes} votos.")

    def run_log_replication_test(self):
        print("\n=== INICIANDO TESTE DE REPLICAÇÃO DE LOG ===")
        leader = next(n for n in self.nodes.values() if n.state == "Leader")
        
        # Cliente submete comando ao líder
        command = "SET x=10"
        new_entry = LogEntry(leader.current_term, command)
        leader.log.append(new_entry)
        
        prev_index = len(leader.log) - 2
        prev_term = leader.log[prev_index].term if prev_index >= 0 else -1
        
        success_count = 1
        for peer_id in leader.peer_ids:
            peer = self.nodes[peer_id]
            success, _ = peer.handle_append_entries(
                leader.current_term, leader.node_id,
                prev_index, prev_term, [new_entry], leader.commit_index
            )
            if success:
                success_count += 1

        # Regra de Commit: Maioria
        if success_count > (len(self.nodes) // 2):
            leader.commit_index = len(leader.log) - 1
            print(f"Líder {leader.node_id} comitou o log. Commit Index: {leader.commit_index}")

        # Verifica convergência
        for nid, node in self.nodes.items():
            print(f"[{nid}] Estado: {node.state}, Log: {node.log}, CommitIndex: {node.commit_index}")
            assert node.log == leader.log, f"Divergência de log detectada no {nid}!"

if __name__ == "__main__":
    cluster = RaftCluster(3)
    cluster.run_election_test()
    cluster.run_log_replication_test()
    print("\n[SUCESSO] Testes do Raft executados sem divergência de estado.")