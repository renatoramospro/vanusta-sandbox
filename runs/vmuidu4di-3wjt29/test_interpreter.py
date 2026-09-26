import pytest
from interpreter import parse, run, standard_env, Environment, eval_ast

def test_arithmetic():
    assert run("(+ 1 (* 2 3))") == 7

def test_define_and_lookup():
    code = """
    (define x 10)
    (+ x 5)
    """
    assert run(code) == 15

def test_shadowing_and_lexical_scope():
    # Testa escopo léxico e shadowing estrito
    code = """
    (define x 100)
    (define make-adder (lambda (x) (lambda (y) (+ x y))))
    (define add-100 (make-adder 10))
    (add-100 5)
    """
    # Se fosse escopo dinâmico ou vazamento global, x seria 100.
    # Com escopo léxico puro capturado na closure, x é 10, resultando em 15.
    assert run(code) == 15

def test_fibonacci_recursion():
    fib_code = """
    (define fib (lambda (n)
        (if (= n 0)
            0
            (if (= n 1)
                1
                (+ (fib (- n 1)) (fib (- n 2)))))))
    (fib 20)
    """
    assert run(fib_code) == 6765

def test_invalid_syntax():
    with pytest.raises(SyntaxError):
        parse("(+ 1 2") # parêntese não fechado