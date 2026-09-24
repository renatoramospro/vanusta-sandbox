import ast
import json
import sys

# ---------------------------------------------------------
# 1. Código Servidor WebSocket de Exemplo (Alvo da Inspeção)
# ---------------------------------------------------------
SAMPLE_SERVER_CODE = """
class WebSocketServer:
    def __init__(self):
        self.listeners = {}

    def on(self, event_name):
        def decorator(func):
            self.listeners[event_name] = func
            return func
        return decorator

app = WebSocketServer()

@app.on("user.login")
def handle_login(data):
    \"\"\"Autentica um usuário no sistema via WebSocket.\"\"\"
    pass

@app.on("chat.message")
def handle_chat_message(data):
    \"\"\"Processa e retransmite mensagens de chat.\"\"\"
    pass
"""

# ---------------------------------------------------------
# 2. Mecanismo de Inspeção por AST (Análise Estática)
# ---------------------------------------------------------
class WebSocketInspector(ast.NodeVisitor):
    def __init__(self):
        self.channels = {}

    def visit_FunctionDef(self, node):
        # Procura por decoradores do tipo @app.on("evento")
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Call) and 
                isinstance(decorator.func, ast.Attribute) and 
                decorator.func.attr == 'on'):
                
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    event_name = decorator.args[0].value
                    docstring = ast.get_docstring(node) or "Sem descrição fornecida."
                    
                    self.channels[event_name] = {
                        "action": event_name,
                        "description": docstring.strip(),
                        "function": node.name
                    }
        self.generic_visit(node)

# ---------------------------------------------------------
# 3. Gerador de Contrato AsyncAPI
# ---------------------------------------------------------
def generate_asyncapi_spec(channels_metadata):
    spec = {
        "asyncapi": "2.6.0",
        "info": {
            "title": "API de WebSockets em Tempo Real - Vanusta",
            "version": "1.0.0",
            "description": "Documentação gerada automaticamente via inspeção AST de protocolos."
        },
        "channels": {}
    }

    for event, meta in channels_metadata.items():
        channel_path = f"/{event.replace('.', '/')}"
        spec["channels"][channel_path] = {
            "description": meta["description"],
            "publish": {
                "message": {
                    "summary": f"Mensagem recebida para o evento {event}",
                    "payload": {
                        "type": "object",
                        "x-handled-by": meta["function"]
                    }
                }
            }
        }
    return spec

# ---------------------------------------------------------
# 4. Execução do Experimento e Validação de Cobertura
# ---------------------------------------------------------
def main():
    print("Iniciando inspeção estática do código fonte...")
    tree = ast.parse(SAMPLE_SERVER_CODE)
    
    inspector = WebSocketInspector()
    inspector.visit(tree)
    
    discovered_channels = inspector.channels
    print(print(f"Canais/Eventos descobertos: {list(discovered_channels.keys())}"))

    # Validação do critério de sucesso (100% dos eventos mapeados esperados)
    expected_events = {"user.login", "chat.message"}
    discovered_events = set(discovered_channels.keys())
    
    assert expected_events.issubset(discovered_events), "Erro: Nem todos os eventos foram mapeados!"
    
    # Geração do Contrato AsyncAPI
    asyncapi_doc = generate_asyncapi_spec(discovered_channels)
    
    # Validação de que o documento gerado é um JSON válido e contém os canais corretos
    doc_json = json.dumps(asyncapi_doc, indent=2)
    print("\n--- Documentação AsyncAPI Gerada ---")
    print(doc_json)
    
    assert "asyncapi" in asyncapi_doc, "Contrato inválido: falta tag raiz asyncapi"
    assert "/user/login" in asyncapi_doc["channels"], "Canal user.login ausente na especificação"
    assert "/chat/message" in asyncapi_doc["channels"], "Canal chat.message ausente na especificação"
    
    print("\n[SUCESSO] Inspeção de WebSockets e geração de contrato AsyncAPI concluídas com 100% de cobertura dos eventos estáticos.")

if __name__ == "__main__":
    main()