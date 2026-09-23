import json
import sys

def validar_esquema_json(schema_path):
    """Simula a validação do contrato de mensagem base."""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        assert "properties" in schema, "O Schema deve conter propriedades definidas."
        print(f"[SUCESSO] Schema '{schema.get('title', 'Desconhecido')}' validado com sucesso.")
        return schema
    except Exception as e:
        print(f"[ERRO] Falha ao validar o schema: {e}", file=sys.stderr)
        sys.exit(1)

def validar_asyncapi(asyncapi_path):
    """
    Simula a verificação estricta do documento AsyncAPI.
    Garante que canais, operações e componentes de schema estejam mapeados,
    atacando o equívoco de que Markdown manual substitui o contrato vivo.
    """
    try:
        with open(asyncapi_path, 'r', encoding='utf-8') as f:
            # Simulando leitura do arquivo AsyncAPI (poderia ser YAML, usando JSON aqui para simplicidade da stdlib)
            doc = json.load(f)
            
        assert "asyncapi" in doc, "Documento inválido: falta a chave 'asyncapi'."
        assert "channels" in doc, "Documento inválido: ausência de canais (tópicos/filas) mapeados."
        assert "operations" in doc, "Documento inválido: ausência de operações definidas."
        
        print(f"[SUCESSO] Documento AsyncAPI versão {doc['asyncapi']} verificado.")
        print(f" -> Canais mapeados: {list(doc['channels'].keys())}")
        print(f" -> Operações mapeadas: {len(doc['operations'])}")
        return True
    except Exception as e:
        print(f"[ERRO] Validação do AsyncAPI falhou: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 1. Criar um contrato de exemplo (JSON Schema)
    schema_data = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "OrderCreated",
        "type": "object",
        "properties": {
            "orderId": {"type": "string", "format": "uuid"},
            "totalAmount": {"type": "number"},
            "createdAt": {"type": "string", "format": "date-time"}
        },
        "required": ["orderId", "totalAmount"]
    }
    with open("order_created_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema_data, f, indent=2)

    # 2. Criar o documento AsyncAPI correspondente
    asyncapi_data = {
        "asyncapi": "2.6.0",
        "info": {
            "title": "Order Service Event Portal",
            "version": "1.0.0",
            "description": "Documentação viva de eventos de pedidos assíncronos."
        },
        "channels": {
            "orders/created": {
                "description": "Canal onde eventos de novos pedidos são publicados.",
                "publish": {
                    "operationId": "publishOrderCreated",
                    "message": {
                        "$ref": "#/components/messages/OrderCreatedMessage"
                    }
                }
            }
        },
        "operations": {
            "publishOrderCreated": {
                "action": "send",
                "channel": "orders/created",
                "summary": "Envia um evento quando o pedido é criado."
            }
        },
        "components": {
            "messages": {
                "OrderCreatedMessage": {
                    "name": "OrderCreated",
                    "title": "Order Created Event",
                    "payload": {
                        "$ref": "order_created_schema.json"
                    }
                }
            }
        }
    }
    with open("asyncapi.json", "w", encoding="utf-8") as f:
        json.dump(asyncapi_data, f, indent=2)

    print("--- INICIANDO PIPELINE DE DOCUMENTAÇÃO ASSINCRONA ---")
    validar_esquema_json("order_created_schema.json")
    validar_asyncapi("asyncapi.json")
    print("--- PIPELINE EXECUTADO COM 100% DE SUCESSO ---")