path=main.py
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

            # Verifica se o gatilho de alerta precoce foi ativado
            if current_value >= threshold:
                risk["status"] = "Ativo / Alerta"
                self.incident_log.append({
                    "sprint": sprint_number,
                    "risk_id": risk["id"],
                    "message": f"Gatilho disparado! {metric_name} atingiu {current_value} (limiar: {threshold})"
                })
                print(f"[ALERTA DE RISCO] Risco {risk['id']} ({risk['description']}) ATIVADO. Ação recomendada: Executar plano de mitigação na próxima Daily.")
            else:
                print(f"[Monitoramento] Risco {risk['id']} sob controle. {metric_name}: {current_value} (limiar: {threshold})")

    def get_risk_burndown_status(self):
        """Retorna o status atual do Risk Burndown (quantos riscos estão ativos vs mitigados)."""
        total = len(self.risks)
        ativos = sum(1 for r in self.risks if r["status"] == "Ativo / Alerta")
        mitigados = sum(1 for r in self.risks if r["status"] == "Mitigado")
        return {"total_risks": total, "active": ativos, "mitigated": mitigados}

# --- Execução do Experimento ---
if __name__ == "__main__":
    monitor = AgileRiskMonitor()

    # 1. Identificação inicial de riscos (integração ao planejamento)
    monitor.register_risk(
        risk_id="R1",
        description="Gargalo na revisão de código gerando acúmulo de Pull Requests",
        probability="Alta",
        impact="Alto",
        trigger_metric={"name": "blocked_items_count", "threshold": 3}
    )
    
    monitor.register_risk(
        risk_id="R2",
        description="Volatilidade excessiva de escopo (*Scope Creep*) no meio da Sprint",
        probability="Media",
        impact="Alto",
        trigger_metric={"name": "scope_change_percentage", "threshold": 15}
    )

    # 2. Simulação da Sprint 1 (Sem incidentes graves)
    monitor.evaluate_sprint_metrics(sprint_number=1, metrics={
        "blocked_items_count": 1,
        "scope_change_percentage": 5
    })

    # 3. Simulação da Sprint 2 (Estouro de limites - Disparo de Gatilhos)
    monitor.evaluate_sprint_metrics(sprint_number=2, metrics={
        "blocked_items_count": 4,  # Ultrapassou o limiar de 3
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