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
        # Join simples por igualdade de chaves entre duas fontes alfa
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

    def add_alpha(self, fact_type, predicate=None):
        node = AlphaNode(fact_type, predicate)
        self.alpha_nodes.append(node)
        return node

    def add_rule(self, name, alpha_left, alpha_right, join_key_l, join_key_r, action):
        beta = BetaJoinNode(alpha_left, alpha_right, join_key_l, join_key_r)
        self.beta_nodes.append(beta)
        self.rules.append({"name": name, "beta": beta, "action": action})

    def process_fact(self, fact_type, attributes):
        fact = self.wm.assert_fact(fact_type, attributes)
        # Propaga para os nós alfa
        for alpha in self.alpha_nodes:
            alpha.activate(fact)
        return fact

    def fire_rules(self):
        fired = []
        for rule in self.rules:
            matches = rule["beta"].evaluate()
            if matches:
                for match in matches:
                    fired.append((rule["name"], match, rule["action"]))
        return fired

# --- Experimento e Validação ---

def test_rete_performance_and_correctness():
    print("Iniciando o Motor Rete e inserção de carga de teste...")
    engine = ReteEngine()

    # Criando nós alfa para Clientes VIP e Transações Altas
    alpha_client = engine.add_alpha("Client", lambda f: f["tier"] == "VIP")
    alpha_tx = engine.add_alpha("Transaction", lambda f: f["amount"] > 1000)

    # Regra: Se Cliente é VIP E tem Transação > 1000, disparar alerta de fraude/promoção
    triggered_actions = []
    engine.add_rule(
        name="VIP_High_Transaction",
        alpha_left=alpha_client,
        alpha_right=alpha_tx,
        join_key_l="client_id",
        join_key_r="client_id",
        action=lambda l, r: f"Alerta: Cliente VIP {l['id']} realizou transação de {r['amount']}"
    )

    # Ingerindo fatos em massa (Escala simulada: 10.000 fatos divididos entre Clientes e Transações)
    num_facts = 10000
    start_time = time.time()

    for i in E_range := range(1, num_facts // 2 + 1):
        # Inserir Clientes
        tier = "VIP" if i % 5 == 0 else "Regular"
        engine.process_fact("Client", {"client_id": i, "tier": tier})

        # Inserir Transações correspondentes
        amount = 1500 if i % 5 == 0 else 500
        engine.process_fact("Transaction", {"client_id": i, "amount": amount})

    elapsed_insertion = time.time() - start_time
    print(f"Inseridos {num_facts} fatos em {elapsed_insertion:.4f} segundos.")

    # Avaliação do motor Rete (Disparo de regras)
    eval_start = time.time()
    results = engine.fire_rules()
    eval_duration = (time.time() - eval_start) * 1000 # em milissegundos

    print(f"Resultados processados pela rede Rete em {eval_duration:.2f}ms.")
    print(f"Total de regras disparadas com sucesso: {len(results)}")

    # Verificação do critério de sucesso (< 500ms para inferência)
    assert eval_duration < 500, f"Falha de performance: Levou {eval_duration}ms (Excedeu 500ms)"
    assert len(results) > 0, "Falha de correção: Nenhuma regra foi disparada."
    
    print("Experimento concluído com sucesso e dentro dos parâmetros exigidos pelo Arquiteto.")

if __name__ == "__main__":
    try:
        test_rete_performance_and_correctness()
    except Exception as e:
        print(f"Erro no experimento: {e}")
        sys.exit(1)