import secrets
import string
import hashlib
from datetime import datetime, timedelta, timezone

# --- SECURITY CORE ---

class UserStore:
    """Simula um banco de dados de usuários com senhas hasheadas e saladas."""
    def __init__(self):
        self._users = {}

    def add_user(self, username, password):
        salt = secrets.token_hex(16)
        pw_hash = self._hash_password(password, salt)
        self._users[username] = {'hash': pw_hash, 'salt': salt}

    def _hash_password(self, password, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def verify_user(self, username, password):
        user = self._users.get(username)
        if not user:
            return False
        return user['hash'] == self._hash_password(password, user['salt'])

class MFAManager:
    """Gerencia códigos MFA com proteção contra Brute-Force e Replay."""
    def __init__(self, max_attempts=3, lockout_minutes=5):
        self._mfa_store = {}
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes

    def generate_code(self, user_id: str) -> str:
        """Gera código usando CSPRNG (secrets)."""
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self._mfa_store[user_id] = {
            'code': code,
            'expires_at': datetime.now(timezone.utc) + timedelta(minutes=5),
            'attempts': 0,
            'lockout_until': None
        }
        return code

    def send_code_simulated(self, user_id: str, code: str, method: str):
        """Simula envio sem expor o código nos logs de produção (apenas para o experimento)."""
        # Em produção, o código NÃO seria impresso no log.
        # Aqui, apenas simulamos o canal.
        print(f"[CHANNEL:{method.upper()}] Code sent to {user_id}")

    def verify_code(self, user_id: str, provided_code: str) -> bool:
        entry = self._mfa_store.get(user_id)
        if not entry:
            return False

        # 1. Check Lockout (Brute-force protection)
        if entry['lockout_until'] and datetime.now(timezone.utc) < entry['lockout_until']:
            return False

        # 2. Check Expiration
        if datetime.now(timezone.utc) > entry['expires_at']:
            del self._mfa_store[user_id]
            return False

        # 3. Verify Code
        if entry['code'] == provided_code:
            # SUCCESS: Anti-Replay (Delete immediately)
            del self._mfa_store[user_id]
            return True
        else:
            # FAILURE: Increment attempts and check lockout
            entry['attempts'] += 1
            if entry['attempts'] >= self.max_attempts:
                entry['lockout_until'] = datetime.now(timezone.utc) + timedelta(minutes=self.lockout_minutes)
            return False

# --- APPLICATION LOGIC ---

class VanustaAuthService:
    def __init__(self):
        self.users = UserStore()
        self.mfa = MFAManager()

    def login_step_1(self, username, password):
        """Primeira etapa: Autenticação de credenciais."""
        if self.users.verify_user(username, password):
            code = self.mfa.generate_code(username)
            self.mfa.send_code_simulated(username, code, "email")
            return "MFA_REQUIRED"
        raise ValueError("Invalid credentials")

    def login_step_2(self, username, code):
        """Segunda etapa: Verificação MFA e emissão de token."""
        if self.mfa.verify_code(username, code):
            return f"oauth_token_{secrets.token_urlsafe(16)}"
        raise ValueError("Invalid or expired MFA code (or account locked)")

# --- EXECUTION ---
if __name__ == "__main__":
    auth = VanustaAuthService()
    auth.users.add_user("alice", "password123")
    
    print("--- Teste Fluxo Normal ---")
    try:
        status = auth.login_step_1("alice", "password123")
        print(f"Status: {status}")
        # Para o experimento, pegamos o código gerado internamente (simulando o usuário recebendo)
        actual_code = auth.mfa._mfa_store["alice"]["code"]
        token = auth.login_step_2("alice", actual_code)
        print(f"Token emitido: {token}")
    except Exception as e:
        print(f"Erro: {e}")