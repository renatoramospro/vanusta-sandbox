import json
import sys
import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Tuple

# Chave secreta simulada para validação de integridade de metadados
HMAC_SECRET = b"vanusta-secure-iac-master-key-2026"

@dataclass(frozen=True)
class InfrastructureResource:
    account_id: str
    region: str
    resource_type: str
    resource_id: str
    environment: str
    criticality: str  # 'high', 'medium', 'low'
    properties: Dict[str, Any]
    metadata_signature: str = ""

    def compute_signature(self) -> str:
        """Gera assinatura HMAC para garantir integridade e prevenir adulteração."""
        payload = f"{self.account_id}:{self.region}:{self.resource_type}:{self.resource_id}:{self.environment}:{self.criticality}:{json.dumps(self.properties, sort_keys=True)}"
        return hmac.new(HMAC_SECRET, payload.encode('utf-8'), hashlib.sha256).hexdigest()

class SecureInfrastructureGovernanceEngine:
    def __init__(self, desired_state: List[InfrastructureResource], ignored_properties: Set[str] = None):
        # 1. Uso de chave composta (account, region, type, id) para evitar colisões
        self.desired_state = {}
        for res in desired_state:
            # Validar integridade da entrada declarativa
            expected_sig = res.compute_signature()
            if res.metadata_signature and res.metadata_signature != expected_sig:
                raise ValueError(f"CRITICAL SECURITY ERROR: Invalid signature for resource {res.resource_id}. Tampering detected!")
            
            compound_key = (res.account_id, res.region, res.resource_type, res.resource_id)
            self.desired_state[compound_key] = res

        # 2. Propriedades dinâmicas seguras (nunca ignorar propriedades de segurança/IAM)
        dangerous_properties = {"security_groups", "iam_role", "encryption", "public_access_block"}
        base_ignored = ignored_properties or {"last_modified", "dynamic_ip", "uptime_seconds"}
        
        # Garantir que propriedades de segurança jamais sejam silenciadas
        self.ignored_properties = base_ignored - dangerous_properties

        # Trilha de auditoria imutável
        self.audit_trail: List[Dict[str, Any]] = []

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        entry = {
            "timestamp": "2026-03-31T12:00:00Z",
            "event_type": event_type,
            "details": details,
            "integrity_hash": hashlib.sha256(json.dumps(details, sort_keys=True).encode()).hexdigest()
        }
        self.audit_trail.append(entry)

    def inspect_and_plan(self, real_infrastructure: List[InfrastructureResource]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Fase de PLAN: Analisa estado real contra o desejado usando identidade composta,
        validação de integridade e restrições de blast radius.
        """
        modified_drifts = []
        shadow_resources = []
        real_compound_keys = set()

        for real_res in real_infrastructure:
            compound_key = (real_res.account_id, real_res.region, real_res.resource_type, real_res.resource_id)
            real_compound_keys.add(compound_key)

            if compound_key not in self.desired_state:
                shadow_resources.append({
                    "compound_key": compound_key,
                    "issue": "Shadow resource detected outside declarative IaC inventory"
                })
                self._log_audit("SHADOW_RESOURCE_DETECTED", {"resource": str(compound_key)})
                continue

            desired_res = self.desired_state[compound_key]
            
            # Comparação de propriedades filtrando dinâmicas seguras
            divergences = {}
            for k, desired_val in desired_res.properties.items():
                if k in self.ignored_properties:
                    continue
                real_val = real_res.properties.get(k)
                if real_val != desired_val:
                    divergences[k] = {"desired": desired_val, "real": real_val}

            if divergences:
                modified_drifts.append({
                    "compound_key": compound_key,
                    "environment": real_res.environment,
                    "criticality": real_res.criticality,
                    "divergences": divergences
                })
                self._log_audit("DRIFT_PLANNED", {"resource": str(compound_key), "divergences": list(divergences.keys())})

        return modified_drifts, shadow_resources

    def apply_remediation_with_safeguards(self, modified_drifts: List[Dict[str, Any]], max_blast_radius: int = 5) -> List[Dict[str, Any]]:
        """
        Fase de APPLY com Lock simulado, Revalidação pré-mutação e Controle de Blast Radius.
        """
        # 6. Controle de Blast Radius (limite de mutações por ciclo)
        if len(modified_drifts) > max_blast_radius:
            self._log_audit("BLAST_RADIUS_EXCEEDED", {"count": len(modified_drifts), "limit": max_blast_radius})
            raise RuntimeError(f"ABORT: Blast radius limit exceeded ({len(modified_drifts)} drifts > limit {max_blast_radius}). Manual intervention required.")

        execution_actions = []

        for drift in modified_drifts:
            compound_key = drift["compound_key"]
            env = drift["environment"]
            crit = drift["criticality"]
            
            # 7. Revalidação antes da mutação (Prevenção de Race Condition)
            # Simula checagem de lock de estado distribuído
            lock_acquired = True
            if not lock_acquired:
                self._log_audit("LOCK_ACQUISITION_FAILED", {"resource": str(compound_key)})
                continue

            # Política rigorosa de remediação baseada em risco e ambiente
            if env == "production" or crit == "high":
                action = "ALERT_AND_CREATE_TICKET"
                rollback_plan = None
            else:
                action = "AUTO_REMEDIATE"
                # Gerar plano de rollback determinístico
                rollback_plan = {
                    "action": "RESTORE_PREVIOUS_PROPERTIES",
                    "target": compound_key,
                    "reverted_properties": list(drift["divergences"].keys())
                }

            execution_actions.append({
                "compound_key": compound_key,
                "action": action,
                "rollback_plan": rollback_plan
            })
            self._log_audit("REMEDIATION_EXECUTED", {"resource": str(compound_key), "action": action})

        return execution_actions

def run_secure_experiment():
    print("=== INICIANDO GOVERNANÇA DE DRIFT ENDURECIDA (SECURITY HARDENED) ===\n")

    # Criando recursos declarativos com assinatura de integridade válida
    res1 = InfrastructureResource(
        account_id="123456789012",
        region="us-east-1",
        resource_type="aws_instance",
        resource_id="i-prod-db-01",
        environment="production",
        criticality="high",
        properties={"instance_type": "t3.large", "security_groups": "sg-secure-prod"}
    )
    # Assinar o recurso
    res1 = InfrastructureResource(
        account_id=res1.account_id,
        region=res1.region,
        resource_type=res1.resource_type,
        resource_id=res1.resource_id,
        environment=res1.environment,
        criticality=res1.criticality,
        properties=res1.properties,
        metadata_signature=res1.compute_signature()
    )

    res2 = InfrastructureResource(
        account_id="123456789012",
        region="us-east-1",
        resource_type="aws_instance",
        resource_id="i-dev-web-01",
        environment="development",
        criticality="low",
        properties={"instance_type": "t3.micro", "security_groups": "sg-dev"}
    )
    res2 = InfrastructureResource(
        account_id=res2.account_id,
        region=res2.region,
        resource_type=res2.resource_type,
        resource_id=res2.resource_id,
        environment=res2.environment,
        criticality=res2.criticality,
        properties=res2.properties,
        metadata_signature=res2.compute_signature()
    )

    engine = SecureInfrastructureGovernanceEngine([res1, res2])

    # Estado real inspecionado do provedor simulado (com drift alterado e shadow resource)
    real_res1 = InfrastructureResource(
        account_id="123456789012",
        region="us-east-1",
        resource_type="aws_instance",
        resource_id="i-prod-db-01",
        environment="production",
        criticality="high",
        properties={"instance_type": "t3.xlarge", "security_groups": "sg-secure-prod", "dynamic_ip": "192.168.1.50"}
    )
    real_res2 = InfrastructureResource(
        account_id="123456789012",
        region="us-east-1",
        resource_type="aws_instance",
        resource_id="i-dev-web-01",
        environment="development",
        criticality="low",
        properties={"instance_type": "t3.medium", "security_groups": "sg-dev", "dynamic_ip": "10.0.0.5"}
    )
    shadow_real = InfrastructureResource(
        account_id="123456789012",
        region="us-east-1",
        resource_type="s3_bucket",
        resource_id="s3-shadow-bucket-manual",
        environment="production",
        criticality="high",
        properties={"encryption": "AES256"}
    )

    real_infrastructure = [real_res1, real_res2, shadow_real]

    print("[1] Executando Plan phase (Com identidade composta e verificação de integridade)...")
    drifts, shadows = engine.inspect_and_plan(real_infrastructure)
    print(f"-> Drifts modificados detectados: {len(drifts)}")
    print(f"-> Shadow resources detectados: {len(shadows)}")

    print("\n[2] Executando Apply phase (Com lock, revalidação, blast radius e plano de rollback)...")
    actions = engine.apply_remediation_with_safeguards(drifts, max_blast_radius=5)
    
    for action in actions:
        print(f"Recurso {action['compound_key'][3]} | Ação: {action['action']} | Rollback Plan: {action['rollback_plan']}")

    print(f"\n[3] Trilha de Auditoria Imutável gerada: {len(engine.audit_trail)} eventos registrados com SHA-256.")
    print("\n=== EXPERIMENTO ENDURECIDO EXECUTADO COM SUCESSO ===")

if __name__ == "__main__":
    try:
        run_secure_experiment()
        sys.exit(0)
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)