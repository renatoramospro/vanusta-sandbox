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

    def __lt__(self, other: 'SemVer') -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        
        # Regras de pré-release SemVer 2.0.0:
        # Versão sem pré-release é maior que versão com pré-release.
        if self.prerelease is None and other.prerelease is not None:
            return False
        if self.prerelease is not None and other.prerelease is None:
            return True
        if self.prerelease is None and other.prerelease is None:
            return False
        
        # Ambos têm pré-release
        self_parts = self.prerelease.split('.')
        other_parts = other.prerelease.split('.')
        
        for s_part, o_part in zip(self_parts, other_parts):
            s_is_num = s_part.isdigit()
            o_is_num = o_part.isdigit()
            
            if s_is_num and o_is_num:
                s_num, o_num = int(s_part), int(o_part)
                if s_num != o_num:
                    return s_num < o_num
            elif not s_is_num and not o_is_num:
                if s_part != o_part:
                    return s_part < o_part
            else:
                # Numérico tem menor precedência que não-numérico
                return s_is_num
                
        return len(self_parts) < len(other_parts)

    def __le__(self, other: 'SemVer') -> bool:
        return self == other or self < other

    def __gt__(self, other: 'SemVer') -> bool:
        return not (self <= other)

    def __ge__(self, other: 'SemVer') -> bool:
        return not (self < other)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SemVer):
            return False
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)

    def __repr__(self) -> str:
        pre = f"-{self.prerelease}" if self.prerelease else ""
        return f"{self.major}.{self.minor}.{self.patch}{pre}"


# =====================================================================
# CAMADA 0 (Cont.): Álgebra de Ranges e Interseção
# =====================================================================

class Range:
    """Representa uma restrição SemVer (ex: ^1.2.3, >=2.0.0 <3.0.0)."""
    def __init__(self, op: str, version: SemVer):
        self.op = op
        self.version = version

    @classmethod
    def parse(cls, range_str: str) -> List['Range']:
        rs = range_str.strip()
        if not rs or rs == "*":
            return [cls(">=", SemVer(0, 0, 0))]
        
        # Suporte a múltiplos ranges separados por espaço (ex: ">=1.0.0 <2.0.0")
        parts = rs.split()
        ranges = []
        for p in parts:
            matched = False
            for op in ['>=', '<=', '>', '<', '=', '^', '~']:
                if p.startswith(op):
                    v = SemVer.parse(p[len(op):])
                    ranges.append(cls(op, v))
                    matched = True
                    break
            if not matched:
                # Versão exata implícita
                v = SemVer.parse(p)
                ranges.append(cls('=', v))
        return ranges

    def matches(self, v: SemVer) -> bool:
        if self.op == '=':
            return v == self.version
        elif self.op == '>=':
            return v >= self.version
        elif self.op == '<=':
            return v <= self.version
        elif self.op == '>':
            return v > self.version
        elif self.op == '<':
            return v < self.version
        elif self.op == '^':
            # ^1.2.3 := >=1.2.3 <2.0.0
            # ^0.2.3 := >=0.2.3 <0.3.0
            # ^0.0.3 := >=0.0.3 <0.0.4
            maj = self.version.major
            min_v = self.version.minor
            pat = self.version.patch
            
            if maj > 0:
                upper = SemVer(maj + 1, 0, 0)
            elif min_v > 0:
                upper = SemVer(0, min_v + 1, 0)
            else:
                upper = SemVer(0, 0, pat + 1)
            
            return v >= self.version and v < upper
        elif self.op == '~':
            # ~1.2.3 := >=1.2.3 <1.3.0
            # ~1.2 := >=1.2.0 <1.3.0
            maj = self.version.major
            min_v = self.version.minor
            upper = SemVer(maj, min_v + 1, 0)
            return v >= self.version and v < upper
        return False

    def __repr__(self) -> str:
        return f"{self.op}{self.version}"


class RangeSet:
    """Conjunto de ranges aplicados a um pacote, permitindo interseção e teste de vazio."""
    def __init__(self, constraints: Optional[List[Range]] = None):
        self.constraints: List[Range] = constraints if constraints else []

    def add(self, range_str: str) -> None:
        new_ranges = Range.parse(range_str)
        self.constraints.extend(new_ranges)

    def is_satisfied_by(self, v: SemVer) -> bool:
        return all(r.matches(v) for r in self.constraints)

    def is_empty(self, available_versions: List[SemVer]) -> bool:
        """Verifica se existe alguma versão disponível que satisfaz todas as restrições."""
        return not any(self.is_satisfied_by(v) for v in available_versions)

    def __repr__(self) -> str:
        return " ".join(str(r) for r in self.constraints)


# =====================================================================
# Exceção de Conflito Causal
# =====================================================================

class DependencyConflictError(Exception):
    def __init__(self, package: str, message: str, causal_chain: List[str]):
        super().__init__(message)
        self.package = package
        self.causal_chain = causal_chain

    def __str__(self) -> str:
        chain_str = " -> ".join(self.causal_chain)
        return f"Conflito de Dependência em '{self.package}': {self.args[0]}\nCadeia Causal: {chain_str}"


# =====================================================================
# CAMADA 1 & 2: Resolvedor CSP com Backtracking e Detecção de Ciclo
# =====================================================================

