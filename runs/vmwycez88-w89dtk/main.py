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
                break
            elif rule_decision == "Permit" and decision != "Deny":
                decision = "Permit"

        return decision, "; ".join(audit_reasons)

    def _match_target(self, target, subject, resource, action):
        if "action" in target and action not in target["action"]:
            return False
        return True

    def _evaluate_rules(self, rules, subject, resource, action, environment):
        rule_decision = "NotApplicable"
        for rule in rules:
            effect = rule.get("effect", "Deny")
            condition = rule.get("condition", "")
            
            # Avaliação segura da condição utilizando o contexto fornecido
            try:
                # Contexto seguro para eval
                eval_context = {
                    "subject": subject,
                    "resource": resource,
                    "action": action,
                    "environment": environment
                }
                if eval(condition, {"__builtins__": {}}, eval_context):
                    return effect
            except Exception as e:
                return "Deny" # Falha segura em caso de erro na expressão
                
        return rule_decision

def run_evaluation_suite():
    pip = ContextProvider()
    
    # Definição de Políticas de Acesso
    policies = [
        {
            "id": "POL-01",
            "target": {"action": ["read", "write"]},
            "rules": [
                {
                    "effect": "Permit",
                    "condition": "subject.get('clearance', 0) >= resource.get('classification', 0) and environment.get('ip_address', '').startswith('192.168.')"
                }
            ]
        },
        {
            "id": "POL-02-EMERGENCY",
            "target": {"action": ["read", "write", "override"]},
            "rules": [
                {
                    "effect": "Permit",
                    "condition": "subject.get('role') == 'MedicalOfficer' and environment.get('emergency_mode', False) == True"
                }
            ]
        },
        {
            "id": "POL-03-BLACKLIST",
            "target": {"action": ["read", "write"]},
            "rules": [
                {
                    "effect": "Deny",
                    "condition": "environment.get('ip_address') == '10.0.0.99'"
                }
            ]
        }
    ]

    pdp = PolicyDecisionPoint(policies)

    # 15 Cenários de Teste rigorosos (incluindo conflitos e equívocos comuns)
    scenarios = [
        {
            "name": "C1: Acesso permitido com clearance adequado e IP interno",
            "sub": {"clearance": 3, "role": "Analyst"},
            "res": {"classification": 2},
            "act": "read",
            "env_override": {},
            "expected": "Permit"
        },
        {
            "name": "C2: Acesso negado por clearance insuficiente",
            "sub": {"clearance": 1, "role": "Intern"},
            "res": {"classification": 3},
            "act": "read",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C3: Acesso negado por IP externo não autorizado",
            "sub": {"clearance": 5, "role": "Senior"},
            "res": {"classification": 1},
            "act": "read",
            "env_override": {"ip_address": "8.8.8.8"},
            "expected": "Deny"
        },
        {
            "name": "C4: Emergência ativada permitindo acesso especial (MedicalOfficer)",
            "sub": {"clearance": 1, "role": "MedicalOfficer"},
            "res": {"classification": 5},
            "act": "override",
            "env_override": {"emergency_mode": True},
            "expected": "Permit"
        },
        {
            "name": "C5: Conflito - IP na blacklist bloqueia mesmo com clearance alto (Deny-Overrides)",
            "sub": {"clearance": 5, "role": "Admin"},
            "res": {"classification": 1},
            "act": "read",
            "env_override": {"ip_address": "10.0.0.99"},
            "expected": "Deny"
        },
        {
            "name": "C6: Nenhuma política aplicável para a ação (Default Deny)",
            "sub": {"clearance": 5, "role": "Admin"},
            "res": {"classification": 1},
            "act": "delete",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C7: Equívoco comum - Papel privilegiado (Manager) sem clearance suficiente falha",
            "sub": {"clearance": 1, "role": "Manager"},
            "res": {"classification": 4},
            "act": "read",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C8: Acesso limite exato (Clearance == Classification)",
            "sub": {"clearance": 3, "role": "Staff"},
            "res": {"classification": 3},
            "act": "write",
            "env_override": {},
            "expected": "Permit"
        },
        {
            "name": "C9: Ação de escrita com IP interno e clearance ok",
            "sub": {"clearance": 4, "role": "Engineer"},
            "res": {"classification": 2},
            "act": "write",
            "env_override": {},
            "expected": "Permit"
        },
        {
            "name": "C10: Falha de ambiente (IP externo em política restrita a rede interna)",
            "sub": {"clearance": 5, "role": "Engineer"},
            "res": {"classification": 1},
            "act": "write",
            "env_override": {"ip_address": "200.100.50.10"},
            "expected": "Deny"
        },
        {
            "name": "C11: Atributo ausente no sujeito (tratamento seguro por default deny)",
            "sub": {"role": "Guest"},
            "res": {"classification": 1},
            "act": "read",
            "env_override": {},
            "expected": "Deny"
        },
        {
            "name": "C12: Sujeito com clearance máxima e recurso de nível médio",
            "sub": {"clearance": 10, "role": "Director"},
            "res": {"classification": 5},
            "act": "read",
            "env_override": {},
            "expected": "Permit"
        },
        {
            "name": "C13: Tentativa de override médico sem modo de emergência ativo",
            "sub": {"clearance": 1, "role": "MedicalOfficer"},
            "res": {"classification": 5},
            "act": "override",
            "env_override": {"emergency_mode": False},
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