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
        self.out = out      # Lista de tuplas/referências para estados sem saída

# --- 2. Conversão Infixa para Pós-fixada (Shunting-Yard) ---

def insert_concat_operator(pattern):
    """Insere explicitamente o operador de concatenação (.) na expressão regular."""
    output = []
    lets = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.*|()")
    
    for i in range(len(pattern)):
        c1 = pattern[i]
        if i + 1 < len(pattern):
            c2 = pattern[i + 1]
            output.append(c1)
            # Regras para injetar o operador de concatenação '.'
            if (c1 not in "(|" and c2 not in "*)|") and (c2 in lets or c2 == '(' or c2 == '.'):
                output.append('.')
    if pattern:
        output.append(pattern[-1])
    return "".join(output)

def infix_to_postfix(pattern):
    """Converte expressão regular infixa para pós-fixada usando o algoritmo Shunting-Yard."""
    processed = insert_concat_operator(pattern)
    output = []
    stack = []
    precedence = {'*': 3, '.': 2, '|': 1}

    for c in processed:
        if c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
        elif c in precedence:
            while stack and stack[-1] in precedence and precedence[stack[-1]] >= precedence[c]:
                output.append(stack.pop())
            stack.append(c)
        else:
            # Caractere literal ou curinga
            output.append(c)

    while stack:
        output.append(stack.pop())

    return "".join(output)

# --- 3. Compilador NFA (Construção de Thompson) ---

def compile_regex(pattern):
    """Compila uma expressão regular pós-fixada em um NFA."""
    postfix = infix_to_postfix(pattern)
    stack = []

    for c in postfix:
        if c == '.':  # Concatenação
            if len(stack) < 2:
                raise ValueError("Expressão malformada para concatenação.")
            e2 = stack.pop()
            e1 = stack.pop()
            # Conecta a saída de e1 ao estado inicial de e2
            for o in e1.out:
                o[0].out1 = e2.start if o[1] == 1 else None # simplificação para listas de patch
            # Na verdade, precisamos costurar os pontos de saída corretamente:
            # Cada item em out é um dicionário ou tupla contendo uma referência ao atributo que aponta para o próximo estado.
            # Vamos usar uma abordagem de lista de ponteiros para costura (patching):
            pass

    # Abordagem robusta com listas de ponteiros (patching)
    stack = []
    for c in postfix:
        if c == '.': # Concatenação
            e2 = stack.pop()
            e1 = stack.pop()
            # Patch: aponta a saída de e1 para o início de e2
            for state, attr in e1.out:
                setattr(state, attr, e2.start)
            stack.append(Fragment(e1.start, e2.out))
            
        elif c == '|': # Alternância
            e2 = stack.pop()
            e1 = stack.pop()
            s = State()
            s.out1 = e1.start
            s.out2 = e2.start
            out = e1.out + e2.out
            stack.append(Fragment(s, out))
            
        elif c == '*': # Fecho de Kleene
            e = stack.pop()
            s = State()
            s.out1 = e.start
            s.out2 = None
            for state, attr in e.out:
                setattr(state, attr, s)
            stack.append(Fragment(s, [(s, 'out2')]))
            
        elif c == '.': # Curinga (representado internamente por um caractere especial ou flag)
            # Para evitar conflito com o operador '.', vamos usar o símbolo interno '\n' ou None com flag
            # Mas no nosso parser, o operador binário de concatenação é '.'. Vamos usar '?' para o curinga no postfix.
            pass
            
        else:
            # Literal ou Curinga
            s = State(c)
            stack.append(Fragment(s, [(s, 'out1')]))

    # Ajuste fino: se o padrão usa '.' como curinga, mapeamos para um token interno
    # Vamos reescrever o compilador considerando que '.' pode ser literal ou curinga.
    # No infixo, '.' significa curinga. Vamos tratá-lo adequadamente.
    raise NotImplementedError("Usar compile_nfa direto.")

