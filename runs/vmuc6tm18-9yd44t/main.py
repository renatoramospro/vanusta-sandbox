path=framework_simulation.py
import unittest

class InnovationValueChain:
    """
    Simula a Cadeia de Valor de um Projeto Executivo de Inovação,
    rastreando Atividades, Cost Drivers e Value Drivers.
    """
    def __init__(self, project_name):
        self.project_name = project_name
        self.activities = {}

    def add_activity(self, name, category, cost, value_score):
        """
        category: 'Primary' ou 'Support'
        cost: Custo monetário alocado (ex: em milhares de USD)
        value_score: Pontuação de 1 a 10 representando o impacto na vantagem competitiva
        """
        self.activities[name] = {
            "category": category,
            "cost": cost,
            "value_score": value_score,
            "optimized_cost": cost,
            "optimized_value": value_score
        }

    def optimize_cost_driver(self, name, reduction_percentage, justification):
        """
        Simula a eliminação de desperdício (ex: over-engineering, retrabalho)
        sem afetar o valor gerado.
        """
        if name in self.activities:
            original = self.activities[name]["cost"]
            reduction = original * (reduction_percentage / 100.0)
            self.activities[name]["optimized_cost"] = original - reduction
            print(f"[Cost Driver Otimizado] Atividade '{name}': Custo reduzido de {original} para {self.activities[name]['optimized_cost']:.2f}. Justificativa: {justification}")

    def enhance_value_driver(self, name, value_increment, justification):
        """
        Simula o aumento da geração de valor (ex: IP, robustez, time-to-market).
        """
        if name in self.activities:
            original = self.activities[name]["optimized_value"]
            new_val = min(10.0, original + value_increment)
            self.activities[name]["optimized_value"] = new_val
            print(f"[Value Driver Aprimorado] Atividade '{name}': Valor elevado de {original} para {new_val}. Justificativa: {justification}")

    def evaluate_project_health(self):
        total_orig_cost = sum(a["cost"] for a in self.activities.values())
        total_opt_cost = sum(a["optimized_cost"] for a in self.activities.values())
        avg_opt_value = sum(a["optimized_value"] for a in self.activities.values()) / len(self.activities)
        
        print(f"\n--- Relatório Executivo: {self.project_name} ---")
        print(f"Custo Inicial Total: {total_orig_cost}")
        print(f"Custo Otimizado Total: {total_opt_cost:.2f} (Economia de {total_orig_cost - total_opt_cost:.2f})")
        print(f"Média de Valor Percebido (Score 1-10): {avg_opt_value:.2f}")
        return total_opt_cost, avg_opt_value


class TestInnovationFramework(unittest.TestCase):
    
    def test_framework_execution(self):
        # Inicializa o projeto de inovação executiva
        framework = InnovationValueChain("Projeto Inovação Alpha")
        
        # Adiciona atividades da cadeia de valor
        framework.add_activity("Descoberta e P&D", "Primary", cost=500.0, value_score=8.5)
        framework.add_activity("Prototipagem Rápida", "Primary", cost=300.0, value_score=7.0)
        framework.add_activity("Governança Executiva", "Support", cost=200.0, value_score=6.0)
        
        # Aplicação correta: Reduzir desperdício (Cost Driver) sem cortar valor
        framework.optimize_cost_driver(
            "Prototipagem Rápida", 
            reduction_percentage=20.0, 
            justification="Eliminação de retrabalho por meio de simulação digital prévia."
        )
        
        # Aprimoramento de Value Driver
        framework.enhance_value_driver(
            "Descoberta e P&D", 
            value_increment=1.0, 
            justification="Foco em patenteamento estratégico, aumentando o diferencial competitivo."
        )
        
        opt_cost, opt_value = framework.evaluate_project_health()
        
        # Validações lógicas rigorosas
        self.assertLess(opt_cost, 1000.0, "O custo total deve ser otimizado.")
        self.assertGreaterEqual(opt_value, 8.0, "O valor médio do projeto não pode ser destruído por cortes cegos.")
        print("\n[SUCESSO] O framework validou com sucesso a otimização de custos e preservação/criação de valor.")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)