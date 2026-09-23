import json
import os
import sys
from typing import get_type_hints, Optional, Dict, Any

# ==========================================
# 1. MODELOS DE CÓDIGO (Abordagem Code-First)
# ==========================================
class OrderCreatedEventV1:
    """Contrato da versão 1 do evento de criação de pedido."""
    order_id: str
    amount: float
    customer_email: str

class OrderCreatedEventV2:
    """Contrato da versão 2 do evento (com alteração retrocompatível e quebra)."""
    order_id: str
    amount: float
    customer_email: str
    # Adicionado campo opcional: retrocompatível
    shipping_address: Optional[str] = None 

class OrderCreatedEventBroken:
    """Contrato que quebra o contrato (Breaking Change)."""
    # order_id foi removido! Ou o tipo alterado.
    amount: str # Mudou de float para str!
    customer_email: str


def extract_schema_from_class(cls) -> Dict[str, Any]:
    """Extrai campos e tipos de uma classe Python para um JSON Schema simplificado."""
    hints = get_type_hints(cls)
    properties = {}
    required = []
    
    for field_name, field_type in hints.items():
        # Verifica se é Optional (simplificado para demonstração)
        is_optional = "NoneType" in str(field_type) or "Optional" in str(field_type)
        
        # Mapeia tipo Python para tipo JSON Schema
        type_str = "string"
        if "float" in str(field_type):
            type_str = "number"
        elif "int" in str(field_type):
            type_str = "integer"
            
        properties[field_name] = {"type": type_str}
        if not is_optional:
            required.append(field_name)
            
    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


# ==========================================
# 2. GERADOR DE ASYNCAPI
# ==========================================
def generate_asyncapi_spec(event_name: str, cls) -> Dict[str, Any]:
    """Gera um dicionário representando o documento AsyncAPI."""
    schema = extract_schema_from_class(cls)
    
    asyncapi_doc = {
        "asyncapi": "2.6.0",
        "info": {
            "title": "Order Service Event Portal",
            "version": "1.0.0",
            "description": "Documentação gerada automaticamente a partir do código-fonte."
        },
        "channels": {
            f"order/{event_name}": {
                "publish": {
                    "message": {
                        "name": event_name,
                        "payload": schema
                    }
                }
            }
        }
    }
    return asyncapi_doc


# ==========================================
# 3. VALIDADOR DE BREAKING CHANGES (CI)
# ==========================================
def detect_breaking_changes(old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> list:
    """
    Compara dois schemas e retorna uma lista de breaking changes.
    Equívoco comum combatido aqui: testar apenas se o arquivo é válido sintaticamente,
    sem verificar compatibilidade com consumidores anteriores.
    """
    breaking_changes = []
    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})
    old_required = old_schema.get("required", [])
    
    # 1. Verificar campos removidos
    for field in old_props:
        if field not in new_props:
            breaking_changes.append(f"Campo obrigatório/existente removido: '{field}'")
            
    # 2. Verificar mudança de tipo em campos existentes
    for field, old_def in old_props.items():
        if field in new_props:
            new_def = new_props[field]
            if old_def.get("type") != new_def.get("type"):
                breaking_changes.append(
                    f"Mudança de tipo no campo '{field}': de '{old_def.get('type')}' para '{new_def.get('type')}'"
                )
                
    return breaking_changes


# ==========================================
# 4. EXECUÇÃO DOS TESTES E DEMONSTRAÇÃO
# ==========================================
if __name__ == "__main__":
    print("--- 1. Geração de AsyncAPI a partir de Código ---")
    spec_v1 = generate_asyncapi_spec("order-created", OrderCreatedEventV1)
    print(json.dumps(spec_v1, indent=2))
    
    # Simula salvamento em arquivo Markdown/HTML simplificado
    markdown_output = f"""# Documentação de Eventos
## Canal: `order/order-created`
\`\`\`json
{json.dumps(spec_v1['channels']['order/order-created']['publish']['message']['payload'], indent=2)}
\`\`\`
"""
    with open("contract_doc.md", "w") as f:
        f.write(markdown_output)
    print("\n[OK] Documentação Markdown gerada com sucesso em 'contract_doc.md'.")

    print("\n--- 2. Validação de CI: Teste de Retrocompatibilidade ---")
    schema_v1 = extract_schema_from_class(OrderCreatedEventV1)
    schema_v2 = extract_schema_from_class(OrderCreatedEventV2)
    schema_broken = extract_schema_from_class(OrderCreatedEventBroken)

    # Teste A: Evolução Segura (Adicionar campo opcional)
    changes_v2 = detect_breaking_changes(schema_v1, schema_v2)
    print(f"Evolução V1 -> V2 (Adição de campo opcional). Breaking changes encontradas: {len(changes_v2)}")
    assert len(changes_v2) == 0, "Deveria ser uma mudança retrocompatível!"

    # Teste B: Evolução Quebrada (Breaking Change)
    changes_broken = detect_breaking_changes(schema_v1, schema_broken)
    print(f"Evolução V1 -> Broken. Breaking changes encontradas: {changes_broken}")
    assert len(changes_broken) > 0, "O CI deveria ter detectado a breaking change!"

    print("\n[SUCESSO] Todas as validações e testes de contrato passaram conforme esperado.")