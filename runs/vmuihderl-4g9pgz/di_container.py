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
        
        if interface in self._singletons:
            del self._singletons[interface]

        self._registry[interface] = {
            "implementation": implementation,
            "lifetime": lifetime
        }

    def resolve(self, interface, _resolution_stack=None):
        if _resolution_stack is None:
            _resolution_stack = []

        # Auto-registro se não registrado e for uma classe válida
        if interface not in self._registry:
            if isinstance(interface, type) and interface not in (int, str, float, bool, dict, list, tuple, set):
                self.register(interface, interface, Lifetime.TRANSIENT)
            else:
                raise ServiceNotFoundError(f"Serviço não registrado ou tipo primitivo não injetável: {interface}")

        service_def = self._registry[interface]
        implementation = service_def["implementation"]
        lifetime = service_def["lifetime"]

        if lifetime == Lifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

        # Detecção de dependência circular
        if interface in _resolution_stack:
            path_str = " -> ".join([str(cls.__name__ if hasattr(cls, '__name__') else cls) for cls in _resolution_stack + [interface]])
            raise CircularDependencyError(f"Dependência circular detectada: {path_str}")

        _resolution_stack.append(interface)

        try:
            # Se a implementação não for uma classe (ex: fábrica ou instância pronta)
            if not isinstance(implementation, type):
                instance = implementation
            else:
                try:
                    sig = inspect.signature(implementation)
                except (ValueError, TypeError):
                    # Se não puder inspecionar (ex: built-ins), instancia sem argumentos
                    instance = implementation()
                else:
                    dep_instances = {}
                    for name, param in sig.parameters.items():
                        # Ignorar argumentos variádicos (*args, **kwargs)
                        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                            continue
                        
                        dep_type = param.annotation
                        
                        # Se não há anotação ou é um tipo primitivo/builtin, usar default se existir
                        if dep_type is inspect.Parameter.empty or dep_type in (int, str, float, bool, dict, list, tuple, set):
                            if param.default is not inspect.Parameter.empty:
                                dep_instances[name] = param.default
                                continue
                            else:
                                raise ValueError(f"Parâmetro '{name}' em {implementation.__name__} não possui anotação de tipo válida ou é primitivo sem valor padrão.")

                        # Resolver dependência recursivamente
                        dep_instances[name] = self.resolve(dep_type, _resolution_stack)

                    instance = implementation(**dep_instances)

            if lifetime == Lifetime.SINGLETON:
                self._singletons[interface] = instance

            return instance
        finally:
            _resolution_stack.pop()

# ==========================================
# TESTES CONCRETOS E OBSERVÁVEIS
# ==========================================

class TransientService:
    def __init__(self, timeout: int = 15):
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
    def __init__(self, b: 'ServiceB'):
        self.b = b

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

def test_container():
    container = Container()

    # 1. Teste Transient com parâmetro primitivo default
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