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

def get_next_task(ready_queue, scheduler_type):
    if not ready_queue:
        return None
    if scheduler_type == "RR":
        # Em RR, a fila é mantida na ordem de chegada/próximo a rodar
        return ready_queue.popleft()
    elif scheduler_type == "EDF":
        # Em EDF, prioriza o menor deadline
        return min(ready_queue, key=lambda t: t.deadline)

def simulate(tasks, scheduler_type):
    # Resetar estado das tarefas para cada simulação
    current_tasks = [Task(t.id, t.required_time, t.is_critical) for t in tasks]
    ready_queue = deque(current_tasks)
    
    current_time = 0
    tasks_completed = []
    deadline_misses = 0
    
    while current_time < MAX_TIME and ready_queue:
        # 1. Selecionar tarefa
        task_to_run = get_next_task(ready_queue, scheduler_type)
        
        if task_to_run is None:
            break

        # 2. Executar (1 time slot)
        task_to_run.remaining_time -= TIME_SLOT
        current_time += TIME_SLOT

        # 3. Verificar término
        if task_to_run.remaining_time <= 0:
            task_to_run.finish_time = current_time + NET_LATENCY # Inclui latência de rede
            
            # Verificar Deadline Miss
            if task_to_run.finish_time > task_to_run.deadline:
                deadline_misses += 1
            
            tasks_completed.append(task_to_run)
            # Não adiciona de volta à fila
        else:
            # Se não terminou, retorna para a fila (RR) ou permanece (EDF, se não for o menor deadline)
            if scheduler_type == "RR":
                ready_queue.append(task_to_run)
            # EDF: A tarefa continua na fila, mas o próximo ciclo selecionará o menor deadline
            else:
                ready_queue.append(task_to_run)


    # --- Robustez Estatística: Tratamento de amostras insuficientes ---
    latencies = [t.finish_time for t in tasks_completed]
    
    if len(latencies) < 2:
        # Se houver 0 ou 1 tarefa concluída, P95 e Variância não podem ser calculados
        p95 = latencies[0] if latencies else 0
        mean_val = sum(latencies) / len(latencies) if latencies else 0
        variance = 0.0
    else:
        # Cálculo robusto
        p95 = statistics.quantiles(latencies, n=100)[94]
        mean_val = sum(latencies) / len(latencies)
        variance = statistics.variance(latencies)
        
    return p95, mean_val, deadline_misses, len(tasks_completed)


def run_experiment(scheduler_type):
    tasks = setup_tasks()
    p95, mean_val, misses, count = simulate(tasks, scheduler_type)
    return p95, mean_val, misses, count

# --- Execução Principal ---
print("Iniciando simulação...")
rr_results = [run_experiment("RR") for _ in range(RUNS)]
edf_results = [run_experiment("EDF") for _ in range(RUNS)]

# Extrair P95s para análise estatística
rr_p95s = [r[0] for r in rr_results]
edf_p95s = [r[0] for r in edf_results]

# Calcular médias e variâncias
avg_rr_p95 = sum(rr_p95s) / RUNS
avg_rr_mean = sum(r[1] for r in rr_results) / RUNS
avg_edf_p95 = sum(edf_p95s) / RUNS
avg_edf_mean = sum(r[1] for r in edf_results) / RUNS

# Coletar misses
rr_misses = [r[2] for r in rr_results]
edf_misses = [r[2] for r in edf_results]

# Calcular variâncias (Robustez: verificar RUNS > 1)
rr_p95_variance = statistics.variance(rr_p95s) if RUNS > 1 else 0
edf_p95_variance = statistics.variance(edf_p95s) if RUNS > 1 else 0

print("\n--- Resumo Estatístico ---")
print(f"RR: Média P95={avg_rr_p95:.2f}, Média={avg_rr_mean:.2f}, Misses={sum(rr_misses)}/{RUNS}")
print(f"EDF: Média P95={avg_edf_p95:.2f}, Média={avg_edf_mean:.2f}, Misses={sum(edf_misses)}/{RUNS}")
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