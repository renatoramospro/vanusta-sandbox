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
        # Armazenar registro para referência futura
        self._registrations[service_type] = {'scope': scope, 'factory': factory}
        
    def _get_registration(self, service_type: Type[Service]):
        # Helper para obter o registro
        return self._registrations.get(service_type)

    def get_instance(self, service_type: Type[Service], request_id: str = None, session_id: str = None) -> Service:
        registration = self._get_registration(service_type)
        if not registration:
            raise ValueError(f"Service {service_type.__name__} not registered.")
        
        scope = registration['scope']
        factory = registration['factory']

        # 1. Singleton: Acesso global, sem contexto
        if scope == Scope.SINGLETON:
            if service_type not in self.singletons:
                self.singletons[service_type] = factory()
            return self.singletons[service_type]

        # 2. Transient: Sempre novo
        elif scope == Scope.TRANSIENT:
            return factory()

        # 3. Request/Session: Requer contexto
        elif scope in [Scope.REQUEST, Scope.SESSION]:
            if scope == Scope.REQUEST and not request_id:
                raise ValueError("Contexto (request_id) ausente para escopo Request.")
            if scope == Scope.SESSION and not session_id:
                raise ValueError("Contexto (session_id) ausente para escopo Session.")

            # Busca no contexto apropriado
            context_store = self.request_contexts if scope == Scope.REQUEST else self.session_contexts
            
            if request_id and request_id not in self.request_contexts:
                 raise ValueError("Request ID não encontrado no container.")
            if session_id and session_id not in self.session_contexts:
                 raise ValueError("Session ID não encontrado no container.")

            context = context_store.get(request_id if scope == Scope.REQUEST else session_id)
            
            if not context:
                # Cria e armazena no contexto
                new_instance = factory()
                context[service_type] = new_instance
                
                # Garante que o contexto exista se for a primeira vez
                if scope == Scope.REQUEST and request_id not in self.request_contexts:
                    self.request_contexts[request_id] = {}
                elif scope == Scope.SESSION and session_id not in self.session_contexts:
                    self.session_contexts[session_id] = {}
                
                return new_instance
            
            # Retorna instância existente no contexto
            return context[service_type]

        else:
            raise ValueError(f"Escopo desconhecido: {scope}")

    def end_request(self, request_id: str):
        if request_id in self.request_contexts:
            # Limpa referências do container para permitir GC
            del self.request_contexts[request_id]
            print(f"--- Contexto de Request {request_id} finalizado e referências removidas.")

    def end_session(self, session_id: str):
        if session_id in self.session_contexts:
            # Limpa referências do container para permitir GC
            del self.session_contexts[session_id]
            print(f"--- Contexto de Session {session_id} finalizado e referências removidas.")

# --- Configuração e Teste ---
container = DependencyContainer()
# Registro: Service é sempre o mesmo para todos os testes
container.register(Service, Scope.SINGLETON, lambda: Service("GlobalService"))
container.register(Service, Scope.TRANSIENT, lambda: Service("TransientService"))
container.register(Service, Scope.REQUEST, lambda: Service("RequestService"))
container.register(Service, Scope.SESSION, lambda: Service("SessionService"))


def run_test():
    req1_id = str(uuid.uuid4())
    req2_id = str(uuid.uuid4())
    sess_id = str(uuid.uuid4())
    
    print("=====================================================")
    print("TESTE 1: Singleton (Deve ser o mesmo objeto sempre)")
    s1_a = container.get_instance(Service, request_id=req1_id) # Singleton não precisa de contexto
    s1_b = container.get_instance(Service) # Chamada sem argumentos
    assert s1_a.id == s1_b.id
    print(f"✅ Singleton OK (Reutilização): IDs {s1_a.id} são iguais.")

    print("\n=====================================================")
    print("TESTE 2: Transient (Deve ser diferente a cada chamada)")
    t1 = container.get_instance(Service)
    t2 = container.get_instance(Service)
    assert t1.id != t2.id
    print(f"✅ Transient OK (Diferença): IDs {t1.id} e {t2.id} são diferentes.")

    print("\n=====================================================")
    print("TESTE 3: Request (Reutilização dentro da requisição)")
    # Deve funcionar com req1_id
    r1_a = container.get_instance(Service, request_id=req1_id)
    r1_b = container.get_instance(Service, request_id=req1_id)
    assert r1_a.id == r1_b.id
    print(f"✅ Request OK (Reutilização): IDs {r1_a.id} são iguais em Req 1.")

    print("\n=====================================================")
    print("TESTE 4: Request (Isolamento entre requisições)")
    # Deve ser diferente de r1_a
    r2_a = container.get_instance(Service, request_id=req2_id)
    assert r1_a.id != r2_a.id
    print(f"✅ Request OK (Isolamento): IDs {r1_a.id} e {r2_a.id} são diferentes.")

    print("\n=====================================================")
    print("TESTE 5: Session (Reutilização em requisições diferentes da mesma sessão)")
    # Deve ser o mesmo em req1 e req2, mas diferente de Request
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

    # Verificação de limpeza do container
    assert not container.request_contexts
    assert not container.session_contexts
    print("✅ Descarte OK: Contextos de Request e Session foram removidos do container.")
    print("\n--- Teste concluído com sucesso. ---")


if __name__ == "__main__":
    run_test()