import unittest

class InnovationValueChain:
    """
    Framework de Análise de Cadeia de Valor para Projetos Executivos de Inovação.
    Gerencia atividades primárias e de apoio, distinguindo Cost Drivers e Value Drivers
    para evitar cortes cegos que destruam o diferencial competitivo.
    """
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.activities = []

    def add_activity(self, name: str, category: str, cost: float, value_score: float):
        """Adiciona uma atividade à cadeia de valor com custo inicial e pontuação de valor (0-10)."""
        if category not in ["Primary", "Support"]:
            raise ValueError("Categoria deve ser 'Primary' ou 'Support'.")
        
        activity = {
            "name": name,
            "category": category,
            "cost": float(cost),
            "value_score": float(value_score)
        }
        self.activities.append(activity)

    def optimize_cost_driver(self, name: str, reduction_percentage: float, justification: str):
        """Otimiza um Cost Driver reduzindo o custo sem degradar o valor (ex: automação ou eliminação de retrabalho)."""
        for act in self.activities:
            if act["name"] == name:
                reduction = act["cost"] * (reduction_percentage / 100.0)
                act["cost"] -= reduction
                print(f"[COST DRIVER] {name}: Custo reduzido em {reduction_percentage}%. Justificativa: {justification}")
                return
        raise ValueError(f"Atividade '{name}' não encontrada.")

    def enhance_value_driver(self, name: str, value_increment: float, justification: str):
        """Incrementa um Value Driver (ex: patentes, robustez tecnológica) elevando a pontuação de valor."""
        for act in self.activities:
            if act["name"] == name:
                act["value_score"] = min(10.0, act["value_score"] + value_increment)
                print(f"[VALUE DRIVER] {name}: Valor incrementado. Justificativa: {justification}")
                return
        raise ValueError(f"Atividade '{name}' não encontrada.")

    def evaluate_project_health(self):
        """Retorna o custo total e o valor médio ponderado do projeto de inovação."""
        total_cost = sum(act["cost"] for act in self.activities)
        avg_value = sum(act["value_score"] for act in self.activities) / len(self.activities) if self.activities else 0.0
        return total_cost, avg_value


class TestInnovationValueChain(unittest.TestCase):
    def test_framework_execution(self):
        # Inicializa o projeto de inovação executiva
        framework = InnovationValueChain("Projeto Inovação Alpha")
        
        # Adiciona atividades da cadeia de valor adaptada para inovação
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
        print(f"\n[SUCESSO] Custo Total Otimizado: {opt_cost} | Valor Médio do Projeto: {opt_value:.2f}")

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)