import time

# --- 1. Estrutura do NFA ---

class State:
    def __init__(self, c=None):
        self.c = c          # Caractere da transição (None para épsilon)
        self.out1 = None    # Próximo estado 1
        self.out2 = None    # Próximo estado 2 (para ramificações épsilon)
        self.last_list = 0  # Controle para evitar loops infinitos no epsilon-closure

class Fragment:
    def __init__(self, start, out):
        self.start = start  # Estado inicial do fragmento NFA
        self.out = out      # Lista de tuplas/referências para estados sem saída (pontos de costura)

# --- 2. Conversão Infixa para Pós-fixada ---

def insert_concat_operator(regexp):
    """Insere o operador explícito de concatenação '·' na expressão regular."""
    out = []
    lets = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.")
    
    for i in range(len(regexp)):
        c1 = regexp[i]
        out.append(c1)
        if i + 1 < len(regexp):
            c2 = regexp[i + 1]
            # Concatenação necessária entre: literal/curinga/fecho e literal/curinga/abertura
            if (c1 in lets or c1 == '*' or c1 == ')') and (c2 in lets or c2 == '('):
                out.append('·')
    return "".join(out)

def to_postfix(regexp):
    """Converte expressão regular infixa para pós-fixada usando Shunting-Yard."""
    specials = {'*': 3, '·': 2, '|': 1}
    postfix = []
    stack = []
    
    formatted = insert_concat_operator(regexp)
    for c in formatted:
        if c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
        elif c in specials:
            while stack and stack[-1] != '(' and specials.get(stack[-1], 0) >= specials[c]:
                postfix.append(stack.pop())
            stack.append(c)
        else:
            postfix.append(c)
            
    while stack:
        postfix.append(stack.pop())
        
    return "".join(postfix)

# --- 3. Construção do NFA (Algoritmo de Thompson) ---

MATCH = State(None) # Estado especial de aceitação final

def patch(l, s):
    """Conecta os pontos de saída pendentes (l) ao estado s."""
    for item in l:
        if item[0] == 1:
            item[1].out1 = s
        else:
            item[1].out2 = s

def compile_regex(regexp):
    """Compila uma expressão regular em pós-fixado para um NFA."""
    postfix = to_postfix(regexp)
    stack = []
    
    for c in postfix:
        if c == '·': # Concatenação
            e2 = stack.pop()
            e1 = stack.pop()
            patch(e1.out, e2.start)
            stack.append(Fragment(e1.start, e2.out))
        elif c == '|': # Alternância
            e2 = stack.pop()
            e1 = stack.pop()
            s = State(None)
            s.out1 = e1.start
            s.out2 = e2.start
            stack.append(Fragment(s, e1.out + e2.out))
        elif c == '*': # Fecho de Kleene
            e = stack.pop()
            s = State(None)
            s.out1 = e.start
            patch(e.out, s)
            s.out2 = MATCH # Ou aceita sair
            stack.append(Fragment(s, [(2, s)]))
        else: # Literal ou Curinga (.)
            s = State(c)
            s.out1 = MATCH
            stack.append(Fragment(s, [(1, s)]))
            
    e = stack.pop()
    patch(e.out, MATCH)
    return e.start

# --- 4. Simulador de Busca (NFA Execution) ---

list_id = 0

def add_state(s, clist):
    """Adiciona recursivamente estados alcançáveis via transições épsilon (closure)."""
    global list_id
    if not s or s.last_list == list_id:
        return
    s.last_list = list_id
    
    if s.c is None and s != MATCH:
        # Transições épsilon: explora ambos os ramos
        if s.out1:
            add_state(s.out1, clist)
        if s.out2:
            add_state(s.out2, clist)
    else:
        clist.append(s)

def match(regexp, text):
    """Verifica se a expressão regular corresponde a uma sub string do texto (busca livre)."""
    start_state = compile_regex(regexp)
    
    # Para suportar busca em qualquer posição do texto, inserimos prefixo '.*' implícito se necessário,
    # mas aqui implementamos correspondência exata ou busca com o NFA base.
    global list_id
    
    # Tentamos iniciar o match em cada posição do texto (sub-string matching)
    for i in range(len(text) + 1):
        list_id += 1
        clist = []
        add_state(start_state, clist)
        
        if MATCH in clist:
            return True
            
        if i == len(text):
            break
            
        c = text[i]
        list_id += 1
        nlist = []
        for s in clist:
            if s.c == '.' or s.c == c:
                add_state(s.out1, nlist)
        clist = nlist
        
        if MATCH in clist:
            # Verificar se sobrou apenas o MATCH
            pass

    return False

