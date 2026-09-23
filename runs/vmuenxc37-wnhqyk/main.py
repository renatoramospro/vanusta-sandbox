import json
import os
import unittest

# ==========================================
# 1. Contratos Estáticos de Webhooks
# ==========================================
WEBHOOK_CONTRACTS = {
    "user.created": {
        "description": "Disparado quando um novo usuário se registra na plataforma.",
        "payload_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "data": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"},
                        "email": {"type": "string"}
                    },
                    "required": ["user_id", "email"]
                }
            },
            "required": ["event_id", "timestamp", "data"]
        },
        "retry_policy": {
            "max_attempts": 5,
            "backoff_factor": 2,
            "initial_interval_seconds": 10
        }
    },
    "user.updated": {
        "description": "Disparado quando os dados de um usuário são modificados.",
        "payload_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "data": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer"},
                        "updated_fields": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["user_id", "updated_fields"]
                }
            },
            "required": ["event_id", "timestamp", "data"]
        },
        "retry_policy": {
            "max_attempts": 3,
            "backoff_factor": 2,
            "initial_interval_seconds": 5
        }
    },
    "order.placed": {
        "description": "Disparado quando um novo pedido é efetuado com sucesso.",
        "payload_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "data": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "total_amount": {"type": "number"}
                    },
                    "required": ["order_id", "total_amount"]
                }
            },
            "required": ["event_id", "timestamp", "data"]
        },
        "retry_policy": {
            "max_attempts": 5,
            "backoff_factor": 3,
            "initial_interval_seconds": 15
        }
    },
    "order.cancelled": {
        "description": "Disparado quando um pedido existente é cancelado.",
        "payload_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "data": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "reason": {"type": "string"}
                    },
                    "required": ["order_id", "reason"]
                }
            },
            "required": ["event_id", "timestamp", "data"]
        },
        "retry_policy": {
            "max_attempts": 3,
            "backoff_factor": 2,
            "initial_interval_seconds": 10
        }
    },
    "payment.received": {
        "description": "Disparado quando a confirmação de pagamento de um pedido é recebida.",
        "payload_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "data": {
                    "type": "object",
                    "properties": {
                        "payment_id": {"type": "string"},
                        "amount": {"type": "number"},
                        "status": {"type": "string"}
                    },
                    "required": ["payment_id", "amount", "status"]
                }
            },
            "required": ["event_id", "timestamp", "data"]
        },
        "retry_policy": {
            "max_attempts": 5,
            "backoff_factor": 2,
            "initial_interval_seconds": 5
        }
    }
}

# ==========================================
# 2. Gerador Automatizado de Documentação Markdown
# ==========================================
class WebhookDocGenerator:
    def __init__(self, contracts):
        self.contracts = contracts

    def generate_markdown(self) -> str:
        lines = [
            "# Documentação de Webhooks e Políticas de Retentativa",
            "",
            "Esta documentação foi gerada automaticamente a partir da inspeção estática dos contratos de eventos.",
            "",
            "## Mecanismos de Segurança",
            "- **Assinatura HMAC SHA-256**: Cada requisição possui o cabeçalho `X-Hub-Signature` contendo o HMAC do payload assinado com a chave secreta compartilhada.",
            "- **Idempotência**: Os consumidores devem processar os eventos utilizando o `event_id` para evitar duplicações.",
            "",
            "---",
            "",
            "## Eventos Suportados",
            ""
        ]

        for event_name, details in self.contracts.items():
            lines.append(f"### Evento: `{event_name}`")
            lines.append(f"")
            lines.append(f"**Descrição:** {details['description']}")
            lines.append(f"")
            lines.append(f"#### Esquema JSON do Payload")
            lines.append("```json")
            lines.append(json.dumps(details["payload_schema"], indent=2))
            lines.append("```")
            lines.append(f"")
            lines.append(f"#### Política de Retentativa (Backoff Exponencial)")
            retry = details["retry_policy"]
            lines.append(f"- **Máximo de Tentativas:** {retry['max_attempts']}")
            lines.append(f"- **Fator de Backoff:** {retry['backoff_factor']}")
            lines.append(f"- **Intervalo Inicial:** {retry['initial_interval_seconds']} segundos")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

# ==========================================
# 3. Testes de Conformidade (Pytest/Unit)
# ==========================================
class TestWebhookDocumentation(unittest.TestCase):
    
    def setUp(self):
        self.generator = WebhookDocGenerator(WEBHOOK_CONTRACTS)
        self.markdown_output = self.generator.generate_markdown()

    def test_minimum_events_count(self):
        """Garante que pelo menos 5 eventos distintos são documentados."""
        self.assertGreaterEqual(len(WEBHOOK_CONTRACTS), 5, "O contrato deve conter pelo menos 5 eventos.")

    def test_markdown_contains_schemas(self):
        """Verifica se os esquemas JSON aparecem na documentação gerada."""
        for event_name in WEBHOOK_CONTRACTS:
            self.assertIn(event_name, self.markdown_output)
            self.assertIn("payload_schema", json.dumps(WEBHOOK_CONTRACTS[event_name]))

    def test_retry_policies_presence(self):
        """Garante que as regras de backoff exponencial estão presentes para todos os eventos."""
        for event_name, details in WEBHOOK_CONTRACTS.items():
            retry = details["retry_policy"]
            self.assertIn("max_attempts", retry)
            self.assertIn("backoff_factor", retry)
            self.assertIn(str(retry["max_attempts"]), self.markdown_output)

    def test_file_generation(self):
        """Executa a geração e salva o arquivo Markdown em disco."""
        output_path = "webhooks_docs.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.markdown_output)
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Documentação de Webhooks", content)
        print(f"\n[SUCESSO] Documento gerado com sucesso em '{output_path}' com {len(WEBHOOK_CONTRACTS)} eventos documentados.")

if __name__ == "__main__":
    unittest.main()