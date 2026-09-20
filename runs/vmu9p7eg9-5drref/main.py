import sys
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

# --- 1. Definições de Metadados e Exceções ---

@dataclass
class PluginMetadata:
    name: str
    version: str
    dependencies: Dict[str, str] = field(default_factory=dict) # name -> version_requirement (ex: ">=1.0.0")

class PluginError(Exception):
    pass

class CircularDependencyError(PluginError):
    pass

class MissingDependencyError(PluginError):
    pass

class VersionMismatchError(PluginError):
    pass

# --- 2. Motor de Versão (SemVer Lite) ---

class SemVer:
    """Implementação simplificada de comparação de versões para o experimento."""
    
    @staticmethod
    def parse(version_str: str) -> Tuple[int, int, int]:
        try:
            parts = list(map(int, version_str.split('.')))
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts[:3])
        except ValueError:
            raise ValueError(f"Formato de versão inválido: {version_str}")

    @staticmethod
    def satisfies(version: str, requirement: str) -> bool:
        """
        Suporta requisitos simples:
        '1.2.3' (exata)
        '>=1.2.3' (maior ou igual)
        """
        if requirement.startswith(">="):
            req_ver = SemVer.parse(requirement[2:])
            actual_ver = SemVer.parse(version)
            return actual_ver >= req_ver
        elif requirement.startswith(">"):
            req_ver = SemVer.parse(requirement[1:])
            actual_ver = SemVer.parse(version)
            return actual_ver > req_ver
        else:
            # Comparação exata
            return SemVer.parse(version) == SemVer.parse(requirement)

# --- 3. Interface Base do Plugin ---

class Plugin:
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata

    def initialize(self) -> None:
        pass

# --- 4. Gerenciador de Plugins ---

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.metadata_registry: Dict[str, PluginMetadata] = {}

    def register_plugin(self, plugin: Plugin) -> None:
        self.metadata_registry[plugin.metadata.name] = plugin.metadata
        self.plugins[plugin.metadata.name] = plugin

    def _validate_dependencies(self, name: str):
        """Verifica se as dependências existem e se as versões são compatíveis."""
        metadata = self.metadata_registry[name]
        for dep_name, req_version in metadata.dependencies.items():
            if dep_name not in self.metadata_registry:
                raise MissingDependencyError(f"Plugin '{name}' requer '{dep_name}', mas ele não foi encontrado.")
            
            dep_metadata = self.metadata_registry[dep_name]
            if not SemVer.satisfies(dep_metadata.version, req_version):
                raise VersionMismatchError(
                    f"Versão incompatível para '{name}': requer '{dep_name} {req_version}', "
                    f"mas encontrou '{dep_metadata.version}'."
                )

    def resolve_load_order(self) -> List[str]:
        visited: Set[str] = set()
        visiting: Set[str] = set()
        order: List[str] = []

        def dfs(name: str):
            if name in visiting:
                raise CircularDependencyError(f"Ciclo detectado no plugin: {name}")
            if name in visited:
                return

            # 1. Validar existência e versão antes de prosseguir
            self._validate_dependencies(name)

            visiting.add(name)
            
            # 2. Resolver dependências (Post-order)
            for dep_name in self.metadata_registry[name].dependencies.keys():
                dfs(dep_name)

            visiting.remove(name)
            visited.add(name)
            order.append(name)

        # Garantir que todos os plugins registrados sejam processados
        for plugin_name in list(self.metadata_registry.keys()):
            if plugin_name not in visited:
                dfs(plugin_name)
        
        return order

    def load_all(self):
        order = self.resolve_load_order()
        for name in order:
            self.plugins[name].initialize()
        return order

# --- 5. Experimento de Teste ---

class MockPlugin(Plugin):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.initialized = False

    def initialize(self):
        self.initialized = True

def run_experiment():
    print("=== INICIANDO TESTES DE COMPATIBILIDADE SEMVER ===")

    # Teste 1: Sucesso com Versão Compatível (>=)
    print("\n--- Teste 1: Sucesso com Versão Compatível (>=) ---")
    pm1 = PluginManager()
    pm1.register_plugin(MockPlugin(PluginMetadata("Base", "2.0.0")))
    pm1.register_plugin(MockPlugin(PluginMetadata("App", "1.0.0", {"Base": ">=1.5.0"})))
    
    try:
        order = pm1.load_all()
        print(f"[Sucesso] Ordem de carregamento: {order}")
    except Exception as e:
        print(f"[Falha] Deveria ter passado, mas falhou: {e}")
        sys.exit(1)

    # Teste 2: Falha por Versão Incompatível (Muito antiga)
    print("\n--- Teste 2: Falha por Versão Incompatível (Muito antiga) ---")
    pm2 = PluginManager()
    pm2.register_plugin(MockPlugin(PluginMetadata("Base", "1.0.0")))
    pm2.register_plugin(MockPlugin(PluginMetadata("App", "1.0.0", {"Base": ">=2.0.0"})))
    
    try:
        pm2.load_all()
        print("[Falha] O sistema deveria ter detectado incompatibilidade de versão!")
        sys.exit(1)
    except VersionMismatchError as e:
        print(f"[Sucesso] Erro de versão capturado corretamente: {e}")

    # Teste 3: Falha por Versão Incompatível (Exata)
    print("\n--- Teste 3: Falha por Versão Incompatível (Exata) ---")
    pm3 = PluginManager()
    pm3.register_plugin(MockPlugin(PluginMetadata("Base", "1.2.3")))
    pm3.register_plugin(MockPlugin(PluginMetadata("App", "1.0.0", {"Base": "1.2.4"})))
    
    try:
        pm3.load_all()
        print("[Falha] O sistema deveria ter detectado incompatibilidade de versão exata!")
        sys.exit(1)
    except VersionMismatchError as e:
        print(f"[Sucesso] Erro de versão exata capturado corretamente: {e}")

    # Teste 4: Ciclo (Re-verificação)
    print("\n--- Teste 4: Re-verificação de Ciclo ---")
    pm4 = PluginManager()
    pm4.register_plugin(MockPlugin(PluginMetadata("A", "1.0.0", {"B": "1.0.0"})))
    pm4.register_plugin(MockPlugin(PluginMetadata("B", "1.0.0", {"A": "1.0.0"})))
    
    try:
        pm4.load_all()
        print("[Falha] O sistema deveria ter detectado ciclo!")
        sys.exit(1)
    except CircularDependencyError as e:
        print(f"[Sucesso] Ciclo capturado: {e}")

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO ===")

if __name__ == "__main__":
    run_experiment()