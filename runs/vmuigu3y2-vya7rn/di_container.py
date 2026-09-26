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
        
        # Se houver re-registro, limpamos o singleton antigo para garantir isolamento
        if interface in self._singletons:
            del self._singletons[interface]

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

        # Verificação de dependência circular
        if interface in _resolution_stack:
            cycle_path = " -> ".join([str(s.__name__) if hasattr(s, '__name__') else str(s) for s in _resolution_stack + [interface]])
            raise CircularDependencyError(f"Dependência circular detectada: {cycle_path}")

        service_def = self._registry[interface]
        implementation = service_def["implementation"]
        lifetime = service_def["lifetime"]

        # Se for Singleton e já estiver instanciado, retorna a instância em cache
        if lifetime == Lifetime.SINGLETON and interface in self._singletons:
            return self._singletons[interface]

        # Adiciona à pilha de resolução atual
        _resolution_stack.append(interface)
        try:
            # Inspeção do construtor
            sig = inspect.signature(implementation)
            dep_instances = {}

            for name, param in sig.parameters.items():
                # Ignorar *args e **kwargs
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue

                # Se o parâmetro tem anotação de tipo
                if param.annotation is not inspect.Parameter.empty:
                    dep_type = param.annotation
                    try:
                        dep_instances[name] = self.resolve(dep_type, _resolution_stack)
                    except ServiceNotFoundError:
                        # Se não achou mas tem valor padrão, usa o valor padrão
                        if param.default is not inspect.Parameter.empty:
                            dep_instances[name] = param.default
                        else:
                            raise
                else:
                    # Sem anotação: se tiver valor padrão, usa ele
                    if param.default is not inspect.Parameter.empty:
                        dep_instances[name] = param.default
                    else:
                        raise ValueError(f"Parâmetro '{name}' em {implementation.__name__} não possui anotação de tipo.")

            instance = implementation(**dep_instances)

            if lifetime == Lifetime.SINGLETON:
                self._singletons[interface] = instance

            return instance
        finally:
            _resolution_stack.pop()

# --- Classes de Teste ---

class TransientService:
    def __init__(self, *args, timeout: int = 15):
        self.timeout = timeout

class SingletonService:
    pass

class ServiceLevel2:
    def __init__(self, transient: TransientService):
        self.transient = transient

class ServiceLevel1:
    def __init__(self, level2: ServiceLevel2, singleton: SingletonService):
        self.level2 = level2
        self.singleton = singleton

class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b

class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

def test_container():
    container = Container()

    # 1. Teste Transient
    container.register(TransientService, lifetime=Lifetime.TRANSIENT)
    t1 = container.resolve(TransientService)
    t2 = container.resolve(TransientService)
    assert t1 is not t2, "Transient deve gerar instâncias diferentes."
    assert t1.timeout == 15
    print("Sucesso: Transient gera instâncias isoladas e respeita defaults.")

    # 2. Teste Singleton
    container.register(SingletonService, lifetime=Lifetime.SINGLETON)
    s1 = container.resolve(SingletonService)
    s2 = container.resolve(SingletonService)
    assert s1 is s2, "Singleton deve retornar a mesma instância."
    print("Sucesso: Singleton retorna a mesma instância.")

    # 3. Teste Grafo Multinível
    container.register(ServiceLevel2)
    container.register(ServiceLevel1)
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