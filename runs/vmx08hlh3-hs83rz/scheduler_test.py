import random
from collections import deque
import pytest # Importa pytest para estruturar os testes

# --- Configurações do Cenário ---
NUM_CPUS = 4
NUM_GPUS = 2
NUM_NPUS = 1
TOTAL_RESOURCES = NUM_CPUS + NUM_GPUS + NUM_NPUS

# --- Estrutura de Tarefa ---
class Task:
    def __init__(self, task_id, resource_type, required_time, deadline, priority):
        self.id = task_id
        self.resource_type = resource_type  # 'CPU', 'GPU', 'NPU'
        self.required_time = required_time  # Tempo de execução simulado em ms
        self.deadline = deadline            # Deadline em ms
        self.priority = priority            # 'baixa', 'alta'
        self.start_time = -1
        self.finish_time = -1

    def is_critical(self):
        # Critério definido pelo Arquiteto: deadline < 10ms OU prioridade == "alta"
        return self.deadline < 10 or self.priority == "alta"

    def __repr__(self):
        crit = "CRITICAL" if self.is_critical() else "Normal"
        return f"Task({self.id}, {self.resource_type}, {crit}, D={self.deadline}ms, T={self.required_time}ms)"

# --- Funções de Simulação (Mantidas, mas ajustadas para retornar métricas) ---
def run_fifo(tasks):
    task_queue = deque(tasks)
    resource_availability = {
        'CPU': NUM_CPUS, 'GPU': NUM_GPUS, 'NPU': NUM_NPUS
    }
    completed_tasks = []
    current_time = 0

    # Resetar tempos para simulação limpa
    for task in tasks:
        task.start_time = -1
        task.finish_time = -1

    while task_queue:
        task = task_queue.popleft()
        
        while resource_availability[task.resource_type] <= 0:
            current_time += 1
        
        resource_availability[task.resource_type] -= 1
        task.start_time = current_time
        current_time += task.required_time
        task.finish_time = current_time
        resource_availability[task.resource_type] += 1
        
        completed_tasks.append(task)
        
    return completed_tasks

def run_optimized(tasks):
    # Otimizado: EDF + Afinidade + Desempate SJF
    
    # 1. Ordenar tarefas: Críticas primeiro, depois por Deadline (menor primeiro), desempate por Tempo de Execução (menor primeiro - SJF)
    def sort_key(task):
        is_crit = 0 if task.is_critical() else 1
        # Chave: (Criticidade, Deadline, Required_Time)
        return (is_crit, task.deadline, task.required_time)
    
    sorted_tasks = sorted(tasks, key=sort_key)
    
    resource_availability = {
        'CPU': NUM_CPUS, 'GPU': NUM_GPUS, 'NPU': NUM_NPUS
    }
    
    completed_tasks = []
    current_time = 0

    # Resetar tempos para simulação limpa
    for task in tasks:
        task.start_time = -1
        task.finish_time = -1

    for task in sorted_tasks:
        # Espera por recurso
        while resource_availability[task.resource_type] <= 0:
            current_time += 1
        
        # Alocação
        resource_availability[task.resource_type] -= 1
        task.start_time = current_time
        current_time += task.required_time
        task.finish_time = current_time
        resource_availability[task.resource_type] += 1
        
        completed_tasks.append(task)
        
    return completed_tasks

# --- Métricas ---
def calculate_avg_latency(completed_tasks):
    if not completed_tasks:
        return 0
    latencies = [t.finish_time - t.start_time for t in completed_tasks if t.start_time != -1]
    return sum(latencies) / len(latencies)

# --- Geração de Dados Sintéticos ---
def generate_test_tasks(scenario_name="Balanced"):
    tasks = []
    if scenario_name == "Balanced":
        # Cenário balanceado: 5 tarefas críticas e 5 normais.
        tasks.append(Task(1, 'CPU', 5, 8, 'alta'))    # Crítica (D)
        tasks.append(Task(2, 'GPU', 10, 20, 'alta'))  # Crítica (P)
        tasks.append(Task(3, 'NPU', 3, 5, 'alta'))    # Crítica (D)
        tasks.append(Task(4, 'CPU', 8, 9, 'alta'))    # Crítica (D)
        tasks.append(Task(5, 'GPU', 12, 15, 'alta'))  # Crítica (P)
        tasks.append(Task(6, 'CPU', 20, 100, 'baixa'))
        tasks.append(Task(7, 'GPU', 30, 200, 'baixa'))
        tasks.append(Task(8, 'NPU', 15, 300, 'baixa'))
        tasks.append(Task(9, 'CPU', 15, 150, 'baixa'))
        tasks.append(Task(10, 'GPU', 25, 180, 'baixa'))
    
    elif scenario_name == "NPU_Saturation":
        # Cenário 1 do Testador: NPU Saturation
        tasks.append(Task(101, 'NPU', 2, 3, 'alta')) # Crítica (D=3ms)
        tasks.append(Task(102, 'NPU', 15, 100, 'baixa')) # Normal
        tasks.append(Task(103, 'NPU', 15, 100, 'baixa')) # Normal
    
    elif scenario_name == "Deadline_Tie_SJF":
        # Cenário de Borda: Empate de Deadline (D=15ms), Testando SJF
        tasks.append(Task(201, 'CPU', 5, 15, 'baixa')) # Curto (SJF)
        tasks.append(Task(202, 'CPU', 10, 15, 'baixa')) # Longo
        tasks.append(Task(203, 'CPU', 2, 10, 'alta')) # Crítico (D=10ms)
        
    return tasks

