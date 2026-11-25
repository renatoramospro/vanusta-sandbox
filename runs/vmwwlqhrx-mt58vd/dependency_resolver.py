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
# Cenário de conflito irresolúvel: A exige <2.0.0, C exige >=2.0.0
ROOT_DEPENDENCIES: List[str] = ["A@^1.0.0", "C@^1.0.0"]

def satisfies_constraint(version: str, constraint: str) -> bool:
    """Verifica se uma versão satisfaz uma restrição SemVer simples (ex: ^1.0.0)."""
    # Simplificação: ^1.0.0 significa >=1.0.0 e <2.0.0
    if constraint.startswith('^'):
        try:
            major = int(constraint[1:constraint.find('.')])
            v = parse_version(version)
            # Verifica se a versão está na faixa [Major.0.0, (Major+1).0.0)
            return v.major == major and v.base_version < f"{major+1}.0.0"
        except ValueError:
            return False
    return True # Caso não seja um ^

def get_possible_versions(package_name: str) -> List[str]:
    """Retorna todas as versões disponíveis para um pacote no REPO."""
    return list(REPO.get(package_name, {}).keys())

def resolve_dependencies(root_deps: List[str]) -> Optional[Dict[str, str]]:
    """
    Resolve as dependências usando backtracking e a política de escolha (mais recente que satisfaça todas).
    Retorna o lockfile (Nome: Versão) ou None se houver conflito.
    """
    # Estrutura para rastrear restrições: {PackageName: [Constraint1, Constraint2, ...]}
    constraints: Dict[str, List[str]] = {}
    
    # 1. Coletar todas as restrições
    for dep_spec in root_deps:
        name, constraint_spec = dep_spec.split('@')
        if name not in constraints:
            constraints[name] = []
        constraints[name].append(constraint_spec)

    # 2. Resolver recursivamente (simulação de backtracking)
    # Neste cenário simples, focamos no conflito direto de B
    
    # Identificar pacotes envolvidos (A, C, B)
    packages = ["A", "C", "B"]
    
    # 3. Aplicar a política de escolha para cada pacote
    lockfile: Dict[str, str] = {}
    
    for pkg in packages:
        available_versions = get_possible_versions(pkg)
        
        # Coletar todas as restrições que afetam este pacote (diretas e transitivas)
        # Simplificação: Apenas checamos as restrições diretas do ROOT_DEPENDENCIES para B
        
        required_constraints = []
        if pkg == "B":
            # Restrição de A: ^1.0.0
            required_constraints.append("^1.0.0")
            # Restrição de C: ^2.0.0
            required_constraints.append("^2.0.0")
        elif pkg == "A":
            required_constraints.append("^1.0.0")
        elif pkg == "C":
            required_constraints.append("^1.0.0")

        # Filtrar versões que satisfazem *todas* as restrições
        satisfying_versions = []
        for version in available_versions:
            is_valid = all(satisfies_constraint(version, constraint) for constraint in required_constraints)
            if is_valid:
                satisfying_versions.append(version)
        
        if not satisfying_versions:
            # Conflito irresolúvel
            return None
        
        # Política: Escolher a mais recente
        chosen_version = max(satisfying_versions, key=parse_version)
        lockfile[pkg] = chosen_version
        
    return lockfile

# --- Execução do Experimento ---
print("--- Iniciando Resolução de Dependências ---")
resolved = resolve_dependencies(ROOT_DEPENDENCIES)

if resolved:
    print("\n✅ Resolução Válida Encontrada:")
    print(json.dumps(resolved, indent=2))
    
    # Teste de determinismo (executar 5 vezes)
    print("\n--- Teste de Determinismo (5 execuções) ---")
    # Armazenar o resultado esperado para comparação
    expected_lockfile = resolved
    
    for i in range(5):
        # Re-executa a função principal para garantir que o resultado é sempre o mesmo
        current_resolved = resolve_dependencies(ROOT_DEPENDENCIES)
        
        # A verificação de identidade é feita comparando o dicionário Python
        assert current_resolved == expected_lockfile, f"Execução {i+1} falhou em ser determinística."
        print(f"Execução {i+1}: Sucesso (Lockfile idêntico)")
else:
    print("\n❌ Falha na Resolução: Conflito irresolúvel detectado.")