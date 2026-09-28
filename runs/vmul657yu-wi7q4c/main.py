import json
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set

@dataclass
class InfrastructureResource:
    resource_id: str
    resource_type: str
    environment: str
    criticality: str  # ex: 'high', 'medium', 'low'
    properties: Dict[str, Any]

class AdvancedDriftDetectorAndRemediator:
    def __init__(self, desired_state: List[InfrastructureResource], ignored_properties: Set[str] = None):
        self.desired_state = {res.resource_id: res for res in desired_state}
        # 2. Exclusão de propriedades dinâmicas para mitigar falsos positivos
        self.ignored_properties = ignored_properties or {"last_modified", "dynamic_ip", "uptime_seconds"}

    def inspect_infrastructure(self, real_infrastructure: List[InfrastructureResource]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Inspeciona o estado real e categoriza os drifts:
        - modified_resources: Recursos declarados que divergem do desejado (filtrando propriedades dinâmicas).
        - shadow_resources: Recursos presentes na nuvem real mas ausentes no IaC (Shadow resources).
        """
        modified_drifts = []
        shadow_resources = []
        
        real_resource_ids = set()

        for real_res in real_infrastructure:
            real_resource_ids.add(real_res.resource_id)
            
            # 1. Detecção de Shadow Resources (recursos adicionados manualmente fora do IaC)
            if real_res.resource_id not in self.desired_state:
                shadow_resources.append({
                    "resource_id": real_res.resource_id,
                    "resource_type": real_res.resource_type,
                    "environment": real_res.environment,
                    "issue": "Shadow resource detected (not present in declarative IaC)"
                })
                continue
            
            desired_res = self.desired_state[real_res.resource_id]
            divergences = {}

            # Comparação de propriedades ignorando chaves dinâmicas
            all_keys = set(desired_res.properties.keys()).union(set(real_res.properties.keys()))
            for key in all_keys:
                if key in self.ignored_properties:
                    continue
                
                val_desired = desired_res.properties.get(key)
                val_real = real_res.properties.get(key)
                
                if val_desired != val_real:
                    divergences[key] = {
                        "desired": val_desired,
                        "real": val_real
                    }

            if divergences:
                modified_drifts.append({
                    "resource_id": real_res.resource_id,
                    "resource_type": real_res.resource_type,
                    "environment": real_res.environment,
                    "criticality": real_res.criticality,
                    "divergences": divergences
                })

        return {
            "modified": modified_drifts,
            "shadow": shadow_resources
        }

    def apply_remediation_policy(self, drift: Dict[str, Any]) -> str:
        """
        3. Política de remediação condicional baseada no Ambiente E na Criticidade da propriedade.
        """
        env = drift["environment"]
        criticality = drift["criticality"]
        divergent_keys = list(drift["divergences"].keys())
        
        # Se houver alteração em propriedades de alta criticidade (ex: security groups, IAM), exige revisão humana mesmo em dev
        security_keys = {"security_groups", "iam_role", "public_access"}
        has_security_drift = any(k in security_keys for k in divergent_keys)

        if env == "production" or criticality == "high" or has_security_drift:
            return "ALERT_AND_CREATE_TICKET (High risk or Production drift requires manual review)"
        else:
            return "AUTO_REMEDIATE (Low-risk development drift reverted successfully)"

def run_experiment():
    print("=== INICIANDO EXPERIMENTO APERFEIÇOADO DE DRIFT DETECTION ===")

    # Estado desejado (Declarativo - IaC)
    desired_resources = [
        InfrastructureResource(
            resource_id="i-prod-db-01",
            resource_type="aws_instance",
            environment="production",
            criticality="high",
            properties={"instance_type": "r5.xlarge", "security_groups": "sg-prod-db", "last_modified": "2023-10-01"}
        ),
        InfrastructureResource(
            resource_id="i-dev-web-01",
            resource_type="aws_instance",
            environment="development",
            criticality="low",
            properties={"instance_type": "t3.micro", "security_groups": "sg-dev", "dynamic_ip": "192.168.1.50"}
        )
    ]

    # Estado real inspecionado na nuvem (Simulando desvios, propriedades dinâmicas e shadow resources)
    real_infrastructure = [
        InfrastructureResource(
            resource_id="i-prod-db-01",
            resource_type="aws_instance",
            environment="production",
            criticality="high",
            properties={"instance_type": "r5.2xlarge", "security_groups": "sg-prod-db", "last_modified": "2023-10-05"} # Drift em tipo e propriedade dinâmica alterada
        ),
        InfrastructureResource(
            resource_id="i-dev-web-01",
            resource_type="aws_instance",
            environment="development",
            criticality="low",
            properties={"instance_type": "t3.small", "security_groups": "sg-dev", "dynamic_ip": "192.168.1.99"} # Drift em instância e IP dinâmico (deve ignorar IP)
        ),
        InfrastructureResource(
            resource_id="s3-shadow-bucket-manual",
            resource_type="aws_s3_bucket",
            environment="production",
            criticality="medium",
            properties={"public_access": "enabled"} # Recurso órfão criado manualmente
        )
    ]

    detector = AdvancedDriftDetectorAndRemediator(desired_resources)
    
    print("\n[1] Executando varredura e inspeção de infraestrutura...")
    inspection_result = detector.inspect_infrastructure(real_infrastructure)
    
    modified_drifts = inspection_result["modified"]
    shadow_resources = inspection_result["shadow"]

    print(f"-> Recursos modificados com drift (excluindo dinâmicos): {len(modified_drifts)}")
    print(f"-> Recursos órfãos (Shadow Resources) detectados: {len(shadow_resources)}")

    # Validações de robustez
    assert len(modified_drifts) == 2, "Erro: Deveria detectar drift nos 2 recursos modificados."
    assert len(shadow_resources) == 1, "Erro: Deveria detectar exatamente 1 shadow resource."

    # Verifica se a propriedade dinâmica 'last_modified' e 'dynamic_ip' foram ignoradas corretamente
    for drift in modified_drifts:
        assert "last_modified" not in drift["divergences"], "Erro Falso Positivo: Propriedade dinâmica 'last_modified' não foi ignorada."
        assert "dynamic_ip" not in drift["divergences"], "Erro Falso Positivo: Propriedade dinâmica 'dynamic_ip' não foi ignorada."

    print("\n[2] Aplicando políticas de remediação avançadas...")
    for drift in modified_drifts:
        action = detector.apply_remediation_policy(drift)
        print(f"Modificado: {drift['resource_id']} ({drift['environment']}/{drift['criticality']}) | Divergências: {list(drift['divergences'].keys())} | Ação: {action}")

    for shadow in shadow_resources:
        print(f"Órfão: {shadow['resource_id']} ({shadow['environment']}) | Problema: {shadow['issue']} | Ação: FLAG_FOR_DELETION_OR_IMPORT")

    print("\n=== EXPERIMENTO CORRIGIDO EXECUTADO COM SUCESSO ===")

if __name__ == "__main__":
    try:
        run_experiment()
        sys.exit(0)
    except Exception as e:
        print(f"Erro fatal no experimento: {e}")
        sys.exit(1)