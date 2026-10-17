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

class ReteEngine:
    def __init__(self):
        self.wm = WorkingMemory()
        self.alpha_nodes = []
        self.beta_memory = BetaMemory()
        self.rules = []

    def add_alpha_node(self, fact_type, predicate=None):
        node = AlphaNode(fact_type, predicate)
        self.alpha_nodes.append(node)
        return node

    def add_rule(self, alpha1, alpha2, join_condition, action):
        self.rules.append({
            "alpha1": alpha1,
            "alpha2": alpha2,
            "join_condition": join_condition,
            "action": action
        })

    def process_fact(self, fact_type, attributes):
        fact = self.wm.assert_fact(fact_type, attributes)
        
        # Propagação incremental nos nós Alfa
        activated_alphas = []
        for alpha in self.alpha_nodes:
            if alpha.activate(fact):
                activated_alphas.append(alpha)

        # Propagação incremental nos nós Beta (Joins)
        for rule in self.rules:
            a1 = rule["alpha1"]
            a2 = rule["alpha2"]
            join_cond = rule["join_condition"]

            # Se o fato ativou alpha1, testamos contra todos os itens existentes em alpha2
            if a1 in activated_alphas:
                for f2 in a2.items.values():
                    if join_cond(fact, f2):
                        self.beta_memory.add_token(fact, f2)

            # Se o fato ativou alpha2, testamos contra todos os itens existentes em alpha1
            if a2 in activated_alphas:
                for f1 in a1.items.values():
                    if join_cond(f1, fact):
                        self.beta_memory.add_token(f1, fact)

        return fact

    def retract_fact(self, fact_id):
        fact = self.wm.retract_fact(fact_id)
        if not fact:
            return

        # Propagar remoção nos nós Alfa
        for alpha in self.alpha_nodes:
            alpha.retract(fact)

        # Propagar remoção nas memórias Beta
        self.beta_memory.remove_token_by_fact(fact_id)

    def get_results(self):
        results = []
        for rule in self.rules:
            for l_fact, r_fact in self.beta_memory.tokens.values():
                res = rule["action"](l_fact, r_fact)
                if res:
                    results.append(res)
        return results

def test_rete_performance_and_correctness():
    engine = ReteEngine()

    # Definir nós Alfa
    alpha_trans = engine.add_alpha_node("Transaction", lambda f: f["amount"] > 100)
    alpha_client = engine.add_alpha_node("Client", lambda f: f["status"] == "VIP")

    # Regra: Transação alta (> 100) feita por cliente VIP
    engine.add_rule(
        alpha1=alpha_trans,
        alpha2=alpha_client,
        join_condition=lambda t, c: t["client_id"] == c["client_id"],
        action=lambda t, c: {"alert": f"VIP {c['client_id']} fez transação {t['id']}"}
    )

    num_facts = 10000
    start_time = time.time()

    # Inserção incremental de Clientes e Transações
    f_ids = []
    for i in range(1, num_facts // 2 + 1):
        c = engine.process_fact("Client", {"client_id": i, "status": "VIP" if i % 5 == 0 else "Normal"})
        f_ids.append(c["id"])
        
        amount = 150 if i % 5 == 0 else 500
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
    
    # Correção do SyntaxError anterior: fechamento correto do parêntese
    to_remove = [fid for fid, f in engine.wm.facts.items() if f.get("client_id") == 5]
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