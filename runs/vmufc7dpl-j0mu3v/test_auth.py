import pytest
import time
from auth_system import TokenService, SECRET_KEY, ALGORITHM
import jwt

def test_full_auth_flow():
    service = TokenService()
    username = "alice"

    # 1. Login bem-sucedido
    access_token = service.create_access_token(username)
    refresh_token = service.create_refresh_token(username)
    
    assert access_token is not None
    assert refresh_token is not None

    # 2. Verificar Access Token válido
    user = service.verify_access_token(access_token)
    assert user == username

    # 3. Logout (Blacklist)
    service.revoke_access_token(access_token)
    with pytest.raises(ValueError, match="Token revogado"):
        service.verify_access_token(access_token)

    # 4. Renovação com Refresh Token bem-sucedida (Rotation)
    new_tokens = service.refresh_session(refresh_token)
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != refresh_token

    # 5. Tentativa de reutilizar o Refresh Token antigo (Detecção de Roubo)
    with pytest.raises(ValueError, match="Alerta de Segurança: Refresh Token reutilizado"):
        service.refresh_session(refresh_token)

def test_expired_token():
    service = TokenService()
    # Cria token expirado no passado
    payload = {"sub": "bob", "type": "access", "exp": time.time() - 10}
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(ValueError, match="Token expirado"):
        service.verify_access_token(expired_token)

def test_invalid_signature():
    service = TokenService()
    # Assina com chave incorreta
    payload = {"sub": "bob", "type": "access", "exp": time.time() + 900}
    fake_token = jwt.encode(payload, "chave-errada", algorithm=ALGORITHM)

    with pytest.raises(ValueError, match="Token inválido ou assinatura incorreta"):
        service.verify_access_token(fake_token)

def test_none_algorithm_attack():
    service = TokenService()
    # Tenta forçar ataque alterando o algoritmo para 'none' (vulnerabilidade clássica)
    payload = {"sub": "admin", "type": "access", "exp": time.time() + 900}
    # Forjando cabeçalho e assinatura vazia
    attack_token = jwt.encode(payload, "", algorithm="none")

    with pytest.raises(ValueError):
        service.verify_access_token(attack_token)