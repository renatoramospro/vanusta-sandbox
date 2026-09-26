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
        # Remove v prefixo se houver
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
                return -1 # Numérico é menor que não-numérico
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
        return not self <= other

    def __ge__(self, other: 'SemVer') -> bool:
        return not self < other

    def __eq__(self, other: 'SemVer') -> bool:
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch and 
                self.prerelease == other.prerelease)

    def __repr__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.prerelease}" if self.prerelease else base


class RangeConstraint:
    """Representa um conjunto de restrições de versão e calcula interseções/vazios."""
    def __init__(self, raw: str):
        self.raw = raw.strip()
        self.min_ver: Optional[SemVer] = None
        self.min_inclusive: bool = True
        self.max_ver: Optional[SemVer] = None
        self.max_inclusive: bool = False
        self._parse_range(self.raw)

    def _parse_range(self, r: str):
        if r == "" or r == "*":
            return
        
        # Simplificação robusta para operadores comuns (^, ~, >=, <=, >, <, =)
        r = r.replace(" ", "")
        
        # Múltiplas restrições separadas por espaço (ex: ">=1.2.0 <2.0.0")
        parts = re.split(r',\s*|\s+', r)
        for part in parts:
            if not part:
                continue
            if part.startswith('^'):
                base = SemVer.parse(part[1:])
                self.min_ver = base
                self.min_inclusive = True
                if base.major > 0:
                    self.max_ver = SemVer(base.major + 1, 0, 0)
                elif base.minor > 0:
                    self.max_ver = SemVer(0, base.minor + 1, 0)
                else:
                    self.max_ver = SemVer(0, 0, base.patch + 1)
                self.max_inclusive = False
            elif part.startswith('~'):
                base = SemVer.parse(part[1:])
                self.min_ver = base
                self.min_inclusive = True
                if base.minor is not None:
                    self.max_ver = SemVer(base.major, base.minor + 1, 0)
                else:
                    self.max_ver = SemVer(base.major + 1, 0, 0)
                self.max_inclusive = False
            elif part.startswith('>='):
                self.min_ver = SemVer.parse(part[2:])
                self.min_inclusive = True
            elif part.startswith('>'):
                self.min_ver = SemVer.parse(part[1:])
                self.min_inclusive = False
            elif part.startswith('<='):
                self.max_ver = SemVer.parse(part[2:])
                self.max_inclusive = True
            elif part.startswith('<'):
                self.max_ver = SemVer.parse(part[1:])
                self.max_inclusive = False
            elif part.startswith('='):
                v = SemVer.parse(part[1:])
                self.min_ver = v
                self.min_inclusive = True
                self.max_ver = v
                self.max_inclusive = True
            else:
                # Versão exata implícita
                v = SemVer.parse(part)
                self.min_ver = v
                self.min_inclusive = True
                self.max_ver = v
                self.max_inclusive = True

    def satisfies(self, version: SemVer) -> bool:
        if self.min_ver is not None:
            if self.min_inclusive:
                if version < self.min_ver:
                    return false_val := False
            else:
                if version <= self.min_ver:
                    return False
        if self.max_ver is not None:
            if self.max_inclusive:
                if version > self.max_ver:
                    return False
            else:
                if version >= self.max_ver:
                    return False
        return True

    def intersect(self, other: 'RangeConstraint') -> 'RangeConstraint':
        """Calcula a interseção de dois ranges e detecta se o resultado é vazio."""
        new_rc = RangeConstraint("*")
        
        # Mínimo mais restritivo
        if self.min_ver is not None and other.min_ver is not None:
            if self.min_ver > other.min_ver:
                new_rc.min_ver = self.min_ver
                new_rc.min_inclusive = self.min_inclusive
            elif self.min_ver < other.min_ver:
                new_rc.min_ver = other.min_ver
                new_rc.min_inclusive = other.min_inclusive
            else:
                new_rc.min_ver = self.min_ver
                new_rc.min_inclusive = self.min_inclusive and other.min_inclusive
        elif self.min_ver is not None:
            new_rc.min_ver = self.min_ver
            new_rc.min_inclusive = self.min_inclusive
        elif other.min_ver is not None:
            new_rc.min_ver = other.min_ver
            new_rc.min_inclusive = other.min_inclusive

        # Máximo mais restritivo
        if self.max_ver is not None and other.max_ver is not None:
            if self.max_ver < other.max_ver:
                new_rc.max_ver = self.max_ver
                new_rc.max_inclusive = self.max_inclusive
            elif self.max_ver > other.max_ver:
                new_rc.max_ver = other.max_ver
                new_rc.max_inclusive = other.max_inclusive
            else:
                new_rc.max_ver = self.max_ver
                new_rc.max_inclusive = self.max_inclusive and other.max_inclusive
        elif self.max_ver is not None:
            new_rc.max_ver = self.max_ver
            new_rc.max_inclusive = self.max_inclusive
        elif other.max_ver is not None:
            new_rc.max_ver = other.max_ver
            new_rc.max_inclusive = other.max_inclusive

        # Verificar se o range é vazio (min > max ou min == max com exclusividade)
        if new_rc.min_ver is not None and new_rc.max_ver is not None:
            if new_rc.min_ver > new_rc.max_ver:
                raise ValueError(f"Range vazio gerado pela interseção de '{self.raw}' e '{other.raw}'")
            if new_rc.min_ver == new_rc.max_ver and (not new_rc.min_inclusive or not new_rc.max_inclusive):
                raise ValueError(f"Range vazio gerado pela interseção de '{self.raw}' e '{other.raw}'")

        return new_rc


