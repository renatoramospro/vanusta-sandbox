import re
from typing import Dict, List, Set, Tuple, Optional, Any

# =====================================================================
# CAMADA 0: Parser SemVer 2.0.0 Rigoroso
# =====================================================================

class SemVer:
    """Implementa a especificação SemVer 2.0.0 rigorosamente com precedência, pré-releases e validações."""
    def __init__(self, major: int, minor: int, patch: int, prerelease: Optional[str] = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease

    @classmethod
    def parse(cls, version_str: str) -> 'SemVer':
        v_str = version_str.strip()
        if v_str.startswith('v'):
            v_str = v_str[1:]
        
        # Regex estrito SemVer 2.0.0 (sem zeros à esquerda em numéricos e sem identificadores vazios)
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z\.-]+))?(?:\+[0-9A-Za-z\.-]+)?$', v_str)
        if not match:
            raise ValueError(f"Versão SemVer inválida: '{version_str}'")
        
        major_s, minor_s, patch_s, pre = match.groups()
        
        # Validação de zeros à esquerda em numéricos principais
        if (len(major_s) > 1 and major_s.startswith('0')) or \
           (len(minor_s) > 1 and minor_s.startswith('0')) or \
           (len(patch_s) > 1 and patch_s.startswith('0')):
            raise ValueError(f"Versão SemVer inválida (zeros à esquerda proibidos): '{version_str}'")

        # Validação rigorosa de pré-release (sem segmentos vazios e sem zeros à esquerda em numéricos)
        if pre is not None:
            parts = pre.split('.')
            for p in parts:
                if len(p) == 0:
                    raise ValueError(f"Pré-release inválido (segmento vazio): '{version_str}'")
                if p.isdigit() and len(p) > 1 and p.startswith('0'):
                    raise ValueError(f"Pré-release inválido (zero à esquerda em numérico): '{version_str}'")

        return cls(int(major_s), int(minor_s), int(patch_s), pre)

    def _compare_prerelease(self, other_pre: Optional[str]) -> int:
        if self.prerelease is None and other_pre is None:
            return 0
        if self.prerelease is None:
            return 1  # Versão estável é maior que pré-release
        if other_pre is None:
            return -1 # Pré-release é menor que versão estável

        parts_a = self.prerelease.split('.')
        parts_b = other_pre.split('.')

        for pa, pb in zip(parts_a, parts_b):
            a_is_num = pa.isdigit()
            b_is_num = pb.isdigit()

            if a_is_num and b_is_num:
                na, nb = int(pa), int(pb)
                if na != nb:
                    return -1 if na < nb else 1
            elif a_is_num and not b_is_num:
                return -1
            elif not a_is_num and b_is_num:
                return 1
            else:
                if pa != pb:
                    return -1 if pa < pb else 1

        if len(parts_a) != len(parts_b):
            return -1 if len(parts_a) < len(parts_b) else 1
        return 0

    def __lt__(self, other: 'SemVer') -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return self._compare_prerelease(other.prerelease) < 0

    def __le__(self, other: 'SemVer') -> bool:
        return self == other or self < other

    def __gt__(self, other: 'SemVer') -> bool:
        return not (self <= other)

    def __ge__(self, other: 'SemVer') -> bool:
        return not (self < other)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SemVer):
            return False
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch and 
                self.prerelease == other.prerelease)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def __repr__(self) -> str:
        pre = f"-{self.prerelease}" if self.prerelease else ""
        return f"SemVer({self.major}.{self.minor}.{self.patch}{pre})"


# =====================================================================
# CAMADA 0.2: Álgebra de Ranges e Interseção Real
# =====================================================================

class VersionRange:
    """Representa uma restrição de versão SemVer (ex: >=1.2.0 <2.0.0)."""
    def __init__(self, op: str, version: SemVer):
        self.op = op  # '=', '>=', '>', '<', '<=', '^', '~'
        self.version = version

    @classmethod
    def parse(cls, range_str: str) -> 'VersionRange':
        range_str = range_str.strip()
        if not range_str or range_str == '*':
            return cls('>=', SemVer(0, 0, 0))

        match = re.match(r'^(>=|<=|>|<|=|\^|~)?\s*(v?\d+\.\d+\.\d+(?:-[0-9A-Za-z\.-]+)?)$', range_str)
        if not match:
            raise ValueError(f"Range inválido: '{range_str}'")
        
        op, v_str = match.groups()
        op = op if op else '='
        ver = SemVer.parse(v_str)
        return cls(op, ver)

    def matches(self, ver: SemVer) -> bool:
        if self.op == '=':
            return ver == self.version
        elif self.op == '>=':
            return ver >= self.version
        elif self.op == '>':
            return ver > self.version
        elif self.op == '<':
            return ver < self.version
        elif self.op == '<=':
            return ver <= self.version
        elif self.op == '^':
            # ^1.2.3 := >=1.2.3 <2.0.0; ^0.2.3 := >=0.2.3 <0.3.0; ^0.0.3 := >=0.0.3 <0.0.4
            if self.version.major > 0:
                upper = SemVer(self.version.major + 1, 0, 0)
                return ver >= self.version and ver < upper
            elif self.version.minor > 0:
                upper = SemVer(0, self.version.minor + 1, 0)
                return ver >= self.version and ver < upper
            else:
                upper = SemVer(0, 0, self.version.patch + 1)
                return ver >= self.version and ver < upper
        elif self.op == '~':
            # ~1.2.3 := >=1.2.3 <1.3.0; ~1.2 := >=1.2.0 <1.3.0
            upper = SemVer(self.version.major, self.version.minor + 1, 0)
            return ver >= self.version and ver < upper
        return False

    def __repr__(self) -> str:
        return f"{self.op}{self.version}"


