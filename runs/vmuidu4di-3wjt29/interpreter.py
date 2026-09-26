import re

# --- 1. TOKENIZAÇÃO E PARSING ---

def tokenize(chars):
    """Converte string de código Lisp em lista de tokens."""
    chars = chars.replace('(', ' ( ').replace(')', ' ) ')
    return chars.split()

def read_from_tokens(tokens):
    """Lê uma expressão S-expression a partir de uma lista de tokens."""
    if len(tokens) == 0:
        raise SyntaxError('Erro de sintaxe: tokens inesperados (Fim de arquivo)')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while True:
            if not tokens:
                raise SyntaxError('Erro de sintaxe: parêntese não fechado')
            if tokens[0] == ')':
                break
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # consome o ')'
        return L
    elif ')' == token:
        raise SyntaxError('Erro de sintaxe: parêntese fechado inesperado')
    else:
        return parse_atom(token)

def parse_atom(token):
    """Converte um token string em número ou símbolo."""
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return str(token)

def parse(program):
    """Lê um programa Lisp completo."""
    tokens = tokenize(program)
    expressions = []
    while tokens:
        expressions.append(read_from_tokens(tokens))
    return expressions


# --- 2. AMBIENTE E ESCOPO LÉXICO ---

class Environment:
    """Ambiente para resolução de variáveis com suporte a escopo encadeado (léxico)."""
    def __init__(self, params=(), args=(), outer=None):
        self.env = dict(zip(params, args))
        self.outer = outer

    def find(self, var):
        """Encontra o escopo onde a variável está definida."""
        if var in self.env:
            return self.env
        elif self.outer is not None:
            return self.outer.find(var)
        else:
            raise LookupError(f"Variável não definida: '{var}'")

    def lookup(self, var):
        return self.find(var)[var]

    def define(self, var, value):
        self.env[var] = value


class Procedure:
    """Representa uma Closure definida pelo usuário."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  # Captura o ambiente léxico de definição

    def __call__(self, *args):
        # Cria um novo ambiente encadeado ao ambiente léxico de definição da função
        new_env = Environment(self.params, args, self.outer)
        # O self.outer aqui deve ser o env onde a função foi criada
        # Corrigindo a referenciação para o ambiente capturado:
        bound_env = Environment(self.params, args, self.env)
        return eval_ast(self.body, bound_env)


# --- 3. AVALIADOR (EVAL) ---

def eval_ast(x, env):
    """Avalia a expressão AST no ambiente dado."""
    if isinstance(x, str):
        # Referência a variável / símbolo
        return env.lookup(x)
    elif not isinstance(x, list):
        # Constante literal (número)
        return x
    elif not x:
        return []
    
    # Formas especiais e chamadas de procedimento
    op = x[0]
    if op == 'define':
        _, var, exp = x
        env.define(var, eval_ast(exp, env))
        return None
    elif op == 'lambda':
        _, params, body = x
        return Procedure(params, body, env)
    elif op == 'if':
        _, test, conseq, alt = x
        val = eval_ast(test, env)
        return eval_ast(conseq if val else alt, env)
    else:
        # Chamada de função genérica
        exps = [eval_ast(exp, env) for exp in x]
        procedure = exps[0]
        args = exps[1:]
        if callable(procedure):
            return procedure(*args)
        else:
            raise TypeError(f"Objeto não chamável: {procedure}")


# --- 4. AMBIENTE PADRÃO E RUNNER ---

import operator as op_mod

def standard_env():
    """Cria o ambiente padrão com primitivas aritméticas e lógicas."""
    env = Environment()
    env.env.update({
        '+': op_mod.add,
        '-': op_mod.sub,
        '*': op_mod.mul,
        '/': op_mod.truediv,
        '>': op_mod.gt,
        '<': op_mod.lt,
        '=': op_mod.eq,
    })
    return env

def run(code):
    """Executa um script Lisp e retorna o resultado da última expressão."""
    expressions = parse(code)
    env = standard_env()
    result = None
    for exp in expressions:
        result = eval_ast(exp, env)
    return result