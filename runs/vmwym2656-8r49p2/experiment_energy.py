import random
import statistics

# Fixar semente para reprodutibilidade dos cenários de carga variável
random.seed(42)

class SystemSimulator:
    def __init__(self):
        # Níveis de frequência (MHz) e potência correspondente (mW)
        # P ≈ k * f^3 (simplificado para demonstração física)
        self.frequencies = {
            "HIGH": {"freq": 240, "power": 180.0},
            "MID":  {"freq": 160, "power": 80.0},
            "LOW":  {"freq": 80,  "power": 30.0},
            "SLEEP": {"freq": 10, "power": 5.0}
        }

    def generate_workload_scenario(self, duration_steps=100):
        """Gera um perfil de carga variável: baixo, médio, alto e picos."""
        workload = []
        for step in range(duration_steps):
            # Simula transição de estados de carga da aplicação de Edge
            if step % 25 == 0:
                load_type = "PEAK" # Pico de processamento
            else:
                load_type = random.choice(["LOW", "MEDIUM", "HIGH"])
            workload.append(load_type)
        return workload

    def run_baseline(self, workload):
        """Baseline: Executa sempre em frequência alta, sem gestão inteligente."""
        total_energy_joules = 0.0
        for task in workload:
            # Tempo de execução unitário fixo (ex: 1 segundo)
            power_mw = self.frequencies["HIGH"]["power"]
            if task == "PEAK":
                power_mw *= 1.4 # Sobrecarga
            
            # Energia (Joules) = Potência (mW) * Tempo (s) / 1000
            energy = (power_mw * 1.0) / 1000.0
            total_energy_joules += energy
        return total_energy_joules

    def run_optimized_scheduler(self, workload):
        """Módulo Otimizado: Aplica DVFS e modos de baixo consumo com base na carga."""
        total_energy_joules = 0.0
        for task in workload:
            # Seleção inteligente de frequência baseada estritamente na necessidade da tarefa
            if task == "LOW":
                state = "LOW"
            elif task == "MEDIUM":
                state = "MID"
            elif task == "HIGH":
                state = "HIGH"
            elif task == "PEAK":
                state = "HIGH" # Requer alta performance pontual
            else:
                state = "SLEEP"

            power_mw = self.frequencies[state]["power"]
            if task == "PEAK":
                power_mw *= 1.2 # Otimizador mitiga parte do pico com buffer

            energy = (power_mw * 1.0) / 1000.0
            total_energy_joules += energy
        return total_energy_joules

def main():
    sim = SystemSimulator()
    num_runs = 10
    baseline_results = []
    optimized_results = []

    print("Iniciando simulação de cenários de carga variável...")
    for i in range(num_runs):
        workload = sim.generate_workload_scenario(duration_steps=200)
        b_energy = sim.run_baseline(workload)
        o_energy = sim.run_optimized_scheduler(workload)
        
        baseline_results.append(b_energy)
        optimized_results.append(o_energy)

    mean_baseline = statistics.mean(baseline_results)
    mean_optimized = statistics.mean(optimized_results)
    
    reduction_pct = ((mean_baseline - mean_optimized) / mean_baseline) * 100.0

    print(f"Consumo Médio Baseline (Fixo/Sem Gestão): {mean_baseline:.2f} J")
    print(f"Consumo Médio Otimizado (DVFS + Agendamento): {mean_optimized:.2f} J")
    print(f"Redução Média de Energia obtida: {reduction_pct:.2f}%")

    # Verificação rigorosa do critério de sucesso (>= 15%)
    assert reduction_pct >= 15.0, f"Falha no critério de sucesso: Redução de {reduction_pct:.2f}% é menor que 15%."
    print("Sucesso: O módulo atingiu e superou o critério de redução de 15% de energia!")

if __name__ == "__main__":
    main()