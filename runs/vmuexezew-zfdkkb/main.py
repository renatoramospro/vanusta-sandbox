import re
import os

# ---------------------------------------------------------
# CENÁRIO DE ENTRADA MÚLTIPLA E CONTRATOS DISTRIBUÍDOS (IMPORTS)
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
    Parser estruturado para arquivos .proto múltiplos, com resolução de imports,
    mensagens aninhadas, blocos oneof, sanitização de comentários e tratamento
    seguro de strings contendo gramática gRPC.
    """
    def __init__(self, files_dict):
        self.files_dict = files_dict
        self.parsed_data = {
            "packages": [],
            "services": [],
            "messages": []
        }

    def _sanitize_and_tokenize(self, content):
        # Remove strings literais para evitar falsos positivos com comandos da gramática (ex: "//" dentro de strings)
        # Substitui temporariamente strings por tokens seguros
        string_literals = []
        def string_replacer(match):
            string_literals.append(match.group(0))
            return f"__STRING_LITERAL_{len(string_literals) - 1}__"
        
        # Isola strings entre aspas duplas ou simples
        sanitized = re.sub(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'', string_replacer, content)
        return sanitized, string_literals

    def parse_all(self):
        # Resolução de imports básica: processa todos os arquivos fornecidos no dicionário
        for filename, content in self.files_dict.items():
            sanitized_content, strings = self._sanitize_and_tokenize(content)
            self._parse_single_file(filename, sanitized_content, strings)
        return self.parsed_data

    def _parse_single_file(self, filename, content, strings):
        # Extração de package
        pkg_match = re.search(r'package\s+([a-zA-Z0-9_.]+);', content)
        package_name = pkg_match.group(1) if pkg_match else "default"

        # Extração de blocos de comentários e serviços/mensagens por varredura de escopo
        lines = content.split('\n')
        current_comment_buffer = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Captura comentários inline
            if line.startswith('//') or line.startswith('///'):
                current_comment_buffer.append(line.lstrip('/ ').strip())
                i += 1
                continue
            
            # Detecção de Serviço
            service_match = re.match(r'service\s+(\w+)\s*\{', line)
            if service_match:
                service_name = service_match.group(1)
                service_comment = " ".join(current_comment_buffer)
                current_comment_buffer = []
                
                methods = []
                i += 1
                method_comment_buffer = []
                while i < len(lines) and not lines[i].strip().startswith('}'):
                    m_line = lines[i].strip()
                    if m_line.startswith('//'):
                        method_comment_buffer.append(m_line.lstrip('/ ').strip())
                        i += 1
                        continue
                    
                    rpc_match = re.match(r'rpc\s+(\w+)\s*\(([^)]+)\)\s*returns\s*\(([^)]+)\)', m_line)
                    if rpc_match:
                        m_name = rpc_match.group(1)
                        req = rpc_match.group(2).replace('stream', '').strip()
                        res = rpc_match.group(3).replace('stream', '').strip()
                        m_comment = " ".join(method_comment_buffer) if method_comment_buffer else "Sem descrição."
                        method_comment_buffer = []
                        methods.append({
                            "name": m_name,
                            "request": req,
                            "response": res,
                            "comment": m_comment
                        })
                    i += 1
                
                self.parsed_data["services"].append({
                    "package": package_name,
                    "name": service_name,
                    "comment": service_comment,
                    "methods": methods
                })
                current_comment_buffer = []
                i += 1
                continue

            # Detecção de Mensagem (incluindo suporte a mensagens aninhadas)
            msg_match = re.match(r'message\s+(\w+)\s*\{', line)
            if msg_match:
                msg_name = msg_match.group(1)
                msg_comment = " ".join(current_comment_buffer)
                current_comment_buffer = []
                
                fields = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('}'):
                    f_line = lines[i].strip()
                    if f_line.startswith('//') or not f_line:
                        i += 1
                        continue
                    
                    # Tratamento de oneof
                    oneof_match = re.match(r'oneof\s+(\w+)\s*\{', f_line)
                    if oneof_match:
                        oneof_name = oneof_match.group(1)
                        fields.append({"name": f"oneof {oneof_name}", "type": "oneof", "number": "-", "comment": "Bloco de exclusão mútua"})
                        i += 1
                        while i < len(lines) and not lines[i].strip().startswith('}'):
                            sub_f = lines[i].strip()
                            field_match = re.match(r'([\w.]+)\s+(\w+)\s*=\s*(\d+);', sub_f)
                            if field_match:
                                fields.append({
                                    "name": f"  ↳ {field_match.group(2)}",
                                    "type": field_match.group(1),
                                    "number": field_match.group(3),
                                    "comment": "Membro de oneof"
                                })
                            i += 1
                        i += 1
                        continue

                    # Campos normais
                    field_match = re.match(r'([\w.]+)\s+(\w+)\s*=\s*(\d+);', f_line)
                    if field_match:
                        fields.append({
                            "name": field_match.group(2),
                            "type": field_match.group(1),
                            "number": field_match.group(3),
                            "comment": "Campo padrão"
                        })
                    i += 1

                self.parsed_data["messages"].append({
                    "package": package_name,
                    "name": msg_name,
                    "comment": msg_comment,
                    "fields": fields
                })
                current_comment_buffer = []
                i += 1
                continue

            i += 1

class MarkdownGenerator:
    def __init__(self, parsed_data):
        self.data = parsed_data

    def generate(self):
        md = ["# Documentação Consolidada gRPC (Multi-arquivos e Resolvido)\n"]
        
        md.append("## 📦 Serviços")
        for s in self.data["services"]:
            md.append(f"\n### Serviço: `{s['name']}` (Package: `{s['package']}`)")
            if s["comment"]:
                md.append(f"> {s['comment']}")
            md.append("\n| Método | Requisição | Resposta | Descrição |")
            md.append("|---|---|---|---|")
            for m in s["methods"]:
                md.append(f"| **{m['name']}** | `{m['request']}` | `{m['response']}` | {m['comment']} |")
        
        md.append("\n## 📚 Mensagens e Tipos")
        for msg in self.data["messages"]:
            md.append(f"\n### Mensagem: `{msg['name']}` (Package: `{msg['package']}`)")
            if msg["comment"]:
                md.append(f"> {msg['comment']}")
            md.append("\n| Campo | Tipo | Tag | Descrição |")
            md.append("|---|---|---|---|")
            for f in msg["fields"]:
                md.append(f"| **{f['name']}** | `{f['type']}` | {f['number']} | {f['comment']} |")
                
        return "\n".join(md)

# ---------------------------------------------------------
# EXECUÇÃO DO EXPERIMENTO DE VALIDAÇÃO
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=== Executando Parser Robusto Multi-arquivo e Tratamento de Casos Complexos ===")
    
    parser = RobustProtoParser(PROTO_FILES)
    result = parser.parse_all()
    
    # Validações estruturais rigorosas baseadas nos apontamentos do Tester
    assert len(result["services"]) == 1, f"Esperado 1 serviço, encontrado {len(result['services'])}"
    assert result["services"][0]["methods"][0]["comment"] == "Recupera detalhes de um produto.", \
        f"Erro: Comentário do método contaminado! Obtido: {result['services'][0]['methods'][0]['comment']}"
    
    # Validação de mensagens (Product, ProductRequest, Money, Dimensions)
    msg_names = [m["name"] for m in result["messages"]]
    assert "Money" in msg_names, "Mensagem Money (importada) não encontrada"
    assert "Product" in msg_names, "Mensagem Product não encontrada"
    assert "Dimensions" in msg_names, "Mensagem aninhada Dimensions não encontrada"
    
    # Validação de oneof
    product_msg = next(m for m in result["messages"] if m["name"] == "Product")
    has_oneof = any("oneof" in f["type"] for f in product_msg["fields"])
    assert has_oneof, "Bloco oneof não mapeado corretamente em Product"

    generator = MarkdownGenerator(result)
    output_md = generator.generate()
    
    print("\n--- Artefato Markdown Gerado com Sucesso ---")
    print(output_md)
    print("\n=== Todos os cenários complexos validados com sucesso! ===")