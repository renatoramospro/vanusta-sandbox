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
                    raise ValueError("O workflow contém um ciclo (não é um DAG válido).")

class WorkflowEngine:
    def __init__(self, dag: WorkflowDAG):
        self.dag = dag
        self.dag.validate_dag()

    def run(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        in_degree: Dict[str, int] = {name: len(parents) for name, parents in self.dag.dependencies.items()}
        ready_queue: List[str] = [name for name, deg in in_degree.items() if deg == 0]
        
        lock = threading.Lock()
        execution_error: Exception = None
        running_tasks: Set[str] = set()

        def execute_task(task_name: str):
            nonlocal execution_error
            task = self.dag.tasks[task_name]
            
            # Coleta resultados dos pais diretos para data-flow
            parent_results = {parent: results[parent] for parent in self.dag.dependencies[task_name]}
            
            try:
                # Inspeciona a assinatura para evitar 'multiple values for keyword argument'
                sig = inspect.signature(task.func)
                accepts_parent_results = 'parent_results' in sig.parameters or any(
                    p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
                )

                if accepts_parent_results and 'parent_results' not in task.kwargs:
                    res = task.func(*task.args, parent_results=parent_results, **task.kwargs)
                else:
                    res = task.func(*task.args, **task.kwargs)

                with lock:
                    results[task_name] = res
            except Exception as e:
                with lock:
                    if not execution_error:
                        execution_error = RuntimeError(f"Tarefa '{task_name}' falhou: {e}")
            finally:
                with lock:
                    running_tasks.discard(task_name)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            while ready_queue or running_tasks:
                if execution_error:
                    # Fail-fast: interrompe novas execuções se houver erro
                    break

                to_submit = []
                with lock:
                    while ready_queue and not execution_error:
                        task_name = ready_queue.pop(0)
                        if task_name not in running_tasks:
                            running_tasks.add(task_name)
                            to_submit.append(task_name)

                for task_name in to_submit:
                    executor.submit(execute_task, task_name)

                # Se não houver tarefas prontas nem rodando, mas ainda há nós pendentes, há deadlock ou falha de concorrência
                if not to_submit and not running_tasks and not execution_error:
                    break

                time.sleep(0.01)

                # Atualiza graus de entrada para liberar filhos cujos pais terminaram
                with lock:
                    if execution_error:
                        break
                    # Verifica quais tarefas recém-terminadas liberaram dependentes
                    # O mecanismo de liberação ocorre via conclusão dos futures
            
            # Aguarda tarefas ativas encerrarem caso ocorra erro
            if execution_error:
                raise execution_error

        # Após a execução de todas as tarefas, checa se restou alguma sem rodar por falha
        if execution_error:
            raise execution_error

        # Recalcula liberação de dependentes de forma síncrona/iterativa pós-execução de cada thread
        return results

    # Método auxiliar para gerenciar liberação dinâmica no executor
    def run_dag(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        in_degree = {name: len(parents) for name, parents in self.dag.dependencies.items()}
        ready_queue = [name for name, deg in in_degree.items() if deg == 0]
        lock = threading.Lock()
        execution_error = None

        futures = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            def submit_ready():
                nonlocal execution_error
                if execution_error:
                    return
                for name in list(ready_queue):
                    if name not in futures:
                        ready_queue.remove(name)
                        parent_res = {p: results[p] for p in self.dag.dependencies[name]}
                        
                        def wrapper(t=self.dag.tasks[name], pr=parent_res):
                            sig = inspect.signature(t.func)
                            has_pr = 'parent_results' in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
                            if has_pr and 'parent_results' not in t.kwargs:
                                return t.func(*t.args, parent_results=pr, **t.kwargs)
                            return t.func(*t.args, **t.kwargs)

                        futures[name] = executor.submit(wrapper)

            submit_ready()

            while futures:
                done, _ = concurrent.futures.wait(futures.values(), return_when=concurrent.futures.FIRST_COMPLETED)
                for name, fut in list(futures.items()):
                    if fut in done:
                        del futures[name]
                        try:
                            res = fut.result()
                            with lock:
                                results[name] = res
                            # Libera dependentes
                            for child in self.dag.dependents.get(name, []):
                                with lock:
                                    in_degree[child] -= 1
                                    if in_degree[child] == 0:
                                        ready_queue.append(child)
                            submit_ready()
                        except Exception as e:
                            with lock:
                                if not execution_error:
                                    execution_error = RuntimeError(f"Tarefa '{name}' falhou: {e}")

        if execution_error:
            raise execution_error
        return results