import sys
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional

# --- 1. Definições de Metadados e Exceções ---

@dataclass
class PluginMetadata:
    name: str
    version: str
    # dependências agora podem ser "nome" ou "nome@requisito" (ex: "auth@^1.0.0")
    dependencies: List[str] = field(default_factory=list)

class PluginError(Exception):
    pass

class CircularDependencyError(PluginError):
    pass

class MissingDependencyError(PluginError):
    pass

class VersionMismatchError(PluginError):
    pass

# --- 2. Utilitários de Versão (SemVer) ---

def parse_version(version_str: str) -> Tuple[int, ...]:
    """Converte '1.2.3' em (1, 2, 3)."""
    try:
        return tuple(map(int, version_str.split('.')))
    except ValueError:
        raise PluginError(f"Versão inválida: {version_str}")

def is_compatible(required_spec: str, actual_version_str: str) -> bool:
    """
    Verifica se actual_version_str satisfaz required_spec.
    Suporta:
    - '1.2.3' (Exata)
    - '^1.2.3' (Caret: Compatível com Major 1, >= 1.2.3)
    - '>=1.2.3' (Maior ou igual)
    """
    actual = parse_version(actual_version_str)
    
    if required_spec.startswith('^'):
        spec_ver = parse_version(required_spec[1:])
        # Regra do Caret: Mesma Major, mas >= especificada
        return actual[0] == spec_ver[0] and actual >= spec_ver
    
    if required_spec.startswith('>='):
        spec_ver = parse_version(required_spec[2:])
        return actual >= spec_ver
    
    # Comparação exata
    return actual == parse_version(required_spec)

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

    def _parse_dep_string(self, dep_str: str) -> Tuple[str, Optional[str]]:
        """Separa 'auth@^1.0.0' em ('auth', '^1.0.0')."""
        if '@' in dep_str:
            name, spec = dep_str.split('@', 1)
            return name, spec
        return dep_str, None

    def resolve_load_order(self) -> List[str]:
        visited: Set[str] = set()
        visiting: Set[str] = set()
        order: List[str] = []

        def dfs(name: str):
            if name in visiting:
                raise CircularDependencyError(f"Ciclo detectado no plugin: {name}")
            if name in visited:
                return

            if name not in self.metadata_registry:
                raise MissingDependencyError(f"Dependência não encontrada: {name}")

            visiting.add(name)
            
            # Processar dependências com validação de versão
            current_meta = self.metadata_registry[name]
            for dep_str in current_meta.dependencies:
                dep_name, spec = self._parse_dep_string(dep_str)
                
                # 1. Verificar existência
                if dep_name not in self.metadata_registry:
                    raise MissingDependencyError(f"Plugin '{name}' requer '{dep_name}', mas ele não existe.")
                
                # 2. Verificar compatibilidade de versão
                if spec:
                    actual_ver = self.metadata_registry[dep_name].version
                    if not is_compatible(spec, actual_ver):
                        raise VersionMismatchError(
                            f"Conflito de versão em '{name}': requer '{dep_name}@{spec}', mas encontrou '{actual_ver}'"
                        )
                
                # 3. Recursão
                dfs(dep_name)

            visiting.remove(name)
            visited.add(name)
            order.append(name)

        for plugin_name in self.metadata_registry:
            if plugin_name not in visited:
                dfs(plugin_name)
        
        return order

    def load_all(self) -> List[str]:
        order = self.resolve_load_order()
        loaded = []
        for name in order:
            self.plugins[name].initialize()
            loaded.append(name)
        return loaded

# --- 5. Experimento de Validação ---

class MockPlugin(Plugin):
    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.initialized = False
    def initialize(self):
        self.initialized = True

def run_experiment():
    print("=== INICIANDO TESTES DE COMPATIBILIDADE SEMVER ===")

    # Teste 1: Sucesso com Caret (Compatibilidade de Minor)
    print("\n--- Teste 1: Sucesso com Caret (^1.0.0) ---")
    pm1 = PluginManager()
    pm1.register_plugin(MockPlugin(PluginMetadata("Base", "1.2.5")))
    pm1.register_plugin(MockPlugin(PluginMetadata("App", "1.0.0", ["Base@^1.0.0"])))
    
    try:
        order = pm1.load_all()
        print(f"[Sucesso] Ordem de carregamento: {order}")
    except Exception as e:
        print(f"[Falha] Deveria ter passado, mas falhou: {e}")
        sys.exit(1)

    # Teste 2: Falha por Incompatibilidade de Major (Caret violation)
    print("\n--- Teste 2: Falha por Incompatibilidade de Major ---")
    pm2 = PluginManager()
    pm2.register_plugin(MockPlugin(PluginMetadata("Base", "2.0.0")))
    pm2.register_plugin(MockPlugin(PluginMetadata("App", "1.0.0", ["Base@^1.0.0"])))
    
    try:
        pm2.load_all()
        print("[Falha] O sistema deveria ter detectado conflito de Major version!")
        sys.exit(1)
    except VersionMismatchError as e:
        print(f"[Sucesso] Erro de versão capturado: {e}")

    # Teste 3: Falha por Versão Inferior (>= violation)
    print("\n--- Teste 3: Falha por Versão Inferior (>=) ---")
    pm3 = PluginManager()
    pm3.register_plugin(MockPlugin(PluginMetadata("Base", "1.1.0")))
    pm3.register_plugin(MockPlugin(PluginMetadata("App", "1.0.0", ["Base@>=1.2.0"])))
    
    try:
        pm3.load_all()
        print("[Falha] O sistema deveria ter detectado versão insuficiente!")
        sys.exit(1)
    except VersionMismatchError as e:
        print(f"[Sucesso] Erro de versão capturado: {e}")

    # Teste 4: Sucesso com Versão Exata
    print("\n--- Teste 4: Sucesso com Versão Exata ---")
    pm4 = PluginManager()
    pm4.register_plugin(MockPlugin(PluginMetadata("Base", "1.0.0")))
    pm4.register_plugin(MockPlugin(PluginMetadata("App", "1.0.0", ["Base@1.0.0"])))
    
    try:
        order = pm4.load_all()
        print(f"[Sucesso] Ordem de carregamento: {order}")
    except Exception as e:
        print(f"[Falha] Deveria ter passado, mas falhou: {e}")
        sys.exit(1)

    print("\n=== TODOS OS TESTES DE SEMVER PASSARAM COM SUCESSO ===")

if __name__ == "__main__":
    run_experiment()