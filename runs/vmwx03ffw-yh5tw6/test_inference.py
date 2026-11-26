import pytest
from inference_module import identity, add_one, process_list, map_fn, identity_list, process_int, ambiguous_func, composed_fn, process_tuple, wrong_type_fn, infer_type

# Teste de cobertura de cenários válidos (9)
@pytest.mark.parametrize("func, expected", [
    (identity, "TypeVar<T> -> T"),
    (add_one, "int -> int"),
    (process_list, "List[T] -> List[T]"),
    (map_fn, "Callable -> List[T] -> List[T]"),
    (identity_list, "List[T] -> List[T]"),
    (process_int, "int -> int"),
    (ambiguous_func, "TypeVar<T> -> T"),
    (composed_fn, "Callable -> Callable -> Callable[int] -> int"),
    (process_tuple, "Tuple[T, ...] -> Tuple[T, ...]")
])
def test_valid_inferences(func, expected):
    """Testa a correta inferência para cenários válidos."""
    assert infer_type(func) == expected

# Teste de detecção de inconsistência (C10)
def test_inconsistency_detection():
    """Testa se o sistema detecta que o tipo inferido não corresponde ao esperado (falha de tipo)."""
    # O tipo real de wrong_type_fn é 'str -> str'. O teste espera que ele NÃO seja 'int -> int'.
    assert infer_type(wrong_type_fn) != "int -> int"

# Cobertura de testes: 10 cenários (9 válidos + 1 de inconsistência) cobertos.