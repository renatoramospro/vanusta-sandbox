import hashlib
import random
from collections import deque

# --- Configuração do Sistema ---
NUM_TARGETS = 100
# Metadados de ambiente/toolchain (Essenciais para determinismo real - Correção S1)
TOOLCHAIN_VERSION = "v2.1.0"
PLATFORM = "linux_x64"

# Estrutura: {target_id: [dependencias]}
# Criamos um grafo acíclico simples para simular dependências transitivas
graph = {i: [] for i in range(NUM_TARGETS)}
# Simulação de dependências: cada alvo depende de 1 a 3 alvos anteriores
for i in range(1, NUM_TARGETS):
    deps = random.sample(range(i), min(3, i))
    graph[i].extend(deps)

# Cache: {target_id: hash_do_artefato}
cache = {}
# Estado de alteração: {target_id: True/False}
is_source_changed = {i: False for i in range(NUM_TARGETS)}

def calculate_content_hash(target_id, is_changed):
    """
    Simula o cálculo do hash baseado no conteúdo de entrada E METADADOS DE TOOLCHAIN.
    Correção S1: Inclui TOOLCHAIN_VERSION e PLATFORM para garantir determinismo real.
    """
    if is_changed:
        # Hash muda se o código-fonte mudar
        return hashlib.sha256(f"CONTENT_CHANGE_{target_id}".encode()).hexdigest()
    else:
        # Hash estável se o código E os metadados de build (toolchain/plataforma) não mudaram
        content_string = f"STABLE_CONTENT_{target_id}_{TOOLCHAIN_VERSION}_{PLATFORM}"
        return hashlib.sha256(content_string.encode()).hexdigest()

def build_target(target_id, is_source_changed_flag):
    """Tenta construir um alvo, verificando o cache."""
    current_hash = calculate_content_hash(target_id, is_source_changed_flag)
    
    # Verifica se o artefato já está no cache com o hash correto
    if cache.get(target_id) == current_hash:
        return "CACHE_HIT"
    else:
        # Recompilação necessária
        # Atualiza o cache com o novo hash gerado
        cache[target_id] = current_hash
        return "RECOMPILE"

def run_build(source_changed_id=None):
    """Executa o build em ordem topológica e coleta métricas."""
    # 1. Determinar ordem de build (Topological Sort - BFS/DFS)
    # Como o grafo é acíclico e construído sequencialmente (i depende de j < i), a ordem 0..N-1 é topológica.
    build_order = list(range(NUM_TARGETS))
    
    # 2. Definir estado de alteração para este build
    current_source_changed = {i: (i == source_changed_id) for i in range(NUM_TARGETS)}
    
    total_targets = NUM_TARGETS
    cache_hits = 0
    recompilations = 0
    
    # 3. Executar build
    for target_id in build_order:
        is_changed = current_source_changed[target_id]
        result = build_target(target_id, is_changed)
        
        if result == "CACHE_HIT":
            cache_hits += 1
        else:
            recompilations += 1
            
    hit_rate = (cache_hits / total_targets) * 100 if total_targets > 0 else 0
    return hit_rate, recompilations

# =====================================================================
# 1. BUILD INICIAL (Populando Cache)
# =====================================================================
print("="*50)
print(">>> ETAPA 1: BUILD INICIAL (Populando Cache) <<<")
# No build inicial, todos são recompilados, populando o cache com hashes estáveis
hit_rate_initial, recompilations_initial = run_build(source_changed_id=None)

print("\n--- SIMULAÇÃO: BUILD INICIAL (Populando Cache) ---")
print(f"Total de Alvos: {NUM_TARGETS}")
print(f"Cache Hits: {hit_rate_initial * NUM_TARGETS:.0f} ({hit_rate_initial:.2f}%)")
print(f"Recompilações: {recompilations_initial}")

# =====================================================================
# 2. BUILD REPETIDO (VALIDAÇÃO DE CACHE)
# =====================================================================
print("\n" + "="*50)
print(">>> ETAPA 2: BUILD REPETIDO (VALIDAÇÃO DE CACHE) <<<")
# Sem mudanças, deve ser 100% de hit
hit_rate_stable, _ = run_build(source_changed_id=None)

# Critério de Sucesso: manter >=90% de acertos de cache
assert hit_rate_stable >= 90.0, f"Falha no critério de cache: {hit_rate_stable:.2f}% < 90%"
print("✅ Critério de Cache (>=90%) ATENDIDO.")

# =====================================================================
# 3. BUILD COM ÚNICA ALTERAÇÃO (Testa recompilação transitiva)
# =====================================================================
# Alteramos a fonte 5 (um alvo inicial)
SOURCE_TO_CHANGE = 5
print("\n" + "="*50)
hit_rate_changed, recompilations_changed = run_build(source_changed_id=SOURCE_TO_CHANGE)

# Critério de Sucesso: recompilar no máximo os alvos transitivamente dependentes
assert recompilations_changed > 1, "Falha: A alteração não propagou para alvos dependentes."
assert recompilations_changed < NUM_TARGETS, "Falha: Recompilação de todos os 100 alvos (não incremental)."

print(f"✅ Critério de Recompilação (Incremental) ATENDIDO: {recompilations_changed} recompilações detectadas.")
print("\n--- EXPERIMENTO CONCLUÍDO COM SUCESSO ---")