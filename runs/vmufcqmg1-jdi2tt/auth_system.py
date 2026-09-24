import time
import uuid
import threading
import jwt
from typing import Dict, Set, Optional, Any

SECRET_KEY = "sua-chave-secreta-super-segura-e-longa"
ALGORITHM = "HS256"

class TokenService:
    def __init__(self):
        # Bases de dados em memória para simular armazenamento seguro
        self.users_db: Dict[str, str] = {"alice": "senha_segura_123", "bob": "senha_segura_456"}
        self.blacklist: Set[str] = set()  # Access tokens revogados (logout)
        
        # Estruturas para Refresh Token com Família de Sessões (Rotation & Family Revocation)
        # refresh_token -> {"username": str, "family_id": str, "revoked": bool}
        self.refresh_tokens_db: Dict[str, Dict[str, Any]] = {}
        # family_id -> Set[refresh_token] para revogação em cascata
        self.token_families: Dict[str, Set[str]] = {}
        
        # Lock para garantir atomicidade contra race conditions na rotação
        self._lock = threading.Lock()

    def authenticate_user(self, username: str, password: str) -> bool:
        """Simula a validação de credenciais de login."""
        stored_password = self.users_db.get(username)
        if not stored_password or stored_password != password:
            return False
        return True

    def create_access_token(self, username: str, expires_in_seconds: int = 900) -> str:
        payload = {
            "sub": username,
            "type": "access",
            "exp": time.time() + expires_in_seconds
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, username: str, expires_in_seconds: int = 604800, family_id: Optional[str] = None) -> tuple[str, str]:
        if not family_id:
            family_id = str(uuid.uuid4())
            self.token_families[family_id] = set()

        payload = {
            "sub": username,
            "type": "refresh",
            "family_id": family_id,
            "exp": time.time() + expires_in_seconds
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        self.refresh_tokens_db[token] = {
            "username": username,
            "family_id": family_id,
            "revoked": False
        }
        self.token_families[family_id].add(token)
        return token, family_id

    def verify_access_token(self, token: str) -> Optional[str]:
        if token in self.blacklist:
            raise ValueError("Token revogado (Blacklisted)")
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "access":
                raise ValueError("Tipo de token inválido")
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado")
        except jwt.InvalidTokenError:
            raise ValueError("Token inválido ou assinatura incorreta")

    def revoke_access_token(self, token: str):
        self.blacklist.add(token)

    def refresh_session(self, refresh_token: str) -> Dict[str, str]:
        with self._lock: # Operação atômica para evitar race conditions em requisições simultâneas
            if refresh_token not in self.refresh_tokens_db:
                raise ValueError("Refresh token desconhecido")

            token_info = self.refresh_tokens_db[refresh_token]
            family_id = token_info["family_id"]

            # Se o token já foi revocado ou a família foi comprometida, detecta roubo e revoga tudo
            if token_info["revoked"]:
                self._revoke_entire_family(family_id)
                raise ValueError("Alerta de Segurança: Refresh Token reutilizado (Tentativa de Roubo). Família revogada.")

            try:
                payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                if payload.get("type") != "refresh":
                    raise ValueError("Tipo de token inválido")
            except jwt.ExpiredSignatureError:
                self._revoke_entire_family(family_id)
                raise ValueError("Refresh token expirado")
            except jwt.InvalidTokenError:
                raise ValueError("Refresh token inválido")

            # Rotação: Revoga o token atual da família
            token_info["revoked"] = True

            username = token_info["username"]
            # Emite novo par mantendo a mesma família
            new_access = self.create_access_token(username)
            new_refresh, _ = self.create_refresh_token(username, family_id=family_id)

            return {
                "access_token": new_access,
                "refresh_token": new_refresh
            }

    def _revoke_entire_family(self, family_id: str):
        """Revoga em cascata todos os refresh tokens pertencentes à mesma família."""
        if family_id in self.token_families:
            for token in self.token_families[family_id]:
                if token in self.refresh_tokens_db:
                    self.refresh_tokens_db[token]["revoked"] = True