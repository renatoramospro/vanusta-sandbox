import concurrent.futures
import time
import threading
import inspect
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

        for task_name in self.tasks:
            if task_name not in visited:
                if dfs(task_name):
                    raise ValueError("O grafo de tarefas contém um ciclo (não é um DAG válido).")

class WorkflowEngine:
    def __init__(self, dag: WorkflowDAG, max_workers: int = 4):
        self.dag = dag
        self.max_workers = max_workers
        self.dag.validate_dag()

    def run_dag(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        task_states: Dict[str, str] = {name: "PENDING" for name in self.dag.tasks}
        in_degree: Dict[str, int] = {name: len(self.dag.dependencies[name]) for name in self.dag.tasks}
        
        lock = threading.Lock()
        failure_event = threading.Event()
        execution_error: List[Exception] = []

        # Fila de nós prontos para execução inicial (grau de entrada 0)
        ready_queue = [name for name, deg in in_degree.items() if deg == 0]

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}

            def submit_task(task_name: str):
                if failure_event.is_set():
                    return
                with lock:
                    task_states[task_name] = "RUNNING"
                
                task = self.dag.tasks[task_name]
                parents = self.dag.dependencies[task_name]
                
                # Monta os resultados dos pais para injeção de data-flow
                parent_results = {p: results[p] for p in parents if p in results}

                future = executor.submit(self._execute_task_wrapper, task, parent_results)
                future_to_task[future] = task_name

            with lock:
                for t_name in ready_queue:
                    submit_task(t_name)

            while future_to_task and not failure_event.is_set():
                # Aguarda a conclusão de qualquer tarefa em andamento
                done, _ = concurrent.futures.wait(
                    future_to_task.keys(),
                    return_when=concurrent.futures.FIRST_COMPLETED
                )

                if failure_event.is_set():
                    break

                for future in done:
                    task_name = future_to_task.pop(future)
                    try:
                        res = future.result()
                        with lock:
                            results[task_name] = res
                            task_states[task_name] = "COMPLETED"

                        # Libera os dependentes cujos pais foram concluídos
                        with lock:
                            for child in self.dag.dependents.get(task_name, []):
                                if failure_event.is_set():
                                    break
                                in_degree[child] -= 1
                                if in_degree[child] == 0 and task_states[child] == "PENDING":
                                    submit_task(child)

                    except Exception as e:
                        with lock:
                            task_states[task_name] = "FAILED"
                            failure_event.set()
                            execution_error.append(e)
                        # Interrompe o loop de espera imediatamente
                        break

            if failure_event.is_set():
                err = execution_error[0] if execution_error else RuntimeError("Erro desconhecido no workflow.")
                raise RuntimeError(f"Workflow interrompido devido a falha: {err}") from err

        return results

    def _execute_task_wrapper(self, task: Task, parent_results: Dict[str, Any]) -> Any:
        try:
            sig = inspect.signature(task.func)
            accepts_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            has_param = 'parent_results' in sig.parameters

            if accepts_kwargs or has_param:
                # Injeta parent_results se a função aceitar explicitamente ou via **kwargs
                return task.func(*task.args, parent_results=parent_results, **task.kwargs)
            else:
                return task.func(*task.args, **task.kwargs)
        except Exception as e:
            raise RuntimeError(f"Tarefa '{task.name}' falhou: {e}") from e