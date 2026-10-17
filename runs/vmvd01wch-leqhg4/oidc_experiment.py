import json
import time
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

class MockIdP:
    """Simula um Provedor de Identidade OpenID Connect (ex: Google / Azure AD)."""
    def __init__(self, issuer="https://auth.vanusta.com"):
        self.issuer = issuer
        # Gera chave privada RSA para assinar os tokens
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self.kid = "key-vanusta-1"

    def get_jwks(self):
        """Retorna o JSON Web Key Set (JWKS) com a chave pública para validação."""
        public_numbers = self.public_key.public_numbers()
        e_bytes = public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')
        n_bytes = public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')
        
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self.kid,
                    "n": base64url_encode(n_bytes),
                    "e": base64url_encode(e_bytes)
                }
            ]
        }

    def issue_tokens(self, client_id: str, user_id: str, scopes: list):
        """Emite um ID Token (OIDC) e um Access Token (OAuth 2.0)."""
        now = int(time.time())
        
        # ID Token (contém claims de identidade do OIDC)
        id_token_header = {"alg": "RS256", "typ": "JWT", "kid": self.kid}
        id_token_payload = {
            "iss": self.issuer,
            "sub": user_id,
            "aud": client_id,
            "exp": now + 3600,
            "iat": now,
            "auth_time": now,
            "email": f"{user_id}@vanusta.com"
        }
        
        # Access Token (focado em autorização para APIs)
        access_token_header = {"alg": "RS256", "typ": "JWT", "kid": self.kid}
        access_token_payload = {
            "iss": self.issuer,
            "sub": user_id,
            "client_id": client_id,
            "scope": " ".join(scopes),
            "exp": now + 3600,
            "iat": now
        }

        id_token = self._sign_jwt(id_token_header, id_token_payload)
        access_token = self._sign_jwt(access_token_header, access_token_payload)
        
        return id_token, access_token

    def _sign_jwt(self, header: dict, payload: dict) -> str:
        header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
        payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        
        signature = self.private_key.sign(
            signing_input,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_b64 = base64url_encode(signature)
        return f"{header_b64}.{payload_b64}.{signature_b64}"


class ProtectedResourceServer:
    """API Protegida que valida tokens emitidos pelo IdP usando o JWKS."""
    def __init__(self, idp: MockIdP, expected_audience: str):
        self.idp = idp
        self.expected_audience = expected_audience

    def validate_and_access(self, token: str, required_scope: str) -> dict:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Token malformado.")
        
        header_b64, payload_b64, sig_b64 = parts
        
        # 1. Verifica Assinatura Criptográfica via JWKS
        jwks = self.idp.get_jwks()
        header = json.loads(base64.urlsafe_b64decode(header_b64 + '==').decode('utf-8'))
        
        if header.get("kid") != jwks["keys"][0]["kid"]:
            raise ValueError("Chave (kid) desconhecida.")
            
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = base64.urlsafe_b64decode(sig_b64 + '==')
        
        try:
            self.idp.public_key.verify(
                signature,
                signing_input,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        except Exception:
            raise ValueError("Falha na assinatura criptográfica do token!")

        # 2. Decodifica Payload
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + '==').decode('utf-8'))

        # 3. Valida Claims Obrigatórias
        now = int(time.time())
        if payload.get("exp", 0) < now:
            raise ValueError("Token expirado.")
        if payload.get("iss") != self.idp.issuer:
            raise ValueError("Emissor (iss) inválido.")
        
        # Se for ID Token tem 'aud', se for Access Token pode ter 'client_id' ou 'aud'
        aud = payload.get("aud")
        if aud and aud != self.expected_audience:
            raise ValueError("Audiência (aud) inválida.")

        # 4. Valida Escopos para APIs Protegidas
        scopes = payload.get("scope", "").split()
        if required_scope and required_scope not in scopes:
            raise ValueError(f"Escopo necessário '{required_scope}' ausente.")

        return payload


# --- EXECUTANDO O EXPERIMENTO ---
if __name__ == "__main__":
    print("--- Iniciando Experimento OIDC / API Protegida ---")
    
    # 1. Configurar Provedor e API
    idp = MockIdP(issuer="https://auth.vanusta.com")
    api = ProtectedResourceServer(idp=idp, expected_audience="client-app-123")
    
    # 2. Simular Autenticação de Usuário com Sucesso
    client_id = "client-app-123"
    user_id = "user-alice-99"
    scopes = ["openid", "profile", "api.read"]
    
    id_token, access_token = idp.issue_tokens(client_id, user_id, scopes)
    print("[Sucesso] Tokens emitidos pelo Provedor de Identidade.")
    
    # 3. Acessar API Protegida com Access Token Válido
    claims = api.validate_and_access(access_token, required_scope="api.read")
    print(f"[Sucesso] API acessada por: {claims['sub']} com escopos: {claims['scope']}")

    # 4. Demonstrar Contraexemplo (Equívoco Comum: Aceitar Token sem validação de expiração ou assinatura)
    print("\n--- Testando Contraexemplo (Falha de Segurança) ---")
    # Criando um token expirado intencionalmente
    expired_id, expired_access = idp.issue_tokens(client_id, user_id, scopes)
    
    # Forjando payload expirado
    header_b64, payload_b64, sig_b64 = expired_access.split('.')
    payload_dict = json.loads(base64.urlsafe_b64decode(payload_b64 + '==').decode('utf-8'))
    payload_dict["exp"] = int(time.time()) - 10 # Expirado há 10 segundos
    
    new_payload_b64 = base64url_encode(json.dumps(payload_dict, separators=(',', ':')).encode('utf-8'))
    tampered_token = f"{header_b64}.{new_payload_b64}.{sig_b64}" # Assinatura não bate mais com payload alterado
    
    try:
        api.validate_and_access(tampered_token, required_scope="api.read")
    except ValueError as e:
        print(f"[Contraexemplo Capturado com Sucesso] Acesso negado conforme esperado: {e}")

    print("\nExperimento concluído com sucesso e código de saída 0.")