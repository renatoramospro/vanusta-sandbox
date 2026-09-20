import pytest
from main import (
    register_user, login_step_1, login_step_2_verify, 
    naive_oauth_issue_token, _users, _mfa_store, _attempts_store
)

def setup_module(module):
    """Configura usuários de teste antes de rodar os testes."""
    register_user("alice", "password123")
    register_user("bob", "secure!pass")

def test_secure_password_storage():
    """Valida que as senhas não estão em texto puro."""
    alice_data = _users["alice"]
    assert alice_data['hash'] != b"password123"
    assert isinstance(alice_data['hash'], bytes)

def test_mfa_success_flow():
    """Cenário Comum: Login e MFA bem-sucedidos."""
    # Passo 1: Login com senha
    assert login_step_1("alice", "password123") is True
    
    # Recuperar o código gerado (apenas para o teste)
    code = _mfa_store["alice"]["code"]
    
    # Passo 2: Verificação do código
    token = login_step_2_verify("alice", code)
    assert token.startswith("oauth_token_")

def test_mfa_replay_attack():
    """Cenário Adversarial: Tentativa de reutilizar o mesmo código (Replay)."""
    login_step_1("alice", "password123")
    code = _mfa_store["alice"]["code"]
    
    # Primeiro uso: Sucesso
    login_step_2_verify("alice", code)
    
    # Segundo uso: Deve falhar porque o código foi removido (pop)
    with pytest.raises(ValueError, match="Invalid or already used MFA code"):
        login_step_2_verify("alice", code)

def test_mfa_brute_force_protection():
    """Cenário Adversarial: Tentativa de força bruta no MFA."""
    login_step_1("bob", "secure!pass")
    
    # Tentar códigos errados até o limite
    for _ in range(3):
        with pytest.raises(ValueError):
            login_step_2_verify("bob", "000000")
            
    # A 4ª tentativa (mesmo com código certo) deve ser bloqueada por lockout
    # Primeiro, vamos gerar um código válido para o teste
    from main import generate_mfa_code
    code = generate_mfa_code("bob")
    
    with pytest.raises(PermissionError, match="Account locked"):
        login_step_2_verify("bob", code)

def test_naive_oauth_vulnerability():
    """Demonstra o equívoco comum: OAuth sem MFA é inseguro."""
    # O fluxo 'naïve' emite token apenas com senha, ignorando MFA
    token = naive_oauth_issue_token("alice", "password123")
    assert token == "insecure_token_no_mfa"