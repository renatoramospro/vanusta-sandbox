import hmac
import hashlib
import time
import json

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
        if not isinstance(token, str):
            return False
        parts = token.split(".")
        if len(parts) != 3:
            return False
        header_str, payload_str, signature = parts
        
        # Recalcula assinatura para validar integridade
        message = f"{header_str}.{payload_str}"
        expected_sig = hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return False
            
        payload = json.loads(payload_str)
        if payload.get("exp", 0) < time.time():
            return False
            
        return True
    except Exception:
        return False

def evaluate_zero_trust_policy(token: str, context: dict) -> bool:
    """
    Motor PDP (Policy Decision Point) e PEP (Policy Enforcement Point).
    Avalia simultaneamente com tipagem estrita e blindagem contra entradas adversariais:
    1. Identidade válida (Token criptograficamente íntegro e não expirado).
    2. Contexto de segurança atualizado (< 300s) e risco aceitável (< 50).
    """
    # Passo 1: Verificação de Identidade
    if not verify_token(token):
        return False

    # Garante que o contexto seja um dicionário válido
    if not isinstance(context, dict):
        return False

    # Passo 2: Validação estrita e tipagem segura para Contexto Dinâmico
    current_time = time.time()
    
    raw_timestamp = context.get("timestamp", 0)
    raw_risk_score = context.get("risk_score", 100)

    # Tipagem estrita: valida se os tipos numéricos esperados são respeitados
    try:
        if not isinstance(raw_timestamp, (int, float)):
            return False
        if not isinstance(raw_risk_score, (int, float)) or isinstance(raw_risk_score, bool):
            # bool é subclasse de int em Python, logo filtramos explicitamente para evitar bypass
            return False
            
        context_timestamp = float(raw_timestamp)
        risk_score = float(raw_risk_score)
    except (ValueError, TypeError):
        # Falha segura: em caso de tipo malformado ou injeção, assume negação
        return False

    context_age = current_time - context_timestamp

    # Política Zero Trust: Contexto deve ter menos de 5 minutos (300s) e risco baixo (< 50)
    if context_age > 300 or risk_score >= 50:
        return False

    return True

def run_simulation():
    print("=== INICIANDO SIMULAÇÃO ZERO TRUST (PDP/PEP) ===")
    
    valid_token = generate_token("user_123", 3600)
    expired_token = generate_token("user_123", -10)
    now = time.time()

    print("\n--- Executando Testes Unitários de Política (Incluindo Tipagem Estrita) ---")
    
    # Teste 1: Caso Comum (Token válido + Contexto fresco e seguro)
    t1 = evaluate_zero_trust_policy(valid_token, {"timestamp": now, "risk_score": 10})
    print(f"[PASS] Token Válido + Contexto Fresco/Baixo Risco -> Esperado: True, Obtido: {t1}")
    assert t1 is True

    # Teste 2: Borda Temporal (> 300s)
    t2 = evaluate_zero_trust_policy(valid_token, {"timestamp": now - 301, "risk_score": 10})
    print(f"[PASS] Token Válido + Contexto Antigo (> 5 min) -> Esperado: False, Obtido: {t2}")
    assert t2 is False

    # Teste 3: Risco Elevado
    t3 = evaluate_zero_trust_policy(valid_token, {"timestamp": now, "risk_score": 50})
    print(f"[PASS] Token Válido + Alto Risco de Dispositivo -> Esperado: False, Obtido: {t3}")
    assert t3 is False

    # Teste 4: Cenário Adversarial de Tipagem (risk_score como string inyectada)
    t4 = evaluate_zero_trust_policy(valid_token, {"timestamp": now, "risk_score": "0"})
    print(f"[PASS] Cenário Adversarial (risk_score string '0') -> Esperado: False (Rejeição Segura), Obtido: {t4}")
    assert t4 is False

    # Teste 5: Cenário Adversarial de Tipagem (risk_score como booleano True)
    t5 = evaluate_zero_trust_policy(valid_token, {"timestamp": now, "risk_score": True})
    print(f"[PASS] Cenário Adversarial (risk_score booleano) -> Esperado: False (Rejeição Segura), Obtido: {t5}")
    assert t5 is False

    print("\n--- AVALIAÇÃO DE MÉTRICAS (Critério Refinado do Arquiteto) ---")
    mass_tests = []
    # 50 requisições legítimas
    for i in range(50):
        mass_tests.append((valid_token, {"timestamp": now - i, "risk_score": 10}, True))
    # 50 requisições ilegítimas (com mistos de tempo, risco e tipos maliciosos)
    for i in range(25):
        mass_tests.append((valid_token, {"timestamp": now - 400, "risk_score": 60}, False))
    for i in range(25):
        mass_tests.append((expired_token, {"timestamp": now, "risk_score": "malicious_string"}, False))

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
    print("\n[SUCESSO] O módulo atingiu todos os critérios de segurança Zero Trust com blindagem estrita de tipos!")

if __name__ == "__main__":
    run_simulation()