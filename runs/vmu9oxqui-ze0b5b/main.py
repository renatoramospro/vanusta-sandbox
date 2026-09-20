import sys
from dataclasses import dataclass, field
from typing import Dict, List, Set

# --- 1. Definições de Metadados e Exceções ---

@dataclass
class PluginMetadata:
    name: str
    version: str
    dependencies: List[str] = field(default_factory=list)

class PluginError(Exception):
    pass

class CircularDependencyError(PluginError):
    pass

class MissingDependencyError(PluginError):
    pass

# --- 2. Interface Base do Plugin ---

class Plugin:
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata

    def initialize(self) -> None:
        pass

# --- 3. Gerenciador de Plugins ---

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.metadata_registry: Dict[str, PluginMetadata] = {}

    def register_plugin(self, plugin: Plugin) -> None:
        """Registra o plugin e seus metadados no sistema."""
        self.metadata_registry[plugin.metadata.name] = plugin.metadata
        self.plugins[plugin.metadata.name] = plugin

    def resolve_load_order(self) -> List[str]:
        """
        Resolve a ordem de carregamento usando DFS com detecção de ciclos.
        Estados:
        - Não presente no set 'visited' e 'visiting': UNVISITED
        - Presente em 'visiting': VISITING (Ciclo detectado!)
        - Presente em 'visited': VISITED
        """
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
            
            # Visitar dependências primeiro (Post-order traversal)
            for dep in self.metadata_registry[name].dependencies:
                dfs(dep)

            visiting.remove(name)
            visited.add(name)
            order.append(name)

        # Iniciar DFS para todos os plugins registrados
        for plugin_name in self.metadata_registry:
            if plugin_name not in visited:
                dfs(plugin_name)
        
        return order

    def load_all(self) -> List[str]:
        """Carrega os plugins na ordem correta."""
        order = self.resolve_load_order()
        loaded = []
        for name in order:
            self.plugins[name].initialize()
            loaded.append(name)
        return loaded

# --- 4. Experimento e Testes ---

class MockPlugin(Plugin):
    def __init__(self, metadata: PluginMetadata, log_msg: str = ""):
        super().__init__(metadata)
        self.log_msg = log_msg

    def initialize(self) -> None:
        if self.log_msg:
            print(self.log_msg)

def run_experiment():
    print("=== INICIANDO TESTES DO SISTEMA DE PLUGINS ===")

    # --- Teste 1: Carregamento bem-sucedido com dependências complexas ---
    print("\n--- Teste 1: Carregamento com Dependências (DAG) ---")
    manager = PluginManager()
    
    # Estrutura: A -> B, A -> C, B -> D, C -> D (D é base)
    p_d = MockPlugin(PluginMetadata("D", "1.0.0"), "Plugin D inicializado.")
    p_c = MockPlugin(PluginMetadata("C", "1.0.0", ["D"]), "Plugin C inicializado.")
    p_b = MockPlugin(PluginMetadata("B", "1.0.0", ["D"]), "Plugin B inicializado.")
    p_a = MockPlugin(PluginMetadata("A", "1.0.0", ["B", "C"]), "Plugin A inicializado.")

    for p in [p_a, p_b, p_c, p_d]:
        manager.register_plugin(p)

    try:
        loaded_order = manager.load_all()
        print(f"[Sucesso] Plugins carregados na ordem: {loaded_order}")
        
        # Verificação da ordem: D deve vir antes de B e C; B e C antes de A.
        assert loaded_order.index("D") < loaded_order.index("B")
        assert loaded_order.index("D") < loaded_order.index("C")
        assert loaded_order.index("B") < loaded_order.index("A")
        assert loaded_order.index("C") < loaded_order.index("A")
        print("[Sucesso] Ordem topológica validada.")
    except Exception as e:
        print(f"[Falha] Erro inesperado no Teste 1: {e}")
        sys.exit(1)

    # --- Teste 2: Detecção de Dependência Circular ---
    print("\n--- Teste 2: Detecção de Dependência Circular ---")
    manager_circ = PluginManager()
    
    # Ciclo: X -> Y, Y -> X
    p_x = MockPlugin(PluginMetadata("X", "1.0.0", ["Y"]))
    p_y = MockPlugin(PluginMetadata("Y", "1.0.0", ["X"]))
    
    manager_circ.register_plugin(p_x)
    manager_circ.register_plugin(p_y)

    try:
        manager_circ.load_all()
        print("[Falha] O sistema deveria ter detectado um ciclo!")
        sys.exit(1)
    except CircularDependencyError as e:
        print(f"[Sucesso] Ciclo capturado corretamente: {e}")

    # --- Teste 3: Dependência Inexistente ---
    print("\n--- Teste 3: Dependência Inexistente ---")
    manager_miss = PluginManager()
    p_m = MockPlugin(PluginMetadata("M", "1.0.0", ["Ghost"]))
    manager_miss.register_plugin(p_m)

    try:
        manager_miss.load_all()
        print("[Falha] O sistema deveria ter detectado dependência ausente!")
        sys.exit(1)
    except MissingDependencyError as e:
        print(f"[Sucesso] Erro de dependência ausente capturado: {e}")

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO ===")

if __name__ == "__main__":
    run_experiment()