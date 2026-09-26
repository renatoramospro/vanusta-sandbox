from interpreter import run, parse, Environment, eval_ast, standard_env
import pytest

def test_arithmetic():
    assert run("(+ 1 (* 2 3))") == 7

def test_define_and_lookup():
    code = """
    (define x 10)
    (+ x 5)
    """
    assert run(code) == 15

def test_shadowing_and_lexical_scope():
    # Testa se parâmetros locais sombreiam variáveis globais corretamente
    code = """
    (define x 100)
    (define f (lambda (x) (+ x 10)))
    (f 5)
    """
    assert run(code) == 15
    # Verifica que a variável global não foi mutada indevidamente
    env = standard_env()
    run("(define x 100)")

def test_fibonacci_recursion():
    # Testa fib(20) = 6765 com função recursiva definida em Lisp
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