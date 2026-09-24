import time
import uuid
import threading
import os
import hashlib
import hmac
import jwt
from typing import Dict, Set, Optional, Any, Tuple

# 1. Segredo JWT dinâmico e suporte a rotação de chaves (múltiplos segredos aceitos na verificação)
JWT_SECRET_CURRENT = os.getenv("JWT_SECRET_CURRENT", "chave-secreta-atual-super-segura-e-longa-32-bytes")
JWT_SECRETS_HISTORIC = os.getenv("JWT_SECRETS_HISTORIC", "").split(",")
ALGORITHM = "HS256"

def _hash_token(token: str) -> str:
    """Armazena apenas o hash do refresh token para evitar exposição em claro."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

class TokenService:
    def __init__(self):
        # 2. Armazenamento seguro de senhas com Salt e Hash (evita texto claro)
        self.users_db: Dict[str, Dict[str, str]] = {
            "alice": self._hash_password("senha_segura_123"),
            "bob": self._hash_password("senha_segura_456")
        }
        self.blacklist: Set[str] = set()  # Access tokens revogados (logout)
        
        # 3. Estruturas para Refresh Token com Família de Sessões (Rotation & Family Revocation)
        # token_hash -> {"username": str, "family_id": str, "revoked": bool}
        self.refresh_tokens_db: Dict[str, Dict[str, Any]] = {}
        # family_id -> Set[token_hash] para revogação em cascata
        self.token_families: Dict[str, Set[str]] = {}
        
        # Lock para garantir atomicidade contra race conditions na rotação
        self._lock = threading.Lock()

    def _hash_password(self, password: str) -> str:
        salt = os.urandom(16).hex()
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return f"{salt}${pwd_hash}"

    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Comparação em tempo constante para prevenir timing attacks."""
        try:
            salt, stored_hash = stored_password.split('$')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
            return hmac.compare_digest(stored_hash, pwd_hash)
        except Exception:
            return False

    def authenticate_user(self, username: str, password: str) -> bool:
        """Validação segura de credenciais de login."""
        user_record = self.users_db.get(username)
        if not user_record:
            return False
        return self.verify_password(user_record, password)

    def create_access_token(self, username: str, expires_in_seconds: int = 900) -> str:
        payload = {
            "sub": username,
            "type": "access",
            "exp": time.time() + expires_in_seconds
        }
        return jwt.encode(payload, JWT_SECRET_CURRENT, algorithm=ALGORITHM)

    def create_refresh_token(self, username: str, expires_in_seconds: int = 604800, family_id: Optional[str] = None) -> Tuple[str, str]:
        if not family_id:
            family_id = str(uuid.uuid4())
            with self._lock:
                self.token_families[family_id] = set()

        payload = {
            "sub": username,
            "type": "refresh",
            "family_id": family_id,
            "exp": time.time() + expires_in_seconds
        }
        token = jwt.encode(payload, JWT_SECRET_CURRENT, algorithm=ALGORITHM)
        t_hash = _hash_token(token)
        
        with self._lock:
            self.refresh_tokens_db[t_hash] = {
                "username": username,
                "family_id": family_id,
                "revoked": False
            }
            self.token_families[family_id].add(t_hash)
            
        return token, family_id

    def _decode_jwt(self, token: str) -> dict:
        """Decodifica aceitando a chave atual e chaves históricas (rotação de segredos), blindado contra 'none'."""
        secrets = [JWT_SECRET_CURRENT] + [s for s in JWT_SECRETS_HISTORIC if s]
        last_error = None
        for secret in secrets:
            try:
                return jwt.decode(token, secret, algorithms=[ALGORITHM])
            except jwt.PyJWTError as e:
                last_error = e
        raise ValueError(f"Token inválido ou assinatura incorreta: {last_error}")

    def verify_access_token(self, token: str) -> str:
        payload = self._decode_jwt(token)
        if payload.get("type") != "access":
            raise ValueError("Tipo de token inválido (esperado access)")
        if token in self.blacklist:
            raise ValueError("Token revogado (blacklist)")
        return payload["sub"]

    def revoke_access_token(self, token: str):
        self.blacklist.add(token)

    def refresh_session(self, refresh_token: str) -> Tuple[str, str]:
        """Realiza a rotação do refresh token com detecção de roubo e revogação em cascata atômica."""
        payload = self._decode_jwt(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Tipo de token inválido (esperado refresh)")
            
        username = payload["sub"]
        family_id = payload["family_id"]
        t_hash = _hash_token(refresh_token)

        with self._lock:
            token_data = self.refresh_tokens_db.get(t_hash)
            
            # Se o token não existe na base ou já foi revogado (tentativa de reutilização/roubo)
            if not token_data or token_data["revoked"]:
                # REVOGAÇÃO EM CASCATA DE TODA A FAMÍLIA DE SESSÕES
                if family_id in self.token_families:
                    for fam_token_hash in self.token_families[family_id]:
                        if fam_token_hash in self.refresh_tokens_db:
                            self.refresh_tokens_db[fam_token_hash]["revoked"] = True
                raise ValueError("Alerta de Segurança: Tentativa de reutilização de Refresh Token revogado. Sessão invalidada.")

            # Marca o refresh token atual como revogado (rotação)
            token_data["revoked"] = True

            # Emite um novo par na mesma família
            new_access_token = self.create_access_token(username)
            new_refresh_token, _ = self.create_refresh_token(username, family_id=family_id)

            return new_access_token, new_refresh_token