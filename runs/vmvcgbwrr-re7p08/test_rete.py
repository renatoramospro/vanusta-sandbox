import time
import sys

# --- Implementação do Motor Rete ---

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

class AlphaNode:
    def __init__(self, fact_type, predicate=None):
        self.fact_type = fact_type
        self.predicate = predicate
        self.items = [] # Memória Alfa

    def activate(self, fact):
        if fact["type"] == self.fact_type:
            if self.predicate is None or self.predicate(fact):
                self.items.append(fact)
                return True
        return False

class BetaMemory:
    def __init__(self):
        self.tokens = [] # Lista de tuplas de fatos correspondidos

    def add_token(self, token):
        self.tokens.append(token)

class BetaJoinNode:
    def __init__(self, left_alpha, right_alpha, join_key_left, join_key_right):
        self.left_alpha = left_alpha
        self.right_alpha = right_alpha
        self.left_key = join_key_left
        self.right_key = join_key_right
        self.memory = BetaMemory()

    def evaluate(self):
        self.memory.tokens = []
        for l_fact in self.left_alpha.items:
            for r_fact in self.right_alpha.items:
                if l_fact.get(self.left_key) == r_fact.get(self.right_key):
                    self.memory.add_token((l_fact, r_fact))
        return self.memory.tokens

class ReteEngine:
    def __init__(self):
        self.wm = WorkingMemory()
        self.alpha_nodes = []
        self.beta_nodes = []
        self.rules = []

    def add_alpha_node(self, node):
        self.alpha_nodes.append(node)
        return node

    def add_beta_node(self, node):
        self.beta_nodes.append(node)
        return node

    def process_fact(self, fact_type, attributes):
        fact = self.wm.assert_fact(fact_type, attributes)
        # Propagação para os nós Alfa
        for alpha in self.alpha_nodes:
            alpha.activate(fact)
        return fact

    def fire_rules(self):
        results = []
        for beta in self.beta_nodes:
            tokens = beta.evaluate()
            results.extend(tokens)
        return results

# --- Experimento e Teste de Desempenho ---

def test_rete_performance_and_correctness():
    engine = ReteEngine()

    # Definindo nós Alfa para Clientes VIP e Transações de Alto Valor
    client_alpha = engine.add_alpha_node(
        AlphaNode("Client", lambda f: f.get("tier") == "VIP")
    )
    tx_alpha = engine.add_alpha_node(
        AlphaNode("Transaction", lambda f: f.get("amount", 0) > 1000)
    )

    # Nó Beta para juntar Clientes VIP com suas Transações pelo client_id
    engine.add_beta_node(
        BetaJoinNode(client_alpha, tx_alpha, "client_id", "client_id")
    )

    num_facts = 10000
    start_time = time.time()

    # Correção da sintaxe do loop (sem atribuição walrus no for)
    fact_range = range(1, num_facts // 2 + 1)
    for i in fact_range:
        tier = "VIP" if i % 5 == 0 else "Regular"
        engine.process_fact("Client", {"client_id": i, "tier": tier})

        amount = 1500 if i % 5 == 0 else 500
        engine.process_fact("Transaction", {"client_id": i, "amount": amount})

    elapsed_insertion = time.time() - start_time
    print(f"Inseridos {num_facts} fatos em {elapsed_insertion:.4f} segundos.")

    eval_start = time.time()
    results = engine.fire_rules()
    eval_duration = (time.time() - eval_start) * 1000 # em milissegundos

    print(f"Resultados processados pela rede Rete em {eval_duration:.2f}ms.")
    print(f"Total de regras disparadas com sucesso: {len(results)}")

    assert eval_duration < 500, f"Falha de performance: Levou {eval_duration}ms (Excedeu 500ms)"
    assert len(results) > 0, "Falha de correção: Nenhuma regra foi disparada."
    
    print("Experimento concluído com sucesso e dentro dos parâmetros exigidos.")

if __name__ == "__main__":
    try:
        test_rete_performance_and_correctness()
    except Exception as e:
        print(f"Erro no experimento: {e}")
        sys.exit(1)