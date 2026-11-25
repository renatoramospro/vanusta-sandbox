import collections

# --- Estruturas de Dados ---

class TypeVar:
    """Representa uma variável de tipo (ex: alpha). Usa ID único para robustez."""
    _id_counter = 0
    def __init__(self, name=None):
        if name is None:
            self.id = TypeVar._id_counter
            TypeVar._id_counter += 1
            self.name = f"t{self.id}"
        else:
            self.name = name
            self.id = hash(name) # Simplificação para testes, mas o ID único é crucial
    def __repr__(self):
        return f"TVar('{self.name}')"
    def __eq__(self, other):
        return isinstance(other, TypeVar) and self.id == other.id
    def __hash__(self):
        return hash(self.id)

class Type:
    """Classe base para tipos."""
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        # Comparação robusta baseada em representação canônica
        return isinstance(other, self.__class__) and str(self) == str(other)

class TVar(Type):
    """Variável de tipo (alpha)."""
    def __init__(self, name=None):
        super().__init__()
        self.name = name
    def __str__(self):
        return self.name
    def __repr__(self):
        return f"TVar('{self.name}')"

class TFun(Type):
    """Tipo funcional: T1 -> T2."""
    def __init__(self, arg, result):
        self.arg = arg
        self.result = result
    def __str__(self):
        return f"{self.arg} -> {self.result}"
    def __repr__(self):
        return f"TFun({self.arg}, {self.result})"

# --- Utilitários de Tipos ---

def occurs_check(tv: TVar, type_expr: Type) -> bool:
    """Verifica se a variável de tipo tv ocorre em type_expr. Fail-closed."""
    if isinstance(type_expr, TVar):
        return tv == type_expr
    elif isinstance(type_expr, TFun):
        # Recursão segura, pois a estrutura é finita (TFun)
        return occurs_check(tv, type_expr.arg) or occurs_check(tv, type_expr.result)
    # Fail-closed: se não for TVar ou TFun, não ocorre.
    return False

def substitute(subst: dict, type_expr: Type) -> Type:
    """Aplica uma substituição (mapeamento de TVar -> Type) a um tipo (imutável)."""
    if isinstance(type_expr, TVar):
        # Retorna a substituição se existir, senão o próprio TVar
        return subst.get(type_expr.name, type_expr)
    elif isinstance(type_expr, TFun):
        # Aplica recursivamente a ambos os lados
        return TFun(substitute(subst, type_expr.arg), substitute(subst, type_expr.result))
    return type_expr

def unify(t1: Type, t2: Type, subst: dict) -> dict:
    """
    Unifica t1 e t2, retornando um NOVO dicionário de substituição.
    Usa worklist para evitar recursão profunda e mutação in-place.
    """
    # Cria uma cópia do estado de substituição para garantir imutabilidade em caso de falha
    current_subst = subst.copy()
    
    # Worklist: lista de pares (t1, t2) a serem unificados
    worklist = collections.deque([(t1, t2)])

    while worklist:
        a, b = worklist.popleft()
        
        # Aplica substituições pendentes antes de comparar
        a_sub = substitute(current_subst, a)
        b_sub = substitute(current_subst, b)

        if a_sub == b_sub:
            continue
        
        if isinstance(a_sub, TVar) and isinstance(b_sub, TVar):
            if a_sub == b_sub:
                continue
            # Adiciona a nova unificação à worklist para processamento posterior
            worklist.append((a_sub, b_sub))
            continue
        
        if isinstance(a_sub, TVar):
            # Caso 1: a_sub é TVar. Verifica ocorre_check.
            if occurs_check(a_sub, b_sub):
                raise ValueError("Occurs Check Failed: Cyclic type detected.")
            # Nova substituição: a_sub -> b_sub
            current_subst[a_sub.name] = b_sub
            # Re-processar a worklist com a nova substituição aplicada a todos os elementos restantes
            # Simplificação: re-enfileirar os pares pendentes para que a substituição seja propagada
            # Em um sistema completo, isso seria feito de forma mais eficiente, mas para robustez, re-enfileiramos.
            # Aqui, apenas re-enfileiramos o par atual para que a substituição seja aplicada no próximo loop.
            worklist.append((a_sub, b_sub))
            continue

        if isinstance(b_sub, TVar):
            # Caso 2: b_sub é TVar. Verifica ocorre_check.
            if occurs_check(b_sub, a_sub):
                raise ValueError("Occurs Check Failed: Cyclic type detected.")
            # Nova substituição: b_sub -> a_sub
            current_subst[b_sub.name] = a_sub
            worklist.append((a_sub, b_sub))
            continue

        if isinstance(a_sub, TFun) and isinstance(b_sub, TFun):
            # Caso 3: Ambos são funções. Unificar argumentos e resultados sequencialmente.
            # Adiciona os sub-problemas à worklist
            worklist.append((a_sub.arg, b_sub.arg))
            worklist.append((a_sub.result, b_sub.result))
            continue
        
        # Caso 4: Tipos incompatíveis (ex: TFun vs TVar)
        raise TypeError(f"Cannot unify incompatible types: {a_sub} and {b_sub}")

    return current_subst

# --- Testes ---

def test_occurs_check_success():
    """Teste Occurs Check (Sucesso Simples)."""
    tv = TVar('a')
    t = TFun(TVar('b'), TVar('c'))
    assert occurs_check(tv, t) == False
    print("Teste Occurs Check (Sucesso Simples): OK")

def test_occurs_check_failure():
    """Teste Occurs Check (Falha Cíclica). Deve ser True."""
    tv = TVar('a')
    # Representação de TFun(TVar('a'), ...)
    t = TFun(tv, TVar('b'))
    assert occurs_check(tv, t) == True
    print("Teste Occurs Check (Falha Cíclica): OK")

def test_unification_success():
    """Testa unificação bem-sucedida."""
    t1 = TVar('a')
    t2 = TFun(TVar('b'), TVar('c'))
    subst = {}
    new_subst = unify(t1, t2, subst)
    # CORREÇÃO: Comparar o objeto TFun resultante, não sua string literal esperada.
    expected_type = TFun(TVar('b'), TVar('c'))
    assert new_subst['a'] == expected_type
    print("Teste Unificação (Sucesso): OK")

def test_unification_occurs_check_failure():
    """
    Ataque de propósito: Testa o equívoco comum de que unificação sempre funciona.
    Deve falhar com ValueError devido ao ocorre_check.
    """
    tv = TVar('a')
    # Tentativa de unificar 'a' com TFun(..., 'a')
    t_cyclic = TFun(TVar('b'), tv)
    subst = {}
    try:
        unify(tv, t_cyclic, subst)
        # Se chegou aqui, o ocorre_check falhou
        assert False, "Unificação deveria ter falhado por ocorre_check."
    except ValueError as e:
        assert "Occurs Check Failed" in str(e)
        print("Teste Unificação (Falha Cíclica): OK (Contraexemplo do equívoco)")

# --- Execução do Experimento ---
print("--- Iniciando Experimento de Inferência de Tipos ---")
test_occurs_check_success()
test_occurs_check_failure()
test_unification_success()
test_unification_occurs_check_failure()
print("--- Experimento Concluído com Sucesso (Código 0) ---")