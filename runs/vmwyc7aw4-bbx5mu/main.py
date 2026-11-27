path=abac_engine.py
import json
from datetime import datetime

class ContextProvider:
    """Simula o PIP (Policy Information Point) e o contexto de ambiente."""
    def __init__(self, current_time=None):
        self.current_time = current_time or datetime.now()

    def get_environment_attributes(self):
        return {
            "time": self.current_time.strftime("%H:%M"),
            "day_of_week": self.current_time.strftime("%A"),
            "ip_address": "192.168.1.50"
        }

class PolicyDecisionPoint:
    """Implementa o PDP (Policy Decision Point) com resolução de conflitos Deny-Overrides."""
    def __init__(self, policies):
        self.policies = policies

    def evaluate(self, subject, resource, action, environment):
        applicable_policies = []
        
        # Filtrar políticas aplicáveis
        for policy in self.policies:
            if self._match_target(policy.get("target", {}), subject, resource, action):
                applicable_policies.append(policy)

        if not applicable_policies:
            return "Deny", "Nenhuma política aplicável encontrada (Default Deny)"

        # Algoritmo de Combinação de Decisões: Deny-Overrides (Segurança em Primeiro Lugar)
        decision = "Permit"
        audit_reasons = []

        for policy in applicable_policies:
            rule_decision = self._evaluate_rules(policy.get("rules", []), subject, resource, action, environment)
            audit_reasons.append(f"Política '{policy['id']}' resultou em: {rule_decision}")
            if rule_decision == "Deny":
                decision = "Deny"
                # Deny absoluto detectado
                break
            elif rule_decision == "Permit" and decision != "Deny":
                decision = "Permit"

        return decision, "; ".join(audit_reasons)

    def _match_target(self, target, subject, resource, action):
        # Verifica correspondência básica de alvos
        if "action" in target and action not in target["action"]:
            return False
        return True

    def _evaluate_rules(self, rules, subject, resource, action, environment):
        rule_decision = "NotApplicable"
        for rule in rules:
            effect = rule.get("effect", "Deny")
            condition = rule.get("condition", lambda s, r, a, e: True)
            
            try:
                if condition(subject, resource, action, environment):
                    return effect
            except Exception as e:
                # Falha na avaliação da condição resulta em negação por segurança
                return "Deny"
        return rule_decision

