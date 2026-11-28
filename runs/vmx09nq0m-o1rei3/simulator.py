import time
import random
from collections import deque

# Configurações da simulação
TIME_SLOT = 1  # Unidade de tempo de processamento
NUM_TASKS = 4
CRITICAL_SLA = 50  # ms (simulado em unidades de tempo)
TARGET_REDUCTION = 0.15

class Task:
    def __init__(self, task_id, required_time, is_critical):
        self.id = task_id
        self.required_time = required_time
        self.remaining_time = required_time
        self.is_critical = is_critical
        self.arrival_time = 0
        self.start_time = -1
        self.finish_time = -1

    def __repr__(self):
        crit = "CRITICAL" if self.is_critical else "Normal"
        return f"Task {self.id} ({crit}, Rem: {self.remaining_time})"

def simulate(tasks, scheduler_type):
    # Resetar estados para simulação limpa
    for task in tasks:
        task.remaining_time = task.required_time
        task.start_time = -1
        task.finish_time = -1

    current_time = 0
    completed_tasks = 0
    
    # Usaremos uma lista de tarefas prontas para agendamento
    ready_queue = list(tasks)
    
    # Função de seleção de agendamento
    if scheduler_type == "RR":
        # RR simplesmente pega o próximo na lista (FIFO/Round-Robin implícito)
        def select_task():
            if not ready_queue: return None
            return ready_queue.pop(0)
    elif scheduler_type == "EDF":
        # EDF: Prioriza a tarefa com o menor prazo (neste caso, a mais crítica primeiro)
        # Simplificação: Tarefas críticas têm prioridade máxima.
        def select_task():
            if not ready_queue: return None
            # Ordena: Críticas primeiro, depois por tempo restante (heurística simples)
            ready_queue.sort(key=lambda t: (not t.is_critical, t.remaining_time))
            return ready_queue.pop(0)
    else:
        raise ValueError("Scheduler desconhecido")

    # Loop de simulação
    while completed_tasks < len(tasks):
        task_to_run = select_task()
        
        if task_to_run:
            # Registrar início se for a primeira vez
            if task_to_run.start_time == -1:
                task_to_run.start_time = current_time
            
            # Executar um slot de tempo
            task_to_run.remaining_time -= TIME_SLOT
            current_time += TIME_SLOT

            # Verificar conclusão
            if task_to_run.remaining_time <= 0:
                task_to_run.finish_time = current_time
                completed_tasks += 1
        else:
            # Se a fila estiver vazia, avança o tempo (não deve ocorrer com tarefas pré-carregadas)
            current_time += TIME_SLOT
            
    # Calcular métricas
    critical_latencies = []
    for task in tasks:
        if task.is_critical:
            # Latência = Tempo de Conclusão - Tempo de Chegada (assumindo chegada em 0)
            latency = task.finish_time - task.arrival_time
            critical_latencies.append(latency)
            
    if not critical_latencies:
        return {"P95": 0, "mean": 0}

    critical_latencies.sort()
    
    # Calcular P95 (índice ceil(0.95 * N) - 1)
    p95_index = int(0.95 * len(critical_latencies))
    p95 = critical_latencies[min(p95_index, len(critical_latencies) - 1)]
    
    mean = sum(critical_latencies) / len(critical_latencies)
    
    return {"P95": p95, "mean": mean}

# --- Setup e Execução do Experimento ---

# Tarefas: T0 (Crítica), T1, T2, T3 (Normais)
tasks_base = [
    Task(0, 10, True),  # Crítica, requer 10 slots
    Task(1, 5, False),
    Task(2, 8, False),
    Task(3, 7, False)
]

def run_experiment(scheduler, runs=3):
    results = []
    print(f"\n--- Executando {scheduler} por {runs} rodadas ---")
    for i in range(runs):
        # Simulação com reset de estado
        metrics = simulate(tasks_base, scheduler)
        results.append(metrics)
        print(f"Rodada {i+1}: P95={metrics['P95']}, Média={metrics['mean']:.2f}")
    
    # Análise estatística
    p95_values = [r['P95'] for r in results]
    mean_values = [r['mean'] for r in results]
    
    avg_p95 = sum(p95_values) / runs
    avg_mean = sum(mean_values) / runs
    
    # Variância (para verificar critério de reprodutibilidade)
    p95_variance = sum([(p - avg_p95)**2 for p in p95_values]) / (runs - 1) if runs > 1 else 0
    
    print("\n--- Resumo Estatístico ---")
    print(f"Média P95: {avg_p95:.2f}")
    print(f"Média Média: {avg_mean:.2f}")
    print(f"Variância P95: {p95_variance:.2f}")
    
    return avg_p95, avg_mean, p95_variance

# 1. Baseline (RR)
rr_p95, rr_mean, rr_var = run_experiment("RR")

# 2. Otimizado (EDF/Prioridade)
edf_p95, edf_mean, edf_var = run_experiment("EDF")

# 3. Verificação do Critério de Sucesso
reduction = (rr_p95 - edf_p95) / rr_p95
is_reduction_met = reduction >= TARGET_REDUCTION
is_reproducible = rr_var / rr_p95 < 0.05 # Variância < 5% do valor base

print("\n=========================================")
print("VERIFICAÇÃO DO CRITÉRIO DE SUCESSO")
print(f"Redução de P95 (RR -> EDF): {reduction*100:.2f}% (Meta: {TARGET_REDUCTION*100:.0f}%)")
print(f"Meta de Redução Atingida: {is_reduction_met}")
print(f"Reprodutibilidade (Var P95 < 5%): {is_reproducible}")
print("=========================================")

if is_reduction_met and is_reproducible:
    print("SUCESSO: O módulo atende aos critérios refinados.")
else:
    print("FALHA: Os critérios refinados não foram totalmente atendidos.")