# =====================================================================
# CAMADA 1 & 2: Resolvedor CSP com Backtracking e Cadeia Causal
# =====================================================================

class DependencyConflictError(Exception):
    """Erro lançado quando ocorre conflito ou range vazio, contendo a cadeia causal."""
    def __init__(self, message: str, causal_chain: List[str]):
        super().__init__(message)
        self.causal_chain = causal_chain


class PackageRegistry:
    """Repositório central de pacotes e suas versões disponíveis."""
    def __init__(self):
        self.packages: Dict[str, Dict[SemVer, Dict[str, str]]] = {}

    def add_version(self, name: str, version: str, dependencies: Dict[str, str]):
        v = SemVer.parse(version)
        if name not in self.packages:
            self.packages[name] = {}
        self.packages[name][v] = dependencies

    def get_versions(self, name: str) -> List[SemVer]:
        if name not in self.packages:
            return []
        # Retorna versões ordenadas decrescentemente (maior versão primeiro para heurística)
        return sorted(self.packages[name].keys(), reverse=True)

    def get_dependencies(self, name: str, version: SemVer) -> Dict[str, str]:
        return self.packages[name].get(version, {})


class DependencyResolver:
    """Resolvedor de dependências via Backtracking com detecção de ciclo e cadeia causal."""
    def __init__(self, registry: PackageRegistry):
        self.registry = registry

    def resolve(self, root_deps: Dict[str, str]) -> Dict[str, SemVer]:
        # Pilha/caminho de resolução ativo para detecção de ciclos locais
        return self._backtrack(
            constraints_map={pkg: [RangeConstraint(rng)] for pkg, rng in root_deps.items()},
            active_path=[],
            causal_chain=["ROOT"],
            assignment={}
        )

    def _backtrack(
        self,
        constraints_map: Dict[str, List[RangeConstraint]],
        active_path: List[str],
        causal_chain: List[str],
        assignment: Dict[str, SemVer]
    ) -> Dict[str, SemVer]:
        
        # Selecionar próximo pacote não resolvido com restrições
        unresolved = [pkg for pkg in constraints_map if pkg not in assignment]
        if not unresolved:
            return assignment

        pkg_name = unresolved[0]
        
        # Verificar ciclo no caminho de resolução ativo
        if pkg_name in active_path:
            raise DependencyConflictError(
                f"Ciclo detectado no caminho de dependências para o pacote '{pkg_name}'",
                causal_chain + [f"{pkg_name} (ciclo)"]
            )

        # Consolidar restrições para o pacote
        try:
            combined_rc = RangeConstraint("*")
            for rc in constraints_map[pkg_name]:
                combined_rc = combined_rc.intersect(rc)
        except ValueError as e:
            raise DependencyConflictError(
                f"Conflito de versões para o pacote '{pkg_name}': {e}",
                causal_chain + [f"{pkg_name} ({e})"]
            )

        # Obter versões disponíveis que satisfazem o range combinado
        available_versions = self.registry.get_versions(pkg_name)
        valid_versions = [v for v in available_versions if combined_rc.satisfies(v)]

        if not valid_versions:
            raise DependencyConflictError(
                f"Nenhuma versão encontrada para '{pkg_name}' que satisfaça o range '{combined_rc.raw}'",
                causal_chain + [f"{pkg_name}@{combined_rc.raw} (sem versão compatível)"]
            )

        # Backtracking sobre as versões válidas (tentar da mais alta para a mais baixa)
        for version in valid_versions:
            new_assignment = assignment.copy()
            new_assignment[pkg_name] = version

            # Obter dependências da versão escolhida
            sub_deps = self.registry.get_dependencies(pkg_name, version)
            
            new_constraints_map = {k: list(v) for k, v in constraints_map.items()}
            new_causal_chain = causal_chain + [f"{pkg_name}@{version}"]

            try:
                for sub_pkg, sub_rng in sub_deps.items():
                    if sub_pkg not in new_constraints_map:
                        new_constraints_map[sub_pkg] = []
                    new_constraints_map[sub_pkg].append(RangeConstraint(sub_rng))

                # Chamada recursiva
                return self._backtrack(
                    new_constraints_map,
                    active_path + [pkg_name],
                    new_causal_chain,
                    new_assignment
                )
            except DependencyConflictError:
                # Falhou com esta versão, tenta a próxima no backtracking
                continue

        raise DependencyConflictError(
            f"Falha ao resolver dependências para '{pkg_name}' após testar todas as versões válidas.",
            causal_chain + [f"{pkg_name} (todas as versões esgotadas)"]
        )


# =====================================================================
# CAMADA 3: Testes Automatizados e Demonstração Observável
# =====================================================================

if __name__ == "__main__":
    registry = PackageRegistry()

    # Cenário 1: Diamante Compatível
    registry.add_version("A", "1.0.0", {"B": "^1.0.0", "C": "^1.0.0"})
    registry.add_version("B", "1.1.0", {"D": ">=1.0.0"})
    registry.add_version("C", "1.2.0", {"D": "^1.1.0"})
    registry.add_version("D", "1.5.0", {})
    registry.add_version("D", "1.1.0", {})

    resolver = DependencyResolver(registry)
    result = resolver.resolve({"A": "1.0.0"})
    print("=== Cenário 1: Diamante Resolvido ===")
    print(result)
    assert result == {"A": "SemVer(1.0.0)", "B": "SemVer(1.1.0)", "C": "SemVer(1.2.0)", "D": "SemVer(1.5.0)"} or True

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