def run_evaluation_suite():
    # Definição de Políticas Complexas com DSL em Python
    policies = [
        {
            "id": "POL-001-WorkingHours",
            "target": {"action": ["read", "write"]},
            "rules": [
                {
                    "effect": "Permit",
                    "condition": lambda s, r, a, e: s.get("clearance") >= r.get("classification") and 
                                                    "08:00" <= e.get("time") <= "18:00"
                }
            ]
        },
        {
            "id": "POL-002-EmergencyOverride",
            "target": {"action": ["read", "write", "delete"]},
            "rules": [
                {
                    "effect": "Permit",
                    "condition": lambda s, r, a, e: s.get("role") == "Admin" or e.get("emergency_mode", False)
                }
            ]
        },
        {
            "id": "POL-003-BlacklistIP",
            "target": {"action": ["read", "write", "delete"]},
            "rules": [
                {
                    "effect": "Deny",
                    "condition": lambda s, r, a, e: e.get("ip_address") in ["10.0.0.666"]
                }
            ]
        }
    ]

    pip = ContextProvider()
    pdp = PolicyDecisionPoint(policies)

    # 15 Cenários de Teste Abrangentes (incluindo conflitos e atributos dinâmicos)
    scenarios = [
        # 1-5: Casos normais e limítrofes de horário e clearance
        {"name": "C1: Funcionario com clearance adequado em horario comercial",
         "sub": {"clearance": 3, "role": "Employee"}, "res": {"classification": 2}, "act": "read", "env_override": {"time": "10:00"}, "expected": "Permit"},
        
        {"name": "C2: Funcionario com clearance insuficiente",
         "sub": {"clearance": 1, "role": "Employee"}, "res": {"classification": 3}, "act": "read", "env_override": {"time": "10:00"}, "expected": "Deny"},
        
        {"name": "C3: Acesso fora do horario comercial (Negado por padrao)",
         "sub": {"clearance": 3, "role": "Employee"}, "res": {"classification": 1}, "act": "write", "env_override": {"time": "22:00"}, "expected": "Deny"},
        
        {"name": "C4: Admin acessando fora do horario (Permitido por regra de Admin)",
         "sub": {"clearance": 1, "role": "Admin"}, "res": {"classification": 3}, "act": "delete", "env_override": {"time": "23:00"}, "expected": "Permit"},
        
        {"name": "C5: Modo de emergencia ativado",
         "sub": {"clearance": 1, "role": "External"}, "res": {"classification": 3}, "act": "read", "env_override": {"emergency_mode": True, "time": "02:00"}, "expected": "Permit"},

        # 6-10: Conflitos de Decisão (Deny-Overrides)
        {"name": "C6: Conflito - Funcionario tem clearance mas esta na Blacklist IP",
         "sub": {"clearance": 5, "role": "Employee"}, "res": {"classification": 1}, "act": "read", "env_override": {"time": "12:00", "ip_address": "10.0.0.666"}, "expected": "Deny"},
        
        {"name": "C7: Conflito - Admin com IP na Blacklist (Deny deve prevalecer)",
         "sub": {"clearance": 5, "role": "Admin"}, "res": {"classification": 5}, "act": "delete", "env_override": {"time": "12:00", "ip_address": "10.0.0.666"}, "expected": "Deny"},

        {"name": "C8: Atributo ausente no usuario (Tratamento seguro / Deny)",
         "sub": {"role": "Guest"}, "res": {"classification": 1}, "act": "read", "env_override": {"time": "10:00"}, "expected": "Deny"},

        {"name": "C9: Acao nao mapeada em nenhuma politica",
         "sub": {"clearance": 5, "role": "Admin"}, "res": {"classification": 1}, "act": "execute", "env_override": {"time": "10:00"}, "expected": "Deny"},

        {"name": "C10: Mudanca dinamica de dia/horario limite",
         "sub": {"clearance": 3, "role": "Employee"}, "res": {"classification": 2}, "act": "read", "env_override": {"time": "18:01"}, "expected": "Deny"},

        # 11-15: Testes de robustez contra equívocos comuns mapeados pelo Arquiteto
        {"name": "C11: Equivoco - Confundir RBAC com ABAC (Papel sozinho nao basta sem condicao valida)",
         "sub": {"clearance": 0, "role": "Manager"}, "res": {"classification": 5}, "act": "write", "env_override": {"time": "20:00"}, "expected": "Deny"},

        {"name": "C12: Atributos multiplos combinados (Usuario + Recurso + Ambiente validos)",
         "sub": {"clearance": 4, "role": "Analyst"}, "res": {"classification": 4}, "act": "write", "env_override": {"time": "14:30"}, "expected": "Permit"},

        {"name": "C13: Tentativa de bypass por injecao de atributo de ambiente nulo",
         "sub": {"clearance": 5, "role": "Employee"}, "res": {"classification": 1}, "act": "read", "env_override": {"time": None}, "expected": "Deny"},

        {"name": "C14: Multiplas politicas compativeis resultando em Permit unanime",
         "sub": {"clearance": 5, "role": "Admin"}, "res": {"classification": 1}, "act": "read", "env_override": {"time": "10:00"}, "expected": "Permit"},

        {"name": "C15: Auditoria gerada para transacao negada por falta de clearance",
         "sub": {"clearance": 2, "role": "Employee"}, "res": {"classification": 4}, "act": "write", "env_override": {"time": "11:00"}, "expected": "Deny"}
    ]

    passed = 0
    total = len(scenarios)

    print("=== INICIANDO AVALIAÇÃO DE CENÁRIOS ABAC ===")
    for i, sc in enumerate(scenarios, 1):
        env = pip.get_environment_attributes()
        env.update(sc["env_override"])
        
        decision, audit_log = pdp.evaluate(sc["sub"], sc["res"], sc["act"], env)
        
        success = decision == sc["expected"]
        if success:
            passed += 1
            status = "[PASS]"
        else:
            status = "[FAIL]"

        print(f"{status} {sc['name']} -> Esperado: {sc['expected']} | Obtido: {decision}")
        print(f"      Auditoria: {audit_log}")

    print(f"\nResultado Final: {passed}/{total} cenários corretos.")
    assert passed >= 14, f"Critério de sucesso não atingido: {passed}/15 (Mínimo exigido: 14/15)"
    print("Sucesso: Critério de 14/15 atendido com louvor!")

if __name__ == "__main__":
    run_evaluation_suite()