from typing import List, Set, Dict, Optional

class DataType:
    SAFE = "SAFE"
    SENSITIVE = "SENSITIVE"

class Node:
    def __init__(self, name: str, is_untrusted: bool = False, is_sanitizer: bool = False):
        self.name = name
        self.is_untrusted = is_untrusted  # Se for True, é um 'Sink' potencial
        self.is_sanitizer = is_sanitizer  # Se for True, limpa a 'mancha'
        self.edges: List['Node'] = []     # Representa o fluxo de dados (DFA)

    def add_edge(self, to_node: 'Node'):
        self.edges.append(to_node)

class TaintAnalyzer:
    def __init__(self, sensitive_sources: Dict[str, DataType]):
        self.sensitive_sources = sensitive_sources

    def analyze(self, start_nodes: List[Node]) -> List[str]:
        """
        Realiza uma busca em profundidade (DFS) para encontrar caminhos 
        de dados que levam de uma Source sensível a um Sink não confiável
        sem passar por um Sanitizer.
        """
        leaks = []

        for start_node in start_nodes:
            # Verifica se o nó inicial contém uma fonte sensível
            if start_node.name in self.sensitive_sources and \
               self.sensitive_sources[start_node.name] == DataType.SENSITIVE:
                
                # Inicia busca de propagação de mancha (taint propagation)
                found_leaks = self._dfs_taint(start_node, set(), [])
                leaks.extend(found_leaks)
        
        return list(set(leaks))

    def _dfs_taint(self, current_node: Node, visited: Set[Node], path: List[str]) -> List[str]:
        visited.add(current_node)
        current_path = path + [current_node.name]
        found_leaks = []

        # Se chegamos a um nó não confiável (Sink) e a mancha ainda está ativa
        if current_node.is_untrusted:
            found_leaks.append(f"LEAK DETECTED: {' -> '.join(current_path)}")

        for neighbor in current_node.edges:
            if neighbor not in visited:
                # Se o vizinho for um sanitizador, a mancha é removida para este caminho
                if neighbor.is_sanitizer:
                    # O caminho continua, mas o 'taint' não é propagado para os filhos do sanitizador
                    # em uma análise de fluxo de dados purista. 
                    # Para este experimento, simulamos que o sanitizador limpa o dado.
                    continue 
                else:
                    # Propaga a mancha
                    found_leaks.extend(self._dfs_taint(neighbor, visited.copy(), current_path))
        
        return found_leaks

def run_experiment():
    # 1. Configuração de Fontes Sensíveis
    sources = {
        "API_KEY": DataType.SENSITIVE,
        "USER_PASSWORD": DataType.SENSITIVE,
        "PUBLIC_USER_ID": DataType.SAFE
    }
    analyzer = TaintAnalyzer(sources)

    # 2. Construção de Cenários de Teste

    # CENÁRIO A: Vazamento Direto (Segredo -> Agente Público)
    # API_KEY -> Agent_A -> Web_Search_Agent (Untrusted)
    node_api = Node("API_KEY")
    node_a = Node("Agent_A")
    node_web = Node("Web_Search_Agent", is_untrusted=True)
    node_api.add_edge(node_a)
    node_a.add_edge(node_web)

    # CENÁRIO B: Fluxo Seguro (Segredo -> Sanitizador -> Agente Público)
    # USER_PASSWORD -> Agent_B -> Sanitizer -> Web_Search_Agent
    node_pw = Node("USER_PASSWORD")
    node_b = Node("Agent_B")
    node_sanitizer = Node("Sanitizer", is_sanitizer=True)
    node_web_safe = Node("Web_Search_Agent", is_untrusted=True)
    node_pw.add_edge(node_b)
    node_b.add_edge(node_sanitizer)
    node_sanitizer.add_edge(node_web_safe)

    # CENÁRIO C: Dados Não Sensíveis (Seguro)
    # PUBLIC_USER_ID -> Agent_C -> Web_Search_Agent
    node_id = Node("PUBLIC_USER_ID")
    node_c = Node("Agent_C")
    node_web_safe2 = Node("Web_Search_Agent", is_untrusted=True)
    node_id.add_edge(node_c)
    node_c.add_edge(node_web_safe2)

    # CENÁRIO D: O Equívoco do CFG (Control Flow vs Data Flow)
    # O fluxo de controle parece correto (A chama B), mas o dado é o problema.
    # Agent_D (Trusted) -> Agent_E (Untrusted)
    # Se o Agente D recebe a API_KEY, ele a passa para E.
    node_d = Node("API_KEY") # A fonte é o próprio nó de entrada
    node_e = Node("Agent_E", is_untrusted=True)
    node_d.add_edge(node_e)

    # 3. Execução da Análise
    print("--- Iniciando Análise Estática de Pipeline ---")
    
    test_cases = [
        ("Cenário A (Vazamento Direto)", [node_api], True),
        ("Cenário B (Com Sanitização)", [node_pw], False),
        ("Cenário C (Dados Não Sensíveis)", [node_id], False),
        ("Cenário D (Vazamento via Agente)", [node_d], True),
    ]

    all_leaks = []
    for description, pipeline, should_leak in test_cases:
        print(f"\nTestando {description}...")
        leaks = analyzer.analyze(pipeline)
        if leaks:
            print(f"  [!] Alerta: {leaks}")
            all_leaks.extend(leaks)
        else:
            print("  [✓] Pipeline Seguro.")
        
        # Validação do experimento
        assert (len(leaks) > 0) == should_leak, f"Falha no teste: {description}"

    print("\n--- Resultado Final ---")
    print(f"Total de vazamentos detectados: {len(all_leaks)}")
    print("Status: EXPERIMENTO CONCLUÍDO COM SUCESSO")

if __name__ == "__main__":
    run_experiment()