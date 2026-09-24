import time
import pytest
import jwt
from auth_system import TokenService, SECRET_KEY, ALGORITHM

def test_login_and_credential_validation():
    service = TokenService()
    # Login válido
    assert service.authenticate_user("alice", "senha_segura_123") is True
    # Login inválido (senha incorreta)
    assert service.authenticate_user("alice", "senha_errada") is False
    # Login inválido (usuário inexistente)
    assert service.authenticate_user("usuario_fantasma", "senha_segura_123") is False

def test_full_auth_flow():
    service = TokenService()
    
    # 1. Login e emissão de tokens
    assert service.authenticate_user("alice", "senha_segura_123") is True
    access_token = service.create_access_token("alice")
    refresh_token, family_id = service.create_refresh_token("alice")

    # 2. Verificação de Access Token válido
    username = service.verify_access_token(access_token)
    assert username == "alice"

    # 3. Logout (Revogação de Access Token)
    service.revoke_access_token(access_token)
    with pytest.raises(ValueError, match="Token revogado"):
        service.verify_access_token(access_token)

    # 4. Renovação de Sessão (Rotation)
    new_tokens = service.refresh_session(refresh_token)
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != refresh_token

    # 5. Tentativa de reutilizar o Refresh Token antigo (Detecção de Roubo e Revogação em Cascata)
    with pytest.raises(ValueError, match="Alerta de Segurança: Refresh Token reutilizado"):
        service.refresh_session(refresh_token)

    # 6. O novo refresh token emitido na rotação também deve ser invalidado por causa da revogação da família
    with pytest.raises(ValueError, match="Alerta de Segurança: Refresh Token reutilizado"):
        service.refresh_session(new_tokens["refresh_token"])

def test_expired_token():
    service = TokenService()
    payload = {"sub": "bob", "type": "access", "exp": time.time() - 10}
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(ValueError, match="Token expirado"):
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

def test_concurrent_refresh_race_condition():
    """Testa a operação atômica de rotação sob concorrência."""
    import threading
    service = TokenService()
    refresh_token, _ = service.create_refresh_token("alice")

    results = []
    def attempt_refresh():
        try:
            service.refresh_session(refresh_token)
            results.append("success")
        except ValueError as e:
            results.append(str(e))

    t1 = threading.Thread(target=attempt_refresh)
    t2 = threading.Thread(target=attempt_refresh)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Apenas uma das threads deve conseguir renovar com sucesso; a outra deve falhar por reutilização/revogação
    assert results.count("success") == 1
    assert any("Alerta de Segurança" in res for res in results)