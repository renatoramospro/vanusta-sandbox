import re
import os

# ---------------------------------------------------------
# CONTRATOS DE TESTE MULTI-ARQUIVO COM MENSAGENS ANINHADAS E ONEOF
# ---------------------------------------------------------
PROTO_FILES = {
    "common.proto": """
syntax = "proto3";
package common.v1;

// Representa uma quantia monetária.
message Money {
  string currency = 1;
  double units = 2;
}
""",
    "catalog.proto": """
syntax = "proto3";
package catalog.v1;

import "common.proto";

// Serviço de gerenciamento de estoque e catálogo.
service InventoryService {
  // Recupera detalhes de um produto.
  rpc GetProduct(ProductRequest) returns (Product);
}

message ProductRequest {
  string id = 1;
}

// Produto disponível no catálogo.
message Product {
  string id = 1;
  string name = 2;
  common.v1.Money price = 3;
  
  // Demonstração de mensagem aninhada e oneof interno
  message Dimensions {
    double width = 1;
    double height = 2;
  }
  
  Dimensions dimensions = 4;

  oneof category_details {
    string digital_category = 5;
    string physical_category = 6;
  }
}
"""
}

class RobustProtoParser:
    """
    Parser estruturado baseado em escopo (rastreamento de chaves) para arquivos .proto,
    garantindo suporte a múltiplos arquivos, mensagens aninhadas e oneof.
    """
    def __init__(self, files_dict):
        self.files_dict = files_dict
        self.parsed_data = {
            "packages": [],
            "services": [],
            "messages": []
        }

    def _sanitize_and_tokenize(self, content):
        # Remove strings literais para evitar falsos positivos com comandos da gramática
        string_literals = []
        def string_replacer(match):
            string_literals.append(match.group(0))
            return f"__STRING_LITERAL_{len(string_literals) - 1}__"
        
        sanitized = re.sub(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'', string_replacer, content)
        return sanitized, string_literals

    def parse_all(self):
        for filename, content in self.files_dict.items():
            sanitized_content, strings = self._sanitize_and_tokenize(content)
            self._parse_single_file(filename, sanitized_content)
        return self.parsed_data

    def _parse_single_file(self, filename, content):
        pkg_match = re.search(r'package\s+([a-zA-Z0-9_.]+);', content)
        package_name = pkg_match.group(1) if pkg_match else "default"

        lines = content.split('\n')
        current_comment_buf = []
        
        # Pilha de escopos para rastrear blocos (service, message, etc.)
        scope_stack = []
        brace_count = 0
        
        current_service = None
        current_message = None

        for line in lines:
            stripped = line.strip()
            
            # Captura comentários inline ou de bloco simples
            if stripped.startswith("//"):
                comment_text = stripped.lstrip("/").strip()
                current_comment_buf.append(comment_text)
                continue

            # Processamento de linhas com chaves
            open_braces = stripped.count("{")
            close_braces = stripped.count("}")
            
            # Detecta início de serviço
            svc_match = re.search(r'service\s+([a-zA-Z0-9_]+)', stripped)
            if svc_match:
                current_service = {
                    "name": svc_match.group(1),
                    "package": package_name,
                    "comment": " ".join(current_comment_buf),
                    "methods": []
                }
                self.parsed_data["services"].append(current_service)
                current_comment_buf = []
                scope_stack.append("service")

            # Detecta início de mensagem (principal ou aninhada)
            msg_match = re.search(r'message\s+([a-zA-Z0-9_]+)', stripped)
            if msg_match:
                msg_name = msg_match.group(1)
                # Se estiver dentro de outra mensagem, podemos registrar com prefixo ou no escopo global
                current_message = {
                    "name": msg_name,
                    "package": package_name,
                    "comment": " ".join(current_comment_buf),
                    "fields": []
                }
                self.parsed_data["messages"].append(current_message)
                current_comment_buf = []
                scope_stack.append("message")

            # Detecta métodos RPC dentro de serviços
            rpc_match = re.search(r'rpc\s+([a-zA-Z0-9_]+)\s*\(([^)]+)\)\s*returns\s*\(([^)]+)\)', stripped)
            if rpc_match and current_service:
                method_name = rpc_match.group(1)
                req_type = rpc_match.group(2).strip()
                res_type = rpc_match.group(3).strip()
                
                current_service["methods"].append({
                    "name": method_name,
                    "request": req_type,
                    "response": res_type,
                    "comment": " ".join(current_comment_buf)
                })
                current_comment_buf = []

            # Detecta campos de mensagens ou oneof
            if current_message and not msg_match and not svc_match:
                field_match = re.search(r'([a-zA-Z0-9_.]+)\s+([a-zA-Z0-9_]+)\s*=\s*\d+;', stripped)
                oneof_match = re.search(r'oneof\s+([a-zA-Z0-9_]+)', stripped)
                
                if field_match:
                    current_message["fields"].append({
                        "type": field_match.group(1),
                        "name": field_match.group(2),
                        "comment": " ".join(current_comment_buf)
                    })
                    current_comment_buf = []
                elif oneof_match:
                    current_message["fields"].append({
                        "type": f"oneof {oneof_match.group(1)}",
                        "name": oneof_match.group(1),
                        "comment": " ".join(current_comment_buf)
                    })
                    current_comment_buf = []

            # Atualiza contagem de chaves e pilha de escopo
            brace_count += open_braces - close_braces
            for _ in range(open_braces):
                pass
            for _ in range(close_braces):
                if scope_stack:
                    exited = scope_stack.pop()
                    if exited == "message":
                        current_message = None
                    elif exited == "service":
                        current_service = None

            if brace_count <= 0:
                brace_count = 0
                scope_stack.clear()
                current_service = None
                current_message = None

