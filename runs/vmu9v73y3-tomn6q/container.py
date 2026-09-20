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
        self._registry: Dict[Any, Dict[str, Any]] = {}
        self._singletons: Dict[Any, Any] = {}

    def register(self, interface: Any, implementation: Optional[Any] = None, scope: str = "transient", factory: Optional[Callable] = None):
        if scope not in ("singleton", "transient"):
            raise ValueError(f"Escopo inválido: {scope}. Use 'singleton' ou 'transient'.")
        impl = implementation or interface
        self._registry[interface] = {
            "implementation": impl,
            "scope": scope,
            "factory": factory
        }

    def resolve(self, cls: Any) -> Any:
        return asyncio.run(self.resolve_async(cls))

    async def resolve_async(self, cls: Any) -> Any:
        resolving_stack: list[Any] = []
        return await self._resolve_recursive(cls, resolving_stack)

    async def _resolve_recursive(self, cls: Any, stack: list[Any]) -> Any:
        if cls in stack:
            raise CircularDependencyError(stack + [cls])

        if cls in self._singletons:
            return self._singletons[cls]

        registration = self._registry.get(cls)
        
        # Se não estiver registrado, tenta registrar transient por padrão (auto-wiring)
        if not registration:
            if inspect.isclass(cls):
                self.register(cls, scope="transient")
                registration = self._registry[cls]
            else:
                raise TypeError(f"'{cls}' não está registrado no container e não é uma classe instanciável.")

        impl = registration["implementation"]
        factory = registration["factory"]
        scope = registration["scope"]

        if cls in stack:
            raise CircularDependencyError(stack + [cls])

        stack.append(cls)
        try:
            if factory is not None:
                instance = factory()
                if inspect.isawaitable(instance):
                    instance = await instance
            elif inspect.isclass(impl):
                sig = inspect.signature(impl.__init__)
                try:
                    # get_type_hints resolve forward references em formato de string
                    globalns = getattr(impl, "__globals__", None)
                    type_hints = get_type_hints(impl.__init__, globalns=globalns)
                except Exception:
                    type_hints = {}

                resolved_args = {}
                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue
                    
                    dep_type = type_hints.get(param_name, param.annotation)
                    if dep_type == inspect.Parameter.empty:
                        raise TypeError(f"Não foi possível resolver o parâmetro '{param_name}' de {impl.__name__} sem anotação de tipo válida.")
                    
                    # Se for string (forward reference não resolvida por get_type_hints), tenta buscar no globalns
                    if isinstance(dep_type, str):
                        if globalns and dep_type in globalns:
                            dep_type = globalns[dep_type]
                        else:
                            raise TypeError(f"Forward reference '{dep_type}' para o parâmetro '{param_name}' em {impl.__name__} não pudo ser resolvida.")

                    resolved_args[param_name] = await self._resolve_recursive(dep_type, stack)

                instance = impl(**resolved_args)
            elif callable(impl):
                instance = impl()
                if inspect.isawaitable(instance):
                    instance = await instance
            else:
                instance = impl

            if scope == "singleton":
                self._singletons[cls] = instance

            return instance
        finally:
            stack.pop()

async def run_tests():
    container = DIContainer()

    # 1. Teste de Dependências Aninhadas (3 níveis, sync e async)
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

    l1_instance = await container.resolve_async(Level1)
    assert l1_instance.l2.l3.value == 42, "Falha na resolução de dependências aninhadas."
    print("Sucesso: 3 níveis de dependências aninhadas resolvidos.")

    # 2. Teste de Escopos Singleton vs Transient
    inst1 = await container.resolve_async(Level1)
    inst2 = await container.resolve_async(Level1)
    assert inst1 is inst2, "Singleton falhou."

    l3_inst1 = await container.resolve_async(Level3)
    l3_inst2 = await container.resolve_async(Level3)
    assert l3_inst1 is not l3_inst2, "Transient falhou."
    print("Sucesso: Escopos singleton e transient validados corretamente.")

    # 3. Teste de Detecção de Dependência Circular com Forward References (String Annotations)
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
        print(f"Sucesso: Detectada dependência circular com Forward Reference -> {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())