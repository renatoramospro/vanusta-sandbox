import pytest
from calc import soma, divide

def test_soma():
    assert soma(2, 3) == 5

def test_divide():
    assert divide(10, 4) == 2.5

def test_divide_por_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
