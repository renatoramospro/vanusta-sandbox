path=main.py
import hmac
import hashlib
import json
import base64
import time
import uuid

# Segredo compartilhado do domínio Vanusta-Core
SECRET_KEY = b"vanusta-core-secret-key-2026"

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def base64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding < 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))

def create_jwt(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_enc = base64url_encode(json.dumps(header).encode("utf-8"))
    payload_enc = base64url_encode(json.dumps(payload).encode("utf-8"))
    
    message = f"{header_enc}.{payload_enc}".encode("utf-8")
    signature = hmac.new(SECRET_KEY, message, hashlib.sha256).digest()
    sig_enc = base64url_encode(signature)
    
    return f"{header_enc}.{payload_enc}.{sig_enc}"

def verify_jwt(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token JWT malformado")
    
    header_enc, payload_enc, sig_enc = parts
    message = f"{header_enc}.{payload_enc}".encode("utf-8")
    expected_sig = hmac.new(SECRET_KEY, message, hashlib.sha256).digest()
    
    if not hmac.compare_digest(base64url_encode(expected_sig), sig_enc):
        raise ValueError("Assinatura JWT inválida")
    
    payload = json.loads(base64url_decode(payload_enc).decode("utf-8"))
    if payload.get("exp", 0) < time.time():
        raise ValueError("Token expirado")
        
    return payload


# --- Componentes do Sistema Distribuído ---

class CentralRevocationService:
    """Serviço Central de Revogação com Pub/Sub assíncrono para os microserviços."""
    def __init__(self):
        self.blocklist = set()
        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def revoke_token(self, jti: str):
        print(f"\n[Central] Revogando JTI: {jti}")
        self.blocklist.add(jti)
        event = {"event": "REVOKE", "jti": jti, "timestamp": time.time()}
        
        # Disparando Pub/Sub para os microserviços (Consistência Eventual)
        for sub in self.subscribers:
            sub(event)

    def is_revoked(self, jti: str) -> bool:
        return jti in self.blocklist


class Microservice:
    """Microserviço do Vanusta-Core com cache local e resiliência Fail-Open."""
    def __init__(self, name: str, central_service: CentralRevocationService):
        self.name = name
        self.central = central_service
        self.local_cache = set()
        
        # Registrando no Pub/Sub do serviço central
        self.central.subscribe(self.on_revocation_event)

    def on_revocation_event(self, event: dict):
        if event["event"] == "REVOKE":
            self.local_cache.add(event["jti"])
            print(f"[{self.name}] Cache local atualizado via Pub/Sub para JTI: {event['jti']}")

    def validate_token(self, token: str, network_failure: bool = False):
        try:
            # 1. Validação Criptográfica Local (< 1ms)
            payload = verify_jwt(token)
            jti = payload.get("jti")

            # 2. Verificação de Revogação no Cache Local
            if jti in self.local_cache:
                print(f"[{self.name}] REJEITADO: Token revogado encontrado no cache local (JTI: {jti})")
                return False

            # 3. Consulta ao Serviço Central (com simulação de falha de rede)
            if network_failure:
                raise ConnectionError("Falha de comunicação com o Serviço Central de Revogação")

            if self.central.is_revoked(jti):
                print(f"[{self.name}] REJEITADO: Token revogado na base central (JTI: {jti})")
                return False

            print(f"[{self.name}] APROVADO: Token válido e ativo para sub={payload.get('sub')}")
            return True

        except Exception as e:
            # Estratégia de Fail-Open: Se o serviço central falhar, permite acesso baseado na expiração natural
            if "Falha de comunicação" in str(e):
                print(f"[{self.name}] ALERTA (Fail-Open Ativo): Serviço central inacessível. Permitindo acesso com base na validade criptográfica.")
                return True
            print(f"[{self.name}] REJEITADO por erro de validação: {e}")
            return False


if __name__ == "__main__":
    print("=== INICIALIZANDO ARQUITETURA DE REVOGAÇÃO VANUSTA-CORE ===")
    central = CentralRevocationService()

    # Instanciando microserviços do ecossistema
    auth_service = Microservice("Servico-Auth", central)
    order_service = Microservice("Servico-Pedidos", central)
    payment_service = Microservice("Servico-Pagamentos", central)

    # Emitindo um token válido com JTI único
    token_payload = {
        "sub": "usuario_123",
        "jti": "jti-uuid-abc-999",
        "exp": time.time() + 3600
    }
    valid_jwt = create_jwt(token_payload)

    print("\n--- CENÁRIO 1: Validação de Token Ativo ---")
    order_service.validate_token(valid_jwt)

    print("\n--- CENÁRIO 2: Revogação em Tempo Real (Logout do Usuário) ---")
    start_time = time.time()
    central.revoke_token("jti-uuid-abc-999")
    propagation_time = (time.time() - start_time) * 1000
    print(f"[Métrica] Tempo de propagação do evento Pub/Sub: {propagation_time:.2f}ms (Dentro do SLA de <10s)")

    print("\n--- CENÁRIO 3: Tentativa de Uso do Token Revogado ---")
    payment_service.validate_token(valid_jwt)

    print("\n--- CENÁRIO 4: Resiliência a Falhas de Rede (Serviço Central Indisponível) ---")
    new_token_payload = {
        "sub": "usuario_456",
        "jti": "jti-uuid-def-888",
        "exp": time.time() + 3600
    }
    new_jwt = create_jwt(new_token_payload)
    
    # Simulando queda do serviço central de revogação
    order_service.validate_token(new_jwt, network_failure=True)

    print("\n=== EXPERIMENTO EXECUTADO COM SUCESSO ===")