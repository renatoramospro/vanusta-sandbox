import time
import random
from collections import deque
import statistics

# --- Configurações da simulação (Ajustadas para estabilidade e teste de rede) ---
TIME_SLOT = 1  # Unidade de tempo de processamento
NUM_TASKS = 4
CRITICAL_SLA = 50  # Unidades de tempo (SLA)
TARGET_REDUCTION = 0.15
MAX_TIME = 100  # Limite de tempo total para evitar timeout
NET_LATENCY = 5  # Simulação de latência de rede fixa (em unidades de tempo)
RUNS = 3

class Task:
    def __init__(self, task_id, required_time, is_critical):
        self.id = task_id
        self.required_time = required_time
        self.remaining_time = required_time
        self.is_critical = is_critical
        self.arrival_time = 0
        self.start_time = -1
        self.finish_time = -1
        self.deadline = 0 # Definido com base no SLA

    def __repr__(self):
        crit = "CRITICAL" if self.is_critical else "Normal"
        return f"Task {self.id} ({crit}, Rem: {self.remaining_time})"

def setup_tasks():
    # T0: Crítica (SLA 50), T1-T3: Normais
    tasks = [
        Task(0, 15, True),  # Crítica
        Task(1, 10, False),
        Task(2, 12, False),
        Task(3, 8, False)
    ]
    # Definir deadlines (Arrival + SLA)
    for task in tasks:
        task.deadline = task.arrival_time + CRITICAL_SLA if task.is_critical else float('inf')
    return tasks

def simulate(tasks, scheduler_type):
    # Resetar estados
    for task in tasks:
        task.remaining_time = task.required_time
        task.start_time = -1
        task.finish_time = -1
    
    current_time = 0
    completed_tasks = 0
    deadline_misses = 0
    
    # Usaremos uma lista de tarefas prontas para agendamento
    ready_queue = list(tasks)
    
    while current_time < MAX_TIME and completed_tasks < len(tasks):
        
        # 1. Seleção de Tarefa
        selected_task = None
        if scheduler_type == "RR":
            if ready_queue:
                selected_task = ready_queue.pop(0)
        elif scheduler_type == "EDF":
            # EDF: Prioriza a tarefa com o menor deadline
            ready_queue.sort(key=lambda t: t.deadline)
            if ready_queue:
                selected_task = ready_queue.pop(0)
        
        if selected_task:
            # 2. Execução (Processamento Local)
            selected_task.remaining_time -= TIME_SLOT
            
            if selected_task.start_time == -1:
                selected_task.start_time = current_time
            
            current_time += TIME_SLOT
            
            # 3. Verificação de Conclusão e Deadline
            if selected_task.remaining_time <= 0:
                selected_task.finish_time = current_time
                completed_tasks += 1
                
                # Verificação de Deadline Miss (incluindo latência de rede)
                # Latência Total = Tempo de Processamento + Latência de Rede
                total_latency = selected_task.finish_time + NET_LATENCY - selected_task.arrival_time
                if selected_task.is_critical and total_latency > selected_task.deadline:
                    deadline_misses += 1
                
                # Colocar de volta na fila se não for o fim da simulação
                if completed_tasks < len(tasks):
                    ready_queue.append(selected_task)
            else:
                # Se não terminou, coloca de volta na fila (para RR/EDF)
                ready_queue.append(selected_task)
        else:
            # Se não houver tarefas prontas, avança o tempo (simulando espera/I/O)
            current_time += TIME_SLOT
            
    # Cálculo de Métricas
    latencies = []
    for task in tasks:
        if task.finish_time != -1:
            # Latência total = Tempo de Término + Latência de Rede - Tempo de Chegada
            latency = task.finish_time + NET_LATENCY - task.arrival_time
            latencies.append(latency)
            
    if not latencies:
        return 0, 0, 0, 0 # Falha total
        
    p95 = statistics.quantiles(latencies, n=100)[94]
    mean_val = statistics.mean(latencies)
    
    return p95, mean_val, deadline_misses, len(latencies)

def run_experiment(scheduler_type):
    tasks = setup_tasks()
    p95, mean_val, misses, count = simulate(tasks, scheduler_type)
    return p95, mean_val, misses, count

# --- Execução Repetida (3 vezes) ---
rr_results = [run_experiment("RR") for _ in range(RUNS)]
edf_results = [run_experiment("EDF") for _ in range(RUNS)]

# Extrair métricas
rr_p95s = [r[0] for r in rr_results]
rr_means = [r[1] for r in rr_results]
rr_misses = [r[2] for r in rr_results]

edf_p95s = [r[0] for r in edf_results]
edf_means = [r[1] for r in edf_results]
edf_misses = [r[2] for r in edf_results]

# Estatísticas Finais
avg_rr_p95 = statistics.mean(rr_p95s)
avg_edf_p95 = statistics.mean(edf_p95s)
avg_rr_mean = statistics.mean(rr_means)
avg_edf_mean = statistics.mean(edf_means)

# Variância P95 (para reprodutibilidade)
rr_p95_variance = statistics.variance(rr_p95s) if RUNS > 1 else 0
edf_p95_variance = statistics.variance(edf_p95s) if RUNS > 1 else 0

print("\n--- Resumo Estatístico ---")
print(f"RR: Média P95={avg_rr_p95:.2f}, Média={avg_rr_mean:.2f}, Misses={sum(rr_misses)}/3")
print(f"EDF: Média P95={avg_edf_p95:.2f}, Média={avg_edf_mean:.2f}, Misses={sum(edf_misses)}/3")
print(f"Variância P95 RR: {rr_p95_variance:.2f}")
print(f"Variância P95 EDF: {edf_p95_variance:.2f}")

# 3. Verificação do Critério de Sucesso
reduction = (avg_rr_p95 - avg_edf_p95) / avg_rr_p95 if avg_rr_p95 > 0 else 0
is_reduction_met = reduction >= TARGET_REDUCTION
# Critério de reprodutibilidade: Variância P95 < 5% do valor base (RR)
is_reproducible = rr_p95_variance / avg_rr_p95 < 0.05 if avg_rr_p95 > 0 else False

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