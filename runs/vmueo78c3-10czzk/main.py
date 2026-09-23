import os
import json
import glob
import unittest

class ContractValidationError(Exception):
    """Exceção levantada quando um contrato de webhook falha na validação estática."""
    pass


class WebhookContractInspector:
    """Inspeciona contratos estáticos de webhooks, valida esquemas e calcula políticas de retry."""
    
    def __init__(self, contracts_dir="contracts"):
        self.contracts_dir = contracts_dir
        self.contracts = {}

    def load_contracts(self):
        """Lê os arquivos JSON estáticos de contratos a partir do diretório."""
        pattern = os.path.join(self.contracts_dir, "*.json")
        for filepath in glob.glob(pattern):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    event_name = data.get("event_name")
                    if not event_name:
                        raise ContractValidationError(f"O arquivo {filepath} não possui 'event_name'.")
                    self.contracts[event_name] = data
                except json.JSONDecodeError as e:
                    raise ContractValidationError(f"Erro ao decodificar JSON em {filepath}: {e}")
        return self.contracts

    def validate_semantic_schema(self, contract):
        """Validação semântica e estrutural estricta do contrato e do JSON Schema."""
        schema = contract.get("payload_schema")
        if not schema or not isinstance(schema, dict):
            raise ContractValidationError(f"Contrato {contract.get('event_name')} possui 'payload_schema' inválido ou ausente.")
        
        if schema.get("type") != "object":
            raise ContractValidationError(f"O esquema raiz para {contract.get('event_name')} deve ser do tipo 'object'.")
        
        properties = schema.get("properties", {})
        if "event_id" not in properties or "timestamp" not in properties or "data" not in properties:
            raise ContractValidationError(f"Contrato {contract.get('event_name')} viola o padrão obrigatório: deve conter event_id, timestamp e data.")

        # Validação da Política de Retentativa
        retry = contract.get("retry_policy")
        if not retry or not isinstance(retry, dict):
            raise ContractValidationError(f"Contrato {contract.get('event_name')} possui 'retry_policy' inválida.")
        
        max_attempts = retry.get("max_attempts")
        if not isinstance(max_attempts, int) or max_attempts <= 0:
            raise ContractValidationError(f"Contrato {contract.get('event_name')} tem max_attempts inválido: {max_attempts} (deve ser inteiro > 0).")
        
        factor = retry.get("backoff_factor")
        if not isinstance(factor, (int, float)) or factor < 1.0:
            raise ContractValidationError(f"Contrato {contract.get('event_name')} tem backoff_factor inválido: {factor}.")
            
        initial = retry.get("initial_interval_seconds")
        if not isinstance(initial, (int, float)) or initial <= 0:
            raise ContractValidationError(f"Contrato {contract.get('event_name')} tem initial_interval_seconds inválido: {initial}.")

        return True

    def calculate_backoff_sequence(self, retry_policy, include_jitter=True):
        """
        Calcula a sequência exata de intervalos de espera entre tentativas.
        Se max_attempts = N, existem (N - 1) intervalos de espera (retentativas).
        Fórmula: Intervalo = Initial * (Factor ^ (attempt_index)) + Opcional Jitter
        """
        max_attempts = retry_policy["max_attempts"]
        factor = retry_policy["backoff_factor"]
        initial = retry_policy["initial_interval_seconds"]
        
        intervals = []
        # Existem (max_attempts - 1) tentativas de reenvio após a falha inicial
        num_retries = max_attempts - 1
        for i in range(num_retries):
            interval = initial * (factor ** i)
            if include_jitter:
                # Jitter determinístico simulado de ±10% para testes consistentes
                jitter = interval * 0.1 * (1 if i % 2 == 0 else -1)
                interval = round(interval + jitter, 2)
            intervals.append(interval)
        return intervals

    def generate_markdown(self):
        """Gera documentação Markdown detalhada a partir dos contratos inspecionados."""
        lines = [
            "# Documentação Oficial de Webhooks e Políticas de Retentativa",
            "",
            "Esta documentação foi gerada automaticamente por inspeção estática de contratos.",
            "",
            "---",
            ""
        ]

        for event_name, contract in sorted(self.contracts.items()):
            self.validate_semantic_schema(contract)
            desc = contract.get("description", "Sem descrição.")
            schema = contract.get("payload_schema")
            retry = contract.get("retry_policy")
            backoff_seq = self.calculate_backoff_sequence(retry)

            lines.append(f"## Evento: `{event_name}`")
            lines.append(f"**Descrição:** {desc}")
            lines.append("")
            lines.append("### Esquema do Payload (JSON Schema)")
            lines.append("```json")
            lines.append(json.dumps(schema, indent=2))
            lines.append("```")
            lines.append("")
            lines.append("### Política de Retentativa e Resiliência")
            lines.append(f"- **Tentativas Máximas (`max_attempts`):** {retry['max_attempts']} (1 tentativa inicial + {retry['max_attempts'] - 1} retentativas)")
            lines.append(f"- **Fator de Backoff (`backoff_factor`):** {retry['backoff_factor']}")
            lines.append(f"- **Intervalo Inicial (`initial_interval_seconds`):** {retry['initial_interval_seconds']}s")
            lines.append(f"- **Sequência Calculada de Espera (com Jitter):** `{backoff_seq}` segundos")
            lines.append("")
            lines.append("> **Nota de Arquitetura:** A garantia de entrega (*At-Least-Once Delivery*) assegura que o evento será reenviado em caso de falha de rede ou timeout (HTTP 5xx). O consumidor **deve** implementar **idempotência** (ex: utilizando o `event_id` único) para evitar efeitos duplicados em processamentos repetidos.")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# ==========================================