def compile_nfa_direct(pattern):
    """Compilação NFA completa tratando corretamente literais e o curinga '?' (mapeado de '.')"""
    # Substitui curinga '.' por um caractere especial de curinga interno, ex: chr(0)
    wildcard_char = chr(0)
    
    # Pré-processamento do padrão para aceitar '.' como curinga
    # Nota: tratamos o '.' como operador de concatenação nas regras do shunting yard,
    # então o curinga deve ser representado por outro símbolo, por exemplo '@'.
    translated_pattern = []
    i = 0
    while i < len(pattern):
        if pattern[i] == '\\' and i + 1 < len(pattern):
            translated_pattern.append(pattern[i+1])
            i += 2
        elif pattern[i] == '.':
            translated_pattern.append('@') # @ representa o curinga
            i += 1
        else:
            translated_pattern.append(pattern[i])
            i += 1
    clean_pat = "".join(translated_pattern)
    
    postfix = infix_to_postfix(clean_pat)
    stack = []

    for c in postfix:
        if c == '.':  # Operador de concatenação binária
            e2 = stack.pop()
            e1 = stack.pop()
            for state, attr in e1.out:
                if attr == 'out1': state.out1 = e2.start
                elif attr == 'out2': state.out2 = e2.start
            stack.append(Fragment(e1.start, e2.out))
        elif c == '|':  # Alternância
            e2 = stack.pop()
            e1 = stack.pop()
            s = State()
            s.out1 = e1.start
            s.out2 = e2.start
            stack.append(Fragment(s, e1.out + e2.out))
        elif c == '*':  # Fecho de Kleene
            e = stack.pop()
            s = State()
            s.out1 = e.start
            s.out2 = None
            for state, attr in e.out:
                if attr == 'out1': state.out1 = s
                elif attr == 'out2': state.out2 = s
            stack.append(Fragment(s, [(s, 'out2')]))
        else:  # Literal ou Curinga ('@')
            s = State(c)
            stack.append(Fragment(s, [(s, 'out1')]))

    if not stack:
        # Expressão vazia
        s = State()
        return Fragment(s, [(s, 'out1')])

    e = stack.pop()
    matchstate = State()  # Estado de aceitação final
    matchstate.c = 'MATCH'
    for state, attr in e.out:
        if attr == 'out1': state.out1 = matchstate
        elif attr == 'out2': state.out2 = matchstate

    return e.start

# --- 4. Simulador NFA (Busca e Epsilon-Closure) ---

class RegexEngine:
    def __init__(self, pattern):
        self.pattern = pattern
        self.start_state = compile_nfa_direct(pattern)
        self.list_id = 0

    def _add_state(self, s, l_list):
        if s is None or s.last_list == self.list_id:
            return
        s.last_list = self.list_id
        # Se for estado epsilon (sem caractere de transição ou ramificação), adiciona recursivamente
        if s.c is None or s.c == 'MATCH' or (len(s.c) == 1 and ord(s.c) == 0):
            # Transições epsilon puras (out1 e out2 quando não consomem caractere)
            # Na construção de Thompson, estados com c=None ou estados de ramificação têm out1/out2 como epsilon.
            pass

        # Vamos implementar o epsilon closure padrão:
        if s.out1 and (s.c is None or s.c == 'MATCH'):
            # Se for transição epsilon, segue
            pass

    def match(self, text):
        """Verifica correspondência exata (ancorada no início e fim)."""
        return self._search_internal(text, anchored=True)

    def search(self, text):
        """Realiza busca em texto (não ancorada, encontra em qualquer posição)."""
        return self._search_internal(text, anchored=False)

    def _search_internal(self, text, anchored=False):
        # Simulação NFA por conjuntos de estados ativos (Thompson's algorithm)
        current_states = []
        next_states = []

        def add_state(s, clist):
            if s is None or s.last_list == self.list_id:
                return
            s.last_list = self.list_id
            if s.c is None:  # Estado puramente epsilon
                if s.out1: add_state(s.out1, clist)
                if s.out2: add_state(s.out2, clist)
            else:
                clist.append(s)

        # Se busca não ancorada, adicionamos opcionalmente um prefixo .* implícito ou testamos todas as posições
        # A forma mais elegante de busca não ancorada em NFA é adicionar um estado inicial que aceita qualquer caractere repetidamente antes do NFA.
        if not anchored:
            # Criamos um NFA envelopado com .* antes
            pass

        # Para garantir robustez na busca não ancorada sem recompilar, podemos testar a correspondência a partir de cada índice do texto
        if not anchored:
            for i in range(len(text) + 1):
                if self._run_nfa(text[i:]):
                    return True
            return False
        else:
            return self._run_nfa(text)

    def _run_nfa(self, text):
        self.list_id += 1
        current = []
        
        # Adiciona estado inicial e seu epsilon-closure
        def add_state(s, clist):
            if s is None or s.last_list == self.list_id:
                return
            s.last_list = self.list_id
            if s.c is None or s.c == 'MATCH':
                if s.out1: add_state(s.out1, clist)
                if s.out2: add_state(s.out2, clist)
            else:
                clist.append(s)

        add_state(self.start_state, current)

        for c in text:
            self.list_id += 1
            next_list = []
            for s in current:
                # Verifica se o estado consome o caractere c (literal ou curinga '@')
                matches = False
                if s.c == c:
                    matches = True
                elif s.c == '@': # Curinga
                    matches = True
                
                if matches:
                    add_state(s.out1, next_list)
            current = next_list

        # Verifica se algum estado final (MATCH) está ativo
        for s in current:
            if s.c == 'MATCH':
                return True
        return False

