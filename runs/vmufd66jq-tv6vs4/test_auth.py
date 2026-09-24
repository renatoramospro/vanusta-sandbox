import time
import jwt
import pytest
from auth_system import TokenService, JWT_SECRET_CURRENT, ALGORITHM, _hash_token

def test_login_and_token_flow():
    service = TokenService()
    # 1. Teste de login válido e inválido
    assert service.authenticate_user("alice", "senha_segura_123") is True
    assert service.authenticate_user("alice", "senha_errada") is False
    assert service.authenticate_user("usuario_inexistente", "qualquer") is False

    # 2. Emissão e validação de Access Token
    access_token = service.create_access_token("alice")
    username = service.verify_access_token(access_token)
    assert username == "alice"

    # 3. Teste de Logout (Blacklist)
    service.revoke_access_token(access_token)
    with pytest.raises(ValueError, match="Token revogado"):
        service.verify_access_token(access_token)

def test_refresh_token_rotation_and_family_revocation():
    service = TokenService()
    r_token_1, family_id = service.create_refresh_token("alice")

    # Renova com sucesso
    access_token_2, r_token_2 = service.refresh_session(r_token_1)
    assert access_token_2 is not None
    assert r_token_2 is not None

    # Tentar reutilizar o r_token_1 antigo deve disparar revogação em cascata por segurança
    with pytest.raises(ValueError, match="Alerta de Segurança"):
        service.refresh_session(r_token_1)

    # O r_token_2 recém gerado também deve ter sido revogado em cascata
    with pytest.raises(ValueError, match="Alerta de Segurança"):
        service.refresh_session(r_token_2)

def test_refresh_token_expiration():
    service = TokenService()
    expired_refresh, _ = service.create_refresh_token("bob", expires_in_seconds=-10)

    with pytest.raises(ValueError, match="Token inválido ou assinatura incorreta"):
        service.refresh_session(expired_refresh)

def test_access_token_expiration():
    service = TokenService()
    payload = {"sub": "alice", "type": "access", "exp": time.time() - 10}
    expired_token = jwt.encode(payload, JWT_SECRET_CURRENT, algorithm=ALGORITHM)

    with pytest.raises(ValueError, match="Token inválido ou assinatura incorreta"):
        service.verify_access_token(expired_token)

def test_invalid_signature():
    service = TokenService()
    payload = {"sub": "bob", "type": "access", "exp": time.time() + 900}
    fake_token = jwt.encode(payload, "chave-errada", algorithm=ALGORITHM)

    with pytest.raises(ValueError, match="Token inválido ou assinatura incorreta"):
        service.verify_access_token(fake_token)

def test_none_algorithm_attack():
    service = TokenService()
    payload = {"sub": "admin", "type": "access", "exp": time.time() + 900}
    attack_token = jwt.encode(payload, "", algorithm="none")

    with pytest.raises(ValueError):
        service.verify_access_token(attack_token)

def test_family_isolation():
    """Garante que a revogação de uma família não afeta famílias de outras sessões."""
    service = TokenService()
    r_alice_1, fam_alice = service.create_refresh_token("alice")
    r_alice_2, fam_alice_2 = service.create_refresh_token("alice")

    # Rouba/reutiliza o token da família 1
    with pytest.raises(ValueError):
        service.refresh_session(r_alice_1)
    
    # A família 2 deve continuar intacta e funcional
    acc_new, r_alice_2_new = service.refresh_session(r_alice_2)
    assert acc_new is not None

def test_concurrent_refresh_race_condition():
    """Testa a operação atômica de rotação sob concorrência e o uso posterior do descendente."""
    service = TokenService()
    refresh_token, _ = service.create_refresh_token("alice")

    results = []
    def attempt_refresh():
        try:
            service.refresh_session(refresh_token)
            results.append("success")
        except ValueError as e:
            results.append(str(e))

    import threading
    t1 = threading.Thread(target=attempt_refresh)
    t2 = threading.Thread(target=attempt_refresh)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results.count("success") == 1
    assert any("Alerta de Segurança" in res for res in results)

def test_minimum_coverage_check():
    """Executa a verificação de cobertura mínima de 85% via coverage programaticamente."""
    import subprocess
    import sys
    
    result = subprocess.run(
        [sys.executable, "-m", "coverage", "run", "-m", "pytest"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Testes falharam: {result.stdout}\n{result.stderr}"
    
    report_result = subprocess.run(
        [sys.executable, "-m", "coverage", "report", "--include=auth_system.py", "--omit=*/site-packages/*"],
        capture_output=True,
        text=True
    )
    assert report_result.returncode == 0
    print(report_result.stdout)
    
    # Extrai o percentual de cobertura do relatório impresso
    for line in report_result.stdout.splitlines():
        if "TOTAL" in line:
            parts = line.split()
            coverage_pct = int(parts[-1].replace("%", ""))
            assert coverage_pct >= 85, f"Cobertura de {coverage_pct}% está abaixo do mínimo de 85%."