import time
import sys

# --- Implementação Incremental do Motor Rete ---

class WorkingMemory:
    def __init__(self):
        self.facts = {}
        self.next_id = 1

    def assert_fact(self, fact_type, attributes):
        fact_id = self.next_id
        self.next_id += 1
        fact = {"id": fact_id, "type": fact_type, **attributes}
        self.facts[fact_id] = fact
        return fact

    def retract_fact(self, fact_id):
        if fact_id in self.facts:
            return self.facts.pop(fact_id)
        return None

class AlphaNode:
    def __init__(self, fact_type, predicate=None):
        self.fact_type = fact_type
        self.predicate = predicate
        self.items = {}  # {fact_id: fact} para acesso O(1) em retract

    def activate(self, fact):
        if fact["type"] == self.fact_type:
            if self.predicate is None or self.predicate(fact):
                self.items[fact["id"]] = fact
                return True
        return False

    def retract(self, fact):
        if fact["id"] in self.items:
            del self.items[fact["id"]]
            return True
        return False

class BetaMemory:
    def __init__(self):
        # Armazena tokens como tuplas (l_fact, r_fact) e índices para remoção rápida
        self.tokens = {} # {(l_id, r_id): (l_fact, r_fact)}

    def add_token(self, l_fact, r_fact):
        key = (l_fact["id"], r_fact["id"])
        self.tokens[key] = (l_fact, r_fact)

    def remove_token_by_fact(self, fact_id):
        keys_to_remove = [k for k in self.tokens if k[0] == fact_id or k[1] == fact_id]
        for k in keys_to_remove:
            del self.tokens[k]

class BetaJoinNode:
    def __init__(self, left_alpha, right_alpha, join_key_left, join_key_right):
        self.left_alpha = left_alpha
        self.right_alpha = right_alpha
        self.left_key = join_key_left
        self.right_key = join_key_right
        self.memory = BetaMemory()
        
        # Índices para hash join incremental
        self.left_index = {}   # {val: [l_fact, ...]}
        self.right_index = {}  # {val: [r_fact, ...]}

    def assert_left(self, l_fact):
        val = l_fact.get(self.left_key)
        if val is not None:
            self.left_index.setdefault(val, []).append(l_fact)
            if val in self.right_index:
                for r_fact in self.right_index[val]:
                    self.memory.add_token(l_fact, r_fact)

    def assert_right(self, r_fact):
        val = r_fact.get(self.right_key)
        if val is not None:
            self.right_index.setdefault(val, []).append(r_fact)
            if val in self.left_index:
                for l_fact in self.left_index[val]:
                    self.memory.add_token(l_fact, r_fact)

    def retract_fact(self, fact):
        fact_id = fact["id"]
        self.memory.remove_token_by_fact(fact_id)
        
        # Limpar índices
        for val, lst in self.left_index.items():
            self.left_index[val] = [f for f in lst if f["id"] != fact_id]
        for val, lst in self.right_index.items():
            self.right_index[val] = [f for f in lst if f["id"] != fact_id]

class ReteEngine:
    def __init__(self):
        self.wm = WorkingMemory()
        self.alpha_nodes = []
        self.beta_nodes = []

    def add_alpha_node(self, node):
        self.alpha_nodes.append(node)
        return node

    def add_beta_node(self, node):
        self.beta_nodes.append(node)
        return node

    def process_fact(self, fact_type, attributes):
        fact = self.wm.assert_fact(fact_type, attributes)
        for alpha in self.alpha_nodes:
            if alpha.activate(fact):
                # Propagação incremental para nós Beta
                for beta in self.beta_nodes:
                    if beta.left_alpha == alpha:
                        beta.assert_left(fact)
                    elif beta.right_alpha == alpha:
                        beta.assert_right(fact)
        return fact

    def retract_fact(self, fact_id):
        fact = self.wm.retract_fact(fact_id)
        if fact:
            for alpha in self.alpha_nodes:
                if alpha.retract(fact):
                    for beta in self.beta_nodes:
                        beta.retract_fact(fact)
        return fact

    def get_results(self):
        results = []
        for beta in self.beta_nodes:
            results.extend(list(beta.memory.tokens.values()))
        return results

def test_rete_performance_and_correctness():
    engine = ReteEngine()

    client_alpha = engine.add_alpha_node(
        AlphaNode("Client", lambda f: f.get("tier") == "VIP")
    )
    tx_alpha = engine.add_alpha_node(
        AlphaNode("Transaction", lambda f: f.get("amount", 0) > 1000)
    )

    engine.add_beta_node(
        BetaJoinNode(client_alpha, tx_alpha, "client_id", "client_id")
    )

    num_facts = 10000
    start_time = time.time()

    fact_range = range(1, num_facts // 2 + 1)
    f_ids = []
    for i in fact_range:
        tier = "VIP" if i % 5 == 0 else "Regular"
        c = engine.process_fact("Client", {"client_id": i, "tier": tier})
        f_ids.append(c["id"])

        amount = 1500 if i % 5 == 0 else 500
        t = engine.process_fact("Transaction", {"client_id": i, "amount": amount})
        f_ids.append(t["id"])

    elapsed_insertion = time.time() - start_time
    print(f"Inseridos e processados {num_facts} fatos incrementalmente em {elapsed_insertion:.4f} segundos.")

    eval_start = time.time()
    results = engine.get_results()
    eval_duration = (time.time() - eval_start) * 1000 # em milissegundos

    print(f"Resultados obtidos da rede Rete em {eval_duration:.2f}ms.")
    print(f"Total de regras disparadas com sucesso: {len(results)}")

    # Teste adversarial de retract (remoção incremental)
    initial_results_count = len(results)
    # Remover o primeiro fato de cliente VIP inserido
    first_client_id = 5
    # Encontrar e remover fatos correspondentes ao client_id 5
    to_remove = [fid for fid, f in engine.wm.facts.items() if f.get("client_id"] == 5]
    for fid in to_remove:
        engine.retract_fact(fid)

    new_results = engine.get_results()
    print(f"Resultados após retract incremental: {len(new_results)}")

    assert eval_duration < 500, f"Falha de performance: Levou {eval_duration}ms (Excedeu 500ms)"
    assert len(new_results) < initial_results_count, "Falha no retract: tokens obsoletos não foram removidos incrementalmente."
    
    print("Experimento incremental e teste adversarial concluídos com sucesso.")

if __name__ == "__main__":
    try:
        test_rete_performance_and_correctness()
    except Exception as e:
        print(f"Erro no experimento: {e}")
        sys.exit(1)