class MarkdownGenerator:
    """Gera documentação técnica em Markdown a partir do dicionário estruturado."""
    def __init__(self, parsed_data):
        self.data = parsed_data

    def generate(self):
        lines = ["# Documentação de Contratos gRPC\n"]
        
        lines.append("## Serviços\n")
        for svc in self.data["services"]:
            lines.append(f"### Serviço: `{svc['name']}`")
            if svc["comment"]:
                lines.append(f"> {svc['comment']}\n")
            lines.append("| Método | Requisição | Resposta | Descrição |")
            lines.append("|---|---|---|---|")
            for m in svc["methods"]:
                lines.append(f"| `{m['name']}` | `{m['request']}` | `{m['response']}` | {m['comment']} |")
            lines.append("")

        lines.append("## Mensagens\n")
        for msg in self.data["messages"]:
            lines.append(f"### Mensagem: `{msg['name']}`")
            if msg["comment"]:
                lines.append(f"> {msg['comment']}\n")
            lines.append("| Campo | Tipo | Descrição |")
            lines.append("|---|---|---|")
            for f in msg["fields"]:
                lines.append(f"| `{f['name']}` | `{f['type']}` | {f.get('comment', '')} |")
            lines.append("")

        return "\n".join(lines)

if __name__ == "__main__":
    print("=== Executando Parser Robusto com Suporte a Mensagens Aninhadas ===")
    
    parser = RobustProtoParser(PROTO_FILES)
    result = parser.parse_all()
    
    # Validações estruturais rigorosas
    assert len(result["services"]) == 1, f"Esperado 1 serviço, encontrado {len(result['services'])}"
    assert result["services"][0]["methods"][0]["comment"] == "Recupera detalhes de um produto.", \
        f"Erro: Comentário do método contaminado! Obtido: {result['services'][0]['methods'][0]['comment']}"
    
    msg_names = [m["name"] for m in result["messages"]]
    assert "Money" in msg_names, "Mensagem Money (importada) não encontrada"
    assert "Product" in msg_names, "Mensagem Product não encontrada"
    assert "Dimensions" in msg_names, "Mensagem aninhada Dimensions não encontrada"
    
    product_msg = next(m for m in result["messages"] if m["name"] == "Product")
    has_oneof = any("oneof" in f["type"] for f in product_msg["fields"])
    assert has_oneof, "Bloco oneof não mapeado corretamente em Product"

    generator = MarkdownGenerator(result)
    output_md = generator.generate()
    
    print("\n--- Artefato Markdown Gerado com Sucesso ---")
    print(output_md)
    print("\n=== Todos os testes passaram com sucesso (Código 0) ===")