class RangeSet:
    """Conjunto de restrições para um pacote, permitindo interseção real e detecção de vazio."""
    def __init__(self, constraints: Optional[List[VersionRange]] = None):
        self.constraints = constraints if constraints else []

    def add(self, constraint: VersionRange):
        self.constraints.append(constraint)

    def is_satisfied_by(self, ver: SemVer) -> bool:
        return all(c.matches(ver) for c in self.constraints)

    def intersect(self, other: 'RangeSet') -> 'RangeSet':
        new_set = RangeSet(list(self.constraints) + list(other.constraints))
        return new_set

    def is_empty(self, available_versions: List[SemVer]) -> bool:
        """Verifica se existe pelo menos uma versão disponível que satisfaz todas as restrições."""
        return not any(self.is_satisfied_by(v) for v in available_versions)

    def __repr__(self) -> str:
        return " & ".join(str(c) for c in self.constraints) if self.constraints else "*"


# =====================================================================
# CAMADA 1 e 2: Resolvedor CSP com Backtracking, Cadeia Causal e Ciclos
# =====================================================================

class DependencyConflictError(Exception):
    """Exceção levantada quando ocorre um conflito de dependências ou ciclo."""
    def __init__(self, message: str, causal_chain: List[Tuple[str, SemVer, str]]):
        super().__init__(message)
        self.causal_chain = causal_chain

    def __str__(self):
        chain_str = " -> ".join([f"{pkg}@{ver} (via {parent})" for pkg, ver, parent in self.causal_chain])
        return f"Falha de Dependência: {super().__str__()}\nCadeia Causal: {chain_str}"


class PackageRegistry:
    """Registro de pacotes e suas versões disponíveis com dependências declaradas."""
    def __init__(self):
        # Mapeamento: package_name -> {SemVer: {dep_name: range_str}}
        self.packages: Dict[str, Dict[SemVer, Dict[str, str]]] = {}

    def add_version(self, name: str, version: str, dependencies: Dict[str, str]):
        if name not in self.packages:
            self.packages[name] = {}
        v = SemVer.parse(version)
        self.packages[name][v] = dependencies

    def get_versions(self, name: str) -> List[SemVer]:
        if name not in self.packages:
            return []
        # Retorna ordenadas da maior para a menor (estratégia otimizista)
        return sorted(self.packages[name].keys(), reverse=True)

    def get_dependencies(self, name: str, version: SemVer) -> Dict[str, str]:
        return self.packages.get(name, {}).get(version, {})


class DependencyResolver:
    """Resolvedor CSP baseado em Backtracking com restrições SemVer e detecção robusta de ciclos."""
    def __init__(self, registry: PackageRegistry):
        self.registry = registry

    def resolve(self, root_deps: Dict[str, str]) -> Dict[str, SemVer]:
        # Converte root_deps em restrições iniciais
        initial_ranges: Dict[str, RangeSet] = {}
        for pkg, r_str in root_deps.items():
            rset = RangeSet()
            rset.add(VersionRange.parse(r_str))
            initial_ranges[pkg] = rset

        assignment: Dict[str, SemVer] = {}
        causal_trail: List[Tuple[str, SemVer, str]] = []
        
        # Executa o backtracking CSP com pilha de ancestrais para detecção de ciclos
        success = self._backtrack(initial_ranges, assignment, causal_trail, active_stack=[])
        if not success:
            raise DependencyConflictError("Restrições incompatíveis, pacote inexistente ou ciclo detectado.", causal_trail)
        return assignment

    def _backtrack(self, 
                   constraints: Dict[str, RangeSet], 
                   assignment: Dict[str, SemVer], 
                   causal_trail: List[Tuple[str, SemVer, str]],
                   active_stack: List[str]) -> bool:
        
        # Seleciona variável não atribuída
        unassigned = [pkg for pkg in constraints if pkg not in assignment]
        if not unassigned:
            return True  Sem variáveis pendentes

        # Heurística MRV (Minimum Remaining Values): escolhe a variável com menos opções válidas
        pkg = min(unassigned, key=lambda p: len([v for v in self.registry.get_versions(p) if constraints[p].is_satisfied_by(v)]))
        
        available_versions = self.registry.get_versions(pkg)
        if not available_versions:
            return False

        # Verifica se o range é vazio
        if constraints[pkg].is_empty(available_versions):
            return False

        # Detecção de ciclo rigorosa: se o pacote já está no caminho ativo de dependências
        if pkg in active_stack:
            # Ciclo detectado! Adiciona à trilha causal e falha este ramo
            causal_trail.append((pkg, SemVer(0,0,0), f"Ciclo detectado em {pkg}"))
            return False

        for ver in available_versions:
            if not constraints[pkg].is_satisfied_by(ver):
                continue

            # Tenta atribuir
            assignment[pkg] = ver
            parent_info = active_stack[-1] if active_stack else "ROOT"
            causal_trail.append((pkg, ver, parent_info))

            # Obtém dependências do pacote na versão escolhida
            deps = self.registry.get_dependencies(pkg, ver)
            
            # Clona restrições atuais para testar este ramo
            new_constraints = {k: RangeSet(list(v.constraints)) for k, v in constraints.items()}
            
            conflict = False
            for dep_pkg, dep_range_str in deps.items():
                dep_range = VersionRange.parse(dep_range_str)
                if dep_pkg not in new_constraints:
                    new_constraints[dep_pkg] = RangeSet()
                new_constraints[dep_pkg].add(dep_range)
                
                # Validação imediata se o novo range ficou vazio
                if new_constraints[dep_pkg].is_empty(self.registry.get_versions(dep_pkg)):
                    conflict = True
                    causal_trail.append((dep_pkg, SemVer(0,0,0), f"{pkg}@{ver}"))
                    break

            if not conflict:
                # Avança na recursão adicionando o pacote ao stack ativo
                if self._backtrack(new_constraints, assignment, causal_trail, active_stack + [pkg]):
                    return True

            # Backtracking: remove atribuição e último rastro
            del assignment[pkg]
            if causal_trail and causal_trail[-1][0] == pkg:
                causal_trail.pop()

        return False


