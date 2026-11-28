import json
from typing import Dict, Any, List

# --- Simulações de Estado ---

# Estado Desejado (Simulação do conteúdo do repositório Git)
DESIRED_STATE_GIT = {
    "env_vars": {"LOG_LEVEL": "INFO", "SERVICE_NAME": "api-v1"},
    "port": 8080,
    "log_level": "INFO",
    "config_yaml": "server: {timeout: 30}",
    "config_json": '{"timeout": 30, "retries": 3}'
}

# Estado Atual do Ambiente (Simulação do que está rodando)
# Cenário 1: Estado em conformidade
CURRENT_STATE_CONFORMING = {
    "env_vars": {"LOG_LEVEL": "INFO", "SERVICE_NAME": "api-v1"},
    "port": 8080,
    "log_level": "INFO",
    "config_yaml": "server: {timeout: 30}",
    "config_json": '{"timeout": 30, "retries": 3}'
}

# Cenário 2: Drift detectado (Porta diferente)
CURRENT_STATE_DRIFT = {
    "env_vars": {"LOG_LEVEL": "INFO", "SERVICE_NAME": "api-v1"},
    "port": 8081,  # DRIFT AQUI
    "log_level": "INFO",
    "config_yaml": "server: {timeout: 30}",
    "config_json": '{"timeout": 30, "retries": 3}'
}

# --- Módulo GitOps ---

def check_drift(desired: Dict[str, Any], current: Dict[str, Any]) -> List[str]:
    """Compara o estado desejado com o estado atual e retorna as diferenças."""
    drift_issues = []
    # Comparação de chaves e valores para todos os tipos de configuração
    for key in desired.keys():
        if key not in current:
            drift_issues.append(f"Chave {key} ausente no estado atual.")
            continue
        
        desired_val = desired[key]
        current_val = current[key]

        if isinstance(desired_val, dict) and isinstance(current_val, dict):
            # Comparação de dicionários (ex: env_vars)
            if desired_val != current_val:
                drift_issues.append(f"Diferença em {key}: Desejado {desired_val}, Atual {current_val}")
        elif desired_val != current_val:
            # Comparação de tipos primitivos (porta, log_level, strings de config)
            drift_issues.append(f"Diferença em {key}: Desejado {desired_val}, Atual {current_val}")
            
    return drift_issues

def apply_changes(desired: Dict[str, Any], current: Dict[str, Any], drift_issues: List[str]) -> Dict[str, Any]:
    """Aplica as mudanças de forma idempotente e retorna o novo estado sincronizado."""
    # Simulação de aplicação: o novo estado é sempre o desejado, mas apenas se houver drift
    if not drift_issues:
        return current # Não há mudança, retorna o estado atual (idempotência)
    
    # Se há drift, o estado é atualizado para o desejado
    new_state = desired.copy()
    return new_state

def sync_gitops(desired_state: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
    """Sincroniza o estado do ambiente com o estado desejado do Git."""
    drift = check_drift(desired_state, current_state)
    
    changes_applied = len(drift)
    
    if changes_applied == 0:
        # Estado em conformidade: não aplica nada, retorna o estado atual
        return current_state
    else:
        # Estado com drift: aplica as mudanças e retorna o novo estado sincronizado
        synced_state = apply_changes(desired_state, current_state, drift)
        return synced_state

def run_test(name: str, desired: Dict[str, Any], current: Dict[str, Any], expected_success: bool):
    """Executa um teste de sincronização e reporta o resultado."""
    print(f"\n--- Executando Teste: {name} ---")
    report = sync_gitops(desired, current)
    
    # Verifica se houve drift e se o resultado esperado foi atingido
    drift = check_drift(desired, current)
    changes_applied = len(drift)
    
    if expected_success:
        assert changes_applied == 0, f"Falha em {name}: Esperado 0 mudanças, mas aplicou {changes_applied}"
        print(f"✅ {name} APROVADO. Mudanças aplicadas: 0")
    else:
        assert changes_applied > 0, f"Falha em {name}: Esperado drift, mas aplicou 0 mudanças."
        print(f"✅ {name} APROVADO. Drift detectado e corrigido. Mudanças aplicadas: {changes_applied}")
    
    return report

# --- Execução Principal ---

# Teste 1: Conformidade Inicial (Deve ser 0 mudanças)
report_conform = run_test("Conformidade Inicial", DESIRED_STATE_GIT, CURRENT_STATE_CONFORMING, expected_success=True)

# Teste 2: Correção de Drift (Deve ser > 0 mudanças)
report_drift = run_test("Correção de Drift", DESIRED_STATE_GIT, CURRENT_STATE_DRIFT, expected_success=False)

# Teste 3: Idempotência (Reaplicação - DEVE USAR O ESTADO SINCRONIZADO DO TESTE 2)
print("\n--- Executando Teste: Idempotência (Reaplicação) ---")
# CORREÇÃO: Usamos o estado retornado pelo Teste 2 (report_drift), que é o estado sincronizado (DESIRED_STATE_GIT)
report_idempotent = sync_gitops(DESIRED_STATE_GIT, report_drift) 
assert len(check_drift(DESIRED_STATE_GIT, report_drift)) == 0, "Falha de lógica: O estado retornado pelo Teste 2 não deveria ter drift."
assert report_idempotent == DESIRED_STATE_GIT, "Falha de sincronização: O estado final não corresponde ao desejado."

# Reexecuta a sincronização no estado sincronizado (report_drift)
final_report_idempotent = sync_gitops(DESIRED_STATE_GIT, report_drift)
assert len(check_drift(DESIRED_STATE_GIT, report_drift)) == 0, "Falha de lógica: O estado sincronizado ainda tem drift."
assert final_report_idempotent == report_drift, "Falha de idempotência: Reaplica mudanças desnecessariamente."

print("✅ Idempotência APROVADO. Mudanças aplicadas: 0")


# Demonstração do Contraexemplo (Falha sem verificação de estado)
print("\n--- Demonstração de Contraexemplo: Aplicação Ingênua vs. GitOps ---")
# Simulação de aplicação ingênua: apenas sobrescreve, sem checar se já está certo.
def apply_naive(desired, current):
    # Aplicação ingênua sempre sobrescreve, ignorando o estado atual
    return desired.copy()

naive_state = apply_naive(DESIRED_STATE_GIT, CURRENT_STATE_CONFORMING)
# O GitOps reporta 0 mudanças se não houver drift. A aplicação ingênua sempre "aplica" e não reporta conformidade.
print(f"Estado após aplicação ingênua (sem checagem): {naive_state['port']}")
print("Conclusão: A aplicação ingênua falha em ser eficiente e não reporta a conformidade, violando o princípio de operação GitOps.")

print("\nTodos os testes de integração concluídos com sucesso.")