# Função de busca exata simplificada para testes diretos do NFA
def exact_match(regexp, text):
    global list_id
    start_state = compile_regex(regexp)
    list_id += 1
    clist = []
    add_state(start_state, clist)
    
    for c in text:
        list_id += 1
        nlist = []
        for s in clist:
            if s.c == '.' or s.c == c:
                add_state(s.out1, nlist)
        clist = nlist
        
    list_id += 1
    final_list = []
    for s in clist:
        add_state(s, final_list)
        
    return MATCH in final_list

# --- 5. Suíte de Testes e Demonstração de Equívocos ---

if __name__ == "__main__":
    print("=== INICIANDO TESTES DA ENGINE DE REGEX (NFA) ===")
    
    tests = [
        # Literais e Concatenação
        ("abc", "abc", True),
        ("abc", "def", False),
        # Alternância (|)
        ("a|b", "a", True),
        ("a|b", "b", True),
        ("a|b", "c", False),
        ("(cat|dog)", "cat", True),
        ("(cat|dog)", "dog", True),
        ("(cat|dog)", "bat", False),
        # Fecho de Kleene (*)
        ("a*", "", True),
        ("a*", "a", True),
        ("a*", "aaaa", True),
        ("a*b", "b", True),
        ("a*b", "aaab", True),
        ("a*b", "c", False),
        # Curinga (.)
        ("a.c", "abc", True),
        ("a.c", "axc", True),
        ("a.c", "ac", False),
        # Combinações complexas
        ("a(b|c)*d", "ad", True),
        ("a(b|c)*d", "abbbcd", True),
        ("a(b|c)*d", "acd", True),
        ("a(b|c)*d", "abd", True),
        ("a(b|c)*d", "aecd", False),
        (".*", "qualquer coisa 123", True),
        ("a.b*c", "abbc", True),
        ("a.b*c", "ac", True)
    ]
    
    assert len(tests) >= 25, "O número de testes deve ser pelo menos 25!"
    
    passed = 0
    start_time_total = time.time()
    
    for idx, (pattern, text, expected) in enumerate(tests):
        t0 = time.time()
        result = exact_match(pattern, text)
        t1 = time.time()
        
        duration_ms = (t1 - t0) * 1000
        assert duration_ms < 5.0, fomot: f"Teste {idx} excedeu o limite de 5ms ({duration_ms:.2f}ms)"
        
        if result == expected:
            passed += 1
        else:
            print(f"FALHA no teste {idx}: pattern='{pattern}', text='{text}' (Esperado: {expected}, Obtido: {result})")
            
    total_time_ms = (time.time() - start_time_total) * 1000
    print(f"\nResultados: {passed}/{len(tests)} testes passaram com sucesso!")
    print(f"Tempo total da suíte: {total_time_ms:.2f}ms (Média por busca: {total_time_ms/len(tests):.4f}ms)")
    
    # --- Ataque ao Equívoco Comum: Confundir NFA com DFA / Busca Simples ---
    print("\n[Contraexemplo de Equívoco Comum]")
    print("Muitos assumem que fecho de Kleene e alternância podem ser resolvidos com simples ifs ou sub-strings.")
    print("Tentando validar 'a(b|c)*d' em 'abbbbbbbbbbbbbbbbbbd' usando a engine NFA...")
    
    complex_pat = "a(b|c)*d"
    complex_txt = "a" + "b" * 500 + "d"
    
    t0 = time.time()
    res = exact_match(complex_pat, complex_txt)
    t1 = time.time()
    print(f"Resultado para string de tamanho 502: {res} em {(t1 - t0)*1000:.2f}ms")
    assert res == True, "Falha no reconhecimento de repetição longa via NFA."
    print("SUCESSO: O NFA processou cadeias longas sem explosão de pilha ou falha lógica.")