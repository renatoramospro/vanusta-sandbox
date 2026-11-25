import collections

# --- Estruturas de Dados ---

class TypeVar:
    """Representa uma variável de tipo (ex: alpha)."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, TypeVar) and self.name == other.name
    def __hash__(self):
        return hash(self.name)

class Type:
    """Classe base para tipos."""
    def __repr__(self):
        return str(self)
    def __eq__(self, other):
        return isinstance(other, self.__class__) and str(self) == str(other)

class TVar(Type):
    """Variável de tipo (alpha)."""
    def __init__(self, name):
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
    """Verifica se a variável de tipo tv ocorre em type_expr."""
    if isinstance(type_expr, TVar):
        return tv == type_expr
    elif isinstance(type_expr, TFun):
        return occurs_check(tv, type_expr.arg) or occurs_check(tv, type_expr.result)
    return False

def substitute(subst: dict, type_expr: Type) -> Type:
    """Aplica uma substituição (mapeamento de TVar -> Type) a um tipo."""
    if isinstance(type_expr, TVar):
        return subst.get(type_expr.name, type_expr)
    elif isinstance(type_expr, TFun):
        return TFun(substitute(subst, type_expr.arg), substitute(subst, type_expr.result))
    return type_expr

def unify(t1: Type, t2: Type, subst: dict) -> dict:
    """
    Tenta unificar t1 e t2, retornando o novo mapeamento de substituição.
    Levanta ValueError se a unificação falhar.
    """
    t1 = substitute(subst, t1)
    t2 = substitute(subst, t2)

    if isinstance(t1, TVar):
        if occurs_check(t1, t2):
            raise ValueError("Occurs Check Failed: Cyclic type detected.")
        subst[t1.name] = t2
        return subst
    elif isinstance(t2, TVar):
        # Já tratamos t1=TVar, então t2 deve ser TVar ou TFun. Se for TVar, é tratado acima.
        if occurs_check(t2, t1):
            raise ValueError("Occurs Check Failed: Cyclic type detected.")
        subst[t2.name] = t1
        return subst
    elif isinstance(t1, TFun) and isinstance(t2, TFun):
        # Unifica argumentos e resultados recursivamente
        subst = unify(t1.arg, t2.arg, subst)
        subst = unify(t1.result, t2.result, subst)
        return subst
    else:
        # Tipos concretos ou incompatíveis
        if str(t1) == str(t2):
            return subst
        raise ValueError(f"Unification failed: {t1} != {t2}")

def generalize(type_expr: Type, free_vars: set) -> Type:
    """Generaliza um tipo, quantificando sobre variáveis livres que não estão no contexto."""
    # Em um sistema real, precisaríamos do contexto de variáveis livres do ambiente.
    # Aqui, assumimos que 'free_vars' são as variáveis livres *no escopo atual* que devem ser quantificadas.
    # Para simplificar o teste, se o tipo não tiver TVars, retorna ele mesmo.
    # Em um ambiente completo, seria: {∀α. T | α ∈ free_vars ∩ context_vars}
    return type_expr

def instantiate(type_expr: Type, fresh_tv_gen: callable) -> Type:
    """Instancia um tipo, substituindo cada TVar por uma nova TVar fresca."""
    if isinstance(type_expr, TVar):
        return fresh_tv_gen()
    elif isinstance(type_expr, TFun):
        return TFun(instantiate(type_expr.arg, fresh_tv_gen), instantiate(type_expr.result, fresh_tv_gen))
    return type_expr

# --- Simulação do Lambda-Cálculo (Estrutura mínima) ---

# Representação simplificada de expressões para inferência
class Expr:
    def __init__(self, type_info=None):
        self.type = type_info
    def __repr__(self):
        return f"Expr({self.type})"

# Exemplo de expressão: λx. x (Função de ordem superior)
# Para este experimento, vamos focar na lógica de tipos, não na AST completa.

# --- Teste de Conceito: Let-Polimorfismo e Occurs-Check ---

def test_occurs_check_success():
    """Testa ocorre_check em um caso simples (não cíclico)."""
    tv = TVar('a')
    t = TFun(TVar('b'), TVar('c'))
    assert not occurs_check(tv, t)
    print("Teste Occurs Check (Sucesso Simples): OK")

def test_occurs_check_failure():
    """Testa ocorre_check em um caso cíclico (deve ser True)."""
    tv = TVar('a')
    # Representação de TFun(TVar('a'), ...)
    t = TFun(tv, TVar('b'))
    assert occurs_check(tv, t)
    print("Teste Occurs Check (Falha Cíclica): OK")

def test_unification_success():
    """Testa unificação bem-sucedida."""
    t1 = TVar('a')
    t2 = TFun(TVar('b'), TVar('c'))
    subst = {}
    new_subst = unify(t1, t2, subst)
    # Espera-se que 'a' seja unificado com TFun(TVar('b'), TVar('c'))
    assert new_subst['a'].__str__() == "TVar('b') -> TVar('c')"
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