import time
import pytest
from workflow_engine import Task, WorkflowDAG, WorkflowEngine

def test_successful_dag_execution():
    """
    Testa um DAG de 5 tarefas:
    T1 (sem deps) e T2 (sem deps) rodam em paralelo.
    T3 depende de T1.
    T4 depende de T1 e T2.
    T5 depende de T3 e T4.
    """
    execution_log = []

    def task_func(name, duration=0.01):
        time.sleep(duration)
        execution_log.append(name)
        return f"Resultado_{name}"

    dag = WorkflowDAG()
    dag.add_task(Task("T1", task_func, "T1"))
    dag.add_task(Task("T2", task_func, "T2"))
    dag.add_task(Task("T3", task_func, "T3"), depends_on=["T1"])
    dag.add_task(Task("T4", task_func, "T4"), depends_on=["T1", "T2"])
    dag.add_task(Task("T5", task_func, "T5"), depends_on=["T3", "T4"])

    engine = WorkflowEngine(dag, max_workers=2)
    results = engine.run()

    print(f"Ordem de execução registrada: {execution_log}")
    print(f"Resultados finais: {results}")

    # Verificações fundamentais
    assert set(results.keys()) == {"T1", "T2", "T3", "T4", "T5"}
    # T1 e T2 devem rodar antes de seus dependentes
    assert execution_log.index("T1") < execution_log.index("T3")
    assert execution_log.index("T1") < execution_log.index("T4")
    assert execution_log.index("T2") < execution_log.index("T4")
    assert execution_log.index("T3") < execution_log.index("T5")
    assert execution_log.index("T4") < execution_log.index("T5")

def test_failure_propagation():
    """
    Testa se uma falha em uma tarefa intermediária interrompe o fluxo corretamente.
    """
    def task_ok(name):
        return f"Ok_{name}"

    def task_fail():
        raise ValueError("Erro crítico na tarefa!")

    dag = WorkflowDAG()
    dag.add_task(Task("T1", task_ok, "T1"))
    dag.add_task(Task("T2", task_fail), depends_on=["T1"])
    dag.add_task(Task("T3", task_ok, "T3"), depends_on=["T2"])

    engine = WorkflowEngine(dag)
    
    with pytest.raises(RuntimeError) as excinfo:
        engine.run()
    
    print(f"Erro capturado com sucesso: {excinfo.value}")
    assert "Tarefa 'T2' falhou" in str(excinfo.value)

if __name__ == "__main__":
    test_successful_dag_execution()
    test_failure_propagation