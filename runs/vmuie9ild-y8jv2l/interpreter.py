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
        """Retorna o valor da variável."""
        return self.find(var)[var]

    def update(self, var, value):
        """Atualiza ou define uma variável no ambiente atual."""
        self.env[var] = value


# --- 3. AVALIAÇÃO E PROCEDIMENTOS ---

class Procedure:
    """Representa uma função definida pelo usuário (closure)."""
    def __init__(self, params, body, env):
        self.params = params
        self.body = body
        self.env = env  # Armazena o ambiente léxico de definição

    def __call__(self, *args):
        # Cria um novo ambiente encadeado ao ambiente léxico de definição da função
        new_env = Environment(self.params, args, self.env)
        # Avalia cada expressão do corpo e retorna o resultado da última
        result = None
        for expr in self.body:
            result = eval_ast(expr, new_env)
        return result


def standard_env():
    """Cria o ambiente global padrão com primitivas aritméticas e lógicas."""
    env = Environment()
    env.update('+', lambda *args: sum(args))
    env.update('-', lambda a, b=None: -a if b is None else a - b)
    env.update('*', lambda *args: eval(" * ".join(map(str, args))))
    env.update('/', lambda a, b: a / b)
    env.update('>', lambda a, b: a > b)
    env.update('<', lambda a, b: a < b)
    env.update('=', lambda a, b: a == b)
    return env


def eval_ast(x, env):
    """Avalia uma expressão AST dentro de um ambiente."""
    if isinstance(x, str):  # Símbolo / Variável
        return env.lookup(x)
    elif not isinstance(x, list):  # Literal (número)
        return x
    
    # Formas especiais e chamadas
    if not x:
        return []
    
    op = x[0]
    
    if op == 'define':
        _, var, expr = x
        val = eval_ast(expr, env)
        env.update(var, val)
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