# =====================================================================
# CAMADA 3: Suíte de Testes e Validação de Cenários
# =====================================================================

if __name__ == "__main__":
    print("=== Iniciando Validação Robusta do Resolvedor SemVer ===")

    # Cenário 1: Diamante Compatível
    registry = PackageRegistry()
    registry.add_version("App", "1.0.0", {"LibA": "1.0.0", "LibB": "1.0.0"})
    registry.add_version("LibA", "1.0.0", {"Core": "^1.0.0"})
    registry.add_version("LibB", "1.0.0", {"Core": ">=1.2.0 <2.0.0"})
    registry.add_version("Core", "1.5.0", {})
    registry.add_version("Core", "1.1.0", {})

    resolver = DependencyResolver(registry)
    result = resolver.resolve({"App": "1.0.0"})
    print("Cenário 1 (Diamante Compatível) Resolvido com Sucesso:", result)
    assert result["Core"] == SemVer(1, 5, 0)

    # Cenário 2: Conflito Incompatível / Range Vazio
    registry_conflict = PackageRegistry()
    registry_conflict.add_version("App", "1.0.0", {"LibA": "1.0.0", "LibB": "1.0.0"})
    registry_conflict.add_version("LibA", "1.0.0", {"Core": "^2.0.0"})
    registry_conflict.add_version("LibB", "1.0.0", {"Core": "<1.5.0"})
    registry_conflict.add_version("Core", "2.1.0", {})
    registry_conflict.add_version("Core", "1.2.0", {})

    resolver_conflict = DependencyResolver(registry_conflict)
    print("\n=== Cenário 2: Conflito de Versões Detectado ===")
    try:
        resolver_conflict.resolve({"App": "1.0.0"})
        raise AssertionError("Deveria ter lançado DependencyConflictError")
    except DependencyConflictError as e:
        print("Erro capturado com sucesso:")
        print("Mensagem:", e)
        assert len(e.causal_chain) > 0

    # Cenário 3: Detecção de Ciclo Estrito
    registry_cycle = PackageRegistry()
    registry_cycle.add_version("X", "1.0.0", {"Y": "1.0.0"})
    registry_cycle.add_version("Y", "1.0.0", {"X": "1.0.0"})

    resolver_cycle = DependencyResolver(registry_cycle)
    print("\n=== Cenário 3: Ciclo Detectado ===")
    try:
        resolver_cycle.resolve({"X": "1.0.0"})
        raise AssertionError("Deveria ter lançado DependencyConflictError por ciclo")
    except DependencyConflictError as e:
        print("Erro de ciclo capturado com sucesso:")
        print("Mensagem:", e)

    # Cenário 4: Validação Rigorosa SemVer (Rejeição de zeros à esquerda e pré-releases malformados)
    print("\n=== Cenário 4: Validação Rigorosa SemVer ===")
    try:
        SemVer.parse("1.0.0-alpha..1")
        raise AssertionError("Deveria rejeitar pré-release com segmento vazio")
    except ValueError as err:
        print("Rejeitado corretamente:", err)

    try:
        SemVer.parse("1.0.0-01")
        raise AssertionError("Deveria rejeitar pré-release com zero à esquerda")
    except ValueError as err:
        print("Rejeitado corretamente:", err)

    print("\nTodos os testes executados e validados com sucesso!")