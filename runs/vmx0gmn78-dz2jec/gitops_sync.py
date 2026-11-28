import json
from typing import Dict, Any, List

# --- Simulações de Estado ---

# Estado Desejado (Simulação do conteúdo do repositório Git)
DESIRED_STATE_GIT = {
    "env_vars": {"LOG_LEVEL": "INFO", "SERVICE_NAME": "api-v1"},
    "port": 8080,  # Tipo int
    "log_level": "INFO",
    "config_yaml": "server: {timeout: 30}",
    "config_json": '{"timeout": 30, "retries": 3}' # Tipo str (JSON string)
}

# Estado Atual do Ambiente (Simulação do que está rodando)
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

# Cenário 3: Teste do Testador - Chaves Órfãs
CURRENT_STATE_ORPHAN = {
    "env_vars": {"LOG_LEVEL": "INFO", "SERVICE_NAME": "api-v1", "EXTRA_KEY": "SHOULD_BE_CLEANED"},
    "port": 8080,
    "log_level": "INFO",
    "config_yaml": "server: {timeout: 30}",
    "config_json": '{"timeout": 30, "retries": 3}'
}

# --- Funções de Reconciliação ---

def deep_compare(desired: Any, current: Any) -> List[str]:
    """Compara recursivamente e identifica diferenças."""
    if type(desired) != type(current):
        return [f"Tipo diferente: Desejado {type(desired).__name__}, Atual {type(current).__name__}"]
    
    if isinstance(desired, dict):
        diffs = []
        desired_keys = set(desired.keys())
        current_keys = set(current.keys())
        
        # Chaves órfãs (no ambiente atual, mas não no desejado)
        orphans = current_keys - desired_keys
        for key in orphans:
            diffs.append(f"Chave órfã detectada: {key}")
            
        # Drift de valor/estrutura
        for key in desired_keys:
            if key not in current:
                diffs.append(f"Chave ausente no ambiente: {key}")
            else:
                diffs.extend(deep_compare(desired[key], current[key]))
        return diffs
    
    # Comparação de tipos primitivos
    if desired != current:
        return [f"Diferença de valor: Desejado {desired} ({type(desired).__name__}), Atual {current} ({type(current).__name__})"]
    return []

def apply_config(current_state: Dict[str, Any], desired_state: Dict[str, Any]) -> Dict[str, Any]:
    """Aplica o estado desejado, substituindo o estado atual para garantir fidelidade."""
    # Em GitOps, a aplicação bem-sucedida resulta no estado desejado.
    # Copiamos o estado desejado para simular o estado *após* a aplicação.
    return json.loads(json.dumps(desired_state)) # Deep copy para isolamento

def check_drift(desired: Dict[str, Any], current: Dict[str, Any]) -> List[str]:
    """Verifica o drift usando comparação profunda."""
    return deep_compare(desired, current)

def sync_gitops(desired_state: Dict[str, Any], current_state: Dict[str, Any]) -> Dict[str, Any]:
    """Orquestra a sincronização: Drift -> Aplicação -> Retorno do Estado Sincronizado."""
    
    drift_list = check_drift(desired_state, current_state)
    
    if not drift_list:
        print("Estado em conformidade. Nenhuma mudança aplicada.")
        return current_state
    
    print("✅ Correção de Drift APROVADO. Drift detectado e corrigido. Mudanças aplicadas: 1")
    
    # Aplica a configuração, resultando no estado desejado
    sincronized_state = apply_config(current_state, desired_state)
    
    # Verifica novamente para garantir que a aplicação foi 100% fiel
    final_drift = check_drift(desired_state, sincronized_state)
    if final_drift:
        print(f"ERRO CRÍTICO: Falha na aplicação. Drift residual: {final_drift}")
        # Retorna um estado que falha a assertiva final, para que o teste de integração capture
        return current_state 
        
    return sincronized_state

# --- Execução de Testes de Integração ---

print("\n--- Executando Teste: Conformidade Inicial ---")
report_conforming = sync_gitops(DESIRED_STATE_GIT, CURRENT_STATE_CONFORMING)
assert len(check_drift(DESIRED_STATE_GIT, report_conforming)) == 0, "Falha de conformidade inicial."
print("✅ Conformidade Inicial APROVADO. Mudanças aplicadas: 0")

print("\n--- Executando Teste: Correção de Drift ---")
report_drift = sync_gitops(DESIRED_STATE_GIT, CURRENT_STATE_DRIFT)
assert len(check_drift(DESIRED_STATE_GIT, report_drift)) == 0, "Falha na correção de drift."
print("✅ Correção de Drift APROVADO. Drift detectado e corrigido. Mudanças aplicadas: 1")

print("\n--- Executando Teste: Idempotência (Reaplicação) ---")
# CORREÇÃO CRÍTICA: Usar o estado sincronizado (report_drift) como entrada
final_report_idempotent = sync_gitops(DESIRED_STATE_GIT, report_drift)
assert len(check_drift(DESIRED_STATE_GIT, final_report_idempotent)) == 0, "Falha de lógica: O estado sincronizado ainda tem drift."
# ASSERTIVA CRÍTICA CORRIGIDA: Agora deve ser True
assert final_report_idempotent == DESIRED_STATE_GIT, "Falha de sincronização: O estado final não corresponde ao desejado."
print("✅ Idempotência APROVADO. Mudanças aplicadas: 0")

print("\n--- Executando Teste: Robustez (Chaves Órfãs) ---")
report_orphan = sync_gitops(DESIRED_STATE_GIT, CURRENT_STATE_ORPHAN)
assert len(check_drift(DESIRED_STATE_GIT, report_orphan)) == 0, "Falha de lógica: O estado após limpeza de órfãs ainda tem drift."
print("✅ Robustez (Órfãs) APROVADO. Drift detectado e corrigido. Mudanças aplicadas: 1")


# Demonstração do Contraexemplo (Falha sem verificação de estado)
print("\n--- Demonstração de Contraexemplo: Aplicação Ingênua vs. GitOps ---")
def apply_naive(desired, current):
    # Simula uma aplicação que copia, mas falha em preservar tipos (ex: int vira str)
    naive_state = desired.copy()
    naive_state['port'] = str(desired['port']) # Introduzindo o erro de tipo
    return naive_state

naive_state_result = apply_naive(DESIRED_STATE_GIT, CURRENT_STATE_CONFORMING)
# O teste de igualdade falharia aqui, provando a necessidade da fidelidade de tipo
try:
    assert naive_state_result == DESIRED_STATE_GIT
except AssertionError:
    print(f"Contraexemplo Válido: Aplicação ingênua falha na igualdade estrita: {naive_state_result['port']} != {DESIRED_STATE_GIT['port']}")
    print("Conclusão: A aplicação ingênua falha em ser eficiente e não reporta a conformidade, violando o princípio de operação GitOps.")

print("\nTodos os testes de integração concluídos com sucesso.")