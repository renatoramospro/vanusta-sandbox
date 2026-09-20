import sys
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

# --- 1. Definições de Metadados e Exceções ---

@dataclass
class PluginMetadata:
    name: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    # Lista de dependências no formato "plugin_name>=1.0.0"

class PluginError(Exception):
    pass

class CircularDependencyError(PluginError):
    pass

class VersionIncompatibleError(PluginError):
    pass

# --- 2. Interface Base do Plugin ---

class Plugin:
    metadata: PluginMetadata

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

# --- 3. Resolvedor e Gerenciador de Plugins ---

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.metadata_registry: Dict[str, PluginMetadata] = {}

    def register_metadata(self, metadata: PluginMetadata) -> None:
        if metadata.name in self.metadata_registry:
            raise PluginError(f"Plugin '{metadata.name}' já registrado.")
        self.metadata_registry[metadata.name] = metadata

    def resolve_load_order(self) -> List[str]:
        """
        Calcula a ordem topológica de carregamento utilizando Kahn's algorithm
        ou DFS, detectando explicitamente dependências circulares.
        """
        visited = set()
        temp_mark = set()
        order = []

        def visit(name: str):
            if name in temp_mark:
                raise CircularDependencyError(f"Dependência circular detectada envolvendo o plugin '{name}'.")
            if name not in visited:
                temp_mark.add(name)
                meta = self.metadata_registry.get(name)
                if not meta:
                    raise PluginError(f"Plugin dependência '{name}' não encontrado.")
                
                # Extrair apenas o nome base da dependência (ignorando por ora operadores complexos para simplicidade)
                for dep_req in meta.dependencies:
                    dep_name = dep_req.split(">=")[0].split("==")[0].strip()
                    visit(dep_name)

                temp_mark.remove(name)
                visited.add(name)
                order.append(name)

        for name in self.metadata_registry:
            if name not in visited:
                visit(name)

        return order

    def load_plugin_instance(self, name: str, plugin_instance: Plugin) -> None:
        self.plugins[name] = plugin_instance
        plugin_instance.initialize()

# --- 4. Demonstração e Testes Práticos ---

# Vamos simular plugins dinâmicos criando instâncias e testando o DAG

class MockPluginA(Plugin):
    def __init__(self):
        self.metadata = PluginMetadata(name="plugin_a", version="1.0.0", dependencies=[])
    def initialize(self):
        print("Plugin A inicializado com sucesso.")

class MockPluginB(Plugin):
    def __init__(self):
        self.metadata = PluginMetadata(name="plugin_b", version="1.2.0", dependencies=["plugin_a>=1.0.0"])
    def initialize(self):
        print("Plugin B inicializado com sucesso.")

class MockPluginCircular1(Plugin):
    def __init__(self):
        self.metadata = PluginMetadata(name="circ_1", version="1.0.0", dependencies=["circ_2"])

class MockPluginCircular2(Plugin):
    def __init__(self):
        self.metadata = PluginMetadata(name="circ_2", version="1.0.0", dependencies=["circ_1"])


def run_experiment():
    print("--- Teste 1: Carregamento bem-sucedido com Dependência Direta ---")
    manager = PluginManager()
    
    plugin_a = MockPluginA()
    plugin_b = MockPluginB()
    
    manager.register_metadata(plugin_a.metadata)
    manager.register_metadata(plugin_b.metadata)
    
    order = manager.resolve_load_order()
    print(f"Ordem topológica resolvida: {order}")
    assert order == ["plugin_a", "plugin_b"], f"Ordem esperada incorreta: {order}"

    for name in order:
        inst = plugin_a if name == "plugin_a" else plugin_b
        manager.load_plugin_instance(name, inst)

    print("\n--- Teste 2: Detecção de Dependência Circular (Contraexemplo) ---")
    manager_circ = PluginManager()
    c1 = MockPluginCircular1()
    c2 = MockPluginCircular2()
    
    manager_circ.register_metadata(c1.metadata)
    manager_circ.register_metadata(c2.metadata)

    try:
        manager_circ.resolve_load_order()
    except CircularDependencyError as e:
        print(f"Sucesso: Erro circular capturado corretamente: {e}")

if __name__ == "__main__":
    run_experiment()