class PackageRegistry:
    """Registro simulado de pacotes e suas versões disponíveis com dependências."""
    def __init__(self):
        self.db: Dict[str, Dict[str, Dict[str, str]]] = {}

    def add_version(self, pkg: str, version: str, deps: Dict[str, str]):
        if pkg not in self.db:
            self.db[pkg] = {}
        self.db[pkg][version] = deps

    def get_versions(self, pkg: str) -> List[SemVer]:
        if pkg not in self.db:
            return []
        versions = [SemVer.parse(v) for v in self.db[pkg].keys()]
        # Ordenar da mais recente para a mais antiga (maior precedência primeiro)
        versions.sort(reverse=True)
        return versions

    def get_dependencies(self, pkg: str, version: SemVer) -> Dict[str, str]:
        v_str = str(version)
        if pkg in self.db and v_str in self.db[pkg]:
            return self.db[pkg][v_str]
        return {}


class DependencyResolver:
    """Resolvedor CSP por backtracking com detecção estrita de ciclos e trilha causal."""
    def __init__(self, registry: PackageRegistry):
        self.registry = registry

    def resolve(self, root_deps: Dict[str, str]) -> Dict[str, SemVer]:
        assignment: Dict[str, SemVer] = {}
        constraints: Dict[str, RangeSet] = {}
        
        for pkg, r_str in root_deps.items():
            constraints[pkg] = RangeSet()
            constraints[pkg].add(r_str)

        success, final_assignment, _ = self._backtrack(assignment, constraints, active_path=[])
        if not success:
            raise DependencyConflictError("Raiz", "Não foi possível resolver o conjunto de dependências.", ["App"])
        return final_assignment

    def _backtrack(self, assignment: Dict[str, SemVer], constraints: Dict[str, RangeSet], active_path: List[str]) -> Tuple[bool, Dict[str, SemVer], Optional[str]]:
        # Selecionar próxima variável não resolvida
        unresolved = [pkg for pkg in constraints if pkg not in assignment]
        if not unresolved:
            return True, assignment, None

        pkg = unresolved[0]
        available_versions = self.registry.get_versions(pkg)
        
        if not available_versions:
            return False, assignment, pkg

        # Validar se o RangeSet é vazio para as versões disponíveis
        rset = constraints[pkg]
        if rset.is_empty(available_versions):
            return False, assignment, pkg

        # Tentar versões da maior para a menor (heurística de preferência)
        for version in available_versions:
            if not rset.is_satisfied_by(version):
                continue

            # Clonar estado para testar atribuição
            new_assignment = assignment.copy()
            new_assignment[pkg] = version
            
            new_constraints = {k: RangeSet(list(v.constraints)) for k, v in constraints.items()}
            deps = self.registry.get_dependencies(pkg, version)

            cycle_detected = False
            conflict_pkg = None

            for dep_pkg, dep_range in deps.items():
                # Detecção estrita de ciclos no caminho ativo
                if dep_pkg in active_path:
                    cycle_detected = True
                    conflict_pkg = dep_pkg
                    break

                if dep_pkg not in new_constraints:
                    new_constraints[dep_pkg] = RangeSet()
                
                new_constraints[dep_pkg].add(dep_range)
                
                # Checagem imediata de vazio
                dep_versions = self.registry.get_versions(dep_pkg)
                if new_constraints[dep_pkg].is_empty(dep_versions):
                    conflict_pkg = dep_pkg
                    break

            if cycle_detected:
                chain = active_path + [pkg, conflict_pkg]
                raise DependencyConflictError(conflict_pkg, f"Dependência circular detectada envolvendo '{conflict_pkg}'", chain)

            if conflict_pkg is not None:
                # Falha por range vazio, continuar tentando outras versões
                continue

            # Avançar recursivamente no caminho ativo
            next_active_path = active_path + [pkg]
            success, result_assignment, failed_pkg = self._backtrack(new_assignment, new_constraints, next_active_path)
            
            if success:
                return True, result_assignment, None

        # Sem versão válida encontrada para o pacote
        return False, assignment, pkg


# =====================================================================
# CAMADA 3: Suíte de Testes e Validação de Conflitos e Ciclos
# =====================================================================

if __name__ == "__main__":
    print("=== Iniciando Testes do Resolvedor SemVer ===")

    # Cenário 1: Diamante Compatível
    registry = PackageRegistry()
    registry.add_version("LibA", "1.1.0", {"Core": "^1.0.0"})
    registry.add_version("LibB", "1.2.0", {"Core": "~1.1.0"})
    registry.add_version("Core", "1.1.5", {})
    registry.add_version("Core", "1.2.0", {})

    resolver = DependencyResolver(registry)
    solution = resolver.resolve({"LibA": "^1.0.0", "LibB": "^1.0.0"})
    print("\n=== Cenário 1: Diamante Compatível Resolvido ===")
    print("Solução encontrada:", solution)
    assert solution["Core"] == SemVer.parse("1.1.5") # ^1.0.0 e ~1.1.0 interceptam em 1.1.5

    # Cenário 2: Conflito de Ranges Disjuntos
    registry_conflict = PackageRegistry()
    registry_conflict.add_version("LibA", "1.0.0", {"Core": "^2.0.0"})
    registry_conflict.add_version("Core", "1.5.0", {})
    registry_conflict.add_version("Core", "2.1.0", {})

    resolver_conflict = DependencyResolver(registry_conflict)
    print("\n=== Cenário 2: Conflito de Versões Detectado ===")
    try:
        resolver_conflict.resolve({"LibA": "1.0.0"})
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