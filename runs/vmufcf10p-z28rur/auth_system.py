import time
import jwt
from typing import Dict, Set, Optional

SECRET_KEY = "sua-chave-secreta-super-segura-e-longa"
ALGORITHM = "HS256"

class TokenService:
    def __init__(self):
        # Simula bases de dados em memória para fins didáticos/executáveis
        self.blacklist: Set[str] = set()  # Access tokens revogados (logout)
        self.refresh_tokens_db: Dict[str, str] = {}  # refresh_token -> username
        self.revoked_refresh_tokens: Set[str] = set()  # Refresh tokens já rotacionados/revogados

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
        if refresh_token in self.revoked_refresh_tokens:
            # Alerta de roubo: Revoga toda a árvore/sessão associada se necessário
            raise ValueError("Alerta de Segurança: Refresh Token reutilizado (Tentativa de Roubo)")

        if refresh_token not in self.refresh_tokens_db:
            raise ValueError("Refresh Token desconhecido ou inválido")

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                raise ValueError("Tipo de token inválido")
            
            username = payload.get("sub")
            
            # Rotação: Invalida o refresh token atual
            del self.refresh_tokens_db[refresh_token]
            self.revoked_refresh_tokens.add(refresh_token)

            # Emite novo par
            new_access = self.create_access_token(username)
            new_refresh = self.create_refresh_token(username)

            return {
                "access_token": new_access,
                "refresh_token": new_refresh
            }
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh Token expirado")
        except jwt.InvalidTokenError:
            raise ValueError("Refresh Token inválido")