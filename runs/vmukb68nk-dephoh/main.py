path=experiment_cell_isolation.py
import time

class SharedInfraDatabaseCluster:
    """Simula um cluster de banco de dados compartilhado entre múltiplas células."""
    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self.active_connections = 0

    def query(self, cell_name: str, connections_needed: int):
        if self.active_connections + connections_needed > self.max_connections:
            raise RuntimeError(f"FALHA DE ISOLAMENTO: Célula '{cell_name}' esgotou o pool de conexões compartilhado!")
        self.active_connections += connections_needed
        print(f"[{cell_name}] Query executada com sucesso. Conexões ativas: {self.active_connections}/{self.max_connections}")

def run_experiment():
    print("--- INÍCIO DO EXPERIMENTO: Teste de Isolamento de Célula ---")
    cluster = SharedInfraDatabaseCluster(max_connections=5)

    # Célula A consome conexões normais
    try:
        cluster.query("Cell-A", 2)
    except Exception as e:
        print(e)

    # Célula B realiza um pico de carga (bad query / leak) e esgota o cluster compartilhado
    try:
        print("\n[Cell-B] Iniciando pico de carga...")
        cluster.query("Cell-B", 4) # 2 + 4 = 6 (> 5 max)
    except RuntimeError as err:
        print(f"CAPTURADO O EQUÍVOCO: {err}")
        print("Conclusão: Compartilhar infraestrutura física de dados quebra o isolamento de falhas entre células.")

if __name__ == "__main__":
    run_experiment()