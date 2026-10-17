import json
import time
import base64
import hmac
import hashlib

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

class MockIdP:
    """Simula um Provedor de Identidade OpenID Connect (ex: Google / Azure AD)."""
    def __init__(self, issuer="https://auth.vanusta.com"):
        self.issuer = issuer
        # Chave secreta do IdP para assinatura HMAC-SHA256 (HS256)
        self.secret_key = b"vanusta-secret-signing-key-2026"
        self.kid = "key-vanusta-1"

    def get_jwks(self):
        """Retorna o JWKS simulado contendo metadados da chave de assinatura."""
        return {
            "keys": [
                {
                    "kty": "oct",
                    "use": "sig",
                    "alg": "HS256",
                    "kid": self.kid
                }
            ]
        }

    def _sign(self, message: bytes) -> str:
        signature = hmac.new(self.secret_key, message, hashlib.sha256).digest()
        return base64url_encode(signature)

    def issue_tokens(self, client_id: str, user_id: str, scopes: list):
        """Emite um ID Token (OIDC) e um Access Token (OAuth 2.0)."""
        now = int(time.time())
        
        # ID Token (contém claims de identidade do OIDC)
        id_token_header = {"alg": "HS256", "typ": "JWT", "kid": self.kid}
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
        access_token_header = {"alg": "HS256", "typ": "JWT", "kid": self.kid}
        access_token_payload = {
            "iss": self.issuer,
            "sub": user_id,
            "client_id": client_id,
            "scope": " ".join(scopes),
            "exp": now + 3600,
            "iat": now
        }
        
        def create_jwt(header, payload):
            h_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
            p_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
            message = f"{h_b64}.{p_b64}".encode('utf-8')
            sig = self._sign(message)
            return f"{h_b64}.{p_b64}.{sig}"

        return {
            "id_token": create_jwt(id_token_header, id_token_payload),
            "access_token": create_jwt(access_token_header, access_token_payload),
            "token_type": "Bearer",
            "expires_in": 3600
        }

class ProtectedAPI:
    """Simula uma API protegida que valida tokens emitidos pelo IdP."""
    def __init__(self, issuer: str, expected_aud: str, idp: MockIdP):
        self.issuer = issuer
        self.expected_aud = expected_aud
        self.idp = idp

    def validate_and_access(self, token: str, required_scope: str):
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Token JWT malformado.")
        
        h_b64, p_b64, sig_b64 = parts
        
        # 1. Validação Criptográfica (Integridade e Autenticidade)
        message = f"{h_b64}.{p_b64}".encode('utf-8')
        expected_sig = self.idp._sign(message)
        if not hmac.compare_digest(expected_sig, sig_b64):
            raise ValueError("Assinatura do token inválida!")

        # 2. Decodificação do Payload
        try:
            payload = json.loads(base64url_decode(p_b64).decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Falha ao decodificar payload do JWT: {e}")

        # 3. Validação de Claims Obrigatórias
        if payload.get("iss") != self.issuer:
            raise ValueError(f"Emissor (iss) inválido: {payload.get('iss')}")

        if "aud" in payload and payload.get("aud") != self.expected_aud:
            raise ValueError(f"Audiência (aud) inválida: {payload.get('aud')}")

        # 4. Validação de Expiração
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expirado.")

        # 5. Validação de Escopo (Access Token)
        if "scope" in payload:
            scopes = payload["scope"].split()
            if required_scope not in scopes:
                raise ValueError(f"Escopo insuficiente. Necessário: {required_scope}")

        return payload

if __name__ == "__main__":
    print("=== Iniciando Experimento OIDC / JWT Corrigido ===")
    
    # Inicializa Provedor de Identidade e API Protegida
    idp = MockIdP(issuer="https://auth.vanusta.com")
    api = ProtectedAPI(
        issuer="https://auth.vanusta.com",
        expected_aud="client-app-xyz",
        idp=idp
    )

    # 1. Cenário de Sucesso: Autenticação e emissão de tokens
    print("\n[Cenário 1] Autenticando usuário e emitindo tokens...")
    tokens = idp.issue_tokens(
        client_id="client-app-xyz",
        user_id="user_12345",
        scopes=["openid", "profile", "api.read"]
    )
    print(f"ID Token obtido: {tokens['id_token'][:30]}...")
    print(f"Access Token obtido: {tokens['access_token'][:30]}...")

    # 2. Validação bem-sucedida na API Protegida
    print("\n[Cenário 2] Acessando API protegida com Access Token válido...")
    claims = api.validate_and_access(tokens["access_token"], required_scope="api.read")
    print(f"Acesso concedido com sucesso para o usuário (sub): {claims['sub']}")
    print(f"Claims validadas: iss={claims['iss']}, scope={claims['scope']}")

    # 3. Contraexemplo de Segurança: Tentativa de reutilização de token adulterado
    print("\n[Cenário 3] Contraexemplo de Segurança: Token com payload adulterado...")
    header_b64, payload_b64, sig_b64 = tokens["access_token"].split('.')
    payload_dict = json.loads(base64url_decode(payload_b64).decode('utf-8'))
    
    # Atacante tenta elevar privilégios alterando o scope ou sub
    payload_dict["scope"] = "openid profile api.read api.admin"
    new_payload_b64 = base64url_encode(json.dumps(payload_dict, separators=(',', ':')).encode('utf-8'))
    tampered_token = f"{header_b64}.{new_payload_b64}.{sig_b64}"
    
    try:
        api.validate_and_access(tampered_token, required_scope="api.admin")
    except ValueError as e:
        print(f"[Contraexemplo Capturado com Sucesso] Acesso negado conforme esperado: {e}")

    print("\nExperimento concluído com sucesso e código de saída 0.")