import json
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

@dataclass
class InfrastructureResource:
    resource_id: str
    resource_type: str
    environment: str
    properties: Dict[str, Any]

class DriftDetectorAndRemediator:
    def __init__(self, desired_state: List[InfrastructureResource]):
        # O estado desejado (Declarativo - IaC)
        self.desired_state = {res.resource_id: res for res in desired_state}

    def inspect_real_infrastructure(self, real_infrastructure: List[InfrastructureResource]) -> List[Dict[str, Any]]:
        """
        Simula a inspeção do estado real da nuvem comparando com o desejado.
        Retorna a lista de drifts detectados.
        """
        drifts = []
        for real_res in real_infrastructure:
            res_id = real_res.resource_id
            if res_id not in self.desired_state:
                continue
            
            desired_res = self.desired_state[res_id]
            divergences = {}

            # Comparar propriedades chave
            for key, desired_val in desired_res.properties.items():
                real_val = real_res.properties.get(key)
                if real_val != desired_val:
                    divergences[key] = {
                        "desired": desired_val,
                        "real": real_val
                    }

            if divergences:
                drifts.append({
                    "resource_id": res_id,
                    "resource_type": real_res.resource_type,
                    "environment": real_res.environment,
                    "divergences": divergences
                })
        return drifts

    def apply_remediation_policy(self, drift: Dict[str, Any]) -> str:
        """
        Aplica a política de remediação com base no ambiente e tipo de drift.
        Evita o equívoco de auto-remediação cega em produção.
        """
        env = drift["environment"]
        
        # Política: Em produção, nunca auto-remedia sem aprovação para evitar downtime crítico.
        if env == "production":
            return "ALERT_AND_CREATE_TICKET (Production Drift requires manual review)"
        else:
            # Em ambientes de desenvolvimento/teste, auto-remediação é permitida
            return "AUTO_REEDIATE (Reverted to declarative state successfully)"

def run_experiment():
    print("=== INICIANDO EXPERIMENTO DE DETECÇÃO E REMEDIAÇÃO DE DRIFT ===")

    # 1. Definir o Estado Desejado (IaC)
    desired_resources = [
        InfrastructureResource(
            resource_id="i-prod-web-01",
            resource_type="aws_instance",
            environment="production",
            properties={"instance_type": "t3.medium", "encrypted_storage": True, "public_ip": False}
        ),
        InfrastructureResource(
            resource_id="i-dev-app-01",
            resource_type="aws_instance",
            environment="development",
            properties={"instance_type": "t3.micro", "encrypted_storage": False, "public_ip": True}
        )
    ]

    detector = DriftDetectorAndRemediator(desired_resources)

    # 2. Simular o Estado Real da Nuvem (com Drifts induzidos por alteração manual)
    # Drift 1: Em produção, alguém alterou o tipo de instância manualmente para baratear (não autorizado)
    # Drift 2: Em desenvolvimento, alguém alterou o tipo de instância
    real_resources_with_drift = [
        InfrastructureResource(
            resource_id="i-prod-web-01",
            resource_type="aws_instance",
            environment="production",
            properties={"instance_type": "t2.micro", "encrypted_storage": True, "public_ip": False}
        ),
        InfrastructureResource(
            resource_id="i-dev-app-01",
            resource_type="aws_instance",
            environment="development",
            properties={"instance_type": "t3.small", "encrypted_storage": False, "public_ip": True}
        )
    ]

    print("\n[1] Executando varredura de inspeção de infraestrutura...")
    detected_drifts = detector.inspect_real_infrastructure(real_resources_with_drift)
    
    print(f"-> Total de recursos monitorados: {len(desired_resources)}")
    print(f"-> Drifts detectados: {len(detected_drifts)}")

    assert len(detected_drifts) == 2, "Erro: Deveria ter detectado drift em 100% dos recursos alterados."

    # 3. Processar remediação por política
    print("\n[2] Aplicando políticas de remediação...")
    for drift in detected_drifts:
        action = detector.apply_remediation_policy(drift)
        print(f"Recursos: {drift['resource_id']} ({drift['environment']}) | Divergências: {drift['divergences']} | Ação: {action}")

    print("\n=== EXPERIMENTO EXECUTADO COM SUCESSO ===")

if __name__ == "__main__":
    try:
        run_experiment()
        sys.exit(0)
    except Exception as e:
        print(f"Erro fatal no experimento: {e}")
        sys.exit(1)