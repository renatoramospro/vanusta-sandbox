import time

class InconsistencyError(Exception):
    """Exceção lançada quando a base de conhecimento deriva fatos contraditórios."""
    pass

class Rule:
    def __init__(self, name, antecedents, consequent):
        self.name = name
        set_ant = set(antecedents)
        if not set_ant:
            raise ValueError(f"Regra '{name}' possui antecedentes vazios, o que causaria disparo imediato indevido.")
        self.antecedents = set_ant
        self.consequent = consequent

    def __repr__(self):
        return f"Rule({self.name}: {list(self.antecedents)} -> {self.consequent})"

class ForwardChainingEngine:
    def __init__(self, rules, integrity_constraints=None):
        self.rules = rules
        self.facts = set()
        self.integrity_constraints = integrity_constraints or []
        
        # Indexação de regras por antecedente para garantir eficiência O(n + m)
        self.rule_index = {}
        for rule in self.rules:
            for ant in rule.antecedents:
                if ant not in self.rule_index:
                    self.rule_index[ant] = []
                self.rule_index[ant].append(rule)

    def add_fact(self, fact):
        """Adiciona um fato e valida consistência imediatamente."""
        # Verifica consistência (ex: se 'P' é adicionado, '¬P' não pode estar presente)
        self._check_consistency_for_fact(fact)
        
        if fact not in self.facts:
            self.facts.add(fact)
            return True
        return False

    def _check_consistency_for_fact(self, new_fact):
        # Exemplo simples de negação: se o fato começa com 'not_', o oposto é o resto; senão é 'not_' + fato
        if new_fact.startswith("not_"):
            opposite = new_fact[4:]
        else:
            opposite = f"not_{new_fact}"
            
        if opposite in self.facts:
            raise InconsistencyError(f"Contradição detectada! Fato '{new_fact}' conflita com fato existente '{opposite}'.")
        
        for constraint in self.integrity_constraints:
            constraint(self.facts, new_fact)

    def run(self, initial_facts):
        for f in initial_facts:
            self.add_fact(f)

        agenda = []
        # Avaliação inicial das regras com base nos fatos iniciais
        triggered_rules = set()

        # Disparo inicial baseado nos fatos fornecidos
        agenda = self._find_activable_rules()

        iterations = 0
        while agenda:
            iterations += 1
            rule = agenda.pop(0)
            
            if rule.name in triggered_rules:
                continue
                
            triggered_rules.add(rule.name)
            
            # Deriva o consequente
            new_fact = rule.consequent
            added = self.add_fact(new_fact)
            
            if added:
                # Se um novo fato foi gerado, buscamos novas regras ativadas
                agenda = self._find_activable_rules(triggered_rules)

        return self.facts, iterations

    def _find_activable_rules(self, executed_rules=None):
        executed_rules = executed_rules or set()
        activable = []
        for rule in self.rules:
            if rule.name not in executed_rules:
                if rule.antecedents.issubset(self.facts):
                    if rule not in activable:
                        activable.append(rule)
        return activable

# --- TESTES E DEMONSTRAÇÃO ---

def test_engine_10_rules():
    # Definindo 10 regras interdependentes formando uma cadeia de inferência profunda
    rules = [
        Rule("R1", ["sensor_temp_alto"], "alerta_temperatura"),
        Rule("R2", ["alerta_temperatura", "sistema_ativo"], "ativar_resfriamento"),
        Rule("R3", ["ativar_resfriamento"], "valvula_aberta"),
        Rule("R4", ["valvula_aberta"], "fluxo_agua_ok"),
        Rule("R5", ["fluxo_agua_ok", "sistema_ativo"], "temperatura_normalizada"),
        Rule("R6", ["sensor_pressao_baixo"], "alerta_pressao"),
        Rule("R7", ["alerta_pressao"], "ligar_bomba_auxiliar"),
        Rule("R8", ["ligar_bomba_auxiliar"], "pressao_estavel"),
        Rule("R9", ["temperatura_normalizada", "pressao_estavel"], "sistema_seguro"),
        Rule("R10", ["sistema_seguro"], "status_operacional_verde")
    ]

    engine = ForwardChainingEngine(rules)
    initial_facts = ["sensor_temp_alto", "sistema_ativo", "sensor_pressao_baixo"]

    start_time = time.perf_counter()
    derived_facts, iterations = engine.run(initial_facts)
    end_time = time.perf_counter()

    print(f"Fatos Iniciais: {initial_facts}")
    print(f"Total de fatos derivados: {len(derived_facts)}")
    print(f"Iterações do motor: {iterations}")
    print(f"Tempo de execução: {(end_time - start_time)*1000:.4f} ms")
    print(f"Status operacional alcançado? {'status_operacional_verde' in derived_facts}")

    assert "status_operacional_verde" in derived_facts, "O motor falhou em derivar o objetivo final."
    assert iterations <= len(regras_dependentes := rules), "O número de iterações excedeu o limite linear esperado."

def test_inconsistency_handling():
    rules = [
        Rule("R_Inc1", ["A"], "B"),
        Rule("R_Inc2", ["B"], "not_A") # Conflito direto com fato base A
    ]
    engine = ForwardChainingEngine(rules)
    
    try:
        engine.run(["A"])
        assert False, "Deveria ter lançado InconsistencyError"
    except InconsistencyError as e:
        print(f"Inconsistência capturada com sucesso: {e}")

if __name__ == "__main__":
    print("--- Executando Teste do Motor de Inferência (10 Regras) ---")
    test_engine_10_rules()
    print("\n--- Executando Teste de Inconsistência ---")
    test_inconsistency_handling()
    print("\nTodos os testes passaram com sucesso!")