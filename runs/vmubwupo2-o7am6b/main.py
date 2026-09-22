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

            # EWI Disparado se o valor atual ultrapassar o limiar
            if current_value >= threshold:
                if risk["status"] == "Mitigado":
                    # Correção lógica: reativa o risco mitigado (reincidência)
                    risk["status"] = "Ativo (Reincidente)"
                    msg = (f"[ALERTA DE REINCIDÊNCIA] Risco {risk['id']} mitigado anteriormente "
                           f"voltou a estourar! Métrica {metric_name} atingiu {current_value} (Limiar: {threshold})")
                    self.incident_log.append(msg)
                    print(msg)
                elif risk["status"] == "Identificado":
                    risk["status"] = "Ativo"
                    msg = (f"[ALERTA] Risco {risk['id']} disparado! "
                           f"Métrica {metric_name} atingiu {current_value} (Limiar: {threshold})")
                    self.incident_log.append(msg)
                    print(msg)
                elif risk["status"] == "Ativo":
                    msg = (f"[MANUTENÇÃO DE ALERTA] Risco {risk['id']} continua ativo. "
                           f"Métrica {metric_name} em {current_value} (Limiar: {threshold})")
                    self.incident_log.append(msg)
                    print(msg)
            else:
                print(f"Risco {risk['id']} ({metric_name}): dentro do limiar seguro ({current_value} < {threshold}).")

    def get_risk_burndown_status(self):
        """Retorna a contagem atual de riscos por status para o Risk Burndown."""
        status_count = {"Identificado": 0, "Ativo": 0, "Ativo (Reincidente)": 0, "Mitigado": 0}
        for risk in self.risks:
            status_count[risk["status"]] = status_count.get(risk["status"], 0) + 1
        return status_count

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
    assert status["Ativo (Reincidente)"] == 1, "O risco deveria estar com status 'Ativo (Reincidente)' devido à reincidência"
    assert status["Mitigado"] == 0, "O risco não deve mais constar como mitigado após reincidir"
    assert any("REINCIDÊNCIA" in log for log in monitor.incident_log), "O log deve registrar explicitamente a reincidência"
    
    print("\n[SUCESSO] O modelo tratado corrigiu a f-string e validou com êxito a reincidência de riscos mitigados no cenário adversarial!")