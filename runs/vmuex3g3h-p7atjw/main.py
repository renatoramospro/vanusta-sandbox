import re
import os

# Conteúdo de um arquivo .proto complexo de exemplo para o teste
PROTO_CONTENT = """
syntax = "proto3";

package payment.v1;

option go_package = "github.com/example/payment/v1;paymentv1";

// Serviço responsável pelo processamento de pagamentos e transações financeiras.
service PaymentService {
  // Processa um pagamento único de forma síncrona (Unary).
  rpc ProcessPayment (PaymentRequest) returns (PaymentResponse);

  // Realiza o streaming contínuo de atualizações de transações (Server Streaming).
  rpc StreamTransactions (TransactionStreamRequest) returns (stream TransactionEvent);
}

// Representa a requisição de pagamento.
message PaymentRequest {
  // Identificador único da transação gerado pelo cliente.
  string transaction_id = 1;
  // Valor monetário a ser debitado.
  double amount = 2;
  // Moeda utilizada (ex: USD, BRL).
  string currency = 3;
  
  // Opções de metadados adicionais.
  map<string, string> metadata = 4;
  
  // Itens comprados na transação.
  repeated LineItem items = 5;

  oneof payment_method {
    CreditCard credit_card = 6;
    PixPayment pix = 7;
  }
}

// Item individual dentro de uma transação.
message LineItem {
  string sku = 1;
  int32 quantity = 2;
  double price = 3;
}

message CreditCard {
  string card_number = 4;
  string expiry_date = 5;
}

message PixPayment {
  string pix_key = 1;
}

message PaymentResponse {
  bool success = 1;
  string message = 2;
}

message TransactionStreamRequest {
  string account_id = 1;
}

message TransactionEvent {
  string event_id = 1;
  string status = 2;
}
"""

class ProtoParser:
    """
    Parser robusto para extração de metadados de arquivos .proto,
    capturando pacotes, serviços, métodos, mensagens, campos e comentários inline.
    """
    def __init__(self, proto_text: str):
        self.proto_text = proto_text

    def parse(self) -> dict:
        lines = self.proto_text.splitlines()
        package = ""
        services = []
        messages = []

        current_comment = []
        
        # Estados de parsing simples para demonstração controlada de AST
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Captura comentários
            if line.startswith("//"):
                current_comment.append(line.lstrip("/ ").strip())
                i += 1
                continue
            
            # Captura package
            if line.startswith("package "):
                match = re.match(r"package\s+([^;]+);", line)
                if match:
                    package = match.group(1)
                current_comment = []
                i += 1
                continue

            # Captura Service
            if line.startswith("service "):
                service_name = line.split()[1]
                service_comment = " ".join(current_comment)
                methods = []
                i += 1
                # Percorre o corpo do serviço
                while i < len(lines):
                    s_line = lines[i].strip()
                    if s_line.startswith("//"):
                        current_comment.append(s_line.lstrip("/ ").strip())
                        i += 1
                        continue
                    if s_line.startswith("}"):
                        i += 1
                        break
                    if "rpc" in s_line:
                        # Ex: rpc ProcessPayment (PaymentRequest) returns (PaymentResponse);
                        m_match = re.search(r"rpc\s+(\w+)\s*\((.*?)\)\s*returns\s*\((.*?)\)", s_line)
                        if m_match:
                            m_name, m_req, m_res = m_match.groups()
                            methods.append({
                                "name": m_name,
                                "request": m_req.strip(),
                                "response": m_res.strip(),
                                "comment": " ".join(current_comment)
                            })
                        current_comment = []
                    i += 1
                services.append({"name": service_name, "comment": service_comment, "methods": methods})
                current_comment = []
                continue

            # Captura Message
            if line.startswith("message "):
                msg_name = line.split()[1]
                msg_comment = " ".join(current_comment)
                fields = []
                i += 1
                while i < len(lines):
                    m_line = lines[i].strip()
                    if m_line.startswith("//"):
                        current_comment.append(m_line.lstrip("/ ").strip())
                        i += 1
                        continue
                    if m_line.startswith("}"):
                        i += 1
                        break
                    if m_line.startswith("oneof "):
                        # Tratamento simplificado para blocos oneof
                        oneof_name = m_line.split()[1]
                        fields.append({
                            "type": "oneof",
                            "name": oneof_name,
                            "number": "",
                            "comment": " ".join(current_comment)
                        })
                        current_comment = []
                        i += 1
                        continue
                    if "=" in m_line and not m_line.startswith("option"):
                        # Ex: string transaction_id = 1; ou map<string, string> metadata = 4;
                        f_match = re.match(r"([\w<>,\s]+)\s+(\w+)\s*=\s*(\d+);", m_line)
                        if f_match:
                            f_type, f_name, f_num = f_match.groups()
                            fields.append({
                                "type": f_type.strip(),
                                "name": f_name.strip(),
                                "number": f_num.strip(),
                                "comment": " ".join(current_comment)
                            })
                        current_comment = []
                    i += 1
                messages.append({"name": msg_name, "comment": msg_comment, "fields": fields})
                current_comment = []
                continue

            i += 1

        return {
            "package": package,
            "services": services,
            "messages": messages
        }

