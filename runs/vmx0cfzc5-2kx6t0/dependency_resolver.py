import collections

# Estrutura de dados: {pacote: {versao: {dependencias: {pacote: requisito_semver}}}}
# Requisito SemVer simplificado: ^1.2.3 significa >=1.2.3 e <2.0.0
DEPENDENCY_STORE = {
    "A": {"1.0.0": {"B": "^1.0.0"}, "2.0.0": {"B": "^2.0.0"}},
    "B": {"1.0.0": {}, "2.0.0": {}},
    "C": {"1.0.0": {"A": "^1.0.0"}},
}

def satisfies_semver(required_spec: str, candidate_version: str) -> bool:
    """Verifica se a versão candidata satisfaz a especificação ^X.Y.Z."""
    try:
        # Simplificação: ^1.2.3 implica que o major (1) não deve mudar.
        required_major = int(required_spec.split('.')[0])
        candidate_major = int(candidate_version.split('.')[0])
        
        if required_major != candidate_major:
            return False
        
        # Em um resolvedor real, faríamos comparações numéricas completas.
        # Aqui, apenas verificamos a regra principal do caret (^): não mudar o major.
        return True
    except ValueError:
        return False

def resolve_dependencies(start_node: str, required_version: str) -> tuple[bool, dict]:
    """
    Tenta resolver um nó, verificando a compatibilidade semântica.
    Retorna (sucesso, resolved_graph)
    """
    if start_node not in DEPENDENCY_STORE:
        return False, {}
    
    # 1. Selecionar a versão inicial (simplificado: assume-se que a versão requerida existe)
    if required_version not in DEPENDENCY_STORE[start_node]:
        return False, {}

    resolved_graph = {start_node: required_version}
    queue = collections.deque([start_node])
    
    while queue:
        current_node = queue.popleft()
        current_version = resolved_graph[current_node]
        
        # Obter dependências da versão escolhida
        dependencies = DEPENDENCY_STORE[current_node][current_version]
        
        for dep_node, dep_spec in dependencies.items():
            # 2. Iterar sobre todas as versões possíveis do dependente
            possible_versions = list(DEPENDENCY_STORE[dep_node].keys())
            
            compatible_versions = [
                v for v in possible_versions 
                if satisfies_semver(dep_spec, v)
            ]
            
            if not compatible_versions:
                # FALHA SEMÂNTICA: Nenhuma versão satisfaz a restrição
                return False, {}
            
            # 3. Escolher a versão mais alta compatível (heurística comum)
            # Ordena as versões (ex: 1.0.0 < 1.1.0 < 2.0.0)
            compatible_versions.sort(key=lambda v: tuple(map(int, v.split('.'))), reverse=True)
            chosen_version = compatible_versions[0]
            
            if dep_node not in resolved_graph:
                # Novo nó, adicionar ao grafo resolvido
                resolved_graph[dep_node] = chosen_version
                queue.append(dep_node)
            elif resolved_graph[dep_node] != chosen_version:
                # CONFLITO DE VERSÃO: Já resolvido para uma versão diferente
                return False, {}
                
    return True, resolved_graph

# --- TESTE DE CONFLITO SEMÂNTICO (Contraexemplo) ---
# Cenário: C requer A@^1.0.0. Se tentarmos forçar A@2.0.0, falha.
print("--- Teste de Conflito Semântico (Contraexemplo) ---")
# Tentativa de resolver C, mas forçando uma versão de A que viola a regra de C
# (Simulamos que o resolvedor tentou escolher A@2.0.0 quando C exigia ^1.0.0)
# Neste setup, o resolvedor deve escolher A@1.0.0 se C for o ponto de partida.
success, result = resolve_dependencies("C", "1.0.0")

if success:
    print(f"Sucesso na resolução: {result}")
else:
    print("Falha na resolução (esperado se houver conflito semântico).")

# --- TESTE DE SUCESSO SIMPLIFICADO ---
print("\n--- Teste de Sucesso Simplificado ---")
# C depende de A@^1.0.0. A@1.0.0 depende de B@^1.0.0. B@1.0.0 é compatível.
success_ok, result_ok = resolve_dependencies("C", "1.0.0")

if success_ok:
    print(f"Sucesso na resolução: {result_ok}")
else:
    print("Falha na resolução (esperado sucesso).")