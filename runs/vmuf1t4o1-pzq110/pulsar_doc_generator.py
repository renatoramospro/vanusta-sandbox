import sys
import yaml
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ValidationError

# ==========================================
# 1. Definição do Esquema (Pydantic)
# ==========================================
# O uso do Pydantic resolve o equívoco comum de ler YAML sem validar tipos ou
# chaves obrigatórias, garantindo fail-fast se o arquivo de configuração estiver corrompido.

SubscriptionType = Literal["Exclusive", "Shared", "Failover", "Key_Shared"]
TopicType = Literal["persistent", "non-persistent"]

class RetentionPolicyConfig(BaseModel):
    time_minutes: Optional[int] = Field(None, ge=0, description="Tempo de retenção em minutos")
    size_mb: Optional[int] = Field(None, ge=0, description="Tamanho máximo de retenção em MB")

class SubscriptionConfig(BaseModel):
    name: str = Field(..., min_length=1)
    type: SubscriptionType

class TopicConfig(BaseModel):
    name: str = Field(..., min_length=1)
    type: TopicType = "persistent"
    partitions: int = Field(1, ge=1, description="Número de partições do tópico")
    ttl_seconds: Optional[int] = Field(None, ge=0, description="Time-To-Live para mensagens não consumidas")
    retention: Optional[RetentionPolicyConfig] = None
    subscriptions: List[SubscriptionConfig] = Field(default_factory=list)

class PulsarClusterConfig(BaseModel):
    cluster_name: str
    tenant: str
    namespace: str
    topics: List[TopicConfig] = Field(default_factory=list)


# ==========================================
# 2. Gerador de Documentação Markdown
# ==========================================
class PulsarMarkdownGenerator:
    def __init__(self, config: PulsarClusterConfig):
        self.config = config

    def generate(self) -> str:
        lines = []
        lines.append(f"# Documentação do Cluster Apache Pulsar: {self.config.cluster_name}")
        lines.append("")
        lines.append(f"- **Tenant:** `{self.config.tenant}`")
        lines.append(f"- **Namespace:** `{self.config.namespace}`")
        lines.append("")
        lines.append("## Índice de Tópicos")
        lines.append("")
        
        for topic in self.config.topics:
            lines.append(f"- [{topic.name}](#tópico-{topic.name.replace('/', '-').lower()})")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Detalhes dos Tópicos")
        lines.append("")

        for topic in self.config.topics:
            lines.append(f"### Tópico: `{topic.name}`")
            lines.append("")
            lines.append(f"| Propriedade | Valor |")
            lines.append(f"| :--- | :--- |")
            lines.append(f"| **Tipo** | `{topic.type}` |")
            lines.append(f"| **Partições** | `{topic.partitions}` |")
            
            ttl_str = f"{topic.ttl_seconds} segundos" if topic.ttl_seconds is not None else "Ilimitado (ou padrão do namespace)"
            lines.append(f"| **TTL de Mensagens** | {ttl_str} |")
            
            if topic.retention:
                ret_parts = []
                if topic.retention.time_minutes is not None:
                    ret_parts.append(f"Tempo: {topic.retention.time_minutes} min")
                if topic.retention.size_mb is not None:
                    ret_parts.append(f"Tamanho: {topic.retention.size_mb} MB")
                retention_str = ", ".join(ret_parts) if ret_parts else "Nenhuma"
            else:
                retention_str = "Padrão do Namespace"
            
            lines.append(f"| **Política de Retenção** | {retention_str} |")
            lines.append("")
            
            lines.append("#### Assinaturas (Subscriptions)")
            lines.append("")
            if topic.subscriptions:
                lines.append("| Nome da Assinatura | Tipo de Assinatura |")
                lines.append("| :--- | :--- |")
                for sub in topic.subscriptions:
                    lines.append(f"| `{sub.name}` | `{sub.type}` |")
            else:
                lines.append("*Nenhuma assinatura configurada diretamente.*")
            
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


# ==========================================
# 3. Função Auxiliar de Execução
# ==========================================
def generate_markdown_from_yaml(yaml_content: str) -> str:
    data = yaml.safe_load(yaml_content)
    # Validação rigorosa via Pydantic (levanta ValidationError se inválido)
    validated_config = PulsarClusterConfig(**data)
    generator = PulsarMarkdownGenerator(validated_config)
    return generator.generate()

if __name__ == "__main__":
    sample_yaml = """
    cluster_name: "production-us-east"
    tenant: "financeiro"
    namespace: "pagamentos"
    topics:
      - name: "transacoes-pix"
        type: "persistent"
        partitions: 4
        ttl_seconds: 86400
        retention:
          time_minutes: 1440
          size_mb: 50000
        subscriptions:
          - name: "processador-pagamento"
            type: "Failover"
          - name: "auditoria-analytics"
            type: "Shared"
    """
    
    md_output = generate_markdown_from_yaml(sample_yaml)
    print("=== Markdown Gerado com Sucesso ===")
    print(md_output)