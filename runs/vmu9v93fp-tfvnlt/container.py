import asyncio
import inspect
from typing import Any, Callable, Dict, Optional, Type, get_type_hints

class CircularDependencyError(Exception):
    """Lançado quando uma dependência circular é detectada, contendo a cadeia."""
    def __init__(self, chain: list[Type]):
        chain_str = " -> ".join([cls.__name__ for cls in chain])
        super().__init__(f"Dependência circular detectada: {chain_str}")
        self.chain = chain

class DIContainer:
    def __init__(self):
        self._registry: Dict[Type, Dict[str, Any]] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type, implementation: Optional[Type] = None, scope: str = "transient", factory: Optional[Callable] = None):
        if scope not in ("singleton", "transient"):
            raise ValueError(f"Escopo inválido: {scope}. Use 'singleton' ou 'transient'.")
        impl = implementation or interface
        self._registry[interface] = {
            "implementation": impl,
            "scope": scope,
            "factory": factory
        }

    def resolve(self, cls: Type[Any]) -> Any:
        return asyncio.run(self.resolve_async(cls))

    async def resolve_async(self, cls: Type[Any]) -> Any:
        resolving_stack: list[Type] = []
        return await self._resolve_recursive(cls, resolving_stack)

    async def _resolve_recursive(self, cls: Type[Any], stack: list[Type]) -> Any:
        if cls in stack:
            raise CircularDependencyError(stack + [cls])

        if cls in self._singletons:
            return self._singletons[cls]

        registration = self._registry.get(cls)
        implementation = registration["implementation"] if registration else cls
        scope = registration["scope"] if registration else "transient"
        factory = registration["factory"] if registration else None

        stack.append(cls)
        try:
            if factory:
                sig = inspect.signature(factory)
                type_hints = get_type_hints(factory, globalns=factory.__globals__)
                resolved_args = {}
                for param_name, param in sig.parameters.items():
                    param_type = type_hints.get(param_name, param.annotation)
                    if param_type == inspect.Parameter.empty:
                        raise TypeError(f"Não foi possível resolver o parâmetro '{param_name}' da fábrica de {cls.__name__} sem anotação.")
                    resolved_args[param_name] = await self._resolve_recursive(param_type, stack)
                
                if inspect.iscoroutinefunction(factory):
                    instance = await factory(**resolved_args)
                else:
                    instance = factory(**resolved_args)
            else:
                sig = inspect.signature(implementation)
                type_hints = get_type_hints(implementation, globalns=implementation.__globals__)
                resolved_args = {}
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = type_hints.get(param_name, param.annotation)
                    if param_type == inspect.Parameter.empty:
                        raise TypeError(f"Não foi possível resolver o parâmetro '{param_name}' de {implementation.__name__} sem anotação de tipo.")
                    resolved_args[param_name] = await self._resolve_recursive(param_type, stack)

                if inspect.iscoroutinefunction(implementation.__init__):
                    instance = implementation(**resolved_args)
                else:
                    instance = implementation(**resolved_args)

            if scope == "singleton":
                self._singletons[cls] = instance

            return instance
        finally:
            stack.pop()

async def run_tests():
    container = DIContainer()

    # 1. Teste de Forward Reference (String annotations) + Ciclo
    class CircularA:
        def __init__(self, b: "CircularB"):
            self.b = b

    class CircularB:
        def __init__(self, a: CircularA):
            self.a = a

    container.register(CircularA)
    container.register(CircularB)

    try:
        await container.resolve_async(CircularA)
        raise AssertionError("Deveria ter lançado CircularDependencyError")
    except CircularDependencyError as e:
        print(f"Sucesso: Detectada dependência circular com Forward References -> {e}")

    # 2. Teste de aninhamento de 3 níveis com escopos
    class Level3:
        pass

    class Level2:
        def __init__(self, l3: Level3):
            self.l3 = l3

    class Level1:
        def __init__(self, l2: Level2):
            self.l2 = l2

    container.register(Level3, scope="transient")
    container.register(Level2, scope="singleton")
    container.register(Level1, scope="transient")

    instance1 = await container.resolve_async(Level1)
    instance2 = await container.resolve_async(Level1)
    
    assert isinstance(instance1, Level1)
    assert instance1.l2 is instance2.l2, "Singleton falhou"
    assert instance1.l3 is not instance2.l3, "Transient falhou"
    print("Sucesso: 3 níveis de dependências e escopos validados com Forward/Type Hints.")

if __name__ == "__main__":
    asyncio.run(run_tests())