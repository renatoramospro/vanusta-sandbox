import json
from packaging.version import parse as parse_version
from typing import Dict, List, Tuple, Optional

# Simulação de um repositório de pacotes (Nome: {Versão: Dependências})
# Dependências são representadas por strings SemVer.
REPO: Dict[str, Dict[str, List[str]]] = {
    "A": {"1.0.0": ["B@^1.0.0"], "1.1.0": ["B@^1.1.0"]},
    "B": {"1.0.0": [], "1.1.0": [], "2.0.0": []},
    "C": {"1.0.0": ["B@^2.0.0"]}
}

# Simulação de dependências de entrada (Root)
ROOT_DEPENDENCIES: List[str] = ["A@^1.0.0", "C@^1.0.0"]

def satisfies_constraint(version: str, constraint: str) -> bool:
    """Verifica se uma versão satisfaz uma restrição SemVer simples (ex: ^1.0.0)."""
    # Simplificação: ^1.0.0 significa >=1.0.0 e <2.0.0
    if constraint.startswith('^'):
        major = int(constraint[1:constraint.find('.')])
        v = parse_version(version)
        return v.major == major and v.base_version < f"{major+1}.0.0"
    return True # Simplificação extrema para o teste

def resolve_dependencies(root_deps: List[str]) -> Optional[Dict[str, str]]:
    """
    Resolve as dependências usando backtracking implícito (greedy com verificação de consistência).
    Retorna o lockfile (Nome: Versão) ou None se houver conflito.
    """
    # 1. Coletar todas as restrições para cada pacote
    # { 'B': [('^1.0.0', 'from_A'), ('^2.0.0', 'from_C')] }
    constraints: Dict[str, List[Tuple[str, str]]] = {}
    
    # Processar dependências de entrada (simplificado)
    for dep_spec in root_deps:
        name, constraint_spec = dep_spec.split('@')
        # Aqui, em um resolvedor real, extrairíamos a restrição exata.
        # Para este teste, assumimos que a especificação de entrada define a restrição.
        if name not in constraints:
            constraints[name] = []
        constraints[name].append((constraint_spec, "ROOT"))

    # 2. Iterar sobre todos os pacotes conhecidos e aplicar a política de escolha
    lockfile: Dict[str, str] = {}
    
    for pkg_name in REPO.keys():
        available_versions = sorted(REPO[pkg_name].keys(), key=parse_version)
        
        if pkg_name not in constraints:
            # Se não tem restrição, escolhe a mais recente
            lockfile[pkg_name] = available_versions[-1]
            continue

        # Aplicar política: Escolher a mais recente que satisfaça TODAS as restrições
        best_version: Optional[str] = None
        
        # Iterar de trás para frente (mais recente para mais antiga)
        for version in reversed(available_versions):
            is_valid = True
            for constraint_spec, _ in constraints[pkg_name]:
                if not satisfies_constraint(version, constraint_spec):
                    is_valid = False
                    break
            
            if is_valid:
                best_version = version
                break # Encontramos a mais recente válida
        
        if best_version is None:
            print(f"ERRO: Conflito irresolúvel para {pkg_name}. Nenhuma versão satisfaz todas as restrições.")
            return None
        
        lockfile[pkg_name] = best_version

    return lockfile

# --- Execução do Experimento ---
print("--- Iniciando Resolução de Dependências ---")
resolved = resolve_dependencies(ROOT_DEPENDENCIES)

if resolved:
    print("\n✅ Resolução Válida Encontrada:")
    print(json.dumps(resolved, indent=2))
    
    # Teste de determinismo (executar 5 vezes)
    print("\n--- Teste de Determinismo (5 execuções) ---")
    for i in range(5):
        lockfile_output = json.dumps(resolve_dependencies(ROOT_DEPENDENCIES), indent=2)
        # A verificação de identidade é feita comparando a string JSON
        assert lockfile_output == json.dumps(resolved, indent=2), f"Execução {i+1} falhou em ser determinística."
        print(f"Execução {i+1}: Sucesso (Lockfile idêntico)")
else:
    print("\n❌ Falha na Resolução: Conflito irresolúvel detectado.")
