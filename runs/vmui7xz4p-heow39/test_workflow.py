import time
import pytest
from workflow_engine import Task, WorkflowDAG, WorkflowEngine

def test_concurrent_execution_overlap():
    """
    Comprova sobreposição temporal (concorrência) entre T1 e T2
    ao medir o tempo de execução conjunto versus a soma individual.
    """
    execution_timestamps = {}

    def slow_task(sleep_time, parent_results=None):
        name = "T1" if sleep_time == 0.15 else "T2"
        start = time.time()
        time.sleep(sleep_time)
        end = time.time()
        execution_timestamps[name] = (start, end)
        return f"Result_{name}"

    dag = WorkflowDAG()
    dag.add_task(Task("T1", slow_task, 0.15))
    dag.add_task(Task("T2", slow_task, 0.15))
    dag.add_task(Task("T3", lambda parent_results: len(parent_results["T1"]) + len(parent_results["T2"])), depends_on=["T1", "T2"])

    engine = WorkflowEngine(dag)
    
    start_total = time.time()
    results = engine.run_dag()
    end_total = time.time()

    assert "T1" in execution_timestamps and "T2" in execution_timestamps
    t1_start, t1_end = execution_timestamps["T1"]
    t2_start, t2_end = execution_timestamps["T2"]

    overlap = max(0, min(t1_end, t2_end) - max(t1_start, t2_start))
    print(f"Tempo de sobreposição medida: {overlap:.4f}s")
    
    total_duration = end_total - start_total
    print(f"Duração total do workflow: {total_duration:.4f}s")
    
    # Comprovação de execução concorrente: tempo total menor que a soma serial (0.3s)
    assert total_duration < 0.28, "A execução deveria ocorrer em paralelo/concorrente, mas demorou muito."
    assert results["T3"] == len("Result_T1") + len("Result_T2")

def test_failure_propagation():
    """
    Testa se uma falha em uma tarefa intermediária interrompe o fluxo e propaga o erro.
    """
    def task_ok(parent_results=None):
        return "Ok"

    def task_fail(parent_results=None):
        raise ValueError("Erro crítico simulado!")

    dag = WorkflowDAG()
    dag.add_task(Task("T1", task_ok))
    dag.add_task(Task("T2", task_fail), depends_on=["T1"])
    dag.add_task(Task("T3", task_ok), depends_on=["T2"])

    engine = WorkflowEngine(dag)
    
    with pytest.raises(RuntimeError) as excinfo:
        engine.run_dag()
    
    print(f"Erro capturado com sucesso: {excinfo.value}")
    assert "Tarefa 'T2' falhou" in str(excinfo.value)

if __name__ == "__main__":
    test_concurrent_execution_overlap()
    test_failure_propagation()