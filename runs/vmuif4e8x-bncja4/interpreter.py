import re

# --- 1. EXCEÇÃO CUSTOMIZADA ---

class LispSyntaxError(Exception):
    """Exceção para erros de sintaxe no interpretador Lisp."""
    pass


# --- 2. TOKENIZAÇÃO E PARSING ---

def tokenize(chars):
    """Converte string de código Lisp em lista de tokens."""
    chars = chars.replace('(', ' ( ').replace(')', ' ) ')
    return chars.split()

def read_from_tokens(tokens):
    """Lê uma expressão S-expression a partir de uma lista de tokens."""
    if len(tokens) == 0:
        raise LispSyntaxError('Erro de sintaxe: tokens inesperados (Fim de arquivo)')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while True:
            if not tokens:
                raise LispSyntaxError('Erro de sintaxe: parêntese não fechado')
            if tokens[0] == ')':
                break
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # consome o ')'
        return L
    elif ')' == token:
        raise LispSyntaxError('Erro de sintaxe: parêntese fechado inesperado')
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


# --- 3. AMBIENTE E ESCOPO LÉXICO ---

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
            raise NameError(f"Variável não definida: '{var}'")

    def lookup(self, var):
        return self.find(var)[var]

    def update(self, var, val):
        self.find(var)[var] = val

    def define(self, var, val):
        self.env[var] = val


class Procedure:
    """Representa uma função definida pelo usuário (Closure)."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  # Ambiente léxico de definição

    def __call__(self, *args):
        # Cria um novo ambiente encadeado ao ambiente de definição da closure
        new_env = Environment(self.params, args, outer=self.env)
        result = None
        for exp in self.body:
            result = eval_ast(exp, new_env)
        return result


# --- 4. PRIMITIVAS E AVALIAÇÃO (EVAL) ---

def standard_env():
    """Cria o ambiente padrão com operadores aritméticos e de comparação."""
    env = Environment()
    env.define('+', lambda *args: sum(args))
    env.define('-', lambda a, b: a - b)
    env.define('*', lambda a, b: a * b)
    env.define('/', lambda a, b: a / b)
    env.define('>', lambda a, b: a > b)
    env.define('<', lambda a, b: a < b)
    env.define('=', lambda a, b: a == b)
    return env

def eval_ast(x, env):
    """Avalia uma expressão AST no ambiente dado."""
    if isinstance(x, str):
        # Referência a variável
        return env.lookup(x)
    elif not isinstance(x, list):
        # Constante literal (número)
        return x
    elif not x:
        return []
    
    # Formas especiais
    op = x[0]
    if op == 'define':
        _, var, exp = x
        env.define(var, eval_ast(exp, env))
        return None
    elif op == 'if':
        _, test, conseq, alt = x
        result = eval_ast(test, env)
        if result:
            return eval_ast(conseq, env)
        else:
            return eval_ast(alt, env)
    elif op == 'lambda':
        _, params, *body = x
        return Procedure(params, body, env)
    else:
        # Chamada de função padrão (aplicação)
        exps = [eval_ast(exp, env) for exp in x]
        proc = exps[0]
        args = exps[1:]
        return proc(*args)


def run(program_code):
    """Executa um script contendo múltiplas expressões Lisp."""
    env = standard_env()
    expressions = parse(program_code)
    result = None
    for exp in expressions:
        result = eval_ast(exp, env)
    return result