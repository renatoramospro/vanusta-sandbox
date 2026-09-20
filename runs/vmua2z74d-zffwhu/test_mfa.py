import pytest
from main import VanustaAuthService

@pytest.fixture
def auth_service():
    service = VanustaAuthService()
    service.users.add_user("bob", "secure_pass")
    return service

def test_successful_mfa_flow(auth_service):
    """Valida o caminho feliz: login -> mfa -> token."""
    auth_service.login_step_1("bob", "secure_pass")
    # Recupera o código gerado para o teste
    code = auth_service.mfa._mfa_store["bob"]["code"]
    token = auth_service.login_step_2("bob", code)
    assert "oauth_token_" in token

def test_password_is_not_plain_text(auth_service):
    """Garante que a senha não está armazenada em texto puro (Segurança)."""
    user_data = auth_service.users._users["bob"]
    assert user_data["hash"] != "secure_pass"
    assert "salt" in user_data

def test_mfa_replay_attack(auth_service):
    """Garante que um código usado uma vez não pode ser reutilizado (Anti-Replay)."""
    auth_service.login_step_1("bob", "secure_pass")
    code = auth_service.mfa._mfa_store["bob"]["code"]
    
    # Primeiro uso: Sucesso
    auth_service.login_step_2("bob", code)
    
    # Segundo uso: Deve falhar pois o código foi deletado
    with pytest.raises(ValueError, match="Invalid or expired MFA code"):
        auth_service.login_step_2("bob", code)

def test_brute_force_protection(auth_service):
    """Garante que após X tentativas falhas, o usuário é bloqueado (Rate Limiting)."""
    auth_service.login_step_1("bob", "secure_pass")
    
    # Tentar 3 vezes com código errado (limite do MFAManager)
    for _ in range(3):
        with pytest.raises(ValueError):
            auth_service.login_step_2("bob", "000000")
            
    # A 4ª tentativa, mesmo com o código CORRETO, deve falhar devido ao lockout
    actual_code = auth_service.mfa._mfa_store["bob"]["code"]
    with pytest.raises(ValueError, match="account locked"):
        auth_service.login_step_2("bob", actual_code)

def test_invalid_credentials(auth_service):
    """Valida que credenciais erradas não iniciam o MFA."""
    with pytest.raises(ValueError, match="Invalid credentials"):
        auth_service.login_step_1("bob", "wrong_password")