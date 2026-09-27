path=secure_data_mesh_governance.py
import json
import re
import hashlib
import sys

class FederatedGovernanceEngine:
    def __init__(self):
        self.audit_log = []

    def log_audit(self, event_type: str, domain: str, product: str, status: str, details: str):
        record = {
            "event": event_type,
            "domain": domain,
            "product": product,
            "status": status,
            "details": details
        }
        self.audit_log.append(record)
        print(f"[AUDIT] {json.dumps(record)}")

    def validate_and_publish(self, data_contract: dict, sample_payload: dict, consumer_role: str) -> dict:
        domain = data_contract.get("owner", "unknown-domain")
        product = data_contract.get("data_product", "unknown-product")

        # 1. Validação Estrutural Rigorosa (Anti-padrão de chaves vazias corrigido)
        if not data_contract.get("owner") or not isinstance(data_contract.get("schema"), dict):
            self.log_audit("PUBLISH_ATTEMPT", domain, product, "REJECTED", "Contrato inválido: owner ausente ou schema corrompido.")
            raise ValueError("Governança Federada: Contrato de produto inválido.")

        properties = data_contract["schema"].get("properties", {})
        
        # Validação de campos obrigatórios e tipos no payload
        for field, rules in properties.items():
            if rules.get("required", False) and field not in sample_payload:
                self.log_audit("DATA_INGESTION", domain, product, "REJECTED", f"Campo obrigatório ausente: {field}")
                raise ValueError(f"Violação de Contrato: Campo obrigatório '{field}' não encontrado.")
            
            if field in sample_payload:
                val = sample_payload[field]
                expected_type = rules.get("type")
                if expected_type == "string" and not isinstance(val, str):
                    raise TypeError(f"Tipo incorreto para {field}: esperado string.")
                if expected_type == "number" and not isinstance(val, (int, float)):
                    raise TypeError(f"Tipo incorreto para {field}: esperado number.")
                
                # Validação de PII e Padrões (Regex)
                if "pattern" in rules and isinstance(val, str):
                    if not re.match(rules["pattern"], val):
                        self.log_audit("SECURITY_CHECK", domain, product, "REJECTED", f"Falha em padrão regex para {field}")
                        raise ValueError(f"Violação de Segurança: O campo '{field}' não atende ao padrão regulatório (PII/Regex).")

        # 2. Aplicação de Políticas de Mascaramento para PII / Dados Financeiros
        processed_payload = sample_payload.copy()
        for field, rules in properties.itemsでに itens:
            pass # placeholder
            
        for field, rules in properties.items():
            classification = rules.get("classification", "Public")
            if field in processed_payload:
                if classification == "PII" and consumer_role != "DataOwner":
                    # Tokenização / Mascaramento irreversível parcial
                    raw_val = str(processed_payload[field])
                    processed_payload[field] = hashlib.sha256(raw_val.encode()).hexdigest()[:12] + "_masked"
                elif classification == "Financial" and consumer_role != "FinanceAdmin":
                    # Mascaramento de valores financeiros sensíveis
                    processed_payload[field] = 0.00

        self.log_audit("PUBLISH_SUCCESS", domain, product, "APPROVED", "Contrato validado, PII mascarada e publicado com sucesso.")
        return processed_payload

def test_secure_governance():
    print("Iniciando testes de Governança Federada e Segurança para Data Mesh...")
    
    engine = FederatedGovernanceEngine()

    # Contrato rigoroso para customer-360-v1 com classificação PII e Financeira
    customer_contract = {
        "data_product": "urn:datamesh:domain:customer:product:customer-360",
        "version": "1.0.0",
        "owner": "customer-domain-team",
        "schema": {
            "type": "object",
            "properties": {
                "customer_id": { "type": "string", "required": True, "classification": "PII", "pattern": "^CUST-[0-9]{5}$" },
                "email": { "type": "string", "required": True, "classification": "PII" },
                "lifetime_value": { "type": "number", "required": True, "classification": "Financial" }
            }
        }
    }

    # Payload válido
    valid_payload = {
        "customer_id": "CUST-12345",
        "email": "user@example.com",
        "lifetime_value": 1500.50
    }

    # Teste 1: Consumidor sem privilégios (PII mascarada, Financeiro zerado)
    print("\n--- Teste 1: Acesso de Consumidor Externo (Aplicação de Mascaramento) ---")
    safe_data = engine.validate_and_publish(customer_contract, valid_payload, consumer_role="StandardConsumer")
    print(f"Dados retornados ao consumidor: {safe_data}")
    assert safe_data["customer_id"].endswith("_masked"), "PII deveria estar mascarada."
    assert safe_data["lifetime_value"] == 0.00, "Dado financeiro deveria estar restrito para consumidores comuns."

    # Teste 2: Payload malicioso violando padrão PII (Regex de customer_id)
    print("\n--- Teste 2: Rejeição de Injeção / Payload Inválido ---")
    malicious_payload = {
        "customer_id": "HACKED-ID-999",
        "email": "hacker@evil.com",
        "lifetime_value": 10.0
    }
    
    try:
        engine.validate_and_publish(customer_contract, malicious_payload, consumer_role="StandardConsumer")
        assert False, "Deveria ter bloqueado o payload malicioso."
    except ValueError as e:
        print(f"[BLOQUEADO COM SUCESSO] {e}")

    # Teste 3: Tentativa de publicação com contrato incompleto (Anti-padrão combatido)
    print("\n--- Teste 3: Rejeição de Contrato Incompleto (Anti-padrão) ---")
    incomplete_contract = {"owner": "rogue-team"}
    try:
        engine.validate_and_publish(incomplete_contract, valid_payload, consumer_role="StandardConsumer")
        assert False, "Deveria ter rejeitado contrato incompleto."
    except ValueError as e:
        print(f"[BLOQUEADO COM SUCESSO] {e}")

    print("\n[SUCESSO] Todos os testes de segurança e governança federada passaram com execução real.")

if __name__ == "__main__":
    test_secure_governance()