import sys
import yaml
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ValidationError

# ==========================================
# 1. Definição do Esquema (Pydantic)
# ==========================================
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
        lines.append("## Tópicos Configurados")
        lines.append("")

        if not self.config.topics:
            lines.append("_Nenhum tópico configurado._")
            return "\n".join(lines)

        for topic in self.config.topics:
            lines.append(f"### Tópico: `{topic.name}`")
            lines.append(f"- **Tipo:** `{topic.type}`")
            lines.append(f"- **Partições:** `{topic.partitions}`")
            
            if topic.ttl_seconds is not None:
                lines.append(f"- **TTL (Time-To-Live):** `{topic.ttl_seconds} segundos`")
            else:
                lines.append("- **TTL (Time-To-Live):** _Não configurado_")

            if topic.retention:
                ret_parts = []
                if topic.retention.time_minutes is not None:
                    ret_parts.append(f"Tempo: {topic.retention.time_minutes} min")
                if topic.retention.size_mb is not None:
                    ret_parts.append(f"Tamanho: {topic.retention.size_mb} MB")
                ret_str = ", ".join(ret_parts) if ret_parts else "Padrão"
                lines.append(f"- **Política de Retenção:** `{ret_str}`")
            else:
                lines.append("- **Política de Retenção:** _Padrão do Namespace_")

            lines.append("")
            lines.append("#### Assinaturas (Subscriptions)")
            if not topic.subscriptions:
                lines.append("_Nenhuma assinatura definida para este tópico._")
            else:
                lines.append("| Nome da Assinatura | Tipo de Assinatura |")
                lines.append("| :--- | :--- |")
                for sub in topic.subscriptions:
                    lines.append(f"| `{sub.name}` | `{sub.type}` |")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

def generate_markdown_from_yaml(yaml_content: str) -> str:
    raw_data = yaml.safe_load(yaml_content)
    config = PulsarClusterConfig(**raw_data)
    generator = PulsarMarkdownGenerator(config)
    return generator.generate()