import json

class AgileRiskMonitor:
    def __init__(self):
        self.risks = []
        self.incident_log = []

    def register_risk(self, risk_id, description, probability, impact, trigger_metric):
        """Registra um risco no backlog de riscos do projeto ágil."""
        self.risks.append({
            "id": risk_id,
            "description": description,
            "probability": probability,  # Alta, Media, Baixa
            "impact": impact,            # Alto, Medio, Baixo
            "trigger_metric": trigger_metric, # Métrica que dispara o alerta
            "status": "Identificado"
        })

    def evaluate_sprint_metrics(self, sprint_number, metrics):
        """
        Avalia os sinais vitais da sprint (métricas) e cruza com os gatilhos de risco.
        Demonstra o monitoramento em tempo real sem criar reuniões extras.
        """
        print(f"\n--- Avaliando Sinais Vitais da Sprint {sprint_number} ---")
        print(f"Métricas recebidas: {metrics}")

        for risk in self.risks:
            if risk["status"] == "Mitigado":
                continue

            metric_name = risk["trigger_metric"]["name"]
            threshold = risk["trigger_metric"]["threshold"]
            current_value = metrics.get(metric_name, 0)

            # EWI (Early Warning Indicator): Dispara se a métrica ultrapassar o limiar
            if current_value >= threshold:
                risk["status"] = "Ativo / Alerta"
                incident_msg = (
                    f"[EWI DISPARADO] Sprint {sprint_number}: Risco {risk['id']} "
                    f"('{risk['description']}') ativado. Métrica '{metric_name}' "
                    f"atingiu {current_value} (Limiar: {threshold})."
                )
                self.incident_log.append(incident_msg)
                print(incident_msg)
            else:
                print(f"Risco {risk['id']}: Dentro do limiar seguro ({current_value} < {threshold}).")

    def get_risk_burndown_status(self):
        """Retorna o estado atual do Risk Burndown para acompanhamento no painel."""
        total_risks = len(self.risks)
        active_risks = sum(1 for r in self.risks if r["status"] == "Ativo / Alerta")
        mitigated_risks = sum(1 for r in self.risks if r["status"] == "Mitigado")
        
        return {
            "total_risks": total_risks,
            "active": active_risks,
            "mitigated": mitigated_risks
        }

if __name__ == "__main__":
    # 1. Inicialização do Monitor
    monitor = AgileRiskMonitor()

    # 2. Cadastro de Riscos com Early Warning Indicators (EWI)
    monitor.register_risk(
        risk_id="R1",
        description="Gargalo por itens bloqueados em Code Review excessivo",
        probability="Media",
        impact="Alto",
        trigger_metric={"name": "blocked_items_count", "threshold": 3}
    )

    monitor.register_risk(
        risk_id="R2",
        description="Scope Creep por inclusão de histórias fora da Sprint Planning",
        probability="Alta",
        impact="Medio",
        trigger_metric={"name": "scope_change_percentage", "threshold": 15}
    )

    # 3. Simulação de Métricas em uma Sprint (Disparando os riscos)
    monitor.evaluate_sprint_metrics(sprint_number=4, metrics={
        "blocked_items_count": 4,     # Ultrapassou o limiar de 3
        "scope_change_percentage": 20 # Ultrapassou o limiar de 15%
    })

    # 4. Verificação do Risk Burndown
    status = monitor.get_risk_burndown_status()
    print("\n--- Relatório Final de Risk Burndown ---")
    print(json.dumps(status, indent=2))
    print(f"Log de Incidentes Registrados: {len(monitor.incident_log)}")

    # Validação assertiva para o ambiente de teste
    assert status["total_risks"] == 2, "Deveria haver 2 riscos cadastrados"
    assert status["active"] == 2, "Ambos os riscos deveriam estar ativos após estouro de métricas"
    print("\n[SUCESSO] O modelo simulou com êxito a detecção de riscos em tempo real via métricas ágeis!")