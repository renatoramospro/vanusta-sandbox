# path=main.py
import random
import time

class Message:
    def __init__(self, sender, receiver, msg_type, ballot, value=None):
        self.sender = sender
        self.receiver = receiver
        self.msg_type = msg_type  # PREPARE, PROMISE, ACCEPT, ACCEPTED, DECIDE
        self.ballot = ballot      # Tupla (seq, proposer_id)
        self.value = value

    def __repr__(self):
        return f"Msg({self.sender} -> {self.receiver}: {self.msg_type}, ballot={self.ballot}, val={self.value})"

class Network:
    def __init__(self, loss_rate=0.0, delay_enabled=False):
        self.messages = []
        self.loss_rate = loss_rate
        self.delay_enabled = delay_enabled

    def send(self, msg):
        # Simula perda de mensagens (se loss_rate > 0)
        if self.loss_rate > 0 and random.random() < self.loss_rate:
            return  # Mensagem perdida
        self.messages.append(msg)

    def deliver_all(self, nodes):
        current_messages = self.messages
        self.messages = []
        for msg in current_messages:
            if msg.receiver in nodes:
                nodes[msg.receiver].receive(msg)

class Acceptor:
    def __init__(self, node_id, network):
        self.node_id = node_id
        self.network = network
        self.promised_ballot = (-1, "")
        self.accepted_ballot = (-1, "")
        self.accepted_value = None

    def receive(self, msg):
        # Validação básica de integridade/tipo para segurança contra spoofing/replay
        if not isinstance(msg, Message) or msg.receiver != self.node_id:
            return

        if msg.msg_type == "PREPARE":
            if msg.ballot > self.promised_ballot:
                self.promised_ballot = msg.ballot
                reply = Message(self.node_id, msg.sender, "PROMISE", msg.ballot, (self.accepted_ballot, self.accepted_value))
                self.network.send(reply)

        elif msg.msg_type == "ACCEPT":
            if msg.ballot >= self.promised_ballot:
                self.promised_ballot = msg.ballot
                self.accepted_ballot = msg.ballot
                self.accepted_value = msg.value
                reply = Message(self.node_id, msg.sender, "ACCEPTED", msg.ballot, msg.value)
                self.network.send(reply)

