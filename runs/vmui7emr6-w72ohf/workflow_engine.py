import concurrent.futures
import time
from typing import Callable, Dict, List, Set, Any

class Task:
    def __init__(self, name: str, func: Callable[..., Any], *args, **kwargs):
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs

class WorkflowDAG:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, Set[str]] = {} # task -> set of parents
        self.dependents: Dict[str, Set[str]] = {}   # task -> set of children

    def add_task(self, task: Task, depends_on: List[str] = None):
        if task.name in self.tasks:
            raise ValueError(f"Tarefa '{task.name}' já existe no workflow.")
        self.tasks[task.name] = task
        self.dependencies[task.name] = set(depends_on or [])
        self.dependents.setdefault(task.name, set())

        for parent in self.dependencies[task.name]:
            if parent not in self.tasks:
                raise ValueError(f"Dependência '{parent}' não encontrada para a tarefa '{task.name}'.")
            self.dependents.setdefault(parent, set()).add(task.name)

    def validate_dag(self):
        # Detecção de ciclos usando DFS
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.dependents.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in self.tasks:
            if node not in visited:
                if dfs(node):
                    raise ValueError("Ciclo detectado no grafo de tarefas! O workflow deve ser um DAG.")

class WorkflowEngine:
    def __init__(self, dag: WorkflowDAG, max_workers: int = 4):
        self.dag = dag
        self.max_workers = max_workers

    def run(self) -> Dict[str, Any]:
        self.dag.validate_dag()
        
        in_degree = {node: len(self.dag.dependencies[node]) for node in self.dag.tasks}
        results: Dict[str, Any] = {}
        failed = False
        error_message = None

        # Fila de nós prontos para execução
        ready_queue = [node for node, degree in in_degree.items() if degree == 0]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}

            while ready_queue or future_to_task:
                if failed:
                    # Se houve falha, cancela futuros pendentes e sai
                    for f in future_to_task:
                        f.cancel()
                    break

                # Enfileira todas as tarefas que estão prontas
                while ready_queue:
                    node = ready_queue.pop(0)
                    task = self.dag.tasks[node]
                    future = executor.submit(task.func, *task.args, **task.kwargs)
                    future_to_task[future] = node

                if not future_to_task:
                    break

                # Espera pelo menos uma tarefa terminar
                done, _ = concurrent.futures.wait(
                    future_to_task.keys(), 
                    return_when=concurrent.futures.FIRST_COMPLETED
                )

                for future in done:
                    node = future_to_task.pop(future)
                    try:
                        result = future.result()
                        results[node] = result
                        
                        # Decrementa o grau de entrada dos filhos
                        for child in self.dag.dependents.get(node, []):
                            in_degree[child] -= 1
                            if in_degree[child] == 0:
                                ready_queue.append(child)

                    except Exception as exc:
                        failed = True
                        error_message = f"Tarefa '{node}' falhou com erro: {exc}"
                        break

        if failed:
            raise RuntimeError(f"Workflow interrompido devido a falha: {error_message}")

        return results