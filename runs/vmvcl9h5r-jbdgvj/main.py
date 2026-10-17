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
        self.out = out  # Lista de estados cujas saídas precisam ser conectadas (patch)

def patch(list_of_states, target):
    for s in list_of_states:
        if s.out1 is None:
            s.out1 = target
        elif s.out2 is None:
            s.out2 = target

def append(l1, l2):
    return l1 + l2

# ==========================================
# 2. Conversão Infixa para Pós-fixa (RPN)
# ==========================================

def insert_concat_operator(pattern):
    """Insere o operador explícito de concatenação ('.') no regex."""
    res = []
    for i in range(len(pattern)):
        c1 = pattern[i]
        res.append(c1)
        if i + 1 < len(pattern):
            c2 = pattern[i+1]
            # Inverte concat se c1 for operando ou fechar parêntese/quantificador e c2 for operando ou abrir parêntese
            if c1 not in "(|\\" and c2 not in "*+?)|]":
                res.append('.')
    return "".join(res)

def infix_to_postfix(pattern):
    """Converte expressão regular infixa para pós-fixa (RPN) usando Shunting-Yard."""
    pat = insert_concat_operator(pattern)
    output = []
    stack = []
    
    precedence = {'*': 3, '+': 3, '?': 3, '.': 2, '|': 1}
    
    i = 0
    while i < len(pat):
        c = pat[i]
        if c == '\\':
            if i + 1 < len(pat):
                output.append(pat[i:i+2])
                i += 2
                continue
        
        if c.isalnum() or c == '.' or c == ' ':
            output.append(c)
        elif c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
        elif c in precedence:
            while (stack and stack[-1] in precedence and 
                   precedence[stack[-1]] >= precedence[c]):
                output.append(stack.pop())
            stack.append(c)
        i += 1
        
    while stack:
        output.append(stack.pop())
        
    return "".join(output)

# ==========================================
# 3. Construtor NFA (Thompson's Algorithm)
# ==========================================

def compile_regex(pattern):
    postfix = infix_to_postfix(pattern)
    stack = []
    
    i = 0
    while i < len(postfix):
        c = postfix[i]
        if c == '\\':
            if i + 1 < len(postfix):
                atom_char = postfix[i+1]
                s = State(atom_char)
                stack.append(Frag(s, [s]))
                i += 2
                continue
        
        if c.isalnum() or c == ' ':
            s = State(c)
            stack.append(Frag(s, [s]))
        elif c == '.': # Concatenação
            if len(stack) < 2:
                raise ValueError(f"Pilha insuficiente para concatenação em '{pattern}' (pos {i})")
            e2 = stack.pop()
            e1 = stack.pop()
            patch(e1.out, e2.start)
            stack.append(Frag(e1.start, e2.out))
        elif c == '|': # Alternância
            if len(stack) < 2:
                raise ValueError(f"Pilha insuficiente para alternância em '{pattern}' (pos {i})")
            e2 = stack.pop()
            e1 = stack.pop()
            s = State(EPSILON)
            s.out1 = e1.start
            s.out2 = e2.start
            stack.append(Frag(s, append(e1.out, e2.out)))
        elif c == '*': # Kleene Star (0 ou mais)
            if len(stack) < 1:
                raise ValueError(f"Pilha insuficiente para '*' em '{pattern}' (pos {i})")
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            patch(e.out, s)
            stack.append(Frag(s, [s]))
        elif c == '+': # Positivo (1 ou mais)
            if len(stack) < 1:
                raise ValueError(f"Pilha insuficiente para '+' em '{pattern}' (pos {i})")
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            patch(e.out, s)
            stack.append(Frag(e.start, [s]))
        elif c == '?': # Opcional (0 ou 1)
            if len(stack) < 1:
                raise ValueError(f"Pilha insuficiente para '?' em '{pattern}' (pos {i})")
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            stack.append(Frag(s, append(e.out, [s])))
        i += 1
        
    if len(stack) != 1:
        raise ValueError(f"Expressão regular inválida ou mal formada: '{pattern}'")
        
    e = stack.pop()
    accept_state = State(None)
    patch(e.out, accept_state)
    return Frag(e.start, [accept_state])

# ==========================================
# 4. Simulador NFA (Simulação de Estados)
# ==========================================

def add_state(clist, s, visited):
    if s is None or s in visited:
        return
    visited.add(s)
    if s.c is EPSILON:
        # Se for estado de aceitação (sem out1 e out2 e sem caractere), ele não expande
        if s.out1 is not None:
            add_state(clist, s.out1, visited)
        if s.out2 is not None:
            add_state(clist, s.out2, visited)
    else:
        clist.append(s)

def step(clist, c):
    nlist = []
    visited = set()
    for s in clist:
        if s.c == c or s.c == '.':
            add_state(nlist, s.out1, visited)
            if s.out2 is not None:
                add_state(nlist, s.out2, visited)
    return nlist

def match_nfa(nfa, text):
    current = []
    add_state(current, nfa.start, set())
    
    for c in text:
        current = step(current, c)
        
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