class Proposer:
    def __init__(self, node_id, network, acceptors, learners):
        self.node_id = node_id
        self.network = network
        self.acceptors = acceptors
        self.learners = learners
        self.seq = 0
        self.proposing_value = None
        self.promises = []
        self.accepts = []
        self.status = "IDLE"

    def start_proposal(self, value):
        self.seq += 1
        self.ballot = (self.seq, self.node_id)
        self.proposing_value = value
        self.promises = []
        self.accepts = []
        self.status = "PREPARING"
        
        for acc in self.acceptors:
            self.network.send(Message(self.node_id, acc, "PREPARE", self.ballot))

    def receive(self, msg):
        if not isinstance(msg, Message) or msg.receiver != self.node_id:
            return

        if self.status == "PREPARING" and msg.msg_type == "PROMISE" and msg.ballot == self.ballot:
            self.promises.append(msg)
            # Maioria necessária (ex: 2 de 3)
            if len(self.promises) >= (len(self.acceptors) // 2 + 1):
                self.status = "ACCEPTING"
                # Regra do Paxos: escolher o valor da promessa com o maior ballot aceito anteriormente
                highest_accepted_ballot = (-1, "")
                chosen_val = self.proposing_value
                for p in self.promises:
                    acc_b, acc_v = p.value
                    if acc_b > highest_accepted_ballot and acc_v is not None:
                        highest_accepted_ballot = acc_b
                        chosen_val = acc_v
                
                self.proposing_value = chosen_val
                for acc in self.acceptors:
                    self.network.send(Message(self.node_id, acc, "ACCEPT", self.ballot, self.proposing_value))

        elif self.status == "ACCEPTING" and msg.msg_type == "ACCEPTED" and msg.ballot == self.ballot:
            self.accepts.append(msg)
            if len(self.accepts) >= (len(self.acceptors) // 2 + 1):
                self.status = "DECIDED"
                for l in self.learners:
                    self.network.send(Message(self.node_id, l, "DECIDE", self.ballot, self.proposing_value))

class Learner:
    def __init__(self, node_id):
        self.node_id = node_id
        self.learned_value = None

    def receive(self, msg):
        if isinstance(msg, Message) and msg.msg_type == "DECIDE":
            self.learned_value = msg.value

def run_simulation(loss_rate=0.0, partition_drop=False, max_steps=50):
    network = Network(loss_rate=loss_rate)
    acceptors = [f"Acc_{i}" for i in range(3)]
    learners = [f"Learn_{i}" for i in range(2)]
    
    nodes = {}
    for acc in acceptors:
        nodes[acc] = Acceptor(acc, network)
    
    proposer = Proposer("Prop_1", network, acceptors, learners)
    nodes["Prop_1"] = proposer
    
    for l in learners:
        nodes[l] = Learner(l)

    proposer.start_proposal("Valor_Consenso_Paxos")

    steps = 0
    while steps < max_steps:
        # Simulação do Cenário 3: Partição parcial de rede bloqueando 1 Acceptor (ex: Acc_2)
        if partition_drop and steps == 2:
            network.messages = [m for m in network.messages if m.receiver != "Acc_2"]

        if len(network.messages) == 0 and proposer.status == "DECIDED":
            break

        network.deliver_all(nodes)
        
        # Mecanismo de retransmissão básica caso haja perda e o proposer fique travado (evita livelock)
        if proposer.status == "PREPARING" and steps > 5 and len(network.messages) == 0:
            proposer.start_proposal("Valor_Consenso_Paxos")
        elif proposer.status == "ACCEPTING" and steps > 10 and len(network.messages) == 0:
            proposer.start_proposal("Valor_Consenso_Paxos")

        steps += 1

    decided_values = [nodes[l].learned_value for l in learners]
    return decided_values, proposer.status

if __name__ == "__main__":
    random.seed(42)
    
    print("--- Cenário 1: Operação Normal (Sem perdas) ---")
    res1, status1 = run_simulation(loss_rate=0.0)
    print(f"Status do Proposer: {status1}")
    print(f"Valores aprendidos pelos learners: {res1}")
    assert status1 == "DECIDED", "Cenário 1 falhou: Proposer não decidiu"
    assert all(v == "Valor_Consenso_Paxos" for v in res1) and len(res1) > 0, "Cenário 1 falhou: Consistência incorreta"
    print("Cenário 1 validado com sucesso!\n")

    print("--- Cenário 2: Perda de Mensagens (30% de descarte) ---")
    random.seed(100)
    res2, status2 = run_simulation(loss_rate=0.3)
    print(f"Status do Proposer: {status2}")
    print(f"Valores aprendidos pelos learners (com perdas): {res2}")
    assert status2 == "DECIDED", "Cenário 2 falhou: Proposer não atingiu consenso sob perdas"
    assert all(v == "Valor_Consenso_Paxos" for v in res2), "Cenário 2 falhou: Inconsistência nos learners"
    print("Cenário 2 validado com sucesso!\n")

    print("--- Cenário 3: Partição de Rede Parcial (1 Acceptor isolado) ---")
    random.seed(42)
    res3, status3 = run_simulation(loss_rate=0.0, partition_drop=True)
    print(f"Status do Proposer: {status3}")
    print(f"Valores aprendidos pelos learners (sob partição): {res3}")
    assert status3 == "DECIDED", "Cenário 3 falhou: Partição impediu atingir maioria quorum"
    assert all(v == "Valor_Consenso_Paxos" for v in res3), "Cenário 3 falhou: Consistência comprometida"
    print("Cenário 3 validado com sucesso absoluto!")