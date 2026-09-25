import socket
import struct
import sys

# --- 1. FUNÇÕES DE PARSING E CONSTRUÇÃO BINÁRIA (DNS) ---

def build_dns_query(domain: str, qtype: int = 1) -> bytes:
    """
    Constrói uma mensagem de consulta DNS binária (RFC 1035).
    Formato do Cabeçalho (12 bytes):
    - ID (16 bits)
    - Flags (16 bits): 0x0100 (Standard query)
    - QDCOUNT (16 bits): 1
    - ANCOUNT, NSCOUNT, ARCOUNT (16 bits cada): 0
    """
    header = struct.pack("!HHHHHH", 0x1334, 0x0100, 1, 0, 0, 0)
    
    # Formata o domínio em labels (ex: "example.com" -> \x07example\x03com\x00)
    qname = b""
    for part in domain.split("."):
        qname += struct.pack("B", len(part)) + part.encode("ascii")
    qname += b"\x00"
    
    # QTYPE (1 = A, 15 = MX) e QCLASS (1 = IN)
    question = qname + struct.pack("!HH", qtype, 1)
    return header + question

def parse_dns_response(data: bytes):
    """
    Faz o parsing binário de uma resposta DNS, extraindo o cabeçalho,
    a pergunta, e as seções de resposta (Answer) e autoridade (Authority).
    Demonstra a complexidade da análise de pacotes de rede em baixo nível.
    """
    if len(data) < 12:
        raise ValueError("Pacote DNS muito curto para conter o cabeçalho.")
        
    header = struct.unpack("!HHHHHH", data[:12])
    tx_id, flags, qdcount, ancount, nscount, arcount = header
    
    # Validação de flags básicas
    is_response = (flags & 0x8000) != 0
    rcode = flags & 0x000F
    
    print(f"[Parser] ID: {tx_id:#06x} | É resposta: {is_response} | RCODE: {rcode} | ANCOUNT: {ancount} | NSCOUNT: {nscount}")
    
    # Parse simples da seção de perguntas para avançar o ponteiro
    offset = 12
    questions = []
    for _ in range(qdcount):
        qname_parts = []
        while offset < len(data):
            length = data[offset]
            offset += 1
            if length == 0:
                break
            # Tratamento de ponteiros de compressão (simplificado para o teste)
            if (length & 0xC0) == 0xC0:
                offset += 1 # Pula o segundo byte do ponteiro
                break
            qname_parts.append(data[offset:offset+length].decode("ascii", errors="ignore"))
            offset += length
        # Lê QTYPE e QCLASS
        if offset + 4 <= len(data):
            qtype, qclass = struct.unpack("!HH", data[offset:offset+4])
            offset += 4
            questions.append((".".join(qname_parts), qtype))
            
    answers = []
    # Parse das respostas (Answer Section)
    for _ in range(ancount):
        if offset >= len(data):
            break
        # Pula o nome (assumindo compressão 0xC00C ou similar nos testes)
        if offset + 2 <= len(data) and (data[offset] & 0xC0) == 0xC0:
            offset += 2
        else:
            while offset < len(data) and data[offset] != 0:
                offset += 1
            offset += 1 # null byte
            
        if offset + 10 <= len(data):
            rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset+10])
            offset += 10
            rdata = data[offset:offset+rdlength]
            offset += rdlength
            
            if rtype == 1: # A Record (IPv4)
                ip = ".".join(map(str, rdata))
                answers.append({"type": "A", "data": ip})
            elif rtype == 15: # MX Record
                if len(rdata) >= 3:
                    preference = struct.unpack("!H", rdata[:2])[0]
                    mx_host = rdata[2:].decode("ascii", errors="ignore") # simplificado
                    answers.append({"type": "MX", "preference": preference, "data": mx_host})
                    
    return {"answers": answers, "flags": flags, "rcode": rcode}


# --- 2. SIMULADOR DE RESOLUÇÃO ITERATIVA ---