# Testes Automatizados de Conformidade
# ==========================================
class TestWebhookInspectionAndCompliance(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.inspector = WebhookContractInspector("contracts")
        cls.contracts = cls.inspector.load_contracts()
        cls.markdown = cls.inspector.generate_markdown()

    def test_at_least_five_events_inspected(self):
        """Garante que pelo menos 5 eventos distintos são carregados e documentados."""
        self.assertGreaterEqual(len(self.contracts), 5, f"Esperado pelo menos 5 eventos, encontrados {len(self.contracts)}.")

    def test_semantic_validation_passes(self):
        """Verifica se todos os contratos carregados passam na validação semântica."""
        for name, contract in self.contracts.items():
            with self.subTest(event=name):
                self.assertTrue(self.inspector.validate_semantic_schema(contract))

    def test_backoff_math_precision(self):
        """Valida matematicamente a distinção entre tentativas totais e intervalos de espera."""
        # Exemplo: max_attempts = 5 implica exatamente 4 intervalos de espera
        retry_policy = {"max_attempts": 5, "backoff_factor": 2.0, "initial_interval_seconds": 10}
        intervals = self.inspector.calculate_backoff_sequence(retry_policy, include_jitter=False)
        self.assertEqual(len(intervals), 4, "Para 5 tentativas, deve haver exatamente 4 intervalos de espera.")
        self.assertEqual(intervals, [10.0, 20.0, 40.0, 80.0])

    def test_invalid_contract_rejection(self):
        """Garante que contratos malformados ou com max_attempts inválido falham na inspeção estática."""
        invalid_contract = {
            "event_name": "bad.event",
            "description": "Evento inválido",
            "payload_schema": {"type": "object", "properties": {"event_id": {}, "timestamp": {}, "data": {}}},
            "retry_policy": {"max_attempts": 0, "backoff_factor": 2.0, "initial_interval_seconds": 10}
        }
        with self.assertRaises(ContractValidationError):
            self.inspector.validate_semantic_schema(invalid_contract)

    def test_markdown_generation_and_idempotency_note(self):
        """Verifica se o arquivo Markdown é gerado e contém notas vitais de idempotência."""
        output_path = "webhooks_docs.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.markdown)
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Documentação Oficial de Webhooks", content)
            self.assertIn("idempotência", content)
            self.assertIn("At-Least-Once Delivery", content)
            for event_name in self.contracts:
                self.assertIn(event_name, content)
        print(f"\n[SUCESSO] Inspeção estática de {len(self.contracts)} contratos concluída, documentação gerada em '{output_path}' com validação semântica e matemática rigorosa.")


if __name__ == "__main__":
    unittest.main()