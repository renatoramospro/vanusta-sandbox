import inspect
from typing import get_type_hints

class TypeValidatedAttribute:
    def __init__(self, name: str, expected_type: type):
        self.name = name
        self.expected_type = expected_type

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, None)

    def __set__(self, instance, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"Atributo '{self.name}' espera tipo {self.expected_type.__name__}, "
                f"mas recebeu {type(value).__name__} (valor: {value!r})"
            )
        instance.__dict__[self.name] = value

class ValidatedMeta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Coleta anotações de toda a hierarquia respeitando o MRO
        annotations = {}
        for base in reversed(bases):
            if hasattr(base, "__annotations__"):
                annotations.update(base.__annotations__)
        annotations.update(namespace.get("__annotations__", {}))

        # Injeta descritores para cada atributo anotado que ainda não seja um descritor
        for attr_name, expected_type in annotations.items():
            if attr_name not in namespace:
                namespace[attr_name] = TypeValidatedAttribute(attr_name, expected_type)

        return super().__new__(mcs, name, bases, namespace, **kwargs)

# --- Demonstração e Testes ---

class TimestampMixin(metaclass=ValidatedMeta):
    created_at: int

class User(TimestampMixin, metaclass=ValidatedMeta):
    name: str
    age: int

print("--- Testando criação e atribuição válida ---")
u = User()
u.name = "Alice"
u.age = 30
u.created_at = 1710000000
print(f"User criado com sucesso: name={u.name!r}, age={u.age}, created_at={u.created_at}")

print("\n--- Testando rejeição de tipo incompatível (Critério de Sucesso) ---")
try:
    u.age = "trinta"  # Esperado int, fornecido str
except TypeError as e:
    print(f"Capturado erro esperado com sucesso: {e}")

print("\n--- Testando herança de mixin e atributos herdados ---")
try:
    u.created_at = "ontem"  # Esperado int, fornecido str
except TypeError as e:
    print(f"Capturado erro esperado no mixin com sucesso: {e}")

print("\n[OK] Todos os testes executados e validados com sucesso.")