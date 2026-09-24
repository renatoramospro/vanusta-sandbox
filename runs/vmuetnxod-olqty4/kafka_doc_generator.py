import json
import os
import re
import sys

# ==========================================
# SIMULAÇÃO DE INFRAESTRUTURA KAFKA & SCHEMA REGISTRY
# ==========================================
class MockKafkaAdminClient:
    """Simula o AdminClient do Apache Kafka para descoberta de tópicos e configurações."""
    def __init__(self, topics_metadata):
        self.topics_metadata = topics_metadata

    def list_topics(self):
        return list(self.topics_metadata.keys())

    def describe_configs(self, topics):
        configs = {}
        for topic in topics:
            if topic in self.topics_metadata:
                meta = self.topics_metadata[topic]
                configs[topic] = {
                    "retention.ms": meta.get("retention_ms", "604800000"),
                    "cleanup.policy": meta.get("cleanup_policy", "delete"),
                    "partitions": str(meta.get("partitions", 3))
                }
        return configs

class MockSchemaRegistryClient:
    """Simula o Confluent Schema Registry para extração de contratos Avro."""
    def __init__(self, schemas):
        self.schemas = schemas

    def get_latest_schema(self, subject):
        if subject in self.schemas:
            return {
                "subject": subject,
                "version": 1,
                "schema": self.schemas[subject]
            }
        raise Exception(f"Schema not found for subject: {subject}")

