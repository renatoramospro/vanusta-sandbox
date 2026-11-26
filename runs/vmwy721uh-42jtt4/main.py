path=main.py
import unittest
from datetime import datetime

# --- 1. Motor ABAC ---

class ABACEngine:
    def __init__(self, policies):
        self.policies = policies

    def evaluate(self, user: dict, resource: dict, environment: dict) -> tuple[bool, str, list]:
        """
        Avalia as políticas ABAC. 
        Retorna: (decisão_permitida, razao, log_auditoria)
        """
        audit_log = []
        matched_policies = []

        # Regra de precedência: Negação explícita sobrepõe permissão
        for policy in self.policies:
            if policy["match"](user, resource, environment):
                matched_policies.append(policy["id"])
                audit_log.append(f"Política {policy['id']} acionada.")
                if policy["effect"] == "Deny":
                    return False, f"Negado pela política {policy['id']}", audit_log
                elif policy["effect"] == "Permit":
                    return True, f"Permitido pela política {policy['id']}", audit_log

        return False, "Negado por padrão (Default Deny)", audit_log


# --- 2. Definição de Políticas ---

# Política 1: Negação global fora do horário comercial (Ambiente)
def match_business_hours(user, resource, environment):
    hour = environment.get("current_hour", 12)
    return not (8 <= hour <= 18)

# Política 2: Dono do recurso pode ler seu próprio recurso
def match_resource_owner(user, resource, environment):
    return user.get("id") == resource.get("owner_id")

# Política 3: Funcionário do mesmo departamento pode acessar se nível for suficiente
def match_department_and_clearance(user, resource, environment):
    same_dept = user.get("department") == resource.get("department")
    user_clearance = user.get("clearance_level", 0)
    resource_classification = resource.get("classification_level", 0)
    return same_dept and (user_clearance >= resource_classification)


POLICIES = [
    {
        "id": "POL-01-BusinessHours",
        "effect": "Deny",
        "match": match_business_hours
    },
    {
        "id": "POL-02-OwnerAccess",
        "effect": "Permit",
        "match": match_resource_owner
    },
    {
        "id": "POL-03-DeptClearance",
        "effect": "Permit",
        "match": match_department_and_clearance
    }
]


# --- 3. Testes Automatizados e Validação do Critério de Sucesso ---

class TestABACModule(unittest.TestCase):
    def setUp(self):
        self.engine = ABACEngine(POLICIES)

    def test_owner_access_during_business_hours(self):
        user = {"id": "u1", "department": "TI", "clearance_level": 1}
        resource = {"id": "r1", "owner_id": "u1", "department": "TI", "classification_level": 1}
        env = {"current_hour": 10}

        allowed, reason, log = self.engine.evaluate(user, resource, env)
        self.assertTrue(allowed)
        self.assertEqual(reason, "Permitido pela política POL-02-OwnerAccess")
        print(f"\n[TESTE OK] Dono acessando no horário comercial: {reason} | Log: {log}")

    def test_deny_outside_business_hours(self):
        user = {"id": "u1", "department": "TI", "clearance_level": 1}
        resource = {"id": "r1", "owner_id": "u1", "department": "TI", "classification_level": 1}
        env = {"current_hour": 22} # Fora do horário

        allowed, reason, log = self.engine.evaluate(user, resource, env)
        self.assertFalse(allowed)
        self.assertIn("POL-01-BusinessHours", reason)
        print(f"[TESTE OK] Acesso fora de hora negado corretamente: {reason} | Log: {log}")

    def test_colleague_access_with_clearance(self):
        user = {"id": "u2", "department": "Financeiro", "clearance_level": 3}
        resource = {"id": "r2", "owner_id": "u1", "department": "Financeiro", "classification_level": 2}
        env = {"current_hour": 14}

        allowed, reason, log = self.engine.evaluate(user, resource, env)
        self.assertTrue(allowed)
        self.assertEqual(reason, "Permitido pela política POL-03-DeptClearance")
        print(f"[TESTE OK] Colega com clearance adequado aprovado: {reason} | Log: {log}")

    def test_colleague_access_insufficient_clearance(self):
        user = {"id": "u3", "department": "Financeiro", "clearance_level": 1}
        resource = {"id": "r2", "owner_id": "u1", "department": "Financeiro", "classification_level": 3}
        env = {"current_hour": 14}

        allowed, reason, log = self.engine.evaluate(user, resource, env)
        self.assertFalse(allowed)
        self.assertEqual(reason, "Negado por padrão (Default Deny)")
        print(f"[TESTE OK] Colega sem clearance negado (Default Deny): {reason} | Log: {log}")

    def test_counter_example_naive_deny_all_policy(self):
        """
        Demonstra o equívoco de usar uma política simplista que apenas nega tudo.
        Se usarmos uma política 'Deny All', falharemos em todos os cenários onde 
        o acesso deveria ser permitido (falsos negativos em massa).
        """
        naive_policies = [{"id": "DENY-ALL", "effect": "Deny", "match": lambda u, r, e: True}]
        naive_engine = ABACEngine(naive_policies)

        user = {"id": "u1", "department": "TI", "clearance_level": 1}
        resource = {"id": "r1", "owner_id": "u1", "department": "TI", "classification_level": 1}
        env = {"current_hour": 10}

        allowed, reason, _ = naive_engine.evaluate(user, resource, env)
        
        # O teste comprova que a política ingênua falha em permitir o acesso legítimo do dono
        self.assertFalse(allowed)
        print(f"[CONTRAEXEMPLO OK] Política 'Deny All' falha ao permitir acesso legítimo do dono. Decisão obtida: {allowed} ({reason})")


if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)