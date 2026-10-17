import sys
import time

# ==========================================
# 1. Componentes do NFA (Thompson's Construction)
# ==========================================

EPSILON = None

class State:
    def __init__(self, c=EPSILON):
        self.c = c
        self.out1 = None
        self.out2 = None

class Frag:
    def __init__(self, start, out):
        self.start = start
        self.out = out  # Lista de referências de saída (endpoints)

def patch(l, s):
    for f in l:
        if f.out1 is None:
            f.out1 = s
        elif f.out2 is None:
            f.out2 = s

def append(l1, l2):
    return l1 + l2

# ==========================================
# 2. Conversão Infixa para Pós-fixa (RPN)
# ==========================================

def insert_concat_operator(pattern):
    """Insere explicitamente o operador '.' de concatenação."""
    res = []
    for i in range(len(pattern)):
        c1 = pattern[i]
        res.append(c1)
        if i + 1 < len(pattern):
            c2 = pattern[i+1]
            # c1 pode ser seguido por c2 sem concatenação se:
            # c1 pertence a { '(', '|', '\\' } ou c2 pertence a { '*', '+', '?', ')', '|', ']' }
            if c1 not in "(|\\" and c2 not in "*+?)|]":
                res.append('.')
    return "".join(res)

def infix_to_postfix(pattern):
    """Converte expressão regular infixa para pós-fixa (RPN) usando Shunting-Yard."""
    pat = insert_concat_operator(pattern)
    output = []
    stack = []
    
    precedence = {
        '|': 1,
        '.': 2,
        '?': 3,
        '*': 3,
        '+': 3,
    }
    
    i = 0
    while i < len(pat):
        c = pat[i]
        if c == '\\':
            if i + 1 < len(pat):
                output.append(pat[i:i+2])
                i += 2
                continue
            else:
                output.append(c)
                i += 1
                continue
        elif c == '(':
            stack.append(c)
            i += 1
        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
            i += 1
        elif c in precedence:
            while (stack and stack[-1] != '(' and 
                   stack[-1] in precedence and 
                   precedence[stack[-1]] >= precedence[c]):
                output.append(stack.pop())
            stack.append(c)
            i += 1
        else:
            output.append(c)
            i += 1
            
    while stack:
        output.append(stack.pop())
        
    return output

# ==========================================
# 3. Compilação NFA (Thompson's Construction)
# ==========================================

def compile_regex(pattern):
    postfix = infix_to_postfix(pattern)
    stack = []
    
    for token in postfix:
        if token == '.':
            if len(stack) < 2:
                raise ValueError(f"Pilha insuficiente para concatenação '.' em '{pattern}'")
            e2 = stack.pop()
            e1 = stack.pop()
            patch(e1.out, e2.start)
            stack.append(Frag(e1.start, e2.out))
        elif token == '|':
            if len(stack) < 2:
                raise ValueError(f"Pilha insuficiente para alternância '|' em '{pattern}'")
            e2 = stack.pop()
            e1 = stack.pop()
            s = State(EPSILON)
            s.out1 = e1.start
            s.out2 = e2.start
            stack.append(Frag(s, append(e1.out, e2.out)))
        elif token == '*':
            if len(stack) < 1:
                raise ValueError(f"Pilha insuficiente para operador '*' em '{pattern}'")
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            patch(e.out, s)
            stack.append(Frag(s, [s]))
        elif token == '+':
            if len(stack) < 1:
                raise ValueError(f"Pilha insuficiente para operador '+' em '{pattern}'")
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            patch(e.out, s)
            stack.append(Frag(e.start, [s]))
        elif token == '?':
            if len(stack) < 1:
                raise ValueError(f"Pilha insuficiente para operador '?' em '{pattern}'")
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            # Opcional: cria um caminho direto por EPSILON
            stack.append(Frag(s, append(e.out, [s])))
        else:
            # Operando (caractere ou escape)
            if len(token) == 2 and token[0] == '\\':
                char_val = token[1]
            else:
                char_val = token
            
            s = State(char_val)
            stack.append(Frag(s, [s]))
            
    if len(stack) != 1:
        raise ValueError(f"Expressão malformada '{pattern}': pilha final com tamanho {len(stack)}")
        
    e = stack.pop()
    matchstate = State(None) # Estado de aceitação final
    patch(e.out, matchstate)
    return Frag(e.start, [matchstate])

# ==========================================
# 4. Simulação de NFA (Subconjunto / Epsilon Closure)
# ==========================================

def add_state(s, clist, visited):
    if s is None or s in visited:
        return
    visited.add(s)
    if s.c == EPSILON:
        # Se for estado epsilon, expande recursivamente out1 e out2
        if s.out1:
            add_state(s.out1, clist, visited)
        if s.out2:
            add_state(s.out2, clist, visited)
    else:
        clist.append(s)

def epsilon_closure(start_state):
    clist = []
    visited = set()
    add_state(start_state, clist, visited)
    return clist

def step(clist, c):
    nlist = []
    visited = set()
    for s in clist:
        if s.c == c or s.c == '.': # '.' curinga básico se implementado
            add_state(s.out1, nlist, visited)
            add_state(s.out2, nlist, visited)
    return nlist

def match_nfa(nfa, text):
    current = epsilon_closure(nfa.start)
    for c in text:
        current = step(current, c)
        if not current:
            break
            
    # Verifica se algum estado atual alcança o estado de aceitação final (nfa.out[0])
    for s in current:
        if s == nfa.out[0]:
            return True
            
    return False

# ==========================================
# 5. Execução de Testes e Validação de Complexidade
# ==========================================

if __name__ == "__main__":
    print("=== INICIALIZANDO TESTES DO MOTOR DE REGEX (NFA) ===")
    
    test_cases = [
        ("a(b|c)*d", "abbbcd", True),
        ("a(b|c)*d", "ad", True),
        ("a(b|c)*d", "abebcd", False),
        ("a+b*c?", "aaab", True),
        ("a+b*c?", "c", False),
        ("(ab)+c", "abababc", True),
        ("(ab)+c", "abc", True),
        ("a.*b", "axxxxxbyyyyy", True),
        ("a(b|c)?d", "abd", True),
        ("a(b|c)?d", "acd", True),
    ]

    for i, (pat, txt, expected) in enumerate(test_cases):
        nfa = compile_regex(pat)
        res = match_nfa(nfa, txt)
        print(f"Teste {i+1}: Padrão '{pat}' em '{txt}' -> Esperado: {expected}, Obtido: {res}")
        assert res == expected, f"Falha no teste {i+1}!"

    print("\nTodos os 10 padrões complexos validados com sucesso!")

    # Demonstração de Complexidade Linear
    print("\n=== DEMONSTRAÇÃO DE COMPLEXIDADE LINEAR ===")
    pattern = "a*a*a*a*b"
    nfa_lin = compile_regex(pattern)
    
    for size in [100, 1000, 10000]:
        long_text = "a" * size + "c"
        start_time = time.perf_counter()
        match_nfa(nfa_lin, long_text)
        end_time = time.perf_counter()
        print(f"Texto tamanho {size}: {(end_time - start_time)*1000:.4f} ms")

    print("\n[SUCESSO] Correção aplicada com sucesso e motor validado.")