# ==========================================
# GERADOR DE DOCUMENTAÇÃO KAFKA
# ==========================================
class KafkaDocGenerator:
    def __init__(self, admin_client, schema_registry_client, output_dir="docs/topics"):
        self.admin = admin_client
        self.registry = schema_registry_client
        self.output_dir = output_dir

    def extract_and_generate(self):
        os.makedirs(self.output_dir, exist_ok=True)
        topics = self.admin.list_topics()
        configs = self.admin.describe_configs(topics)
        
        generated_files = []
        
        for topic in topics:
            cfg = configs.get(topic, {})
            subject = f"{topic}-value"
            
            try:
                schema_data = self.registry.get_latest_schema(subject)
                schema_json = json.loads(schema_data["schema"])
            except Exception:
                schema_json = {"type": "record", "name": "Unknown", "fields": []}
            
            markdown_content = self._render_markdown(topic, cfg, schema_json)
            
            file_path = os.path.join(self.output_dir, f"{topic}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            generated_files.append(file_path)
            print(f"[SUCESSO] Documentação gerada para o tópico: {topic} -> {file_path}")
            
        return generated_files

    def _render_markdown(self, topic, config, schema):
        fields = schema.get("fields", [])
        fields_rows = ""
        for field in fields:
            f_name = field.get("name", "N/A")
            f_type = str(field.get("type", "N/A"))
            f_doc = field.get("doc", "Sem descrição.")
            fields_rows += f"| `{f_name}` | `{f_type}` | {f_doc} |\n"

        if not fields_rows:
            fields_rows = "| N/A | N/A | Nenhum campo mapeado. |\n"

        md = f"""# Tópico Kafka: `{topic}`

## 📌 Metadados Operacionais
- **Partições:** {config.get('partitions', 'N/A')}
- **Política de Retenção (`cleanup.policy`):** {config.get('cleanup.policy', 'N/A')}
- **Tempo de Retenção (`retention.ms`):** {config.get('retention.ms', 'N/A')} ms

## 📑 Contrato de Dados (Esquema Avro)
- **Nome do Schema:** `{schema.get('name', 'N/A')}`
- **Namespace:** `{schema.get('namespace', 'N/A')}`

### Campos do Contrato
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
{fields_rows}
---
*Gerado automaticamente pelo Pipeline de Documentação Kafka da Vanusta.*
"""
        return md

class DocLinter:
    """Valida se os arquivos Markdown gerados atendem aos critérios estruturais da Vanusta."""
    @staticmethod
    def lint_file(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        required_sections = [
            "## 📌 Metadados Operacionais",
            "## 📑 Contrato de Dados (Esquema Avro)",
            "### Campos do Contrato"
        ]
        
        for section in required_sections:
            if section not in content:
                raise AssertionError(f"Erro de Lint em {file_path}: Seção obrigatória ausente -> '{section}'")
        
        # Validação básica de sintaxe Markdown (presença de títulos e tabelas)
        if "# Tópico Kafka:" not in content:
            raise AssertionError(f"Erro de Lint em {file_path}: Título principal ausente.")
            
        print(f"[LINT OK] Arquivo validado com sucesso: {file_path}")
        return True

# ==========================================
# EXECUÇÃO DO EXPERIMENTO (5 TÓPICOS DE TESTE)
# ==========================================
if __name__ == "__main__":
    # Mock data para os 5 tópicos exigidos pelo critério de sucesso
    mock_topics_metadata = {
        "vanusta.orders.v1": {"retention_ms": "604800000", "cleanup_policy": "delete", "partitions": 6},
        "vanusta.payments.v1": {"retention_ms": "1209600000", "cleanup_policy": "delete", "partitions": 4},
        "vanusta.customers.v1": {"retention_ms": "-1", "cleanup_policy": "compact", "partitions": 2},
        "vanusta.inventory.v1": {"retention_ms": "259200000", "cleanup_policy": "delete", "partitions": 3},
        "vanusta.notifications.v1": {"retention_ms": "86400000", "cleanup_policy": "delete", "partitions": 8},
    }

    mock_schemas = {
        "vanusta.orders.v1-value": json.dumps({
            "type": "record",
            "name": "OrderEvent",
            "namespace": "com.vanusta.orders",
            "fields": [
                {"name": "order_id", "type": "string", "doc": "Identificador único do pedido."},
                {"name": "amount", "type": "double", "doc": "Valor total da transação."},
                {"name": "status", "type": "string", "doc": "Estado atual do pedido."}
            ]
        }),
        "vanusta.payments.v1-value": json.dumps({
            "type": "record",
            "name": "PaymentEvent",
            "namespace": "com.vanusta.payments",
            "fields": [
                {"name": "payment_id", "type": "string", "doc": "ID do pagamento."},
                {"name": "method", "type": "string", "doc": "Método utilizado (CREDIT_CARD, PIX)."}
            ]
        }),
        "vanusta.customers.v1-value": json.dumps({
            "type": "record",
            "name": "CustomerProfile",
            "namespace": "com.vanusta.customers",
            "fields": [
                {"name": "customer_id", "type": "string", "doc": "ID do cliente."},
                {"name": "email", "type": "string", "doc": "E-mail de contato."}
            ]
        }),
        "vanusta.inventory.v1-value": json.dumps({
            "type": "record",
            "name": "InventoryUpdate",
            "namespace": "com.vanusta.inventory",
            "fields": [
                {"name": "sku", "type": "string", "doc": "Código SKU do produto."},
                {"name": "quantity", "type": "int", "doc": "Quantidade em estoque."}
            ]
        }),
        "vanusta.notifications.v1-value": json.dumps({
            "type": "record",
            "name": "NotificationDispatch",
            "namespace": "com.vanusta.notifications",
            "fields": [
                {"name": "notification_id", "type": "string", "doc": "ID da notificação."},
                {"name": "channel", "type": "string", "doc": "Canal de envio (SMS, EMAIL, PUSH)."}
            ]
        }),
    }

    admin = MockKafkaAdminClient(mock_topics_metadata)
    registry = MockSchemaRegistryClient(mock_schemas)
    
    generator = KafkaDocGenerator(admin, registry, output_dir="docs/topics")
    generated_files = generator.extract_and_generate()
    
    print("\n--- INICIANDO VALIDAÇÃO DE LINT ---")
    for file_path in generated_files:
        DocLinter.lint_file(file_path)
        
    print(f"\n[SUCESSO ABSOLUTO] {len(generated_files)} tópicos processados, documentados e validados com sucesso!")