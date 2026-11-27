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
    Avalia simultaneamente:
    1. Identidade válida (Token criptograficamente íntegro e não expirado).
    2. Contexto de segurança atualizado (< 300s) e risco aceitável (< 50).
    """
    # Passo 1: Verificação de Identidade
    if not verify_token(token):
        return False

    # Passo 2: Verificação de Contexto Dinâmico (Anti-Equívoco Comum)
    current_time = time.time()
    context_timestamp = context.get("timestamp", 0)
    context_age = current_time - context_timestamp
    risk_score = context.get("risk_score", 100)

    # Política Zero Trust: Contexto deve ter menos de 5 minutos (300s) e risco baixo
    if context_age > 300 or risk_score >= 50:
        return False

    return True

def run_simulation():
    print("=== INICIANDO SIMULAÇÃO ZERO TRUST (PDP/PEP) ===")
    
    valid_token = generate_token("user-alice-123")
    expired_token = generate_token("user-bob-456", exp_offset=-360) # Expirado
    tampered_token = valid_token[:-5] + "12345" # Assinatura corrompida

    now = time.time()

    # Casos de teste individuais demonstrando o conceito
    unit_tests = [
        ("Token Válido + Contexto Fresco/Baixo Risco", valid_token, {"timestamp": now, "risk_score": 10}, True),
        ("Token Válido + Contexto Antigo (> 5 min)", valid_token, {"timestamp": now - 400, "risk_score": 10}, False),
        ("Token Válido + Alto Risco de Dispositivo", valid_token, {"timestamp": now, "risk_score": 85}, False),
        ("Token Expirado + Contexto Fresco", expired_token, {"timestamp": now, "risk_score": 10}, False),
        ("Token Corrompido/Falso + Contexto Fresco", tampered_token, {"timestamp": now, "risk_score": 10}, False),
    ]

    print("\n--- Executando Testes Unitários de Política ---")
    for name, token, ctx, expected in unit_tests:
        result = evaluate_zero_trust_policy(token, ctx)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] {name} -> Esperado: {expected}, Obtido: {result}")
        assert result == expected, f"Falha no caso: {name}"

    print("\n--- AVALIAÇÃO DE MÉTRICAS (Critério Refinado do Arquiteto) ---")
    
    # Gerando massa de teste balanceada (50 legítimas, 50 ilegítimas)
    mass_tests = []
    
    # 50 Requisições Legítimas (Devem passar)
    for i in range(50):
        mass_tests.append((valid_token, {"timestamp": now - (i % 100), "risk_score": 5}, True))
        
    # 50 Requisições Ilegítimas (Devem ser rejeitadas por token inválido ou contexto ruim)
    for i in range(25):
        # Contexto antigo ou de alto risco com token válido
        mass_tests.append((valid_token, {"timestamp": now - 400, "risk_score": 60}, False))
    for i in range(25):
        # Token inválido com contexto fresco
        mass_tests.append((expired_token, {"timestamp": now, "risk_score": 10}, False))

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