import time
import jwt
from typing import Dict, Set, Optional

SECRET_KEY = "sua-chave-secreta-super-segura-e-longa"
ALGORITHM = "HS256"

class TokenService:
    def __init__(self):
        # Simula bases de dados em memória para fins didáticos/executáveis
        self.blacklist: Set[str] = {}  # Access tokens revogados (logout)
        self.refresh_tokens_db: Dict[str, str] = {}  # refresh_token -> username
        self.revoked_refresh_tokens: Set[str] = {}  # Refresh tokens já rotacionados/revogados

    def create_access_token(self, username: str, expires_in_seconds: int = 900) -> str:
        payload = {
            "sub": username,
            "type": "access",
            "exp": time.time() + expires_in_seconds
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, username: str, expires_in_seconds: int = 604800) -> str:
        payload = {
            "sub": username,
            "type": "refresh",
            "exp": time.time() + expires_in_seconds
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        self.refresh_tokens_db[token] = username
        return token

    def verify_access_token(self, token: str) -> Optional[str]:
        if token in self.blacklist:
            raise ValueError("Token revogado (Blacklisted)")
        
        try:
            # Exigimos explicitamente o algoritmo para evitar ataques de alg=none
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

    def refresh_session(self, old_refresh_token: str) -> Dict[str, str]:
        if old_refresh_token in self.revoked_refresh_tokens:
            # Rotação de segurança: reutilização de refresh token revogado indica roubo!
            # Invalidamos todos os tokens associados a este usuário (simulado limpando a base do user)
            username = self.refresh_tokens_db.get(old_refresh_token)
            if username:
                self._revoke_all_user_refresh_tokens(username)
            raise ValueError("Alerta de Segurança: Refresh Token reutilizado! Sessão invalidada por suspeita de roubo.")

        if old_refresh_token not in self.refresh_tokens_db:
            raise ValueError("Refresh token desconhecido")

        try:
            payload = jwt.decode(old_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                raise ValueError("Tipo de token inválido")
            username = payload.get("sub")
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token expirado")
        except jwt.InvalidTokenError:
            raise ValueError("Refresh token inválido")

        # Rotação de Refresh Token: invalida o antigo e emite um novo par
        username = self.refresh_tokens_db.pop(old_refresh_token, None)
        self.revoked_refresh_tokens.add(old_refresh_token)

        new_access_token = self.create_access_token(username)
        new_refresh_token = self.create_refresh_token(username)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }

    def _revoke_all_user_refresh_tokens(self, username: str):
        tokens_to_remove = [t for t, u in self.refresh_tokens_db.items() if u == username]
        for t in tokens_to_remove:
            self.refresh_tokens_db.pop(t, None)
            self.revoked_refresh_tokens.add(t)