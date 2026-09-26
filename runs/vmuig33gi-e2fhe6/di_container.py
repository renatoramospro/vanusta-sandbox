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
        # Armazena as fábricas/construtores e seus ciclos de vida
        self._registry = {}
        # Armazena instâncias únicas para serviços Singleton
        self._singletons = {}

    def register(self, interface, implementation, lifetime=Lifetime.TRANSIENT):
        self._registry[interface] = {
            "implementation": implementation,
            "lifetime": lifetime
        }

    def resolve(self, interface, _resolution_stack=None):
        if _resolution_stack is None:
            _resolution_stack = []

        if interface not in self._registry:
            raise ServiceNotFoundError(f"Serviço não registrado: {interface}")

        # Verificação de dependência circular
        if interface in _resolution_stack:
            cycle_path = " -> ".join([str(s) for s in _resolution_stack + [interface]])
            raise CircularDependencyError(f"Dependência circular detectada: {cycle_path}")

        service_def = self._registry[interface]
        implementation = service_def["implementation"]
        lifetime = service_def["lifetime"]

        # Se for Singleton e já estiver instanciado, retorna a instância existente
        if lifetime == Lifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

        # Adiciona ao topo da pilha de resolução atual
        _resolution_stack.append(interface)

        try:
            # Se a implementação for uma função/fábrica ou um objeto chamável que não seja classe
            if callable(implementation) and not inspect.isclass(implementation):
                instance = implementation(self)
            elif inspect.isclass(implementation):
                # Inspeciona o construtor (__init__) para injeção baseada em tipos/parâmetros
                sig = inspect.signature(implementation.__init__)
                parameters = sig.parameters
                
                # Ignora 'self'
                dep_instances = []
                for param_name, param in parameters.items():
                    if param_name == 'self':
                        continue
                    
                    dep_type = param.annotation
                    if dep_type == inspect.Parameter.empty:
                        raise TypeError(f"O parâmetro '{param_name}' em {implementation.__name__} não possui anotação de tipo.")
                    
                    # Resolução recursiva passando a pilha de resolução atual
                    dep_instances.append(self.resolve(dep_type, _resolution_stack))
                
                instance = implementation(*dep_instances)
            else:
                instance = implementation

            if lifetime == Lifetime.SINGLETON:
                self._singletons[interface] = instance

            return instance
        finally:
            # Remove da pilha ao retornar (backtracking seguro para múltiplos ramos)
            _resolution_stack.pop()

# --- DEMONSTRAÇÃO E TESTES ---

class Engine:
    def __init__(self):
        self.id = id(self)

class Transmission:
    def __init__(self):
        self.id = id(self)

class Car:
    def __init__(self, engine: Engine, transmission: Transmission):
        self.engine = engine
        self.transmission = transmission

# Classes para testar dependência circular
class ServiceA:
    def __init__(self, b: 'ServiceB'):
        pass

class ServiceB:
    def __init__(self, a: ServiceA):
        pass

def test_container():
    container = Container()

    # 1. Teste de Transient (deve gerar instâncias diferentes)
    container.register(Engine, Engine, Lifetime.TRANSIENT)
    
    engine1 = container.resolve(Engine)
    engine2 = container.resolve(Engine)
    
    assert engine1 is not engine2, "Transient deveria criar novas instâncias a cada resolução!"
    print("Sucesso: Transient gera instâncias isoladas.")

    # 2. Teste de Singleton (deve reter a mesma instância)
    container.register(Transmission, Transmission, Lifetime.SINGLETON)
    
    trans1 = container.resolve(Transmission)
    trans2 = container.resolve(Transmission)
    
    assert trans1 is trans2, "Singleton deveria retornar a mesma instância!"
    print("Sucesso: Singleton retorna a mesma instância.")

    # 3. Teste de Grafo Multinível (Car depende de Engine e Transmission)
    container.register(Car, Car, Lifetime.TRANSIENT)
    
    car = container.resolve(Car)
    assert isinstance(car, Car)
    assert isinstance(car.engine, Engine)
    assert isinstance(car.transmission, Transmission)
    print("Sucesso: Grafo multinível resolvido com sucesso.")

    # 4. Teste de Detecção de Dependência Circular (Contraexemplo controlado)
    container.register(ServiceA, ServiceA, Lifetime.TRANSIENT)
    container.register(ServiceB, ServiceB, Lifetime.TRANSIENT)

    try:
        container.resolve(ServiceA)
        raise AssertionError("Deveria ter lançado CircularDependencyError!")
    except CircularDependencyError as e:
        print(f"Sucesso: Exceção capturada corretamente -> {e}")

if __name__ == "__main__":
    test_container()
    print("Todos os testes do container de DI passaram com êxito!")