class MarkdownDocumentationGenerator:
    """
    Gera documentação Markdown a partir do dicionário estruturado extraído do proto.
    """
    def __init__(self, metadata: dict):
        self.data = metadata

    def generate(self) -> str:
        md = []
        md.append(f"# Documentação da API gRPC: `{self.data['package']}`\n")
        md.append("Gerado automaticamente a partir de definições Protocol Buffers (`.proto`).\n")
        
        md.append("## 📦 Serviços\n")
        if not self.data["services"]:
            md.append("_Nenhum serviço encontrado._\n")
        for svc in self.data["services"]:
            md.append(f"### Serviço: `{svc['name']}`")
            if svc["comment"]:
                md.append(f"\n> {svc['comment']}\n")
            md.append("| Método | Requisição | Resposta | Descrição |")
            md.append("|---|---|---|---|")
            for m in svc["methods"]:
                req = f"`{m['request']}`"
                res = f"`{m['response']}`"
                md.append(f"| **{m['name']}** | {req} | {res} | {m['comment']} |")
            md.append("")

        md.append("## 📝 Mensagens e Tipos\n")
        for msg in self.data["messages"]:
            md.append(f"### `message {msg['name']}`")
            if msg["comment"]:
                md.append(f"\n> {msg['comment']}\n")
            md.append("| Campo | Tipo | Número | Descrição |")
            md.append("|---|---|---|---|")
            for f in msg["fields"]:
                if f["type"] == "oneof":
                    md.append(f"| *oneof* **{f['name']}** | `bloco condicional` | - | {f['comment']} |")
                else:
                    md.append(f"| **{f['name']}** | `{f['type']}` | {f['number']} | {f['comment']} |")
            md.append("")

        return "\n".join(md)

# Execução do experimento e validação
if __name__ == "__main__":
    print("=== Executando Parser e Gerador de Documentação gRPC ===")
    
    parser = ProtoParser(PROTO_CONTENT)
    parsed_data = parser.parse()
    
    # Validações estruturais para garantir fidelidade
    assert parsed_data["package"] == "payment.v1", f"Esperado package payment.v1, obtido {parsed_data['package']}"
    assert len(parsed_data["services"]) == 1, "Deveria ter encontrado 1 serviço"
    assert len(parsed_data["messages"]) == 7, f"Deveria ter encontrado 7 mensagens, encontrou {len(parsed_data['messages'])}"
    
    generator = MarkdownDocumentationGenerator(parsed_data)
    markdown_output = generator.generate()
    
    print("\n--- Artefato Markdown Gerado com Sucesso ---")
    print(markdown_output[:500] + "\n[... truncado para exibição ...]\n")
    
    # Demonstração do contraexemplo (por que regex simples falha sem contexto estrutural)
    print("=== Demonstração do Equívoco Comum (Regex Ingênuo vs Parser Estrutural) ===")
    naive_regex = re.findall(r"message\s+(\w+)", PROTO_CONTENT)
    print(f"Regex ingênuo encontrou apenas os nomes das mensagens: {naive_regex}")
    print("Conclusão: O regex ingênuo perde completamente os tipos dos campos, números de tags, aninhamentos e comentários associados.")
    print("Teste concluído com sucesso absoluto!")