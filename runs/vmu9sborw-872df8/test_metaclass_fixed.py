import typing
import unittest
import types

def validate_type(value, expected_type):
    """Valida se o valor corresponde ao tipo esperado, suportando tipos genéricos (ex: list[int], dict[str, int]),
    Union, Optional e tipos concretos padrão."""
    if expected_type is typing.Any:
        return True

    origin = typing.get_origin(expected_type)
    args = typing.get_args(expected_type)

    # Caso 1: Tipos genéricos (ex: list[int], dict[str, str])
    if origin is not None:
        if not isinstance(value, origin):
            return False
        
        # Validação recursiva dos argumentos do genérico
        if args:
            if origin is list or origin is set or origin is tuple:
                # Se tuple tiver múltiplos argumentos (ex: tuple[int, str])
                if origin is tuple and len(args) == 2 and args[1] is ...:
                    return all(validate_type(item, args[0]) for item in value)
                elif origin is tuple and len(args) != len(value):
                    return False
                return all(validate_type(item, args[0]) for item in value)
            elif origin is dict:
                key_type, val_type = args if len(args) == 2 else (typing.Any, typing.Any)
                return all(validate_type(k, key_type) and validate_type(v, val_type) for k, v in value.items())
        return True

    # Caso 2: Union ou Optional (ex: int | None ou Union[int, str])
    if isinstance(expected_type, types.UnionType) or getattr(expected_type, "__origin__", None) is typing.Union:
        union_types = typing.get_args(expected_type)
        return any(validate_type(value, t) for t in union_types)

    # Caso 3: Tipos concretos normais
    return isinstance(value, expected_type)


class TypedProperty:
    """Descritor que valida o tipo do valor atribuído, compatível com __slots__ e genéricos."""
    def __init__(self, name: str, expected_type: type):
        self.name = name
        self.expected_type = expected_type
        self.private_name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        # Suporta tanto classes com __dict__ quanto com __slots__
        if hasattr(instance, self.private_name):
            return getattr(instance, self.private_name)
        raise AttributeError(f"'{owner.__name__}' object has no attribute '{self.name}'")

    def __set__(self, instance, value):
        if not validate_type(value, self.expected_type):
            raise TypeError(
                f"Atributo '{self.name}' espera {self.expected_type}, "
                f"mas recebeu {type(value).__name__} ({value!r})"
            )
        setattr(instance, self.private_name, value)


class ValidatedMeta(type):
    """Metaclasse que injeta validadores de tipo em todos os atributos anotados,
    suportando MRO, herança complexa, tipos genéricos e __slots__."""
    def __new__(mcs, name, bases, namespace, **kwargs):
        annotations = {}
        # Coleta anotações de toda a hierarquia (MRO)
        for base in reversed(bases):
            if hasattr(base, "__annotations__"):
                annotations.update(base.__annotations__)
        
        # Adiciona anotações da própria classe
        if "__annotations__" in namespace:
            annotations.update(namespace["__annotations__"])

        # Tratamento de __slots__: se a classe define __slots__, precisamos garantir
        # que os atributos privados correspondentes (ex: _attr) estejam nos __slots__
        # para evitar AttributeError em tempo de atribuição.
        slots = namespace.get("__slots__", None)
        if slots is not None:
            # Se __slots__ for uma string ou iterável, convertemos/ajustamos para incluir os privados
            if isinstance(slots, str):
                slots_list = [slots]
            else:
                slots_list = list(slots)
            
            for attr_name in annotations:
                private_slot = f"_{attr_name}"
                if private_slot not in slots_list:
                    slots_list.append(private_slot)
            namespace["__slots__"] = tuple(slots_list)

        # Substitui atributos anotados por descritores TypedProperty
        for attr_name, attr_type in annotations.items():
            if attr_name not in namespace:
                namespace[attr_name] = TypedProperty(attr_name, attr_type)

        return super().__new__(mcs, name, bases, namespace, **kwargs)


# ==========================================
# TESTES UNITÁRIOS COMPROVANDO A CORREÇÃO
# ==========================================

class TestValidatedMetaFixes(unittest.TestCase):

    def test_generic_types_validation(self):
        class Container(metaclass=ValidatedMeta):
            items: list[int]
            mapping: dict[str, int]

        c = Container()
        # Atribuição válida
        c.items = [1, 2, 3]
        c.mapping = {"a": 1, "b": 2}
        self.assertEqual(c.items, [1, 2, 3])
        self.assertEqual(c.mapping, {"a": 1, "b": 2})

        # Atribuição inválida: lista com string em vez de int
        with self.assertRaises(TypeError):
            c.items = [1, "dois", 3]  # type: ignore

        # Atribuição inválida: dicionário com valor incorreto
        with self.assertRaises(TypeError):
            c.mapping = {"a": "um"}  # type: ignore

    def test_slots_compatibility(self):
        class SlottedModel(metaclass=ValidatedMeta):
            __slots__ = ("id", "name")
            id: int
            name: str

        s = SlottedModel()
        s.id = 10
        s.name = "Alice"

        self.assertEqual(s.id, 10)
        self.assertEqual(s.name, "Alice")

        # Verifica rejeição de tipo incorreto em classe com __slots__
        with self.assertRaises(TypeError):
            s.id = "dez"  # type: ignore

        # Verifica que __slots__ realmente impede atributos fora do escopo
        with self.assertRaises(AttributeError):
            s.invalid_attr = 99  # type: ignore


if __name__ == "__main__":
    unittest.main(verbosity=2)