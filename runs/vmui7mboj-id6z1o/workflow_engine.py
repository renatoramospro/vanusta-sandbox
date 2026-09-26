import concurrent.futures
import time
import threading
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
                    raise ValueError(f"Ciclo detectado no DAG envolvendo a tarefa '{task_name}'.")

class WorkflowEngine:
    def __init__(self, dag: WorkflowDAG, max_workers: int = 4):
        self.dag = dag
        self.max_workers = max_workers
        self.dag.validate_dag()

    def run(self) -> Dict[str, Any]:
        in_degree = {name: len(parents) for name, parents in self.dag.dependencies.items()}
        results: Dict[str, Any] = {}
        lock = threading.Lock()
        
        # Fila de tarefas prontas para execução (grau de entrada 0)
        ready_queue = [name for name, deg in in_degree.items() if deg == 0]
        
        running_futures = {}
        execution_error = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            
            def submit_ready_tasks():
                nonlocal execution_error
                if execution_error:
                    return
                for name in list(ready_queue):
                    if execution_error:
                        break
                    ready_queue.remove(name)
                    task = self.dag.tasks[name]
                    
                    # Coleta resultados dos pais para injetar na tarefa filha (Data-Flow)
                    parent_results = {p: results[p] for p in self.dag.dependencies[name]}
                    
                    future = executor.submit(self._execute_task, task, parent_results)
                    running_futures[future] = name

            with lock:
                submit_ready_tasks()

            while running_futures:
                if execution_error:
                    # Cancela futuros pendentes que ainda não iniciaram
                    for f in list(running_futures.keys()):
                        f.cancel()
                    break

                done, _ = concurrent.futures.wait(
                    running_futures.keys(),
                    return_when=concurrent.futures.FIRST_COMPLETED
                )

                for future in done:
                    task_name = running_futures.pop(future)
                    try:
                        res = future.result()
                        with lock:
                            results[task_name] = res
                            # Libera dependentes
                            for child in self.dag.dependents.get(task_name, []):
                                in_degree[child] -= 1
                                if in_degree[child] == 0 and not execution_error:
                                    ready_queue.append(child)
                            submit_ready_tasks()
                    except Exception as e:
                        with lock:
                            execution_error = RuntimeError(f"Tarefa '{task_name}' falhou: {e}")
                            # Interrompe o processamento propagando o erro

        if execution_error:
            raise execution_error

        return results

    def _execute_task(self, task: Task, parent_results: Dict[str, Any]):
        # Passa os resultados das dependências para a função se ela aceitar ou via kwargs
        return task.func(*task.args, parent_results=parent_results, **task.kwargs)