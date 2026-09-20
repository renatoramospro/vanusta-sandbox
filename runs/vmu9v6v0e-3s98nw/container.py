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
        resolving_stack: list[Type] = []
        return await self._resolve_recursive(cls, resolving_stack)

    async def _resolve_recursive(self, cls: Type[Any], stack: list[Type]) -> Any:
        if cls in stack:
            raise CircularDependencyError(stack + [cls])

        if cls in self._singletons:
            return self._singletons[cls]

        registration = self._registry.get(cls)
        
        # Se não estiver explicitamente registrado, assumimos registro transient padrão
        if not registration:
            implementation = cls
            scope = "transient"
            factory = None
        else:
            implementation = registration["implementation"]
            scope = registration["scope"]
            factory = registration["factory"]

        stack.append(cls)
        try:
            if factory:
                sig = inspect.signature(factory)
                try:
                    hints = get_type_hints(factory, globalns=factory.__globals__, localns=vars(sys.modules[factory.__module__]))
                except Exception:
                    hints = {}
                
                kwargs = {}
                for param_name, param in sig.parameters.items():
                    param_type = hints.get(param_name, param.annotation)
                    if isinstance(param_type, str):
                        # Tenta resolver forward reference em string
                        param_type = self._resolve_string_annotation(param_type, implementation)
                    if param_type is inspect.Parameter.empty:
                        raise TypeError(f"Não foi possível resolver o parâmetro '{param_name}' da factory de {implementation.__name__}.")
                    kwargs[param_name] = await self._resolve_recursive(param_type, stack)
                
                if inspect.iscoroutinefunction(factory):
                    instance = await factory(**kwargs)
                else:
                    instance = factory(**kwargs)
            else:
                init_method = implementation.__init__
                sig = inspect.signature(init_method)
                try:
                    hints = get_type_hints(implementation, globalns=implementation.__globals__, localns=vars(sys.modules[implementation.__module__]))
                except Exception:
                    hints = {}

                kwargs = {}
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = hints.get(param_name, param.annotation)
                    if isinstance(param_type, str):
                        param_type = self._resolve_string_annotation(param_type, implementation)
                    if param_type is inspect.Parameter.empty:
                        raise TypeError(f"Não foi possível resolver o parâmetro '{param_name}' de {implementation.__name__} sem anotação de tipo.")
                    kwargs[param_name] = await self._resolve_recursive(param_type, stack)

                # Suporta construtores assíncronos (ex: __ainit__ ou classes com métodos async)
                if inspect.iscoroutinefunction(implementation):
                    instance = await implementation(**kwargs)
                else:
                    instance = implementation(**kwargs)

            if scope == "singleton":
                self._singletons[cls] = instance

            return instance
        finally:
            stack.pop()

    def _resolve_string_annotation(self, type_str: str, context_cls: Type) -> Type:
        # Tenta buscar no módulo da classe e builtins
        module = sys.modules.get(context_cls.__module__)
        if module and hasattr(module, type_str):
            return getattr(module, type_str)
        # Tenta buscar no registro do container
        for registered_type in self._registry:
            if registered_type.__name__ == type_str:
                return registered_type
        raise TypeError(f"Não foi possível resolver a anotação em string '{type_str}' para {context_cls.__name__}.")

async def run_tests():
    container = DIContainer()

    # 1. Teste de aninhamento profundo (10 classes)
    classes = []
    for i in range(1, 11):
        class_name = f"Level{i}"
        if i == 1:
            code = f"class {class_name}: pass"
        else:
            prev_name = f"Level{i-1}"
            code = f"class {class_name}:\n    def __init__(self, dep: {prev_name}): self.dep = dep"
        
        namespace = {}
        exec(code, globals(), namespace)
        cls = namespace[class_name]
        classes.append(cls)
        container.register(cls)

    top_instance = await container.resolve_async(classes[-1])
    assert top_instance is not None
    print("Sucesso: 10 níveis de dependências aninhadas resolvidos.")

    # 2. Teste de Forward References (String annotations)
    class ForwardA:
        def __init__(self, b: "ForwardB"):
            self.b = b

    class ForwardB:
        pass

    container.register(ForwardA)
    container.register(ForwardB)
    fa = await container.resolve_async(ForwardA)
    assert isinstance(fa.b, ForwardB)
    print("Sucesso: Forward references (string annotations) resolvidas com sucesso.")

    # 3. Teste de Detecção de Dependência Circular com String
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
        print(f"Sucesso: Detectada dependência circular esperada com Forward References -> {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())