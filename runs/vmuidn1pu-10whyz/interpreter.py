import re

# --- 1. TOKENIZAÇÃO E PARSING ---

def tokenize(chars):
    """Converte string de código Lisp em lista de tokens."""
    # Substitui parênteses por espaços delimitados para facilitar o split
    chars = chars.replace('(', ' ( ').replace(')', ' ) ')
    return chars.split()

def read_from_tokens(tokens):
    """Lê uma expressão S-expression a partir de uma lista de tokens."""
    if len(tokens) == 0:
        raise SyntaxError('Erro de sintaxe: tokens inesperados (Fim de arquivo)')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while tokens[0] != ')':
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
    """Ambiente para resolução de variáveis com suporte a escopo encadenado (léxico)."""
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
        self.env = env  # Captura o ambiente de definição (escopo léxico)

    def __call__(self, *args):
        # Cria um novo ambiente encadeado no ambiente de definição da closure
        new_env = Environment(self.params, args, self.outer_env())
        # Avalia cada expressão do corpo e retorna o último valor
        result = None
        for expr in self.body:
            result = eval_ast(expr, new_env)
        return result

    def outer_env(self):
        return self.env


# --- 3. AVALIADOR (EVAL) ---

def standard_env():
    """Cria o ambiente padrão com primitivas aritméticas e lógicas."""
    env = Environment()
    env.env.update({
        '+': lambda *args: sum(args),
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b,
        '<': lambda a, b: a < b,
        '>': lambda a, b: a > b,
        '=': lambda a, b: a == b,
    })
    return env

def eval_ast(x, env):
    """Avalia uma expressão Lisp no ambiente fornecido."""
    if isinstance(x, str):  # Símbolo / Variável
        return env.lookup(x)
    elif not isinstance(x, list):  # Constante (número)
        return x
    
    # É uma lista (Forma Especial ou Aplicação de Função)
    if not x:
        return []
    
    op = x[0]
    
    if op == 'define':
        _, var, expr = x
        val = eval_ast(expr, env)
        env.define(var, val)
        return val
    elif op == 'if':
        _, test, conseq, alt = x
        if eval_ast(test, env):
            return eval_ast(conseq, env)
        else:
            return eval_ast(alt, env)
    elif op == 'lambda':
        _, params, *body = x
        return Procedure(params, body, env)
    else:
        # Aplicação de função padrão
        exps = [eval_ast(arg, env) for arg in x]
        procedure = exps[0]
        args = exps[1:]
        if callable(procedure):
            return procedure(*args)
        else:
            raise TypeError(f"Objeto não é uma função: {procedure}")

def run(program_str):
    """Executa um script contendo múltiplas expressões."""
    expressions = parse(program_str)
    env = standard_env()
    result = None
    for expr in expressions:
        result = eval_ast(expr, env)
    return result