import threading
from typing import Dict, Type, Callable, Any, List
import uuid

# --- 1. Definição de Escopos ---
class Scope:
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    REQUEST = "request"

# --- 2. Serviços de Exemplo ---
class ServiceA:
    """Serviço que deve ser Singleton."""
    def __init__(self):
        self.id = str(uuid.uuid4())
        print(f"ServiceA (Singleton) criado com ID: {self.id}")

    def get_id(self):
        return self.id

class ServiceB:
    """Serviço que deve ser Transient (novo a cada requisição)."""
    def __init__(self):
        self.id = str(uuid.uuid4())
        print(f"ServiceB (Transient) criado com ID: {self.id}")

    def get_id(self):
        return self.id

class ServiceC:
    """Serviço que deve ser Request-scoped (isolado por thread)."""
    def __init__(self):
        self.id = str(uuid.uuid4())
        print(f"ServiceC (Request) criado com ID: {self.id}")

    def get_id(self):
        return self.id

# --- 3. Container de DI ---
class DependencyContainer:
    def __init__(self):
        # Mapeamento de Tipo -> Configuração de Serviço
        self._registrations: Dict[Type, Dict[str, Any]] = {}
        # Cache de Singletons
        self._singletons: Dict[Type, Any] = {}
        # Cache de Request (isolado por thread)
        self._request_scopes: threading.local = threading.local()
        # Serviços que precisam ser descartados
        self._disposable_services: List[Any] = []

    def register(self, service_type: Type, scope: str, dependencies: List[Type] = None):
        """Registra um serviço com seu escopo."""
        self._registrations[service_type] = {
            "scope": scope,
            "dependencies": dependencies or []
        }

    def _resolve_dependencies(self, dependencies: List[Type]) -> List[Any]:
        """Resolve todas as dependências aninhadas recursivamente."""
        resolved = []
        for dep_type in dependencies:
            resolved.append(self.resolve(dep_type))
        return resolved

    def resolve(self, service_type: Type) -> Any:
        """Resolve e retorna uma instância do serviço conforme seu escopo."""
        if service_type not in self._registrations:
            raise ValueError(f"Serviço {service_type.__name__} não registrado no container.")

        config = self._registrations[service_type]
        scope = config["scope"]

        if scope == Scope.SINGLETON:
            if service_type not in self._singletons:
                instance = self._create_instance(service_type, config)
                self._singletons[service_type] = instance
                self._disposable_services.append(instance)
            return self._singletons[service_type]

        elif scope == Scope.TRANSIENT:
            return self._create_instance(service_type, config)

        elif scope == Scope.REQUEST:
            # Verifica o escopo da thread atual
            if not hasattr(self._request_scopes, service_type):
                instance = self._create_instance(service_type, config)
                self._request_scopes.service_type = instance
                self._disposable_services.append(instance)
            return getattr(self._request_scopes, service_type)
        
        else:
            raise NotImplementedError(f"Escopo {scope} não suportado.")

    def _create_instance(self, service_type: Type, config: Dict[str, Any]) -> Any:
        """Cria a instância, resolvendo suas dependências."""
        dependencies = config["dependencies"]
        resolved_deps = self._resolve_dependencies(dependencies)
        
        # Cria a instância passando as dependências via construtor
        return service_type(*resolved_deps)

    def dispose_all(self):
        """Chama o método de descarte em todos os serviços gerenciados."""
        print("\n--- Iniciando Descarte de Serviços ---")
        for service in self._disposable_services:
            # Assumindo que serviços descartáveis implementam um método dispose()
            if hasattr(service, 'dispose'):
                service.dispose()
        self._disposable_services.clear()
        print("--- Descarte Concluído ---")

# --- 4. Testes de Ciclo de Vida ---

def test_singleton_lifecycle():
    print("\n===== TESTE: SINGLETON =====")
    container = DependencyContainer()
    container.register(ServiceA, Scope.SINGLETON)
    
    a1 = container.resolve(ServiceA)
    a2 = container.resolve(ServiceA)
    
    assert a1.get_id() == a2.get_id()
    print(f"Sucesso: IDs iguais ({a1.get_id()}). Singleton mantido.")
    container.dispose_all()

def test_transient_lifecycle():
    print("\n===== TESTE: TRANSIENT =====")
    container = DependencyContainer()
    container.register(ServiceB, Scope.TRANSIENT)
    
    b1 = container.resolve(ServiceB)
    b2 = container.resolve(ServiceB)
    
    assert b1.get_id() != b2.get_id()
    print(f"Sucesso: IDs diferentes ({b1.get_id()} vs {b2.get_id()}). Transient criado novamente.")
    container.dispose_all()

def test_request_lifecycle_single_thread():
    print("\n===== TESTE: REQUEST (Single Thread) =====")
    container = DependencyContainer()
    container.register(ServiceC, Scope.REQUEST)
    
    c1 = container.resolve(ServiceC)
    c2 = container.resolve(ServiceC)
    
    assert c1.get_id() == c2.get_id()
    print(f"Sucesso: IDs iguais ({c1.get_id()}). Request mantido na thread atual.")
    container.dispose_all()

def test_request_lifecycle_multi_thread():
    print("\n===== TESTE: REQUEST (Multi Thread) =====")
    container = DependencyContainer()
    container.register(ServiceC, Scope.REQUEST)
    
    results = []
    
    def worker():
        c = container.resolve(ServiceC)
        results.append(c.get_id())

    thread1 = threading.Thread(target=worker)
    thread2 = threading.Thread(target=worker)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    
    # Esperamos que os IDs sejam diferentes, pois cada thread tem seu escopo 'request' isolado
    assert results[0] != results[1]
    print(f"Sucesso: IDs diferentes ({results[0]} vs {results[1]}). Isolamento de thread (Request) verificado.")
    container.dispose_all()

def test_nested_dependencies():
    print("\n===== TESTE: DEPENDÊNCIAS ANINHADAS =====")
    # Criamos um serviço que depende de ServiceA (Singleton) e ServiceB (Transient)
    class ServiceD:
        def __init__(self, a: ServiceA, b: ServiceB):
            self.a = a
            self.b = b
        def get_ids(self):
            return self.a.get_id(), self.b.get_id()

    container = DependencyContainer()
    container.register(ServiceA, Scope.SINGLETON)
    container.register(ServiceB, Scope.TRANSIENT)
    container.register(ServiceD, Scope.TRANSIENT, dependencies=[ServiceA, ServiceB])
    
    d1 = container.resolve(ServiceD)
    d2 = container.resolve(ServiceD)
    
    # A deve ser a mesma instância (Singleton)
    assert d1.a.get_id() == d2.a.get_id()
    # B deve ser uma instância diferente (Transient)
    assert d1.b.get_id() != d2.b.get_id()
    print("Sucesso: Dependências aninhadas resolvidas corretamente (A=Singleton, B=Transient).")
    container.dispose_all()


if __name__ == "__main__":
    test_singleton_lifecycle()
    test_transient_lifecycle()
    test_request_lifecycle_single_thread()
    test_request_lifecycle_multi_thread()
    test_nested_dependencies()
    print("\n--- TODOS OS TESTES DE CICLO DE VIDA PASSARAM COM SUCESSO ---")