class MockDNSRootServer:
    """Simula o comportamento de um Root Server na hierarquia DNS."""
    def handle_query(self, query_bytes: bytes) -> bytes:
        # Raiz direciona para o servidor TLD .com
        # Retorna uma resposta com autoridade/referência (NS)
        header = struct.pack("!HHHHHH", 0x1334, 0x8180, 1, 0, 1, 0) # QR=1, AA=0
        # Copia a pergunta original (simplificado: assumimos que recebemos a query)
        return header + query_bytes[12:] + b"\xc0\x0c\x00\x02\x00\x01\x00\x00\x0e\x10\x00\x04\x03tld\x03com\x00"

class MockAuthoritativeServer:
    """Simula o servidor autoritativo final que possui o registro A ou MX."""
    def __init__(self, record_type, record_value):
        self.record_type = record_type
        self.record_value = record_value

    def handle_query(self, query_bytes: bytes) -> bytes:
        header = struct.pack("!HHHHHH", 0x1334, 0x8180, 1, 1, 0, 0) # QR=1, AA=1 (Authoritative)
        question = query_bytes[12:]
        
        # Constrói o RDATA com base no tipo solicitado
        if self.record_type == 1: # A Record
            rdata = socket.inet_aton(self.record_value)
        elif self.record_type == 15: # MX Record
            rdata = struct.pack("!H", 10) + b"\x07mailserver"
        else:
            rdata = b""
            
        r_type_val = self.record_type
        rdata_len = len(rdata)
        
        # Answer record
        answer = b"\xc0\x0c" + struct.pack("!HHIH", r_type_val, 1, 300, rdata_len) + rdata
        return header + question + answer


def iterative_resolve(domain: str, qtype: int) -> dict:
    """
    Executa a resolução iterativa simulada:
    1. Consulta o Root Server.
    2. Identifica o redirecionamento.
    3. Consulta o Servidor Autoritativo final.
    """
    print(f"\n[Iterative Resolver] Iniciando resolução para '{domain}' (QTYPE={qtype})...")
    
    # Passo 1: Consulta o Root Server
    root_server = MockDNSRootServer()
    query = build_dns_query(domain, qtype)
    
    print("[Iterative Resolver] -> Consultando Root Server (.)")
    root_response = root_server.handle_query(query)
    
    # Passo 2: Simula transição para Autoritativo (Na prática iterativa real, 
    # seguiria o glue record do TLD até o servidor do domínio).
    print("[Iterative Resolver] <- Recebido referral do Root. Consultando Servidor Autoritativo...")
    
    if qtype == 1:
        auth_server = MockAuthoritativeServer(record_type=1, record_value="93.184.216.34")
    else:
        auth_server = MockAuthoritativeServer(record_type=15, record_value="mail.example.com")
        
    auth_response = auth_server.handle_query(query)
    parsed = parse_dns_response(auth_response)
    
    return parsed


# --- 3. TESTES AUTOMATIZADOS DO EXPERIMENTO ---

def test_iterative_dns_resolution():
    print("=== INICIANDO TESTES DO SERVIDOR DNS ITERATIVO ===")
    
    # Teste 1: Consulta tipo A (Endereço IP)
    result_a = iterative_resolve("example.com", qtype=1)
    print(f"Resultado A obtido: {result_a}")
    assert result_a["rcode"] == 0, "RCODE deve ser 0 (No Error)"
    assert len(result_a["answers"]) > 0, "Deve retornar ao menos um registro A"
    assert result_a["answers"][0]["type"] == "A"
    assert result_a["answers"][0]["data"] == "93.184.216.34"
    
    # Teste 2: Consulta tipo MX (Mail Exchanger)
    result_mx = iterative_resolve("example.com", qtype=15)
    print(f"Resultado MX obtido: {result_mx}")
    assert result_mx["rcode"] == 0, "RCODE deve ser 0 (No Error)"
    assert len(result_mx["answers"]) > 0, "Deve retornar ao menos um registro MX"
    assert result_mx["answers"][0]["type"] == "MX"

    print("\n[Sucesso] Todos os testes de parsing binário e resolução iterativa passaram com êxito!")

if __name__ == "__main__":
    test_iterative_dns_resolution()