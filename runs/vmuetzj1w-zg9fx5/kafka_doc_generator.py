import json
import os
import re
import sys
import glob

# ==========================================
# SIMULAÇÃO DE INFRAESTRUTURA KAFKA & SCHEMA REGISTRY (ROBUSTA)
# ==========================================
class MockKafkaAdminClient:
    """Simula o AdminClient do Kafka, suportando configurações ausentes reais."""
    def __init__(self, topics_metadata):
        self.topics_metadata = topics_metadata

    def list_topics(self):
        return list(self.topics_metadata.keys())

    def describe_configs(self, topics):
        configs = {}
        for topic in topics:
            if topic in self.topics_metadata:
                meta = self.topics_metadata[topic]
                cfg = {}
                # Se a propriedade não estiver explicitamente configurada, não inventamos default
                if "retention_ms" in meta:
                    cfg["retention.ms"] = str(meta["retention_ms"])
                if "cleanup_policy" in meta:
                    cfg["cleanup.policy"] = meta["cleanup_policy"]
                if "partitions" in meta:
                    cfg["partitions"] = str(meta["partitions"])
                configs[topic] = cfg
        return configs

class MockSchemaRegistryClient:
    """Simula o Schema Registry suportando versões, compatibilidade e múltiplos esquemas."""
    def __init__(self, schemas_data):
        self.schemas_data = schemas_data

    def get_latest_schema(self, subject):
        if subject in self.schemas_data:
            return self.schemas_data[subject]
        return None

