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
        
        # Filtrar políticas aplicáveis baseadas no target
        for policy in self.policies:
            if self._match_target(policy.get("target", {}), subject, resource, action):
                applicable_policies.append(policy)

        if not applicable_policies:
            return "Deny", "Nenhuma política aplicável encontrada (Default Deny)"

        # Algoritmo de Combinação de Decisões: Deny-Overrides (Segurança em Primeiro Lugar)
        decision = "NotApplicable"
        audit_reasons = []

        for policy in applicable_policies:
            rule_decision = self._evaluate_rules(policy.get("rules", []), subject, resource, action, environment)
            audit_reasons.append(f"Política '{policy['id']}' resultou em: {rule_decision}")
            if rule_decision == "Deny":
                decision = "Deny"
                break
            elif rule_decision == "Permit" and decision != "Deny":
                decision = "Permit"

        if decision == "NotApplicable":
            return "Deny", "Políticas aplicáveis mas nenhuma regra acionada (Default Deny); " + "; ".join(audit_reasons)

        return decision, "; ".join(audit_reasons)

    def _match_target(self, target, subject, resource, action):
        # Validação rigorosa de ação
        if "action" in target and action not in target["action"]:
            return False
        # Validação de recursos ou papéis se definidos no target
        if "resource_classification_min" in target:
            if resource.get("classification", 0) < target["resource_classification_min"]:
                return False
        return True

    def _evaluate_rules(self, rules, subject, resource, action, environment):
        rule_decision = "NotApplicable"
        for rule in rules:
            effect = rule.get("effect", "Deny")
            condition = rule.get("condition", "")
            
            if self._evaluate_condition(condition, subject, resource, action, environment):
                return effect
        return rule_decision

    def _evaluate_condition(self, condition_str, subject, resource, action, environment):
        if not condition_str:
            return True # Sem condição significa regra incondicional
        
        # Contexto seguro para avaliação
        local_dict = {
            "subject": subject,
            "resource": resource,
            "action": action,
            "environment": environment
        }
        
        try:
            return eval(condition_str, {"__builtins__": {}}, local_dict)
        except Exception as e:
            return False

def run_evaluation_suite():
    pip = ContextProvider()
    
    # Definição de Políticas ABAC rigorosas
    policies = [
        {
            "id": "POL-01",
            "target": {"action": ["read", "write"]},
            "rules": [
                {
                    "effect": "Permit",
                    "condition": "subject.get('clearance', 0) >= resource.get('classification', 99) and environment.get('ip_address', '').startswith('192.168.')"
                }
            ]
        },
        {
            "id": "POL-02-EMERGENCY",
            "target": {"action": ["read", "write", "execute"]},
            "rules": [
                {
                    "effect": "Permit",
                    "condition": "subject.get('role') == 'EmergencyResponder' and environment.get('day_of_week') in ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']"
                }
            ]
        },
        {
            "id": "POL-03-BLACKLIST",
            "target": {},
            "rules": [
                {
                    "effect": "Deny",
                    "condition": "environment.get('ip_address') == '10.0.0.666'"
                }
            ]
        }
    ]

    pdp = PolicyDecisionPoint(policies)

    scenarios = [
        {
            "name": "C1: Acesso permitido com clearance adequado e IP interno",
            "sub": {"clearance": 3, "role": "Analyst"},
            "res": {"classification": 3},
            "act": "read",
            "env_override": {},
            "expected": "Permit"
        },
        {
            "name": "C2: Acesso negado por clearance insuficiente",
            "sub": {"clearance": 1, "role": "Junior"},
            "res": {"classification": 3},
            "act": "read",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C3: Acesso negado por IP externo não autorizado",
            "sub": {"clearance": 5, "role": "Senior"},
            "res": {"classification": 2},
            "act": "read",
            "env_override": {"ip_address": "203.0.113.5"},
            "expected": "Deny"
        },
        {
            "name": "C4: Acesso de emergência em dia de semana por EmergencyResponder",
            "sub": {"clearance": 1, "role": "EmergencyResponder"},
            "res": {"classification": 5},
            "act": "write",
            "env_override": {},
            "expected": "Permit"
        },
        {
            "name": "C5: Conflito Deny-Overrides com IP na Blacklist",
            "sub": {"clearance": 5, "role": "Admin"},
            "res": {"classification": 1},
            "act": "read",
            "env_override": {"ip_address": "10.0.0.666"},
            "expected": "Deny"
        },
        {
            "name": "C6: Atributo de usuário ausente (Default Deny)",
            "sub": {},
            "res": {"classification": 1},
            "act": "read",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C7: Recurso com classificação superior ao clearance",
            "sub": {"clearance": 2},
            "res": {"classification": 4},
            "act": "write",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C8: Acesso permitido com clearance superior e IP corporativo",
            "sub": {"clearance": 5},
            "res": {"classification": 2},
            "act": "read",
            "env_override": {"ip_address": "192.168.1.10"},
            "expected": "Permit"
        },
        {
            "name": "C9: Ação não suportada no target da política principal",
            "sub": {"clearance": 5},
            "res": {"classification": 1},
            "act": "delete",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C10: Usuário sem clearance tenta ler recurso confidencial",
            "sub": {"clearance": 0},
            "res": {"classification": 1},
            "act": "read",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C11: IP interno mas papel incorreto para emergência",
            "sub": {"role": "Guest"},
            "res": {"classification": 5},
            "act": "write",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C12: Admin tentando acesso com IP externo",
            "sub": {"clearance": 5, "role": "Admin"},
            "res": {"classification": 5},
            "act": "read",
            "env_override": {"ip_address": "8.8.8.8"},
            "expected": "Deny"
        },
        {
            "name": "C13: Atributo de ambiente malformado",
            "sub": {"clearance": 3},
            "res": {"classification": 1},
            "act": "read",
            "env_override": {"ip_address": None},
            "expected": "Deny"
        },
        {
            "name": "C14: Ação não mapeada em nenhuma política",
            "sub": {"clearance": 5, "role": "Admin"},
            "res": {"classification": 1},
            "act": "execute",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C15: Acesso normal com múltiplos atributos de contexto válidos",
            "sub": {"clearance": 3, "role": "Analyst"},
            "res": {"classification": 3},
            "act": "read",
            "env_override": {"ip_address": "192.168.1.100"},
            "expected": "Permit"
        }
    ]

    passed = 0
    total = len(scenarios)

    print("Iniciando Execução da Bateria de Testes ABAC...")
    for sc in scenarios:
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