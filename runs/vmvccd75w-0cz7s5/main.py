import time
import sys

class CooperativeScheduler:
    def __init__(self):
        self.task_queue = []

    def spawn(self, coroutine):
        """Adiciona uma nova tarefa (gerador) à fila do scheduler."""
        self.task_queue.append(coroutine)

    def run(self):
        """Executa o loop principal do scheduler em política Round-Robin."""
        completed_tasks = 0
        while self.task_queue:
            # Remove a primeira tarefa da fila (FIFO)
            task = self.task_queue.pop(0)
            try:
                # Retoma a execução da corrotina até o próximo yield
                # O valor enviado para o send() pode ser usado se a corrotina esperar um valor
                task.send(None)
                # Se não esgotou, joga de volta ao final da fila (Round-Robin)
                self.task_queue.append(task)
            except StopIteration:
                # A corrotina terminou sua execução
                completed_tasks += 1
            except Exception as e:
                # Tratamento de robustez: se uma tarefa falhar, o scheduler sobrevive
                print(f"[Aviso] Tarefa lançou exceção tratada pelo scheduler: {e}")
        
        return completed_tasks

# Função geradora que simula uma tarefa cooperativa
def worker_task(task_id, steps, results_dict):
    counter = 0
    for i in range(steps):
        counter += 1
        # Cede o controle voluntariamente para o scheduler
        yield
    results_dict[task_id] = counter

if __name__ == "__main__":
    print("Iniciando teste de 10.000 corrotinas cooperativas...")
    scheduler = CooperativeScheduler()
    results = {}
    
    num_tasks = 10000
    steps_per_task = 5

    # Criando 10.000 corrotinas
    for i in range(num_tasks):
        scheduler.spawn(worker_task(i, steps_per_task, results))

    start_time = time.perf_counter()
    completed = scheduler.run()
    end_time = time.perf_counter()

    total_time_ms = (end_time - start_time) * 1000.0
    total_switches = num_tasks * steps_per_task
    # Evita divisão por zero caso total_switches seja 0 (não é o caso)
    avg_switch_overhead_us = (total_time_ms * 1000.0) / total_switches if total_switches > 0 else 0

    print(f"Tarefas concluídas com sucesso: {completed}/{num_tasks}")
    print(f"Tempo total de execução: {total_time_ms:.4f} ms")
    print(f"Total de trocas de contexto (yield/resume): {total_switches}")
    print(f"Overhead médio por troca de contexto: {avg_switch_overhead_us:.3f} µs")

    # Validações e Asserções para garantir o critério de sucesso
    assert completed == num_tasks, f"Erro: Apenas {completed} de {num_tasks} terminaram."
    assert len(results) == num_tasks, "Erro: Nem todas as tarefas registraram resultados."
    
    # O overhead médio por troca deve ser amplamente inferior a 1ms (1000us), tipicamente < 5us em Python
    assert avg_switch_overhead_us < 1000.0, f"Overhead muito alto: {avg_switch_overhead_us} µs"
    print("SUCESSO: Todas as asserções passaram com folga!")