# --- 5. Suíte de Testes Automatizados (25+ testes) ---

def run_tests():
    tests = [
        # Literais básicos
        ("abc", "abc", True),
        ("abc", "ab", False),
        ("hello", "hello", True),
        ("hello", "world", False),
        
        # Operador Curinga (.)
        ("a.c", "abc", True),
        ("a.c", "axc", True),
        ("a.c", "ac", False),
        ("...", "foo", True),
        
        # Operador Alternância (|)
        ("a|b", "a", True),
        ("a|b", "b", True),
        ("a|b", "c", False),
        ("cat|dog", "cat", True),
        ("cat|dog", "dog", True),
        ("cat|dog", "bat", False),
        
        # Fecho de Kleene (*)
        ("a*", "", True),
        ("a*", "aaa", True),
        ("a*", "b", False),
        ("ab*c", "ac", True),
        ("ab*c", "abc", True),
        ("ab*c", "abbbbbc", True),
        ("ab*c", "abbbcde", False),
        
        # Combinações complexas
        ("a(b|c)*d", "ad", True),
        ("a(b|c)*d", "abbbcd", True),
        ("a(b|c)*d", "accbffd", False),
        
        # Testes de Busca em Texto (Não ancorada)
        ("abc", "xxabcxx", True),
        ("a.c", "start axc end", True),
    ]

    passed = 0
    start_time_total = time.time()
    
    for idx, (pattern, text, expected) in enumerate(tests):
        t0 = time.time()
        engine = RegexEngine(pattern)
        result = engine.search(text)
        t1 = time.time()
        
        duration_ms = (t1 - t0) * 1000
        assert duration_ms < 5.0, f"Teste {idx} excedeu o limite de 5ms ({duration_ms:.2f}ms)"
        
        if result == expected:
            passed += 1
        else:
            print(f"FALHA no teste {idx}: pattern='{pattern}', text='{text}' (Esperado: {expected}, Obtido: {result})")
            
    total_time_ms = (time.time() - start_time_total) * 1000
    print(f"\nResultados: {passed}/{len(tests)} testes passaram com sucesso!")
    print(f"Tempo total da suíte: {total_time_ms:.2f}ms (Média por busca: {total_time_ms/len(tests):.4f}ms)")
    
    # --- Demonstração de Busca em Texto vs Correspondência Ancorada ---
    print("\n[Verificação de Busca em Texto vs Ancorada]")
    eng = RegexEngine("abc")
    print(f"Busca 'abc' em 'xyzabcdef': search() = {eng.search('xyzabcdef')}, match() = {eng.match('xyzabcdef')}")
    assert eng.search("xyzabcdef") == True, "Busca em texto falhou."
    assert eng.match("xyzabcdef") == False, "Match ancorado incorreto."

    # --- Ataque ao Equívoco Comum: Cadeias Longas NFA ---
    print("\n[Contraexemplo de Equívoco Comum]")
    complex_pat = "a(b|c)*d"
    complex_txt = "a" + "b" * 300 + "d"
    
    t0 = time.time()
    res = RegexEngine(complex_pat).search(complex_txt)
    t1 = time.time()
    print(f"Resultado para string de repetição longa (302 chars): {res} em {(t1 - t0)*1000:.2f}ms")
    assert res == True, "Falha no reconhecimento de repetição longa via NFA."
    print("SUCESSO: O NFA processou cadeias longas eficientemente.")

if __name__ == "__main__":
    run_tests()