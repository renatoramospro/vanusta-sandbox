import importlib.util
import sys
import os
import shutil
import time
from typing import Dict, List, Set, Any

# ==========================================
# 1. Classes de Domínio e Exceções
# ==========================================

class PluginError(Exception):
    pass

class CircularDependencyError(PluginError):
    pass

class VersionMismatchError(PluginError):
    pass

class PluginMetadata:
    def __init__(self, name: str, version: str, dependencies: Dict[str, str] = None):
        self.name = name
        self.version = version
        self.dependencies = dependencies or {}

class Plugin:
    metadata: PluginMetadata

    def initialize(self, context: Dict[str, Any]) -> None:
        raise NotImplementedError

# ==========================================
# 2. Resolução de Versão Semântica (SemVer)
# ==========================================

class VersionChecker:
    @staticmethod
    def parse_version(version_str: str) -> tuple:
        try:
            return tuple(map(int, version_str.split('.')))
        except ValueError:
            raise VersionMismatchError(f"Versão inválida: {version_str}")

    @staticmethod
    def satisfies(installed_version: str, constraint: str) -> bool:
        """
        Suporta restrições simples baseadas em SemVer, ex: '^1.2.0' ou '>=1.0.0'
        """
        installed = VersionChecker.parse_version(installed_version)
        
        if constraint.startswith('^'):
            base_version = VersionChecker.parse_version(constraint[1:])
            # ^1.2.0 significa >=1.2.0 e <2.0.0
            if installed[0] == base_version[0] and installed >= base_version:
                return True
            return False
        elif constraint.startswith('>='):
            base_version = VersionChecker.parse_version(constraint[2:])
            return installed >= base_version
        elif constraint == '*':
            return True
        else:
            return installed == VersionChecker.parse_version(constraint)

# ==========================================
# 3. Gerenciador de Grafo e Dependências (DAG)
# ==========================================

class DependencyResolver:
    @staticmethod
    def resolve_order(plugins: Dict[str, Plugin]) -> List[str]:
        """
        Ordenação topológica usando DFS. Detecta ciclos e lança CircularDependencyError.
        """
        visited = set()
        temp_mark = set()
        order = []

        def visit(plugin_name: str):
            if plugin_name in temp_mark:
                raise CircularDependencyError(f"Dependência circular detectada envolvendo o plugin: {plugin_name}")
            if plugin_name not in visited:
                temp_mark.add(plugin_name)
                
                plugin = plugins.get(plugin_name)
                if not plugin:
                    raise PluginError(f"Plugin dependência '{plugin_name}' não encontrado.")

                # Verificar dependências e restrições de versão
                for dep_name, constraint in plugin.metadata.dependencies.items():
                    if dep_name not in plugins:
                        raise PluginError(f"Plugin '{plugin_name}' depende de '{dep_name}', que não está presente.")
                    
                    dep_version = plugins[dep_name].metadata.version
                    if not VersionChecker.satisfies(dep_version, constraint):
                        raise VersionMismatchError(
                            f"Plugin '{plugin_name}' requer '{dep_name}' versão {constraint}, "
                            f"mas a versão instalada é {dep_version}."
                        )

                    visit(dep_name)

                temp_mark.remove(plugin_name)
                visited.add(plugin_name)
                order.append(plugin_name)

        for name in plugins:
            if name not in visited:
                visit(name)

        return order

# ==========================================
# 4. Loader Dinâmico de Plugins
# ==========================================

class PluginLoader:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}

    def discover_and_load(self) -> Dict[str, Plugin]:
        if not os.path.exists(self.plugin_dir):
            return {}

        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                filepath = os.path.join(self.plugin_dir, filename)
                module_name = filename[:-3]

                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Procurar classes que herdam de Plugin
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, Plugin) and attr is not Plugin:
                            plugin_instance = attr()
                            if not hasattr(plugin_instance, 'metadata'):
                                raise PluginError(f"Plugin {module_name} não possui metadados definidos.")
                            self.plugins[plugin_instance.metadata.name] = plugin_instance

        return self.plugins


