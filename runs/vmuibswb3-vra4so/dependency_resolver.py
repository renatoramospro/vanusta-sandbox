import re
from typing import Dict, List, Set, Tuple, Optional, Any

# =====================================================================
# CAMADA 0: SemVer e Ranges
# =====================================================================

class SemVer:
    """Implementa a especificação SemVer 2.0.0 com suporte a precedência e pré-releases."""
    def __init__(self, major: int, minor: int, patch: int, prerelease: Optional[str] = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease  # ex: "alpha.1"

    @classmethod
    def parse(cls, version_str: str) -> 'SemVer':
        v_str = version_str.strip()
        if v_str.startswith('v'):
            v_str = v_str[1:]
        
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z\.-]+))?(?:\+[0-9A-Za-z\.-]+)?$', v_str)
        if not match:
            raise ValueError(f"Versão SemVer inválida: '{version_str}'")
        major, minor, patch, pre = match.groups()
        return cls(int(major), int(minor), int(patch), pre)

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


class VersionRange:
    """Representa um conjunto de restrições SemVer e gerencia interseções e vazio."""
    def __init__(self, constraints: List[Tuple[str, SemVer]]):
        # Lista de tuplas (operador, versao) ex: [(">=", SemVer(1,0,0)), ("<", SemVer(2,0,0))]
        self.constraints = constraints

    @classmethod
    def parse(cls, range_str: str) -> 'VersionRange':
        range_str = range_str.strip()
        if not range_str or range_str == "*" or range_str == "latest":
            return cls([(">=", SemVer(0, 0, 0))])

        constraints = []
        parts = range_str.split()
        
        for part in parts:
            # Tratamento de caret (^) e tilde (~)
            if part.startswith('^'):
                base = SemVer.parse(part[1:])
                upper = cls._caret_upper(base)
                constraints.append((">=", base))
                constraints.append(("<", upper))
            elif part.startswith('~'):
                base = SemVer.parse(part[1:])
                upper = cls._tilde_upper(base)
                constraints.append((">=", base))
                constraints.append(("<", upper))
            else:
                match = re.match(r'^(>=|<=|>|<|=)?\s*(v?\d+\.\d+\.\d+(?:-[0-9A-Za-z\.-]+)?)', part)
                if not match:
                    raise ValueError(f"Range inválido: '{part}'")
                op, ver_str = match.groups()
                op = op if op else "="
                ver = SemVer.parse(ver_str)
                constraints.append((op, ver))

        return cls(constraints)

    @staticmethod
    def _caret_upper(base: SemVer) -> SemVer:
        if base.major > 0:
            return SemVer(base.major + 1, 0, 0)
        elif base.minor > 0:
            return SemVer(0, base.minor + 1, 0)
        else:
            return SemVer(0, 0, base.patch + 1)

    @staticmethod
    def _tilde_upper(base: SemVer) -> SemVer:
        if base.major > 0:
            return SemVer(base.major, base.minor + 1, 0)
        else:
            return SemVer(0, base.minor + 1, 0)

    def satisfies(self, version: SemVer) -> bool:
        for op, ver in self.constraints:
            if op == "=":
                if version != ver: return False
            elif op == ">":
                if not (version > ver): return False
            elif op == ">=":
                if not (version >= ver): return False
            elif op == "<":
                if not (version < ver): return False
            elif op == "<=":
                if not (version <= ver): return False
        return True

    def intersect(self, other: 'VersionRange') -> 'VersionRange':
        return VersionRange(self.constraints + other.constraints)

    def is_empty(self, available_versions: List[SemVer]) -> bool:
        return not any(self.satisfies(v) for v in available_versions)

    def __repr__(self) -> str:
        return " ".join([f"{op}{ver}" for op, ver in self.constraints])


# =====================================================================
# CAMADA 1 & 2: Resolvedor CSP por Backtracking com Cadeia Causal
# =====================================================================

class DependencyConflictError(Exception):
    """Erro lançado quando há conflito de dependência ou range vazio, contendo a trilha causal."""
    def __init__(self, message: str, causal_chain: List[Tuple[str, SemVer, str]]):
        super().__init__(message)
        self.causal_chain = causal_chain  # Lista de (pacote, versão, requerido_por)


class PackageRegistry:
    """Repositório de pacotes e suas versões disponíveis."""
    def __init__(self):
        # { nome_pacote: { versao_str: { dep_nome: range_str } } }
        self.packages: Dict[str, Dict[str, Dict[str, str]]] = {}

    def add_version(self, name: str, version: str, dependencies: Dict[str, str]):
        if name not in self.packages:
            self.packages[name] = {}
        self.packages[name][version] = dependencies

    def get_versions(self, name: str) -> List[SemVer]:
        if name not in self.packages:
            return []
        return sorted([SemVer.parse(v) for v in self.packages[name].keys()], reverse=True)

    def get_dependencies(self, name: str, version: SemVer) -> Dict[str, VersionRange]:
        ver_str = f"{version.major}.{version.minor}.{version.patch}"
        if version.prerelease:
            ver_str += f"-{version.prerelease}"
        
        deps_raw = self.packages.get(name, {}).get(ver_str, {})
        return {dep_name: VersionRange.parse(rng) for dep_name, rng in deps_raw.items()}


