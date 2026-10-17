import time
import warnings

class InconsistencyError(Exception):
    """Exceção lançada quando a base de conhecimento deriva fatos contraditórios."""
    pass

class CycleDetectedWarning(UserWarning):
    """Aviso emitido quando um ciclo lógico é detectado nas regras."""
    pass

class Rule:
    def __init__(self, name, antecedents, consequent):
        self.name = name
        
        # Validação aprimorada de antecedentes (Segurança: padrão seguro contra dados inválidos)
        if not isinstance(antecedents, (list, tuple, set)) or not antecedents:
            raise ValueError(f"Regra '{name}' deve possuir antecedentes iteráveis e não vazios.")
        
        cleaned_ant = set()
        for ant in antecedents:
            if not isinstance(ant, str) or not ant.strip():
                raise ValueError(f"Regra '{name}' possui antecedente inválido ou vazio: {ant!r}")
            # Validação básica de consistência sintática de formato (ex: semântica de negação malformada)
            if ant == "not_" or consequent == "not_":
                raise ValueError(f"Regra '{name}' possui expressão de negação malformada.")
            cleaned_ant.add(ant.strip())
            
        if not isinstance(consequent, str) or not consequent.strip():
            raise ValueError(f"Regra '{name}' possui consequente inválido: {consequent!r}")

        self.antecedents = cleaned_ant
        self.consequent = consequent.strip()

    def __repr__(self):
        return f"Rule({self.name}: {list(self.antecedents)} -> {self.consequent})"

class ForwardChainingEngine:
    def __init__(self, rules, integrity_constraints=None):
        self.rules = rules
        self.facts = set()
        self.integrity_constraints = integrity_constraints or []
        
        # Análise estática para detecção explícita de ciclos nas regras (Segurança / Revisor)
        self._detect_and_warn_cycles()
        
        # Indexação de regras por antecedente para garantir eficiência O(n + m)
        self.rule_index = {}
        for rule in self.rules:
            for ant in rule.antecedents:
                if ant not in self.rule_index:
                    self.rule_index[ant] = []
                self.rule_index[ant].append(rule)

    def _detect_and_warn_cycles(self):
        """Executa análise estática por DFS para detectar dependências circulares entre regras."""
        # Mapeia fato produzido pelas regras para os antecedentes exigidos por outras regras
        graph = {}
        for rule in self.rules:
            for ant in rule.antecedents:
                if ant not in graph:
                    graph[ant] = []
            # Consequente como chave que aponta para regras que o consomem, 
            # ou mapear dependência direta entre regras:
        
        # Construção de grafo de dependência de regras (Rule A consequent -> Rule B antecedent)
        rule_graph = {r.name: set() for r in self.rules}
        consequent_to_rules = {}
        for r in self.rules:
            if r.consequent not in consequent_to_rules:
                consequent_to_rules[r.consequent] = []
            consequent_to_rules[r.consequent].append(r.name)

        for r in self.rules:
            for ant in r.antecedents:
                if ant in consequent_to_rules:
                    for parent_rule in consequent_to_rules[ant]:
                        if parent_rule != r.name:
                            rule_graph[parent_rule].add(r.name)

        # Detecção de ciclos usando DFS com marcação de cores (0=não visitado, 1=visitando, 2=visitado)
        visited = {}
        def dfs(node, path):
            visited[node] = 1
            path.append(node)
            for neighbor in rule_graph.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    cycle_path = " -> ".join(path + [neighbor])
                    warnings.warn(
                        f"Ciclo lógico detectado nas regras: {cycle_path}. "
                        "Isso pode gerar inferências redundantes.",
                        CycleDetectedWarning
                    )
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        for r in rule_graph:
            if visited.get(r, 0) == 0:
                dfs(r, [])

    def add_fact(self, fact):
        """Adiciona um fato e valida consistência imediatamente."""
        self._check_consistency_for_fact(fact)
        if fact not in self.facts:
            self.facts.add(fact)
            return True
        return False

    def _check_consistency_for_fact(self, new_fact):
        if new_fact.startswith("not_"):
            positive_counterpart = new_fact[4:]
            if positive_counterpart in self.facts:
                raise InconsistencyError(f"Contradição detectada! Fato '{new_fact}' conflita com fato existente '{positive_counterpart}'.")
        else:
            negative_counterpart = f"not_{new_fact}"
            if negative_counterpart in self.facts:
                raise InconsistencyError(f"Contradição detectada! Fato '{new_fact}' conflita com fato existente '{negative_counterpart}'.")

    def run(self, initial_facts):
        queue = []
        for f in initial_facts:
            if self.add_fact(f):
                queue.append(f)

        iterations = 0
        while queue:
            iterations += 1
            current_fact = queue.pop(0)

            if current_fact in self.rule_index:
                for rule in self.rule_index[current_fact]:
                    if rule.antecedents.issubset(self.facts):
                        new_fact = rule.consequent
                        try:
                            if self.add_fact(new_fact):
                                queue.append(new_fact)
                        except InconsistencyError as e:
                            raise InconsistencyError(f"Inconsistência disparada pela regra '{rule.name}': {e}")

        return self.facts, iterations

def test_engine_10_rules():
    rules = [
        Rule("R1", ["sensor_temp_alto"], "alerta_temperatura"),
        Rule("R2", ["alerta_temperatura", "sistema_ativo"], "cooler_ligado"),
        Rule("R3", ["sensor_pressao_baixo"], "alerta_pressao"),
        Rule("R4", ["alerta_pressao", "sistema_ativo"], "valvula_alivio_aberta"),
        Rule("R5", ["cooler_ligado", "valvula_alivio_aberta"], "sistema_estabilizado"),
        Rule("R6", ["sistema_estabilizado", "sistema_ativo"], "modo_seguro"),
        Rule("R7", ["modo_seguro"], "log_auditoria_gerado"),
        Rule("R8", ["log_auditoria_gerado"], "notificacao_enviada"),
        Rule("R9", ["notificacao_enviada", "sistema_estabilizado"], "sistema_seguro"),
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

def test_inconsistency_handling():
    rules = [
        Rule("R_Inc1", ["A"], "B"),
        Rule("R_Inc2", ["B"], "not_A")
    ]
    engine = ForwardChainingEngine(rules)
    
    try:
        engine.run(["A"])
        assert False, "Deveria ter lançado InconsistencyError"
    except InconsistencyError as e:
        print(f"Inconsistência capturada com sucesso: {e}")

def test_cycle_detection_and_safety():
    # Testa detecção explícita de ciclos e validação estrita de antecedentes
    cyclic_rules = [
        Rule("RC1", ["A"], "B"),
        Rule("RC2", ["B"], "A")
    ]
    
    print("Testando detecção estática de ciclos nas regras...")
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        engine = ForwardChainingEngine(cyclic_rules)
        assert len(w) > 0, "O motor deveria ter emitido um aviso de ciclo lógico."
        print(f"Alerta de ciclo capturado com sucesso: {w[0].message}")

    # Testa validação de antecedentes inválidos
    try:
        Rule("R_Inv", [], "B")
        assert False, "Deveria falhar com antecedentes vazios"
    except ValueError as e:
        print(f"Validação de antecedente vazio capturada com sucesso: {e}")

if __name__ == "__main__":
    print("--- Executando Teste do Motor de Inferência (10 Regras) ---")
    test_engine_10_rules()
    print("\n--- Executando Teste de Inconsistência ---")
    test_inconsistency_handling()
    print("\n--- Executando Teste de Detecção de Ciclos e Validação de Regras ---")
    test_cycle_detection_and_safety()
    print("\nTodos os testes passaram com sucesso!")