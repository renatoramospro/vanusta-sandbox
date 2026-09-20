import typing
import types

def is_compatible_type(value, expected_type):
    """Valida se o valor corresponde ao tipo esperado, suportando tipos genéricos, Union e Optional."""
    if expected_type is typing.Any:
        return True

    origin = typing.get_origin(expected_type)
    args = typing.get_args(expected_type)

    # Trata Union e Optional (Union[T, None] ou T | None)
    if origin is typing.Union or (hasattr(types, "UnionType") and isinstance(expected_type, types.UnionType)):
        return any(is_compatible_type(value, arg) for arg in args)

    # Caso 1: Tipos genéricos (ex: list[int], dict[str, int])
    if origin is not None:
        if not isinstance(value, origin):
            return False
        
        # Validação profunda para coleções
        if origin is list or origin is set:
            if args:
                return all(is_compatible_type(item, args[0]) for item in value)
        elif origin is dict:
            if len(args) == 2:
                k_type, v_type = args
                return all(is_compatible_type(k, k_type) and is_compatible_type(v, v_type) 
                           for k, v in value.items())
        elif origin is tuple:
            if args:
                # Trata Tuple[int, ...] (ellipsis)
                if len(args) == 2 and args[1] is Ellipsis:
                    return all(is_compatible_type(item, args[0]) for item in value)
                # Trata Tuple[int, str] (tamanho fixo)
                if len(value) != len(args):
                    return False
                return all(is_compatible_type(v, t) for v, t in zip(value, args))
        return True

    # Caso 2: Tipos concretos padrão
    try:
        return isinstance(value, expected_type)
    except TypeError:
        # Fallback para casos onde isinstance falha com tipos complexos
        return False

class TypedProperty:
    """Descritor que valida o tipo durante a atribuição."""
    def __init__(self, name, expected_type):
        self.name = name
        self.expected_type = expected_type
        self.private_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if not is_compatible_type(value, self.expected_type):
            raise TypeError(
                f"Atributo '{self.name}' deve ser do tipo {self.expected_type}, "
                f"mas recebeu {type(value).__name__} (valor: {value!r})"
            )
        # Usa object.__setattr__ para evitar recursão e permitir uso com __slots__
        # O valor é armazenado no atributo privado definido pelo usuário nos slots
        object.__setattr__(instance, self.private_name, value)

class ValidatedMeta(type):
    """Metaclasse que injeta TypedProperty em atributos anotados."""
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Coleta anotações de toda a hierarquia (MRO)
        annotations = {}
        for base in reversed(name.mro() if hasattr(name, 'mro') else bases):
            if hasattr(base, '__annotations__'):
                annotations.update(base.__annotations__)
        
        # Se a classe atual tem anotações, elas prevalecem
        if '__annotations__' in namespace:
            annotations.update(namespace['__annotations__'])

        # Injeta os descritores no namespace
        for attr_name, attr_type in annotations.items():
            # Só injeta se não for um método ou atributo privado já definido
            if not attr_name.startswith('_') and not callable(namespace.get(attr_name)):
                namespace[attr_name] = TypedProperty(attr_name, attr_type)

        return super().__new__(mcs, name, bases, namespace, **kwargs)

# ==========================================
# EXPERIMENTO DE VALIDAÇÃO
# ==========================================

def run_experiment():
    print("--- Iniciando Experimento de Validação de Tipos ---")

    # 1. Teste de Tipos Genéricos
    print("\n[1] Testando Tipos Genéricos (list[int], dict[str, int])...")
    class Container(metaclass=ValidatedMeta):
        items: list[int]
        mapping: dict[str, int]

    c = Container()
    c.items = [1, 2, 3]
    c.mapping = {"a": 10}
    print("  ✅ Sucesso: Atribuições válidas aceitas.")

    try:
        c.items = [1, "erro", 3]
    except TypeError as e:
        print(f"  ✅ Sucesso: Rejeitou lista com string: {e}")
    else:
        print("  ❌ FALHA: Aceitou lista com tipo incorreto!")

    # 2. Teste de Herança e Mixins
    print("\n[2] Testando Herança e Mixins...")
    class Mixin(metaclass=ValidatedMeta):
        base_val: int

    class Child(Mixin):
        child_val: str

    child = Child()
    child.base_val = 10
    child.child_val = "hello"
    print("  ✅ Sucesso: Atributos herdados e locais funcionam.")

    try:
        child.base_val = "não sou int"
    except TypeError as e:
        print(f"  ✅ Sucesso: Rejeitou tipo incorreto em atributo herdado: {e}")
    else:
        print("  ❌ FALHA: Aceitou tipo incorreto em atributo herdado!")

    # 3. Teste de __slots__ (O ponto crítico)
    print("\n[3] Testando Compatibilidade com __slots__...")
    # Para usar __slots__ com descritores que usam '_attr', 
    # o usuário deve declarar '_attr' nos slots.
    class SlottedModel(metaclass=ValidatedMeta):
        __slots__ = ("_id", "_name") 
        id: int
        name: str

    s = SlottedModel()
    s.id = 1
    s.name = "Vanusta"
    print("  ✅ Sucesso: Atribuições em SlottedModel funcionam.")

    try:
        s.id = "um"
    except TypeError as e:
        print(f"  ✅ Sucesso: Rejeitou tipo incorreto em SlottedModel: {e}")
    else:
        print("  ❌ FALHA: Aceitou tipo incorreto em SlottedModel!")

    try:
        s.unknown = 123
    except AttributeError:
        print("  ✅ Sucesso: __slots__ impediu criação de atributo extra.")
    except Exception as e:
        print(f"  ❌ FALHA: Erro inesperado ao testar atributo extra: {type(e).__name__}: {e}")

    print("\n--- Experimento Finalizado ---")

if __name__ == "__main__":
    run_experiment()