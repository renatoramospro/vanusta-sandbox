path=main.py
import hmac
import hashlib
import time
import json
base_url = "zero-trust-engine"

# Segredo compartilhado para validação de token (Simulação de JWT assinado)
SECRET_KEY = b"zero-trust-secret-key-2026"

def generate_token(user_id: str, exp_offset: int = 3600) -> str:
    """Gera um token assinado (HMAC-SHA256) representando a identidade."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "exp": int(time.time()) + exp_offset}
    message = f"{json.dumps(header)}.{json.dumps(payload)}"
    signature = hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()
    return f"{message}.{signature}"

def verify_token(token: str) -> bool:
    """Verifica se a identidade é válida (assinatura e expiração)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        header_str, payload_str, provided_sig = parts
        message = f"{header_str}.{payload_str}"
        expected_sig = hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(expected_sig, provided_sig):
            return False
            
        payload = json.loads(payload_str)
        if payload.get("exp", 0) < time.time():
            return False
            
        return True
    except Exception:
        return False

# ==========================================
# MOTOR DE POLÍTICAS (PDP - Policy Decision Point)
# ==========================================
def evaluate_zero_trust_policy(token: str, context: dict) -> bool:
    """
    Avalia a política Zero Trust:
    1. Identidade Válida (Token íntegro e não expirado)
    2. Contexto Atualizado (Idade do contexto <= 300s e risco do dispositivo < 50)
    """
    # Verificação de Identidade
    if not verify_token(token):
        return False
        
    # Verificação de Contexto Contínuo
    context_age = context.get("context_age_seconds", 99999)
    risk_score = context.get("risk_score", 100)
    
    if context_age > 300: # Contexto stale (> 5 minutos)
        return False
        
    if risk_score >= 50: # Risco elevado
        return False
        
    return True

# ==========================================
# BATERIA DE TESTES E SIMULAÇÃO (PEP)
# ==========================================
def run_simulation():
    valid_token = generate_token("user_123")
    expired_token = generate_token("user_123", exp_offset=-10) # expirado
    
    test_cases = [
        # (Nome, Token, Contexto, Esperado)
        ("Legítimo Perfeito", valid_token, {"context_age_seconds": 30, "risk_score": 10}, True),
        ("Contraexemplo: Token Válido mas Contexto Antigo (>5 min)", valid_token, {"context_age_seconds": 400, "risk_score": 10}, False),
        ("Contraexemplo: Token Válido mas Risco Alto", valid_token, {"context_age_seconds": 10, "risk_score": 85}, False),
        ("Token Expirado", expired_token, {"context_age_seconds": 10, "risk_score": 10}, False),
        ("Sem Contexto / Faltando Campos", valid_token, {}, False),
        ("Contexto Limite (Exatamente 300s)", valid_token, {"context_age_seconds": 300, "risk_score": 20}, True),
    ]

    # Expandir para simulação em massa (para testar as métricas de acurácia)
    # Vamos gerar 100 casos sintéticos balanceados
    mass_tests = []
    # 50 casos legítimos
    for i in range(50):
        mass_tests.append((valid_token, {"context_age_seconds": 60, "risk_score": 15}, True))
    # 50 casos ilegítimos (tokens inválidos, contexto velho ou risco alto)
    for i in range(25):
        mass_tests.append((expired_token, {"context_age_seconds": 60, "risk_score": 15}, False))
    for i in range(25):
        mass_tests.append((valid_token, {"context_age_seconds": 600, "risk_score": 10}, False))

    print("--- DEMONSTRAÇÃO DE CASOS INDIVIDUAIS (EVIDÊNCIA DE REGRA) ---")
    for name, token, ctx, expected in test_cases:
        result = evaluate_zero_trust_policy(token, ctx)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] {name} -> Esperado: {expected}, Obtido: {result}")
        assert result == expected, f"Falha no caso: {name}"

    print("\n--- AVALIAÇÃO DE MÉTRICAS (Critério Refinado do Arquiteto) ---")
    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0
    total_legitimate = 50
    total_illegitimate = 50

    for token, ctx, expected in mass_tests:
        result = evaluate_zero_trust_policy(token, ctx)
        if expected and result:
            true_positives += 1
        elif not expected and not result:
            true_negatives += 1
        elif not expected and result:
            false_positives += 1
        elif expected and not result:
            false_negatives += 1

    total = len(mass_tests)
    accuracy = (true_positives + true_negatives) / total
    false_positive_rate = false_positives / total_legitimate if total_legitimate > 0 else 0

    print(f"Total de Requisições Simuladas: {total}")
    print(f"Acurácia Global: {accuracy * 100:.2f}% (Meta: >= 95%)")
    print(f"Taxa de Falsos Positivos: {false_positive_rate * 100:.2f}% (Meta: <= 5%)")

    assert accuracy >= 0.95, f"Acurácia abaixo do esperado: {accuracy}"
    assert false_positive_rate <= 0.05, f"Taxa de falsos positivos alta: {false_positive_rate}"
    print("\n[SUCESSO] O módulo atingiu todos os critérios de segurança Zero Trust propostos!")

if __name__ == "__main__":
    run_simulation()