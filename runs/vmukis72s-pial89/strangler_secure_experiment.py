import time
import sys

# --- 1. Camada de Segurança e Contexto (Mitigação de BOLA/IDOR) ---

class CallerContext:
    def __init__(self, user_id: int, roles: list, tenant_id: str):
        self.user_id = user_id
        self.roles = roles
        self.tenant_id = tenant_id

def authorize_request(caller: CallerContext, target_user_id: int) -> bool:
    """
    Garante que o chamador só pode acessar seu próprio perfil (exceto se for ADMIN).
    Evita vulnerabilidades de IDOR/BOLA onde um usuário manipula o ID na rota.
    """
    if "ADMIN" in caller.roles:
        return True
    return caller.user_id == target_user_id


# --- 2. Padrão Circuit Breaker para Resiliência da Fachada ---

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time: float = 1.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = 0.0

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            print(f"[SECURITY/RESILIENCE] Circuit Breaker ABERTO devido a {self.failures} falhas consecutivas.")

    def allow_request(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "HALF-OPEN"
                print(f"[SECURITY/RESILIENCE] Circuit Breaker em HALF-OPEN. Testando recuperação...")
                return True
            return False
        return True


# --- 3. Sistemas Legado e Novo com Consistência de Dados ---

class LegacyMonolith:
    def get_user_profile(self, user_id: int) -> dict:
        return {"id": user_id, "name": f"User {user_id}", "source": "monolith", "version": "v1_legacy", "updated_at": 100}

class ModernMicroservice:
    def get_user_profile(self, user_id: int) -> dict:
        # Simula leitura do novo microsserviço isolado
        return {"id": user_id, "name": f"User {user_id}", "source": "microservice", "version": "v2_modern", "updated_at": 105}


# --- 4. Strangler Facade Segura e Resiliente ---

class SecureStranglerFacade:
    def __init__(self, monolith: LegacyMonolith, microservice: ModernMicroservice):
        self.monolith = monolith
        self.microservice = microservice
        self.migrated_users = {1, 2, 3}  # Domínio migrado
        self.circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_time=0.2)

    def get_profile(self, caller: CallerContext, target_user_id: int) -> dict:
        # Passo de Segurança 1: Controle de Acesso (BOLA/IDOR Prevention)
        if not authorize_request(caller, target_user_id):
            raise PermissionError(f"Acesso negado: Usuário {caller.user_id} tentou acessar dados de {target_user_id}")

        # Passo de Roteamento por Domínio (Feature Toggle por ID/Percentual)
        is_migrated = target_user_id in self.migrated_users

        if not is_migrated:
            # Não migrado -> Roteia direto para o monolito de forma segura
            return self.monolith.get_user_profile(target_user_id)

        # Tráfego destinado ao microsserviço com Circuit Breaker e Fallback controlado
        if not self.circuit_breaker.allow_request():
            # Circuito aberto: Aplica fail-fast ou fallback seguro sem estourar o monolito (Bulkhead/Shedding)
            print(f"[RESILIENCE] Circuito aberto. Rejeitando chamada pesada ou servindo cache obsoleto seguro para user {target_user_id}")
            # Em vez de sobrecarregar o monolito com falhas em cascata, podemos retornar cache ou dados consistentes controlados
            fallback_data = self.monolith.get_user_profile(target_user_id)
            fallback_data["fallback_reason"] = "circuit_breaker_open_shedding"
            return fallback_data

        try:
            # Simula timeout / bulkhead aqui (ex: chamada com limite de tempo)
            profile = self.microservice.get_user_profile(target_user_id)
            self.circuit_breaker.record_success()
            return profile
        except Exception as e:
            self.circuit_breaker.record_failure()
            print(f"[WARNING] Falha no microsserviço para user {target_user_id}: {e}. Acionando fallback controlado.")
            
            # Fallback seguro para o monolito com rastreabilidade de versão/stale data
            fallback_data = self.monolith.get_user_profile(target_user_id)
            fallback_data["fallback_reason"] = "microservice_failure"
            return fallback_data


# --- 5. Execução e Validação dos Cenários Críticos ---

def run_experiment():
    print("=== Iniciando Teste de Strangler Fig (Segurança e Resiliência) ===")
    monolith = LegacyMonolith()
    microservice = ModernMicroservice()
    facade = SecureStranglerFacade(monolith, microservice)

    # Contextos de Chamador (Autenticação simulada)
    user_self = CallerContext(user_id=1, roles=["USER"], tenant_id="tenant_a")
    user_attacker = CallerContext(user_id=2, roles=["USER"], tenant_id="tenant_a")

    # CENÁRIO 1: Teste de Autorização (Prevenção de BOLA/IDOR)
    print("\n--- Cenário 1: Tentativa de Acesso IDOR/BOLA ---")
    try:
        facade.get_profile(user_attacker, target_user_id=1)
        assert False, "Deveria ter barrado o acesso não autorizado"
    except PermissionError as p_err:
        print(f"Sucesso na Segurança: Acesso bloqueado corretamente -> {p_err}")

    # CENÁRIO 2: Roteamento normal para usuário migrado
    print("\n--- Cenário 2: Acesso legítimo a usuário migrado ---")
    res_migrated = facade.get_profile(user_self, target_user_id=1)
    print(f"Resposta Microsserviço: {res_migrated}")
    assert res_migrated["source"] == "microservice", "Deveria vir do microsserviço"

    # CENÁRIO 3: Ativação do Circuit Breaker sob falhas consecutivas do microsserviço
    print("\n--- Cenário 3: Falhas consecutivas e Circuit Breaker ---")
    class FaultyMicroservice:
        def get_user_profile(self, user_id: int) -> dict:
            raise TimeoutError("Microsserviço travou / Timeout")

    faulty_facade = SecureStranglerFacade(monolith, FaultyMicroservice())
    
    # 1ª falha
    res1 = faulty_facade.get_profile(user_self, target_user_id=1)
    print(f"1ª Chamada com falha: {res1['fallback_reason']}")
    
    # 2ª falha (atinge o threshold de 2 e abre o circuito)
    res2 = faulty_facade.get_profile(user_self, target_user_id=1)
    print(f"2ª Chamada com falha: {res2['fallback_reason']}")

    # 3ª chamada (Circuito ABERTO - aciona proteção contra cascata)
    res3 = faulty_facade.get_profile(user_self, target_user_id=1)
    print(f"3ª Chamada com Circuito Aberto: {res3.get('fallback_reason')}")
    assert res3["fallback_reason"] == "circuit_breaker_open_shedding", "Deveria aplicar proteção de circuito aberto"

    print("\n=== Todos os testes de segurança e resiliência passaram com sucesso! ===")

if __name__ == "__main__":
    run_experiment()