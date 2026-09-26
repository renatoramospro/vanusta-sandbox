import inspect
from enum import Enum, auto

class Lifetime(Enum):
    TRANSIENT = auto()
    SINGLETON = auto()

class CircularDependencyError(Exception):
    """Exceção específica lançada ao detectar uma dependência circular."""
    pass

class ServiceNotFoundError(Exception):
    """Exceção lançada quando um serviço não está registrado no container."""
    pass

class Container:
    def __init__(self):
        self._registry = {}
        self._singletons = {}

    def register(self, interface, implementation=None, lifetime=Lifetime.TRANSIENT):
        if implementation is None:
            implementation = interface
        self._registry[interface] = {
            "implementation": implementation,
            "lifetime": lifetime
        }

    def resolve(self, interface, _resolution_stack=None):
        if _resolution_stack is None:
            _resolution_stack = []

        # Se o serviço não estiver registrado, tenta auto-registrar se for uma classe concreta
        if interface not in self._registry:
            if inspect.isclass(interface):
                self.register(interface, interface, Lifetime.TRANSIENT)
            else:
                raise ServiceNotFoundError(f"Serviço não registrado: {interface}")

        # Verificação de dependência circular usando a pilha do ramo atual
        if interface in _resolution_stack:
            cycle_path = " -> ".join([str(s.__name__) if hasattr(s, '__name__') else str(s) for s in _resolution_stack + [interface]])
            raise CircularDependencyError(f"Dependência circular detectada: {cycle_path}")

        registration = self._registry[interface]
        implementation = registration["implementation"]
        lifetime = registration["lifetime"]

        if lifetime == Lifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

        # Adiciona à pilha de resolução do ramo atual
        _resolution_stack.append(interface)

        try:
            # Inspeciona o construtor da implementação
            sig = inspect.signature(implementation.__init__)
            parameters = sig.parameters

            deps = []
            for name, param in parameters.items():
                if name == 'self':
                    continue
                if param.annotation == inspect.Parameter.empty:
                    raise ValueError(f"Parâmetro '{name}' em {implementation.__name__} não possui anotação de tipo.")
                
                dep_type = param.annotation
                # Chamada recursiva passando a pilha para rastrear ciclos no mesmo ramo
                dep_instance = self.resolve(dep_type, _resolution_stack)
                deps.append(dep_instance)

            instance = implementation(*deps)

            if lifetime == Lifetime.SINGLETON:
                self._singletons[interface] = instance

            return instance
        finally:
            # Remove da pilha ao retornar (backtracking do grafo)
            _resolution_stack.pop()

# --- Testes Automatizados ---

class TransientService:
    pass

class SingletonService:
    pass

class ServiceLevel2:
    def __init__(self, transient: TransientService):
        self.transient = transient

class ServiceLevel1:
    def __init__(self, level2: ServiceLevel2, singleton: SingletonService):
        self.level2 = level2
        self.singleton = singleton

# Classes para testar Dependência Circular
class ServiceB:
    pass

class ServiceA:
    def __init__(self, b: ServiceB):
        self.b = b

# Ajustando ServiceB para depender de ServiceA (Ciclo A -> B -> A)
class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

def test_container():
    container = Container()

    # 1. Teste Transient
    container.register(TransientService, TransientService, Lifetime.TRANSIENT)
    t1 = container.resolve(TransientService)
    t2 = container.resolve(TransientService)
    assert t1 is not t2, "Transient deveria gerar instâncias diferentes."
    print("Sucesso: Transient gera instâncias isoladas.")

    # 2. Teste Singleton
    container.register(SingletonService, SingletonService, Lifetime.SINGLETON)
    s1 = container.resolve(SingletonService)
    s2 = container.resolve(SingletonService)
    assert s1 is s2, "Singleton deveria retornar a mesma instância."
    print("Sucesso: Singleton retorna a mesma instância.")

    # 3. Teste Grafo Multinível
    container.register(ServiceLevel2, ServiceLevel2, Lifetime.TRANSIENT)
    container.register(ServiceLevel1, ServiceLevel1, Lifetime.TRANSIENT)
    
    root = container.resolve(ServiceLevel1)
    assert isinstance(root, ServiceLevel1)
    assert isinstance(root.level2, ServiceLevel2)
    assert isinstance(root.level2.transient, TransientService)
    assert isinstance(root.singleton, SingletonService)
    print("Sucesso: Grafo multinível resolvido com sucesso.")

    # 4. Teste Dependência Circular
    container_cycle = Container()
    container_cycle.register(ServiceA, ServiceA, Lifetime.TRANSIENT)
    container_cycle.register(ServiceB, ServiceB, Lifetime.TRANSIENT)

    try:
        container_cycle.resolve(ServiceA)
        raise AssertionError("Deveria ter lançado CircularDependencyError!")
    except CircularDependencyError as e:
        print(f"Sucesso: Exceção capturada corretamente -> {e}")

if __name__ == "__main__":
    test_container()
    print("Todos os testes do container de DI passaram com êxito!")