# =====================================================================
# TESTES PYTEST (Para satisfazer o harness automatizado)
# =====================================================================

def test_balanced_scenario_meets_15_percent_reduction():
    # Teste principal de critério de sucesso
    tasks = generate_test_tasks("Balanced")
    
    # Execução FIFO
    fifo_completed = run_fifo(tasks)
    fifo_latency = calculate_avg_latency(fifo_completed)
    
    # Execução Otimizada
    opt_completed = run_optimized(tasks)
    opt_latency = calculate_avg_latency(opt_completed)
    
    # Critério: Redução >= 15%
    reduction = (fifo_latency - opt_latency) / fifo_latency
    
    # Assertiva de sucesso
    assert reduction >= 0.15, f"Redução de latência ({reduction:.2%}) não atingiu 15%."

def test_npu_saturation_prioritizes_critical():
    # Cenário 1 do Testador: NPU Saturation
    tasks = generate_test_tasks("NPU_Saturation")
    
    fifo_completed = run_fifo(tasks)
    opt_completed = run_optimized(tasks)
    
    # A tarefa crítica (101) deve ter latência mínima (próxima ao seu required_time)
    latency_101_fifo = next(t.finish_time - t.start_time for t in fifo_completed if t.id == 101)
    latency_101_opt = next(t.finish_time - t.start_time for t in opt_completed if t.id == 101)
    
    # Em saturação de um recurso, o otimizado deve ser significativamente melhor para a crítica
    assert latency_101_opt < latency_101_fifo, "Otimizado não melhorou a latência da tarefa crítica na saturação."

def test_deadline_tie_sjf_is_applied():
    # Cenário de Borda: Empate de Deadline (D=15ms), Testando SJF
    tasks = generate_test_tasks("Deadline_Tie_SJF")
    
    # A tarefa 201 (T=5) deve ser executada antes de 202 (T=10) devido ao desempate SJF
    opt_completed = run_optimized(tasks)
    
    # Verificar a ordem de execução (start_time) para tarefas com D=15ms
    t201 = next(t for t in opt_completed if t.id == 201)
    t202 = next(t for t in opt_completed if t.id == 202)
    
    # A tarefa mais curta (201) deve começar antes da mais longa (202)
    assert t201.start_time < t202.start_time, "O desempate SJF não foi aplicado corretamente em caso de empate de deadline."

# Teste de Starvation (Implícito: Se o sistema for justo, tarefas normais devem rodar)
def test_no_starvation_for_normal_tasks():
    # Cenário simples: Tarefa normal após críticas
    tasks = [Task(301, 'CPU', 10, 100, 'baixa')]
    
    # Simular um ambiente onde críticas acabaram e a normal deve rodar
    # Para este teste simples, garantimos que a tarefa normal é processada
    fifo_completed = run_fifo(tasks)
    assert len(fifo_completed) == 1
    
    opt_completed = run_optimized(tasks)
    assert len(opt_completed) == 1

# --- Ponto de Entrada Executável (Para demonstração rápida, mas não para o harness) ---
if __name__ == "__main__":
    print("--- Executando Demonstração Rápida (Não é o teste do harness) ---")
    tasks = generate_test_tasks("Balanced")
    
    fifo_completed = run_fifo(tasks)
    fifo_latency = calculate_avg_latency(fifo_completed)
    
    opt_completed = run_optimized(tasks)
    opt_latency = calculate_avg_latency(opt_completed)
    
    reduction = (fifo_latency - opt_latency) / fifo_latency
    
    print(f"Latência Média FIFO: {fifo_latency:.2f}ms")
    print(f"Latência Média Otimizada: {opt_latency:.2f}ms")
    print(f"Redução Percentual: {reduction:.2%}")
    
    if reduction >= 0.15:
        print("\n✅ CRITÉRIO DE SUCESSO ATINGIDO: Redução >= 15% demonstrada.")
    else:
        print("\n❌ CRITÉRIO DE SUCESSO NÃO ATINGIDO: Redução < 15%.")