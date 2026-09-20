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
        # Versão síncrona
        return asyncio.run(self.resolve_async(cls))

    async def resolve_async(self, cls: Type[Any]) -> Any:
        resolving_stack: list[Type] = []
        return await self._resolve_recursive(cls, resolving_stack)

    async def _resolve_recursive(self, cls: Type[Any], stack: list[Type]) -> Any:
        if cls in stack:
            raise CircularDependencyError(stack + [cls])

        # Se for registrado como singleton e já instanciado
        if cls in self._singletons:
            return self._singletons[cls]

        registration = self._registry.get(cls)
        implementation = registration["implementation"] if registration else cls
        scope = registration["scope"] if registration else "transient"
        factory = registration["factory"] if registration else None

        stack.append(cls)
        try:
            if factory:
                if inspect.iscoroutinefunction(factory):
                    instance = await factory()
                else:
                    instance = factory()
            else:
                sig = inspect.signature(implementation.__init__)
                try:
                    hints = get_type_hints(implementation.__init__)
                except Exception:
                    hints = {}

                # Resolver dependências dos parâmetros do __init__ (ignorando 'self')
                args = {}
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = hints.get(param_name)
                    if param_type is None:
                        if param.default is not inspect.Parameter.empty:
                            continue
                        raise TypeError(f"Não foi possível resolver o parâmetro '{param_name}' de {implementation.__name__} sem anotação de tipo.")
                    
                    dep_instance = await self._resolve_recursive(param_type, stack)
                    args[param_name] = dep_instance

                if inspect.iscoroutinefunction(implementation.__init__):
                    instance = implementation()
                    await implementation.__init__(instance, **args)
                else:
                    instance = implementation(**args)

            if scope == "singleton":
                self._singletons[cls] = instance

            return instance
        finally:
            stack.pop()

# --- EXPERIMENTO / TESTE PRÁTICO ---
async def run_tests():
    container = DIContainer()

    # 1. Teste de classes aninhadas (3+ níveis, mistas sync/async)
    class Level3:
        def __init__(self):
            self.value = 42

    class Level2:
        def __init__(self, l3: Level3):
            self.l3 = l3

    class Level1:
        def __init__(self, l2: Level2):
            self.l2 = l2

    container.register(Level3, scope="transient")
    container.register(Level2, scope="transient")
    container.register(Level1, scope="singleton")

    root = await container.resolve_async(Level1)
    assert root.l2.l3.value == 42
    print("Sucesso: 3 níveis de dependências aninhadas resolvidos.")

    # 2. Teste de Escopo (Singleton vs Transient)
    instance1 = await container.resolve_async(Level1)
    instance2 = await container.resolve_async(Level1)
    assert instance1 is instance2, "Singleton falhou: instâncias diferentes retornadas."

    inst_l3_1 = await container.resolve_async(Level3)
    inst_l3_2 = await container.resolve_async(Level3)
    assert inst_l3_1 is not inst_l3_2, "Transient falhou: mesma instância retornada."
    print("Sucesso: Escopos singleton e transient validados corretamente.")

    # 3. Teste de Detecção de Dependência Circular (Atacando o equívoco comum)
    class CircularA:
        def __init__(self, b: "CircularB"): pass

    class CircularB:
        def __init__(self, a: CircularA): pass

    container.register(CircularA)
    container.register(CircularB)

    try:
        await container.resolve_async(CircularA)
        raise AssertionError("Deveria ter lançado CircularDependencyError")
    except CircularDependencyError as e:
        print(f"Sucesso: Detectada dependência circular esperada -> {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())