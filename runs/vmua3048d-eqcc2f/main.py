import secrets
import string
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

# --- Configurações de Segurança ---
MAX_ATTEMPTS = 3
LOCKOUT_DURATION_SEC = 60
HASH_ITERATIONS = 100000
SALT_SIZE = 16

# --- Stores (Simulando Banco de Dados) ---
# _users: { username: { 'hash': b'', 'salt': b'' } }
_users: Dict[str, Dict[str, bytes]] = {}
# _mfa_store: { user_id: { 'code': str, 'expires_at': datetime } }
_mfa_store: Dict[str, Dict[str, Any]] = {}
# _attempts_store: { user_id: { 'count': int, 'lockout_until': datetime } }
_attempts_store: Dict[str, Dict[str, Any]] = {}

def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Gera hash seguro usando PBKDF2."""
    if salt is None:
        salt = secrets.token_bytes(SALT_SIZE)
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode(), 
        salt, 
        HASH_ITERATIONS
    )
    return pw_hash, salt

def register_user(username: str, password: str):
    """Registra um usuário com senha criptografada."""
    pw_hash, salt = hash_password(password)
    _users[username] = {'hash': pw_hash, 'salt': salt}

def is_locked_out(user_id: str) -> bool:
    """Verifica se o usuário está sob bloqueio por brute-force."""
    attempt = _attempts_store.get(user_id)
    if attempt and attempt['lockout_until'] > datetime.utcnow():
        return True
    return False

def generate_mfa_code(user_id: str, length: int = 6) -> str:
    """Gera código numérico usando CSPRNG (secrets)."""
    code = ''.join(secrets.choice(string.digits) for _ in range(length))
    _mfa_store[user_id] = {
        'code': code,
        'expires_at': datetime.utcnow() + timedelta(minutes=5)
    }
    return code

def send_mfa_code_simulated(user_id: str, code: str, method: str = 'email') -> None:
    """Simula envio sem expor o código nos logs de produção (apenas para o experimento)."""
    # Em produção, o print NÃO conteria o código, apenas a confirmação do envio.
    print(f"[LOG-INFO] MFA code sent via {method} to {user_id}")

def login_step_1(username: str, password: str) -> bool:
    """Fase 1: Autenticação de credenciais."""
    if is_locked_out(username):
        raise PermissionError("Account locked due to too many failed attempts.")

    user_data = _users.get(username)
    if not user_data:
        return False

    # Verifica hash da senha
    check_hash, _ = hash_password(password, user_data['salt'])
    if secrets.compare_digest(check_hash, user_data['hash']):
        # Sucesso na senha: gera MFA
        code = generate_mfa_code(username)
        send_mfa_code_simulated(username, code)
        return True
    else:
        # Falha na senha: incrementa contador de tentativas
        attempt = _attempts_store.get(username, {'count': 0, 'lockout_until': datetime.min})
        attempt['count'] += 1
        if attempt['count'] >= MAX_ATTEMPTS:
            attempt['lockout_until'] = datetime.utcnow() + timedelta(seconds=LOCKOUT_DURATION_SEC)
        _attempts_store[username] = attempt
        return False

def login_step_2_verify(username: str, code: str) -> str:
    """Fase 2: Verificação de MFA e emissão de token."""
    if is_locked_out(username):
        raise PermissionError("Account locked.")

    entry = _mfa_store.get(username)
    
    # Proteção contra Replay: Se não houver entrada, o código já foi usado ou expirou
    if not entry:
        raise ValueError("Invalid or already used MFA code.")

    # Invalidação imediata (Prevenção de Replay)
    _mfa_store.pop(username)

    if datetime.utcnow() > entry['expires_at']:
        raise ValueError("MFA code expired.")

    if secrets.compare_digest(entry['code'], code):
        # Sucesso: Reseta tentativas de erro
        _attempts_store.pop(username, None)
        return f"oauth_token_{secrets.token_urlsafe(32)}"
    else:
        # Falha no código: Incrementa tentativas
        attempt = _attempts_store.get(username, {'count': 0, 'lockout_until': datetime.min})
        attempt['count'] += 1
        if attempt['count'] >= MAX_ATTEMPTS:
            attempt['lockout_until'] = datetime.utcnow() + timedelta(seconds=LOCKOUT_DURATION_SEC)
        _attempts_store[username] = attempt
        raise ValueError("Invalid MFA code.")

# --- Mock de OAuth sem MFA (Para demonstrar o equívoco comum) ---
def naive_oauth_issue_token(username: str, password: str) -> str:
    """Simula um servidor OAuth vulnerável que não exige MFA."""
    user_data = _users.get(username)
    if user_data:
        check_hash, _ = hash_password(password, user_data['salt'])
        if secrets.compare_digest(check_hash, user_data['hash']):
            return "insecure_token_no_mfa"
    raise ValueError("Invalid credentials")