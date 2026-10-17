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
        self.out = out  # Lista de listas/ponteiros para remendos (patch)

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
        
        if c.isalnum() or c == '.':
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
# 3. Compilação para NFA (Thompson's Construction)
# ==========================================

def compile_regex(pattern):
    postfix = infix_to_postfix(pattern)
    stack = []
    
    for c in postfix:
        if c == '.':
            # Concatenação
            e2 = stack.pop()
            e1 = stack.pop()
            patch(e1.out, e2.start)
            stack.append(Frag(e1.start, e2.out))
        elif c == '|':
            # Alternância
            e2 = stack.pop()
            e1 = stack.pop()
            s = State(EPSILON)
            s.out1 = e1.start
            s.out2 = e2.start
            stack.append(Frag(s, append(e1.out, e2.out)))
        elif c == '*':
            # Fecho de Kleene (0 ou mais)
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            patch(e.out, s)
            stack.append(Frag(s, [s]))
        elif c == '+':
            # Operador positivo (1 ou mais)
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            patch(e.out, s)
            stack.append(Frag(e.start, [s]))
        elif c == '?':
            # Opcional (0 ou 1)
            e = stack.pop()
            s = State(EPSILON)
            s.out1 = e.start
            stack.append(Frag(s, append(e.out, [s])))
        else:
            # Caractere literal
            s = State(c if len(c) == 1 else c[1])
            stack.append(Frag(s, [s]))
            
    e = stack.pop()
    match_state = State(None) # Estado de aceitação final
    patch(e.out, match_state)
    return Frag(e.start, match_state)

# ==========================================
# 4. Simulador de NFA (Epsilon-Closure & Simulação)
# ==========================================

def add_state(l, s, list_id, list_states):
    if s is None or list_states.get(s) == list_id:
        return
    list_states[s] = list_id
    if s.c == EPSILON:
        if s.out1:
            add_state(l, s.out1, list_id, list_states)
        if s.out2:
            add_state(l, s.out2, list_id, list_states)
    else:
        l.append(s)

def match_nfa(nfa, text):
    current_list_id = 0
    list_states = {}
    
    clist = []
    current_list_id += 1
    add_state(clist, nfa.start, current_list_id, list_states)
    
    for char in text:
        current_list_id += 1
        nlist = []
        for s in clist:
            if s.c == char or s.c == '.':
                add_state(nlist, s.out1, current_list_id, list_states)
                if s.out2:
                    add_state(nlist, s.out2, current_list_id, list_states)
        clist = nlist
        
    for s in clist:
        if s == nfa.out:
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