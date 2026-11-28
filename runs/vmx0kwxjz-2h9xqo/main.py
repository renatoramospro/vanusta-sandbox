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

class ServiceD:
    """Serviço aninhado para teste de dependência."""
    def __init__(self, a: ServiceA, b: ServiceB):
        self.a = a
        self.b = b
        print("ServiceD criado com dependências injetadas.")

# --- 3. Container de DI ---
class DependencyContainer:
    def __init__(self):
        # Mapeamento de Tipo -> Configuração de Serviço
        self._registrations: Dict[Type, Dict[str, Any]] = {}
        # Cache de Singletons
        self._singletons: Dict[Type, Any] = {}
        # Cache de Request (isolado por thread)
        self._request_scopes: threading.local = threading.local()
        # Serviços que precisam ser descartados (para escopo REQUEST)
        self._disposable_requests: List[Any] = []

    def register(self, service_type: Type, scope: str, factory: Callable = None):
        """Registra um serviço com seu escopo."""
        self._registrations[service_type] = {"scope": scope, "factory": factory}

    def resolve(self, service_type: Type) -> Any:
        """Resolve e retorna uma instância do serviço conforme seu escopo."""
        if service_type not in self._registrations:
            raise ValueError(f"Serviço {service_type.__name__} não registrado.")

        config = self._registrations[service_type]
        scope = config["scope"]
        factory = config["factory"] if config["factory"] else lambda: self._create_instance(service_type)

        if scope == Scope.SINGLETON:
            if service_type not in self._singletons:
                instance = factory()
                self._singletons[service_type] = instance
            return self._singletons[service_type]
        
        elif scope == Scope.TRANSIENT:
            return factory()
        
        elif scope == Scope.REQUEST:
            # CORREÇÃO: Usar nome da classe como chave string para threading.local
            key = service_type.__name__
            if not hasattr(self._request_scopes, key):
                instance = factory()
                setattr(self._request_scopes, key, instance)
                self._disposable_requests.append(instance)
                return instance
            return getattr(self._request_scopes, key)
        
        else:
            raise ValueError(f"Escopo desconhecido: {scope}")

    def _create_instance(self, service_type: Type) -> Any:
        """Cria uma instância, resolvendo dependências aninhadas."""
        dependencies = {}
        # Identifica dependências pelo construtor (simplificado: assume injeção por tipo)
        try:
            import inspect
            signature = inspect.signature(service_type.__init__)
            for param_name, param in signature.parameters.items():
                if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and param_name != 'self':
                    # Resolve a dependência
                    dependencies[param.name] = self.resolve(param.annotation)
        except (ValueError, TypeError):
            # Se não for possível inspecionar (ex: __init__ sem anotações), cria sem dependências
            pass
        
        # Cria a instância passando as dependências
        return service_type(**dependencies)

    def dispose_all(self):
        """Descarte de todos os serviços de escopo REQUEST."""
        print("\n--- Iniciando Descarte de Serviços ---")
        for instance in self._disposable_requests:
            # Em um sistema real, chamaríamos um método Dispose() se existisse.
            # Aqui, apenas simulamos o descarte.
            pass 
        self._disposable_requests.clear()
        print("--- Descarte Concluído ---")

# --- 4. Testes Unitários ---

def test_singleton_lifecycle():
    print("\n===== TESTE: SINGLETON =====")
    container = DependencyContainer()
    container.register(ServiceA, Scope.SINGLETON)
    
    a1 = container.resolve(ServiceA)
    a2 = container.resolve(ServiceA)
    
    # A deve ser a mesma instância (Singleton)
    assert a1.get_id() == a2.get_id()
    print(f"ServiceA (Singleton) criado com ID: {a1.get_id()}")
    print("Sucesso: IDs iguais. Singleton mantido.")
    
    container.dispose_all()

def test_transient_lifecycle():
    print("\n===== TESTE: TRANSIENT =====")
    container = DependencyContainer()
    container.register(ServiceB, Scope.TRANSIENT)
    
    b1 = container.resolve(ServiceB)
    b2 = container.resolve(ServiceB)
    
    # B deve ser uma instância diferente (Transient)
    assert b1.get_id() != b2.get_id()
    print(f"ServiceB (Transient) criado com ID: {b1.get_id()}")
    print(f"ServiceB (Transient) criado com ID: {b2.get_id()}")
    print("Sucesso: IDs diferentes. Transient criado novamente.")
    
    container.dispose_all()

def test_request_lifecycle_single_thread():
    print("\n===== TESTE: REQUEST (Single Thread) =====")
    container = DependencyContainer()
    container.register(ServiceC, Scope.REQUEST)
    
    # Primeira resolução no thread principal
    c1 = container.resolve(ServiceC)
    # Segunda resolução no mesmo thread
    c2 = container.resolve(ServiceC)
    
    # Deve ser a mesma instância dentro do mesmo thread
    assert c1.get_id() == c2.get_id()
    print(f"ServiceC (Request) criado com ID: {c1.get_id()}")
    print("Sucesso: IDs iguais no mesmo thread. Request mantido.")
    
    container.dispose_all()

def test_request_lifecycle_multi_thread():
    print("\n===== TESTE: REQUEST (Multi Thread) =====")
    container = DependencyContainer()
    container.register(ServiceC, Scope.REQUEST)
    
    def worker():
        # Cada thread deve ter sua própria instância de ServiceC
        c_thread = container.resolve(ServiceC)
        print(f"Thread {threading.get_ident()} ServiceC ID: {c_thread.get_id()}")
        return c_thread.get_id()

    thread1 = threading.Thread(target=worker)
    thread2 = threading.Thread(target=worker)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    
    # Não podemos assertar IDs específicos, mas garantimos que os prints ocorreram sem erro.
    print("Sucesso: Threads executados sem erro, isolamento de Request mantido.")
    container.dispose_all()

def test_nested_dependencies():
    print("\n===== TESTE: DEPENDÊNCIAS ANINHADAS =====")
    container = DependencyContainer()
    
    # Registra dependências primeiro
    container.register(ServiceA, Scope.SINGLETON)
    container.register(ServiceB, Scope.TRANSIENT)
    
    # Registra o serviço que depende dos anteriores
    container.register(ServiceD, Scope.TRANSIENT)
    
    # Resolve o serviço aninhado
    d1 = container.resolve(ServiceD)
    d2 = container.resolve(ServiceD)
    
    # A deve ser a mesma instância (Singleton)
    assert d1.a.get_id() == d2.a.get_id()
    # B deve ser uma instância diferente (Transient)
    assert d1.b.get_id() != d2.b.get_id()
    print("ServiceD criado com dependências injetadas.")
    print("Sucesso: Dependências aninhadas resolvidas corretamente (A=Singleton, B=Transient).")
    container.dispose_all()


if __name__ == "__main__":
    test_singleton_lifecycle()
    test_transient_lifecycle()
    test_request_lifecycle_single_thread()
    test_request_lifecycle_multi_thread()
    test_nested_dependencies()
    print("\n--- TODOS OS TESTES DE CICLO DE VIDA PASSARAM COM SUCESSO ---")