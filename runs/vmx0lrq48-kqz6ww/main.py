import weakref
import uuid
from typing import Dict, Any, Type, Callable

# --- Definições de Escopo ---
class Scope:
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    REQUEST = "request"
    SESSION = "session"

# --- Dependência de Teste ---
class Service:
    def __init__(self, name: str):
        self.name = name
        # Atributo para verificar identidade
        self.id = id(self)
        print(f"Service '{self.name}' created with ID: {self.id}")

    def __del__(self):
        # Simulação de limpeza (embora GC seja o real mecanismo)
        print(f"Service '{self.name}' destroyed (ID: {self.id})")

# --- Container de DI ---
class DependencyContainer:
    def __init__(self):
        # Registros globais (Singleton)
        self.singletons: Dict[Type, Any] = {}
        # Contextos dinâmicos (Request/Session)
        self.request_contexts: Dict[str, Dict[Type, Any]] = {}
        self.session_contexts: Dict[str, Dict[Type, Any]] = {}

    def register(self, service_type: Type[Service], scope: str, factory: Callable[[], Service]):
        self.service_type = service_type
        self.scope = scope
        self.factory = factory

    def get_instance(self, service_type: Type[Service], request_id: str = None, session_id: str = None) -> Service:
        
        if self.scope == Scope.SINGLETON:
            if service_type not in self.singletons:
                self.singletons[service_type] = self.factory()
            return self.singletons[service_type]

        elif self.scope == Scope.TRANSIENT:
            return self.factory()

        elif self.scope == Scope.REQUEST and request_id:
            if request_id not in self.request_contexts:
                self.request_contexts[request_id] = {}
            if service_type not in self.request_contexts[request_id]:
                self.request_contexts[request_id][service_type] = self.factory()
            return self.request_contexts[request_id][service_type]

        elif self.scope == Scope.SESSION and session_id:
            if session_id not in self.session_contexts:
                self.session_contexts[session_id] = {}
            if service_type not in self.session_contexts[session_id]:
                self.session_contexts[session_id][service_type] = self.factory()
            return self.session_contexts[session_id][service_type]
        
        raise ValueError("Contexto (request_id/session_id) ausente para escopo dinâmico.")

    # Métodos de limpeza (Crucial para evitar vazamento)
    def end_request(self, request_id: str):
        if request_id in self.request_contexts:
            del self.request_contexts[request_id]
            print(f"\n--- Request {request_id} context cleaned up. ---")

    def end_session(self, session_id: str):
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
            print(f"\n--- Session {session_id} context cleaned up. ---")

# --- Teste de Identidade e Descarte ---
def run_test():
    container = DependencyContainer()
    
    # 1. Configuração do Container
    container.register(Service, Scope.SINGLETON, lambda: Service("Global"))
    container.register(Service, Scope.TRANSIENT, lambda: Service("Transient"))
    container.register(Service, Scope.REQUEST, lambda: Service("Request"))
    container.register(Service, Scope.SESSION, lambda: Service("Session"))

    # IDs de teste
    req1_id = str(uuid.uuid4())
    req2_id = str(uuid.uuid4())
    sess_id = str(uuid.uuid4())

    print("\n=====================================================")
    print("TESTE 1: Singleton (Deve ser o mesmo objeto sempre)")
    s1_a = container.get_instance(Service, request_id=req1_id)
    s1_b = container.get_instance(Service, request_id=req2_id)
    assert s1_a.id == s1_b.id
    print(f"✅ Singleton OK: IDs {s1_a.id} são iguais.")

    print("\n=====================================================")
    print("TESTE 2: Transient (Deve ser um objeto novo a cada chamada)")
    t1 = container.get_instance(Service, request_id=req1_id)
    t2 = container.get_instance(Service, request_id=req1_id)
    assert t1.id != t2.id
    print(f"✅ Transient OK: IDs {t1.id} e {t2.id} são diferentes.")

    print("\n=====================================================")
    print("TESTE 3: Request (Mesma instância em requisições subsequentes da mesma req)")
    r1_a = container.get_instance(Service, request_id=req1_id)
    r1_b = container.get_instance(Service, request_id=req1_id)
    assert r1_a.id == r1_b.id
    print(f"✅ Request OK (Reutilização): IDs {r1_a.id} são iguais dentro de Req 1.")

    print("\n=====================================================")
    print("TESTE 4: Request (Instâncias diferentes entre requisições distintas)")
    r2_a = container.get_instance(Service, request_id=req2_id)
    assert r1_a.id != r2_a.id
    print(f"✅ Request OK (Isolamento): IDs {r1_a.id} e {r2_a.id} são diferentes entre Req 1 e Req 2.")

    print("\n=====================================================")
    print("TESTE 5: Session (Mesma instância em requisições diferentes dentro da mesma sessão)")
    se1_a = container.get_instance(Service, request_id=req1_id, session_id=sess_id)
    se1_b = container.get_instance(Service, request_id=req2_id, session_id=sess_id)
    assert se1_a.id == se1_b.id
    print(f"✅ Session OK (Reutilização): IDs {se1_a.id} são iguais em Req 1 e Req 2 dentro da Sessão.")

    # --- Teste de Descarte (Vazamento de Memória) ---
    print("\n=====================================================")
    print("TESTE 6: Descarte (Simulação de fim de ciclo)")
    
    # 6a. Fim da Requisição 1
    container.end_request(req1_id)
    
    # 6b. Fim da Sessão
    container.end_session(sess_id)
    
    # 6c. Fim da Requisição 2
    container.end_request(req2_id)

    # Nota: A verificação de vazamento real (coleta de lixo) requer profiling externo.
    # No nível de código, garantimos que as referências no container foram removidas.
    # Se o container não tivesse os métodos end_request/end_session, as referências persistiriam.
    assert not container.request_contexts
    assert not container.session_contexts
    print("✅ Descarte OK: Contextos de Request e Session foram removidos do container.")
    print("\n--- Teste concluído com sucesso. ---")


if __name__ == "__main__":
    run_test()