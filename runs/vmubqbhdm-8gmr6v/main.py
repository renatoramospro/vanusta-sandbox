import time
import jwt
from typing import Dict, Set

# Chave secreta compartilhada para assinatura dos tokens
SECRET_KEY = "segredo-super-seguro-vanusta-core"

# ==========================================
# 1. SERVIÇO CENTRAL DE REVOGAÇÃO & PUB/SUB
# ==========================================
class CentralRevocationService:
    def __init__(self):
        self.blocklist: Set[str] = set()
        self.subscribers = []

    def subscribe(self, callback):
        """Registra um microserviço para receber eventos de revogação em tempo real."""
        self.subscribers.append(callback)

    def revoke_token(self, jti: str):
        """Adiciona o JTI à blocklist e dispara o evento Pub/Sub para todos os microserviços."""
        self.blocklist.add(jti)
        print(f"\n[Central] Token JTI '{jti}' REVOGADO. Disparando evento Pub/Sub...")
        
        # Publica o evento para atualizar instantaneamente os caches locais dos microserviços
        for callback in self.subscribers:
            callback(jti)

    def is_revoked(self, jti: str) -> bool:
        """Verifica se o token está na blocklist."""
        return jti in self.blocklist

# ==========================================
# 2. MICROSERVIÇO COM CACHE LOCAL E FALLBACK
# ==========================================
class Microservice:
    def __init__(self, name: str, central_service: CentralRevocationService):
        self.name = name
        self.central_service = central_service
        # Cache local para reduzir latência de consulta (<10ms)
        self.local_cache: Set[str] = set()
        
        # Inscreve-se no canal Pub/Sub do serviço central
        self.central_service.subscribe(self.on_token_revoked_event)

    def on_token_revoked_event(self, jti: str):
        """Reage instantaneamente ao evento de revogação."""
        self.local_cache.add(jti)
        print(f"  -> [{self.name}] Cache local atualizado: JTI '{jti}' invalidado.")

    def validate_token(self, token: str, network_failure: bool = False) -> bool:
        """
        Valida o token aplicando:
        1. Validação Criptográfica e de Expiração.
        2. Checagem na Blocklist (Cache Local / Central).
        3. Tratamento de Falha de Rede (Circuit Breaker / Fail-Open seguro).
        """
        try:
            # Passo 1: Decodificação e validação criptográfica estatística
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            jti = payload.get("jti")
        except jwt.ExpiredSignatureError:
            print(f"[{self.name}] Rejeitado: Token expirado.")
            return False
        except jwt.InvalidTokenError:
            print(f"[{self.name}] Rejeitado: Assinatura JWT inválida.")
            return False

        # Passo 2: Verificação na Blocklist (Cache local primeiro para velocidade)
        if jti in self.local_cache:
            print(f"[{self.name}] Rejeitado: JTI '{jti}' encontrado no cache local de revogação.")
            return False

        # Simulando consulta ao serviço central com possível falha de rede
        try:
            if network_failure:
                raise ConnectionError("Timeout ao conectar com o Serviço Central de Revogação.")
            
            if self.central_service.is_revoked(jti):
                self.local_cache.add(jti)
                print(f"[{self.name}] Rejeitado: JTI '{jti}' revogado pelo serviço central.")
                return False
                
        except ConnectionError as e:
            # Passo 3: Resiliência a Falhas (Fail-Open com aviso de segurança)
            print(f"[{self.name}] ALERTA DE RESILIÊNCIA: {e} -> Aplicando Fallback (Fail-Open baseado apenas em expiração).")
            # Em cenário real, logar métrica de degradação do serviço de revogação

        print(f"[{self.name}] APROVADO: Token válido.")
        return True

# ==========================================
# 3. EXECUÇÃO DO CENÁRIO DE TESTES
# ==========================================
if __name__ == "__main__":
    print("=== INICIALIZANDO VANUSTA-CORE: SISTEMA DE REVOGAÇÃO JWT ===")
    
    central = CentralRevocationService()
    
    # Instanciando microserviços dependentes
    auth_service = Microservice("Servico-Auth", central)
    order_service = Microservice("Servico-Pedidos", central)
    payment_service = Microservice("Servico-Pagamentos", central)

    # Emitindo um token válido com JTI único (evitando colocar payload pesado na blocklist)
    token_payload = {
        "sub": "usuario_123",
        "jti": "jti-uuid-abc-999",
        "exp": time.time() + 3600
    }
    valid_jwt = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")

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
    # Emitindo novo token para testar o fallback
    new_token_payload = {
        "sub": "usuario_456",
        "jti": "jti-uuid-def-888",
        "exp": time.time() + 3600
    }
    new_jwt = jwt.encode(new_token_payload, SECRET_KEY, algorithm="HS256")
    
    # Simulando queda do serviço central de revogação
    order_service.validate_token(new_jwt, network_failure=True)

    print("\n=== EXPERIMENTO EXECUTADO COM SUCESSO ==Y")