# ==========================================
# NORMALIZADOR E GERADOR DE DOCUMENTAÇÃO
# ==========================================
class AdvancedKafkaDocGenerator:
    def __init__(self, admin_client, registry_client, output_dir="docs/topics"):
        self.admin = admin_client
        self.registry = registry_client
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _parse_avro_type(self, avro_type):
        """Trata tipos primitivos, complexos, unions (nulos) e logicalTypes."""
        if isinstance(avro_type, list):
            # Ex: ["null", "string"] ou ["null", {"type": "string", "logicalType": "uuid"}]
            non_nulls = [t for t in avro_type if t != "null"]
            is_nullable = len(avro_type) > len(non_nulls)
            
            if len(non_nulls) == 1:
                inner = non_nulls[0]
                parsed_inner = self._parse_avro_type(inner)
                parsed_inner["nullable"] = is_nullable
                return parsed_inner
            else:
                return {"type": "union", "details": non_nulls, "nullable": is_nullable}
        
        elif isinstance(avro_type, dict):
            t_name = avro_type.get("type", "object")
            logical = avro_type.get("logicalType")
            res = {"type": t_name, "nullable": False}
            if logical:
                res["logicalType"] = logical
            return res
        
        else:
            return {"type": str(avro_type), "nullable": False}

    def _normalize_schema_fields(self, schema_fields):
        normalized = []
        for field in schema_fields:
            parsed = self._parse_avro_type(field.get("type"))
            normalized.append({
                "name": field.get("name"),
                "type": parsed.get("type"),
                "logicalType": parsed.get("logicalType"),
                "nullable": parsed.get("nullable", False),
                "doc": field.get("doc", "Sem descrição.")
            })
        return normalized

    def extract_and_generate(self):
        active_topics = self.admin.list_topics()
        configs = self.admin.describe_configs(active_topics)
        
        generated_files = []
        
        for topic in active_topics:
            topic_cfg = configs.get(topic, {})
            retention = topic_cfg.get("retention.ms", "N/A (Não configurado / Padrão do Broker)")
            cleanup = topic_cfg.get("cleanup.policy", "N/A")
            partitions = topic_cfg.get("partitions", "N/A")
            
            subject = f"{topic}-value"
            schema_meta = self.registry.get_latest_schema(subject)
            
            schema_version = "N/A"
            compatibility = "N/A"
            fields_doc = []
            
            if schema_meta:
                schema_version = schema_meta.get("version", 1)
                compatibility = schema_meta.get("compatibility", "BACKWARD")
                raw_schema = json.loads(schema_meta.get("schema", "{}"))
                fields_doc = self._normalize_schema_fields(raw_schema.get("fields", []))

            # Montagem do Markdown
            md_content = f"""# Tópico: {topic}

## Metadados Operacionais
- **Partições:** {partitions}
- **Retenção (retention.ms):** {retention}
- **Política de Limpeza (cleanup.policy):** {cleanup}

## Contrato Avro (Schema Registry)
- **Subject:** `{subject}`
- **Versão do Schema:** {schema_version}
- **Política de Compatibilidade:** {compatibility}

### Campos do Contrato
| Campo | Tipo Avro | Tipo Lógico | Nulável? | Descrição |
|-------|-----------|-------------|----------|-----------|
"""
            for f in fields_doc:
                logical_str = f["logicalType"] if f["logicalType"] else "-"
                nullable_str = "Sim" if f["nullable"] else "Não"
                md_content += f"| `{f['name']}` | `{f['type']}` | `{logical_str}` | {nullable_str} | {f['doc']} |\n"

            file_path = os.path.join(self.output_dir, f"{topic}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            generated_files.append(file_path)
            print(f"[SUCESSO] Documentação gerada para o tópico: {topic} -> {file_path}")

        # Garbage Collection: Remove arquivos de tópicos que não existem mais no cluster
        existing_files = glob.glob(os.path.join(self.output_dir, "*.md"))
        for file_path in existing_files:
            topic_name = os.path.splitext(os.path.basename(file_path))[0]
            if topic_name not in active_topics:
                os.remove(file_path)
                print(f"[GARBAGE COLLECTION] Tópico obsoleto removido: {file_path}")

        return generated_files

class DocLinter:
    @staticmethod
    def lint_file(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        required_headers = ["## Metadados Operacionais", "## Contrato Avro", "### Campos do Contrato"]
        for header in required_headers:
            if header not in content:
                raise AssertionError(f"Linter falhou em {file_path}: Cabeçalho obrigatório ausente -> '{header}'")
        print(f"[LINT OK] Arquivo validado com sucesso: {file_path}")


# ==========================================
# EXECUÇÃO DO TESTE COM CENÁRIOS COMPLEXOS
# ==========================================
if __name__ == "__main__":
    # Cenários cobrindo: Union anulável, logicalType, config ausente, versão/compatibilidade
    mock_topics_metadata = {
        "vanusta.shipments.v1": {
            "partitions": 4,
            # retention_ms omitido propositalmente para testar config ausente
            "cleanup_policy": "compact"
        },
        "vanusta.accounts.v1": {
            "partitions": 2,
            "retention_ms": "86400000",
            "cleanup_policy": "delete"
        }
    }

    mock_schemas = {
        "vanusta.shipments.v1-value": {
            "version": 2,
            "compatibility": "FULL",
            "schema": json.dumps({
                "type": "record",
                "name": "ShipmentEvent",
                "fields": [
                    {"name": "orderId", "type": "string", "doc": "Identificador único do pedido."},
                    {
                        "name": "trackingCode",
                        "type": ["null", "string"],
                        "default": None,
                        "doc": "Código de rastreio opcional."
                    },
                    {
                        "name": "eventTimestamp",
                        "type": {"type": "long", "logicalType": "timestamp-millis"},
                        "doc": "Momento do evento."
                    }
                ]
            })
        },
        "vanusta.accounts.v1-value": {
            "version": 1,
            "compatibility": "BACKWARD",
            "schema": json.dumps({
                "type": "record",
                "name": "AccountEvent",
                "fields": [
                    {"name": "accountId", "type": "string", "doc": "ID da conta."}
                ]
            })
        }
    }

    # Simula arquivo obsoleto antigo que deve ser removido pelo garbage collector
    os.makedirs("docs/topics", exist_ok=True)
    obsolete_file = "docs/topics/vanusta.deprecated.v0.md"
    with open(obsolete_file, "w") as f:
        f.write("# Tópico Depreciado")

    admin = MockKafkaAdminClient(mock_topics_metadata)
    registry = MockSchemaRegistryClient(mock_schemas)

    generator = AdvancedKafkaDocGenerator(admin, registry, output_dir="docs/topics")
    generated_files = generator.extract_and_generate()

    # Verifica se o arquivo obsoleto foi removido
    assert not os.path.exists(obsolete_file), "Falha no Garbage Collection: arquivo obsoleto não foi removido."

    print("\n--- INICIANDO VALIDAÇÃO DE LINT ---")
    for file_path in generated_files:
        DocLinter.lint_file(file_path)

    print(f"\n[SUCESSO ABSOLUTO] {len(generated_files)} tópicos processados com acurácia semântica, suporte a unions, logicalTypes, controle de versões e GC de artefatos!")