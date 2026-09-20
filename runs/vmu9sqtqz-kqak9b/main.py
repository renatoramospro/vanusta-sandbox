import typing
import types

def is_compatible_type(value, expected_type, depth=0, max_depth=10):
    """
    Valida se o valor corresponde ao tipo esperado, suportando tipos genéricos, 
    Union e Optional, com proteção contra recursão infinita.
    """
    if depth > max_depth:
        raise RecursionError("Excesso de profundidade na validação de tipos genéricos.")

    if expected_type is typing.Any:
        return True

    origin = typing.get_origin(expected_type)
    args = typing.get_args(expected_type)

    # Trata Union e Optional (Union[T, None] ou T | None)
    if origin is typing.Union or (hasattr(types, "UnionType") and isinstance(expected_type, types.UnionType):
        return any(is_compatible_type(value, arg, depth + 1) for arg in args)

    # Se não for um tipo genérico (ex: int, str, list)
    if origin is None:
        return isinstance(value, expected_type)

    # Validação de Coleções (list, set, tuple, dict)
    if isinstance(value, origin):
        if origin in (list, set, tuple) and args:
            # Para tuple, se for tuple[int, str], o tamanho deve bater. 
            # Para simplificação deste experimento, tratamos como coleções homogêneas ou genéricas.
            if origin is tuple and len(args) > 1 and len(value) != len(args):
                return False
            return all(is_compatible_type(item, args[0], depth + 1) for item in value)
        
        if origin is dict and args:
            key_type, val_type = args
            return all(is_compatible_type(k, key_type, depth + 1) and 
                       is_compatible_type(v, val_type, depth + 1) 
                       for k, v in value.items())
        
        return True

    return isinstance(value, origin)

class TypedProperty:
    """Descritor que valida o tipo durante a atribuição."""
    def __init__(self, name, expected_type):
        self.name = name
        self.private_name = f"_{name}"
        self.expected_type = expected_type

    def __get__(self, instance, owner):
        if instance is None:
            return self
        # Tenta buscar no slot privado
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if not is_compatible_type(value, self.expected_type):
            raise TypeError(f"Atributo '{self.name}' deve ser do tipo {self.expected_type}, mas recebeu {type(value)} (valor: {repr(value)})")
        # Usa object.__setattr__ para evitar recursão e permitir __slots__
        object.__setattr__(instance, self.private_name, value)

class ValidatedMeta(type):
    """Metaclasse que injeta descritores e automatiza __slots__."""
    def __new__(mcs, name, bases, attrs):
        # 1. Coletar anotações de toda a hierarquia (MRO)
        annotations = {}
        for base in reversed(bases):
            if hasattr(base, '__annotations__'):
                annotations.update(base.__annotations__)
        if '__annotations__' in attrs:
            annotations.update(attrs['__annotations__'])

        # 2. Preparar slots
        # Pegamos os slots definidos pelo usuário
        user_slots = set(attrs.get('__slots__', []))
        
        # Para cada anotação, precisamos de um slot privado para o descritor armazenar o valor
        private_slots = set()
        for attr_name, attr_type in annotations.items():
            # Se o atributo já for um descritor ou propriedade, não injetamos
            if not isinstance(attrs.get(attr_name), (TypedProperty, property)):
                private_slots.add(f"_{attr_name}")
                # Injetamos o descritor no namespace da classe
                attrs[attr_name] = TypedProperty(attr_name, attr_type)

        # 3. Mesclar slots: slots do usuário + nossos slots privados
        # Importante: não podemos ter nomes duplicados. 
        # Se o usuário definiu 'id' em __slots__, e nós criamos '_id', não há conflito.
        new_slots = tuple(sorted(list(user_slots | private_slots)))
        attrs['__slots__'] = new_slots

        return super().__new__(mcs, name, bases, attrs)

def run_experiment():
    print("--- Iniciando Experimento de Validação de Tipos (Versão Automática) ---")

    # 1. Teste de Tipos Genéricos
    print("\n[1] Testando Tipos Genéricos (list[int], dict[str, int])...")
    class GenericModel(metaclass=ValidatedMeta):
        items: list[int]
        mapping: dict[str, int]

    g = GenericModel()
    g.items = [1, 2, 3]
    g.mapping = {"a": 1, "b": 2}
    print("  ✅ Sucesso: Atribuições válidas aceitas.")

    try:
        g.items = [1, "erro", 3]
    except TypeError as e:
        print(f"  ✅ Sucesso: Rejeitou lista com string: {e}")
    else:
        print("  ❌ FALHA: Aceitou lista com tipo incorreto!")

    # 2. Teste de Herança e Mixins
    print("\n[2] Testando Herança e Mixins...")
    class Base(metaclass=ValidatedMeta):
        base_val: int

    class Mixin(metaclass=ValidatedMeta):
        mixin_val: str

    class Child(Base, Mixin):
        child_val: float

    c = Child()
    c.base_val = 10
    c.mixin_val = "hello"
    c.child_val = 1.5
    print("  ✅ Sucesso: Atributos herdados e locais funcionam.")

    try:
        c.base_val = "não sou int"
    except TypeError as e:
        print(f"  ✅ Sucesso: Rejeitou tipo incorreto em atributo herdado: {e}")
    else:
        print("  ❌ FALHA: Aceitou tipo incorreto em atributo herdado!")

    # 3. Teste de __slots__ (Automação Total)
    print("\n[3] Testando __slots__ (Automação Total)...")
    class SlottedModel(metaclass=ValidatedMeta):
        __slots__ = ("id",) # O usuário define apenas o slot público desejado
        id: int

    s = SlottedModel()
    s.id = 100
    print(f"  ✅ Sucesso: Atribuição em SlottedModel funcionou (id={s.id}).")

    try:
        s.id = "um"
    except TypeError as e:
        print(f"  ✅ Sucesso: Rejeitou tipo incorreto em SlottedModel: {e}")
    else:
        print("  ❌ FALHA: Aceitou tipo incorreto em SlottedModel!")

    try:
        s.extra = 123
    except AttributeError:
        print("  ✅ Sucesso: __slots__ impediu criação de atributo extra.")
    except Exception as e:
        print(f"  ❌ FALHA: Erro inesperado: {type(e).__name__}: {e}")

    print("\n--- Experimento Finalizado ---")

if __name__ == "__main__":
    run_experiment()