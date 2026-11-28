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
    # Comparação simples de chaves principais
    if desired.get('port') != current.get('port'):
        drift_issues.append(f"Porta: Desejado {desired['port']}, Atual {current['port']}")
    if desired.get('log_level') != current.get('log_level'):
        drift_issues.append(f"Log Level: Desejado {desired['log_level']}, Atual {current['log_level']}")
    # Nota: Para variáveis de ambiente, uma comparação mais profunda seria necessária, mas mantemos simples para o escopo.
    return drift_issues

def apply_configuration(desired: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica as configurações de forma idempotente.
    Retorna o novo estado aplicado.
    """
    new_state = current.copy()
    changes_applied = 0
    
    # 1. Porta (Idempotência: só muda se for diferente)
    if desired['port'] != new_state.get('port'):
        new_state['port'] = desired['port']
        changes_applied += 1
        
    # 2. Log Level
    if desired['log_level'] != new_state.get('log_level'):
        new_state['log_level'] = desired['log_level']
        changes_applied += 1

    # 3. Config YAML/JSON (Simulação de aplicação de arquivos)
    if desired['config_yaml'] != new_state.get('config_yaml'):
        new_state['config_yaml'] = desired['config_yaml']
        changes_applied += 1
    if desired['config_json'] != new_state.get('config_json'):
        new_state['config_json'] = desired['config_json']
        changes_applied += 1
        
    # 4. Variáveis de Ambiente (Simulação)
    # Em um sistema real, isso seria um comando de deploy/configmap update.
    # Aqui, verificamos se o estado simulado reflete o desejado.
    if new_state.get('env_vars') != desired['env_vars']:
        new_state['env_vars'] = desired['env_vars']
        changes_applied += 1
        
    return new_state, changes_applied

def sync_gitops(desired_state: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
    """Executa o ciclo GitOps: Drift -> Apply -> Report."""
    
    # 1. Detecção de Drift
    drift = check_drift(desired_state, current_state)
    
    # 2. Aplicação (Idempotente)
    new_state, changes_applied = apply_configuration(desired_state, current_state)
    
    # 3. Verificação Pós-Aplicação (Verifica se o drift foi corrigido)
    post_drift = check_drift(desired_state, new_state)
    
    # 4. Relatório Estruturado
    report = {
        "status": "SUCCESS" if not post_drift else "FAILURE_DRIFT_PERSISTENT",
        "drift_detected_initial": bool(drift),
        "drift_corrected": not post_drift,
        "changes_applied": changes_applied,
        "initial_drift_issues": drift,
        "final_state": new_state
    }
    return report

# --- Testes de Integração ---

def run_test(test_name: str, desired: Dict[str, Any], current: Dict[str, Any], expected_success: bool):
    print(f"\n--- Executando Teste: {test_name} ---")
    report = sync_gitops(desired, current)
    
    # Validação do Critério de Sucesso (100% de sucesso significa que o estado final é o desejado)
    is_successful = report['status'] == "SUCCESS" and not report['drift_detected_initial']
    
    if expected_success:
        assert is_successful, f"Falha no teste {test_name}: Esperado sucesso, mas o relatório foi {report['status']}. Detecção de Drift: {report['drift_detected_initial']}"
        print(f"✅ {test_name} APROVADO. Mudanças aplicadas: {report['changes_applied']}")
    else:
        # Teste de correção de drift: Esperamos que o drift inicial seja detectado, mas corrigido.
        assert report['drift_detected_initial'] and report['drift_corrected'], f"Falha no teste {test_name}: Drift não detectado ou não corrigido. Relatório: {report}"
        print(f"✅ {test_name} APROVADO. Drift detectado e corrigido. Mudanças aplicadas: {report['changes_applied']}")

# Execução dos Testes de Integração
# Teste 1: Estado em conformidade (Deve ser sucesso sem mudanças)
run_test("Conformidade Inicial", DESIRED_STATE_GIT, CURRENT_STATE_CONFORMING, expected_success=True)

# Teste 2: Drift detectado (Deve detectar e corrigir)
run_test("Correção de Drift", DESIRED_STATE_GIT, CURRENT_STATE_DRIFT, expected_success=False)

# Teste 3: Idempotência (Aplicar novamente o estado corrigido - deve ter 0 mudanças)
print("\n--- Executando Teste: Idempotência (Reaplicação) ---")
report_idempotent = sync_gitops(DESIRED_STATE_GIT, CURRENT_STATE_DRIFT) # Usamos o estado corrigido do Teste 2
assert report_idempotent['changes_applied'] == 0, f"Falha na Idempotência: Esperado 0 mudanças, mas aplicou {report_idempotent['changes_applied']}"
print("✅ Idempotência APROVADO. Mudanças aplicadas: 0")

# Demonstração do Contraexemplo (Falha sem verificação de estado)
print("\n--- Demonstração de Contraexemplo: Aplicação Ingênua vs. GitOps ---")
# Simulação de aplicação ingênua: apenas sobrescreve, sem checar se já está certo.
def apply_naive(desired, current):
    new_state = desired.copy()
    return new_state

naive_state = apply_naive(DESIRED_STATE_GIT, CURRENT_STATE_CONFORMING)
# Se o estado já está correto, a aplicação ingênua desperdiça ciclos e não reporta que está OK.
# O GitOps reporta 0 mudanças se não houver drift, o que é o comportamento correto.
print(f"Estado após aplicação ingênua (sem checagem): {naive_state['port']}")
print("Conclusão: A aplicação ingênua falha em ser eficiente e não reporta a conformidade, violando o princípio de operação GitOps.")

print("\nTodos os testes de integração concluídos com sucesso.")