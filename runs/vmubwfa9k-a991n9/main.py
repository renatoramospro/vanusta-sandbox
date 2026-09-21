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
            "probability": probability,
            "impact": impact,
            "trigger_metric": trigger_metric,
            "status": "Identificado"
        })

    def update_risk_status(self, risk_id, new_status):
        """Permite mitigar ou alterar o status do risco manualmente (ex: na Retrospectiva)."""
        for risk in self.risks:
            if risk["id"] == risk_id:
                risk["status"] = new_status

    def evaluate_sprint_metrics(self, sprint_number, metrics):
        """
        Avalia os sinais vitais da sprint e cruza com os gatilhos de risco.
        Permite a reativação de riscos mitigados caso o EWI volte a estourar (cenário adversarial).
        """
        print(f"\n--- Avaliando Sinais Vitais da Sprint {sprint_number} ---")
        print(f"Métricas recebidas: {metrics}")

        for risk in self.risks:
            metric_name = risk["trigger_metric"]["name"]
            threshold = risk["trigger_metric"]["threshold"]
            current_value = metrics.get(metric_name, 0)

            # EWI (Early Warning Indicator): Dispara se a métrica ultrapassar o limiar
            if current_value >= threshold:
                previous_status = risk["status"]
                risk["status"] = "Ativo / Alerta"
                
                if previous_status == "Mitigado":
                    incident_msg = (
                        f"[EWI REINCIDÊNCIA] Sprint {sprint_number}: Risco {risk['id']} "
                        f"('{risk['description']}') REINCIDIU! Métrica '{metric_name}' "
                        f"atingiu {current_value} (Limiar: {threshold})."
                    )
                else:
                    incident_msg = (
                        f"[EWI DISPARADO] Sprint {sprint_number}: Risco {risk['id']} "
                        f"('{risk['description']}') ativado. Métrica '{metric_name}' "
                        f"atingiu {current_value} (Limiar: {threshold}
                    )"
                
                self.incident_log.append(incident_msg)
                print(incident_msg)
            else:
                # Se o risco já estava ativo e agora está abaixo do limiar, podemos considerá-lo sob controle
                if risk["status"] == "Ativo / Alerta":
                    print(f"Risco {risk['id']}: Retornou ao limiar seguro ({current_value} < {threshold}).")
                else:
                    print(f"Risco {risk['id']}: Dentro do limiar seguro ({current_value} < {threshold}).")

    def get_risk_burndown_status(self):
        """Retorna o estado atual do Risk Burndown para acompanhamento no painel."""
        total_risks = len(self.risks)
        active = sum(1 for r in self.risks if "Ativo" in r["status"])
        mitigated = sum(1 for r in self.risks if r["status"] == "Mitigado")
        identified = sum(1 for r in self.risks if r["status"] == "Identificado")

        return {
            "total_risks": total_risks,
            "active": active,
            "mitigated": mitigated,
            "identified": identified
        }

if __name__ == "__main__":
    monitor = AgileRiskMonitor()

    # Cadastro de Risco
    monitor.register_risk(
        risk_id="R1",
        description="Gargalo por itens bloqueados em Code Review excessivo",
        probability="Media",
        impact="Alto",
        trigger_metric={"name": "blocked_items_count", "threshold": 3}
    )

    # Sprint 1: Risco dispara
    monitor.evaluate_sprint_metrics(sprint_number=1, metrics={"blocked_items_count": 4})
    
    # Time aplica mitigação na Retrospectiva
    monitor.update_risk_status("R1", "Mitigado")
    print("\n[AÇÃO] Risco R1 marcado como 'Mitigado' após Retrospectiva.")

    # Sprint 2: Métricas seguras (continua mitigado)
    monitor.evaluate_sprint_metrics(sprint_number=2, metrics={"blocked_items_count": 1})

    # Sprint 3 (Cenário Adversarial): O risco mitigado reincide (métrica estoura novamente)
    monitor.evaluate_sprint_metrics(sprint_number=3, metrics={"blocked_items_count": 5})

    status = monitor.get_risk_burndown_status()
    print("\n--- Relatório Final de Risk Burndown ---")
    print(json.dumps(status, indent=2))

    # Validações Assertivas do Cenário Adversarial
    assert status["active"] == 1, "O risco deveria estar ativo novamente devido à reincidência"
    assert status["mitigated"] == 0, "O risco não deve mais constar como mitigado"
    assert any("REINCIDÊNCIA" in log for log in monitor.incident_log), "O log deve registrar explicitamente a reincidência"
    
    print("\n[SUCESSO] O modelo tratou com êxito a reincidência de riscos mitigados no cenário adversarial!")