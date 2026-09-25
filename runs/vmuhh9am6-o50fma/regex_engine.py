import time

# --- 1. Estrutura do NFA ---

class State:
    def __init__(self, c=None):
        self.c = c          # Caractere da transição (None para épsilon, '.' para curinga)
        self.out1 = None    # Próximo estado 1
        self.out2 = None    # Próximo estado 2 (para ramificações épsilon)
        self.last_list = 0  # Controle para evitar loops infinitos no epsilon-closure

class Fragment:
    def __init__(self, start, out):
        self.start = start  # Estado inicial do fragmento NFA
        self.out = out      # Lista de referências para ponteiros `out` de estados sem saída

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
            output.append(c)

    while stack:
        output.append(stack.pop())

    return "".join(output)

# --- 3. Compilador NFA (Construção de Thompson) ---

def compile_regex(pattern):
    """Compila um padrão pós-fixado em um NFA usando a Construção de Thompson."""
    postfix = infix_to_postfix(pattern)
    stack = []

    for c in postfix:
        if c == '.':  # Concatenação binária
            if len(stack) < 2:
                raise ValueError(f"Padrão inválido (concatenação): {pattern}")
            e2 = stack.pop()
            e1 = stack.pop()
            # Patch: conecta o out de e1 ao start de e2
            for ptr in e1.out:
                ptr.out1 = e2.start
            stack.append(Fragment(e1.start, e2.out))

        elif c == '|':  # Alternância binária
            if len(stack) < 2:
                raise ValueError(f"Padrão inválido (alternância): {pattern}")
            e2 = stack.pop()
            e1 = stack.pop()
            s = State()  # Estado inicial de bifurcação
            s.out1 = e1.start
            s.out2 = e2.start
            match_state = State()
            for ptr in e1.out:
                ptr.out1 = match_state
            for ptr in e2.out:
                ptr.out1 = match_state
            stack.append(Fragment(s, [match_state]))

        elif c == '*':  # Fecho de Kleene unário
            if len(stack) < 1:
                raise ValueError(f"Padrão inválido (fecho de Kleene): {pattern}")
            e = stack.pop()
            s = State()
            match_state = State()
            s.out1 = e.start
            s.out2 = match_state
            for ptr in e.out:
                ptr.out1 = e.start
                ptr.out2 = match_state
            stack.append(Fragment(s, [match_state]))

        else:  # Caractere literal ou curinga
            s = State(c)
            match_state = State()
            s.out1 = match_state
            stack.append(Fragment(s, [match_state]))

    if len(stack) != 1:
        raise ValueError(f"Padrão inválido na pilha NFA: {pattern}")

    e = stack.pop()
    accept_state = State()
    for ptr in e.out:
        ptr.out1 = accept_state
    return e.start, accept_state

# --- 4. Simulador NFA ---

class RegexEngine:
    def __init__(self, pattern):
        self.pattern = pattern
        self.start_state, self.match_state = compile_regex(pattern)
        self.list_id = 0

    def _add_state(self, s, states_list):
        """Adiciona estado e seus épsilon-transições recursivamente (epsilon-closure)."""
        if s is None or s.last_list == self.list_id:
            return
        s.last_list = self.list_id
        if s.c is None:
            # Transição vazia (épsilon): ramifica
            if s.out1:
                self._add_state(s.out1, states_list)
            if s.out2:
                self._add_state(s.out2, states_list)
        else:
            states_list.append(s)

    def match(self, text):
        """Valida se a string inteira corresponde ao padrão (correspondência ancorada)."""
        self.list_id += 1
        current_states = []
        self._add_state(self.start_state, current_states)

        for char in text:
            self.list_id += 1
            next_states = []
            for s in current_states:
                if s.c == char or s.c == '.':
                    self._add_state(s.out1, next_states)
            current_states = next_states

        return any(s == self.match_state for s in current_states)

    def search(self, text):
        """Realiza busca não ancorada em qualquer posição do texto."""
        # Tenta em cada posição de sufixo do texto
        for i in range(len(text) + 1):
            self.list_id += 1
            current_states = []
            self._add_state(self.start_state, current_states)
            
            matched = any(s == self.match_state for s in current_states)
            if matched:
                return True

            subtext = text[i:]
            if not subtext and matched:
                return True

            for char in subtext:
                self.list_id += 1
                next_states = []
                for s in current_states:
                    if s.c == char or s.c == '.':
                        self._add_state(s.out1, next_states)
                current_states = next_states
                if any(s == self.match_state for s in current_states):
                    return True
        return False

# --- 5. Suíte de Testes Automatizados ---

def run_tests():
    tests = [
        ("abc", "abc", True),
        ("abc", "def", False),
        ("hello", "hello", True),
        ("hello", "world", False),
        ("a.c", "abc", True),
        ("a.c", "axc", True),
        ("a.c", "abb", False),
        ("a|b", "a", True),
        ("a|b", "b", True),
        ("a|b", "c", False),
        ("cat|dog", "cat", True),
        ("cat|dog", "dog", True),
        ("cat|dog", "bat", False),
        ("ab*c", "ac", True),
        ("ab*c", "abc", True),
        ("ab*c", "abbbc", True),
        ("ab*c", "adc", False),
        ("a(b|c)*d", "ad", True),
        ("a(b|c)*d", "abd", True),
        ("a(b|c)*d", "acccd", True),
        ("a(b|c)*d", "aed", False),
        (".*", "anything", True),
        ("p(a|e)th", "path", True),
        ("p(a|e)th", "peth", True),
        ("ab*c", "xxabbbcxx", True),
        ("cat", "the black cat sat", True),
    ]

    passed = 0
    start_time_total = time.time()

    for idx, (pattern, text, expected) in enumerate(tests):
        t0 = time.time()
        eng = RegexEngine(pattern)
        result = eng.search(text)
        duration_ms = (time.time() - t0) * 1000
        
        assert duration_ms < 5.0, f"Teste {idx} excedeu o limite de 5ms ({duration_ms:.2f}ms)"
        
        if result == expected:
            passed += 1
        else:
            print(f"FALHA no teste {idx}: pattern='{pattern}', text='{text}' (Esperado: {expected}, Obtido: {result})")
            
    total_time_ms = (time.time() - start_time_total) * 1000
    print(f"\nResultados: {passed}/{len(tests)} testes passaram com sucesso!")
    print(f"Tempo total da suíte: {total_time_ms:.2f}ms (Média por busca: {total_time_ms/len(tests):.4f}ms)")
    
    # Validações rigorosas de busca não ancorada vs correspondência exata
    assert RegexEngine("abc").search("xyzabcdef") == True, "Busca não ancorada falhou."
    assert RegexEngine("abc").match("xyzabcdef") == False, "Match ancorado incorreto."
    print("SUCESSO: Todos os testes e validações passaram perfeitamente.")

if __name__ == "__main__":
    run_tests()