# ==========================================
# 5. Execução dos Testes e Demonstrações
# ==========================================

def setup_mock_plugins_dir(dir_name: str, plugins_code: Dict[str, str]):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
    os.makedirs(dir_name)
    for fname, code in plugins_code.items():
        with open(os.path.join(dir_name, fname), 'w', encoding='utf-8') as f:
            f.write(code)


if __name__ == "__main__":
    print("=== INICIANDO TESTES DO SISTEMA DE PLUGINS ===")

    # Teste 1: Carregamento bem-sucedido de 5 plugins independentes / dependentes em cadeia
    plugins_src = {
        "plugin_core.py": """
from main import Plugin, PluginMetadata
class CorePlugin(Plugin):
    metadata = PluginMetadata("core", "1.0.0")
    def initialize(self, ctx): ctx['core'] = 'loaded'
""",
        "plugin_auth.py": """
from main import Plugin, PluginMetadata
class AuthPlugin(Plugin):
    metadata = PluginMetadata("auth", "1.2.0", {"core": "^1.0.0"})
    def initialize(self, ctx): ctx['auth'] = 'loaded'
""",
        "plugin_db.py": """
from main import Plugin, PluginMetadata
class DBPlugin(Plugin):
    metadata = PluginMetadata("db", "2.0.1", {"core": ">=1.0.0"})
    def initialize(self, ctx): ctx['db'] = 'loaded'
""",
        "plugin_api.py": """
from main import Plugin, PluginMetadata
class APIPlugin(Plugin):
    metadata = PluginMetadata("api", "1.1.0", {"auth": "^1.0.0", "db": "^2.0.0"})
    def initialize(self, ctx): ctx['api'] = 'loaded'
""",
        "plugin_ui.py": """
from main import Plugin, PluginMetadata
class UIPlugin(Plugin):
    metadata = PluginMetadata("ui", "1.0.0", {"api": "^1.0.0"})
    def initialize(self, ctx): ctx['ui'] = 'loaded'
"""
    }

    dir_test = "./temp_plugins"
    setup_mock_plugins_dir(dir_test, plugins_src)

    # Medição de overhead de carregamento
    start_time = time.perf_counter()
    loader = PluginLoader(dir_test)
    raw_plugins = loader.discover_and_load()
    load_order = DependencyResolver.resolve_order(raw_plugins)
    
    context = {}
    for p_name in load_order:
        raw_plugins[p_name].initialize(context)
    end_time = time.perf_counter()

    print(f"[Sucesso] 5 plugins carregados e inicializados na ordem correta: {load_order}")
    print(f"Contexto resultante: {context}")
    print(f"Tempo total de carregamento e resolução: {(end_time - start_time) * 1000:.4f} ms")

    # Teste 2: Tratamento de Dependência Circular (Contraexemplo do equívoco comum)
    circular_src = {
        "plugin_a.py": """
from main import Plugin, PluginMetadata
class PluginA(Plugin):
    metadata = PluginMetadata("plugin_a", "1.0.0", {"plugin_b": "*"})
""",
        "plugin_b.py": """
from main import Plugin, PluginMetadata
class PluginB(Plugin):
    metadata = PluginMetadata("plugin_b", "1.0.0", {"plugin_a": "*"})
"""
    }
    dir_circular = "./temp_circular"
    setup_mock_plugins_dir(dir_circular, circular_src)

    print("\n--- Testando Detecção de Dependência Circular ---")
    try:
        circ_loader = PluginLoader(dir_circular)
        circ_plugins = circ_loader.discover_and_load()
        DependencyResolver.resolve_order(circ_plugins)
        raise AssertionError("Deveria ter falhado por dependência circular!")
    except CircularDependencyError as e:
        print(f"[Capturado com Sucesso] CircularDependencyError lançado corretamente: {e}")

    # Limpeza
    shutil.rmtree(dir_test)
    shutil.rmtree(dir_circular)
    print("\n=== TODOS OS TESTES EXECUTADOS COM SUCESSO ===")