import asyncio
import inspect
import sys
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
        return await self._resolve_recursive(cls, [])

    async def _resolve_recursive(self, cls: Type[Any], stack: list[Type]) -> Any:
        if cls in stack:
            raise CircularDependencyError(stack + [cls])

        if cls in self._singletons:
            return self._singletons[cls]

        if cls not in self._registry:
            # Se não está registrado, tentamos instanciar diretamente (fallback)
            return await self._instantiate(cls, stack)

        reg = self._registry[cls]
        impl = reg["implementation"]
        
        # Se for factory, resolvemos a factory
        if reg["factory"]:
            instance = reg["factory"]() if inspect.iscoroutinefunction(reg["factory"]) else reg["factory"]()
            if inspect.isawaitable(instance):
                instance = await instance
            if reg["scope"] == "singleton":
                self._singletons[cls] = instance
            return instance

        instance = await self._instantiate(impl, stack)

        if reg["scope"] == "singleton":
            self._singletons[cls] = instance
        
        return instance

    async def _instantiate(self, impl: Type[Any], stack: list[Type]) -> Any:
        new_stack = stack + [impl]
        
        # Obter type hints resolvendo Forward References via módulo de origem
        try:
            module = sys.modules.get(impl.__module__)
            globalns = module.__dict__ if module else None
            type_hints = get_type_hints(impl, globalns=globalns)
        except Exception:
            # Fallback para inspeção bruta se get_type_hints falhar
            type_hints = {p.name: p.annotation for p in inspect.signature(impl).parameters.values()}

        sig = inspect.signature(impl)
        kwargs = {}

        for name, param in sig.parameters.items():
            if name in type_hints:
                dep_type = type_hints[name]
                # Ignorar tipos que não são classes (ex: int, str) para injeção automática
                if inspect.isclass(dep_type) or (hasattr(dep_type, "__origin__") and inspect.isclass(dep_type.__origin__)):
                    kwargs[name] = await self._resolve_recursive(dep_type, new_stack)
                else:
                    # Se for um tipo primitivo sem valor padrão, o DI falha ou espera que seja provido
                    if param.default is inspect.Parameter.empty:
                        raise TypeError(f"Não foi possível resolver o parâmetro '{name}' de {impl.__name__} (tipo primitivo sem default).")
                    kwargs[name] = param.default
            elif param.default is inspect.Parameter.empty:
                raise TypeError(f"Parâmetro '{name}' em {impl.__name__} sem anotação de tipo ou valor padrão.")
            else:
                kwargs[name] = param.default

        if inspect.iscoroutinefunction(impl):
            return await impl(**kwargs)
        return impl(**kwargs)

async def run_tests():
    container = DIContainer()
    print("Iniciando testes...")

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
    assert instance1.l2 is instance2.l2, "Singleton falhou: Level2 deve ser a mesma instância"
    assert instance1.l3 is not instance2.l3, "Transient falhou: Level3 deve ser instâncias diferentes"
    print("Sucesso: 3 níveis de dependências e escopos validados.")

    # 3. Teste de Async Factory
    async def async_factory():
        await asyncio.sleep(0.01)
        return "FactoryValue"

    class FactoryConsumer:
        def __init__(self, val: str):
            self.val = val

    container.register(str, implementation=str, factory=async_factory)
    container.register(FactoryConsumer)
    
    consumer = await container.resolve_async(FactoryConsumer)
    assert consumer.val == "FactoryValue"
    print("Sucesso: Async factory validada.")

    print("\nTODOS OS TESTES PASSARAM COM SUCESSO!")

if __name__ == "__main__":
    asyncio.run(run_tests())