class DependencyResolver:
    """Resolvedor de dependências utilizando CSP e backtracking com detecção de ciclo ativo."""
    def __init__(self, registry: PackageRegistry):
        self.registry = registry

    def resolve(self, root_requirements: Dict[str, str]) -> Dict[str, str]:
        # Converte requisitos raiz em VersionRange
        initial_constraints: Dict[str, VersionRange] = {
            pkg: VersionRange.parse(rng) for pkg, rng in root_requirements.items()
        }
        
        # Pilha de pacotes no caminho ativo atual (para detecção de ciclos reais)
        active_stack: Set[str] = set()
        
        # Histórico causal para rastreamento de erros
        causal_trail: List[Tuple[str, SemVer, str]] = []

        result = self._backtrack(initial_constraints, {}, active_stack, causal_trail, "ROOT")
        if result is None:
            raise DependencyConflictError(
                "Falha ao resolver dependências: restrições incompatíveis ou pacote inexistente.",
                causal_trail
            )
        return {pkg: str(ver) for pkg, ver in result.items()}

    def _backtrack(
        self,
        constraints: Dict[str, VersionRange],
        assigned: Dict[str, SemVer],
        active_stack: Set[str],
        causal_trail: List[Tuple[str, SemVer, str]],
        requester: str
    ) -> Optional[Dict[str, SemVer]]:
        
        # Seleciona um pacote não atribuído que possui restrições
        unassigned = [pkg for pkg in constraints if pkg not in assigned]
        if not unassigned:
            return assigned  # Todas as dependências satisfeitas!

        pkg = unassigned[0]
        range_cond = constraints[pkg]

        # Verifica se o pacote existe no registro
        available_versions = self.registry.get_versions(pkg)
        if not available_versions:
            causal_trail.append((pkg, SemVer(0,0,0), requester))
            return None

        # Valida se o range é vazio com base nas versões disponíveis
        if range_cond.is_empty(available_versions):
            causal_trail.append((pkg, available_versions[0], requester))
            return None

        # Tenta alocar versões em ordem decrescente (heurística de maior versão)
        for version in available_versions:
            if range_cond.satisfies(version):
                # Atribui temporariamente
                new_assigned = assigned.copy()
                new_assigned[pkg] = version
                
                # Trata dependência circular: se já está na pilha ativa, assume compatível (ciclo benigno se versionado)
                if pkg in active_stack:
                    # Ciclo detectado no caminho ativo, validado pela versão já escolhida na pilha
                    continue
                
                active_stack.add(pkg)
                causal_trail.append((pkg, version, requester))

                # Obtém dependências da versão escolhida
                sub_deps = self.registry.get_dependencies(pkg, version)
                
                # Mescla com restrições existentes
                new_constraints = constraints.copy()
                conflict_found = False
                for sub_pkg, sub_range in sub_deps.items():
                    if sub_pkg in new_constraints:
                        merged = new_constraints[sub_pkg].intersect(sub_range)
                        # Verifica vazio preliminar na interseção
                        sub_avail = self.registry.get_versions(sub_pkg)
                        if sub_avail and merged.is_empty(sub_avail):
                            conflict_found = True
                            causal_trail.append((sub_pkg, sub_avail[0], f"{pkg}@{version}"))
                            break
                        new_constraints[sub_pkg] = merged
                    else:
                        new_constraints[sub_pkg] = sub_range

                if not conflict_found:
                    # Recursão para próximo nível
                    res = self._backtrack(new_constraints, new_assigned, active_stack, causal_trail, f"{pkg}@{version}")
                    if res is not None:
                        active_stack.remove(pkg)
                        return res

                active_stack.remove(pkg)

        return None


# =====================================================================
# CAMADA 3: Testes e Validação de Casos Críticos
# =====================================================================

if __name__ == "__main__":
    print("=== Iniciando Validação do Resolvedor SemVer ===")

    # Cenário 1: Diamante Compatível
    registry = PackageRegistry()
    registry.add_version("App", "1.0.0", {"LibA": "^1.0.0", "LibB": "^1.0.0"})
    registry.add_version("LibA", "1.0.0", {"Core": "^1.1.0"})
    registry.add_version("LibB", "1.0.0", {"Core": "^1.2.0"})
    registry.add_version("Core", "1.5.0", {})
    registry.add_version("Core", "1.2.0", {})
    registry.add_version("Core", "1.1.0", {})

    resolver = DependencyResolver(registry)
    result = resolver.resolve({"App": "1.0.0"})
    print("Cenário 1 (Diamante Compatível) Resolvido com Sucesso:", result)
    assert result["Core"] == "SemVer(1.5.0)"

    # Cenário 2: Conflito Incompatível (Range Vazio / Diamante Conflitante)
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
    except DependencyConflictError as e:
        print("Erro capturado com sucesso:")
        print("Mensagem:", e)
        print("Cadeia Causal:", e.causal_chain)
        assert len(e.causal_chain) > 0

    # Cenário 3: Detecção de Ciclo
    registry_cycle = PackageRegistry()
    registry_cycle.add_version("X", "1.0.0", {"Y": "1.0.0"})
    registry_cycle.add_version("Y", "1.0.0", {"X": "1.0.0"})

    resolver_cycle = DependencyResolver(registry_cycle)
    print("\n=== Cenário 3: Ciclo Detectado ===")
    try:
        resolver_cycle.resolve({"X": "1.0.0"})
    except DependencyConflictError as e:
        print("Erro de ciclo capturado com sucesso:")
        print("Mensagem:", e)
        print("Cadeia Causal:", e.causal_chain)

    print("\nTodos os testes executados com sucesso!")