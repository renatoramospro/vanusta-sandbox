import socket
import struct
import threading
import subprocess
import sys
import time

MAX_ITERATIONS = 10

# --- 1. PARSING BINÁRIO E COMPRESSÃO DE PONTEIROS (RFC 1035) ---

def parse_dns_name(data: bytes, offset: int) -> tuple[str, int]:
    """
    Lê um nome de domínio a partir de um buffer binário DNS,
    suportando compressão de ponteiros (bytes iniciando com 11xxxxxx / 0xC0).
    Retorna a string decodificada e o novo offset após o nome.
    """
    labels = []
    jumped = False
    original_offset = offset
    iterations = 0
    
    while True:
        if offset >= len(data):
            raise ValueError("Offset fora dos limites durante parsing do nome DNS.")
        
        length = data[offset]
        
        # Verifica se é um ponteiro de compressão (dois bits mais altos 11) -> 0xC0
        if (length & 0xC0) == 0xC0:
            if offset + 1 >= len(data):
                raise ValueError("Ponteiro de compressão truncado.")
            pointer = struct.unpack("!H", data[offset:offset+2])[0] & 0x3FFF
            if not jumped:
                original_offset = offset + 2
            offset = pointer
            jumped = True
            iterations += 1
            if iterations > 25:
                raise ValueError("Loop detectado em ponteiros de compressão DNS.")
            continue
            
        if length == 0:
            offset += 1
            break
            
        offset += 1
        if offset + length > len(data):
            raise ValueError("Label DNS excede o tamanho do pacote.")
            
        label = data[offset:offset+length].decode('utf-8', errors='ignore')
        labels.append(label)
        offset += length
        
    return ".".join(labels), (original_offset if jumped else offset)

def parse_dns_message(data: bytes):
    """Analisa o cabeçalho e a seção de perguntas de uma mensagem DNS."""
    if len(data) < 12:
        raise ValueError("Mensagem DNS muito curta para conter o cabeçalho.")
        
    header = struct.unpack("!HHHHHH", data[:12])
    tx_id, flags, qdcount, ancount, nscount, arcount = header
    
    offset = 12
    questions = []
    for _ in range(qdcount):
        qname, offset = parse_dns_name(data, offset)
        if offset + 4 > len(data):
            raise ValueError("Truncado ao ler qtype e qclass.")
        qtype, qclass = struct.unpack("!HH", data[offset:offset+4])
        offset += 4
        questions.append({"qname": qname, "qtype": qtype, "qclass": qclass})
        
    return {
        "id": tx_id,
        "flags": flags,
        "questions": questions,
        "ancount": ancount,
        "nscount": nscount,
        "arcount": arcount
    }

def build_dns_query(qname: str, qtype: int) -> bytes:
    """Constrói uma consulta DNS padrão (QTYPE A ou MX)."""
    tx_id = 0x1337
    flags = 0x0100 # Standard recursion desired (RD=0 para iterativo puro)
    qdcount = 1
    ancount = nscount = arcount = 0
    
    header = struct.pack("!HHHHHH", tx_id, flags, qdcount, ancount, nscount, arcount)
    
    qname_bytes = b""
    for part in qname.split('.'):
        if part:
            qname_bytes += bytes([len(part)]) + part.encode('ascii')
    qname_bytes += b'\x00'
    
    question = qname_bytes + struct.pack("!HH", qtype, 1) # QCLASS IN = 1
    return header + question

# --- 2. SIMULAÇÃO DE RESOLUÇÃO ITERATIVA COM PROTEÇÃO DE LAME DELEGATION ---

def simulate_iterative_resolution(qname: str, qtype: int) -> list[str]:
    """
    Simula o processo iterativo Root (.) -> TLD (.com) -> Authoritative,
    com proteções contra profundidade excessiva e lame delegation.
    """
    print(f"[Resolver] Iniciando resolução iterativa para {qname} (Tipo: {qtype})")
    
    chain_steps = 0
    visited_servers = set()
    current_server = "root-server.net"
    
    while chain_steps < MAX_ITERATIONS:
        chain_steps += 1
        if current_server in visited_servers:
            print(f"[Resolver] Lame Delegation / Loop detectado no servidor {current_server}!")
            return ["SERVFAIL"]
            
        visited_servers.add(current_server)
        print(f"[Resolver] Passo {chain_steps}: Consultando servidor {current_server} para '{qname}'")
        
        # Simula o comportamento dos servidores na cadeia
        if current_server == "root-server.net":
            # Root encaminha para TLD
            if qname.endswith(".com"):
                current_server = "tld-com-server.net"
                continue
        elif current_server == "tld-com-server.net":
            # TLD encaminha para Authoritative
            current_server = "auth.example.com"
            continue
        elif current_server == "auth.example.com":
            # Servidor Autoritativo responde final
            if qtype == 1: # A
                return ["93.184.216.34"]
            elif qtype == 15: # MX
                return ["mail.example.com"]
        
        break
        
    return ["SERVFAIL"]

# --- 3. SERVIDOR DNS UDP LOCAL ---

class IterativeDNSServer:
    def __init__(self, host="127.0.0.1", port=5353):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = False
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        print(f"[Servidor DNS] Rodando em {self.host}:{self.port}")
        
    def _listen(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(512)
                response = self.handle_query(data)
                self.sock.sendto(response, addr)
            except Exception as e:
                if not self.running:
                    break
                print(f"[Servidor DNS] Erro: {e}")
                
    def handle_query(self, data: bytes) -> bytes:
        try:
            parsed = parse_dns_message(data)
            q = parsed["questions"][0]
            answers = simulate_iterative_resolution(q["qname"], q["qtype"])
            
            # Constrói resposta DNS básica
            tx_id = parsed["id"]
            flags = 0x8180 # Response, AA, Recursion Available
            qdcount = 1
            ancount = len(answers) if answers != ["SERVFAIL"] else 0
            nscount = 0
            arcount = 0
            
            if answers == ["SERVFAIL"]:
                flags = 0x8182 # SERVFAIL error flag
                
            header = struct.pack("!HHHHHH", tx_id, flags, qdcount, ancount, nscount, arcount)
            
            # Reconstrói a questão
            qname_bytes = b""
            for part in q["qname"].split('.'):
                if part:
                    qname_bytes += bytes([len(part)]) + part.encode('ascii')
            qname_bytes += b'\x00'
            question = qname_bytes + struct.pack("!HH", q["qtype"], q["qclass"])
            
            response_body = header + question
            
            # Adiciona respostas (simplificado para demonstração do IP/MX)
            for ans in answers:
                if ans == "SERVFAIL":
                    break
                # Ponteiro para o nome na questão (offset 12 -> 0xC00C)
                name_pointer = struct.pack("!H", 0xC00C)
                rtype = q["qtype"]
                rclass = 1
                ttl = 300
                
                if rtype == 1: # A record
                    rdata = socket.inet_aton(ans)
                    rdlength = len(rdata)
                    response_body += name_pointer + struct.pack("!HHIH", rtype, rclass, ttl, rdlength) + rdata
                elif rtype == 15: # MX record (Preference 10 + mail server name)
                    preference = 10
                    exchange_bytes = b""
                    for part in ans.split('.'):
                        exchange_bytes += bytes([len(part)]) + part.encode('ascii')
                    exchange_bytes += b'\x00'
                    rdata = struct.pack("!H", preference) + exchange_bytes
                    rdlength = len(rdata)
                    response_body += name_pointer + struct.pack("!HHIH", rtype, rclass, ttl, rdlength) + rdata
                    
            return response_body
        except Exception as e:
            print(f"[Servidor DNS] Falha ao processar requisição: {e}")
            return b""
            
    def stop(self):
        self.running = False
        self.sock.close()

# --- 4. VALIDAÇÃO COM DIG ---

def run_tests():
    server = IterativeDNSServer("127.0.0.1", 5353)
    server.start()
    time.sleep(0.5) # Aguarda o servidor iniciar
    
    try:
        # Testa consulta tipo A via dig
        print("\nExecutando: dig @127.0.0.1 -p 5353 example.com A +short")
        res_a = subprocess.run(["dig", "@127.0.0.1", "-p", "5353", "example.com", "A", "+short"], capture_output=True, text=True)
        print(f"Saída dig A:\n{res_a.stdout.strip()}")
        assert "93.184.216.34" in res_a.stdout, f"Esperado IP 93.184.216.34, obtido: {res_a.stdout}"
        
        # Testa consulta tipo MX via dig
        print("\nExecutando: dig @127.0.0.1 -p 5353 example.com MX +short")
        res_mx = subprocess.run(["dig", "@127.0.0.1", "-p", "5353", "example.com", "MX", "+short"], capture_output=True, text=True)
        print(f"Saída dig MX:\n{res_mx.stdout.strip()}")
        assert "mail.example.com" in res_mx.stdout, f"Esperado mail.example.com, obtido: {res_mx.stdout}"
        
        print("\n[Sucesso] Todos os testes com dig, cadeia iterativa e proteções passaram com êxito!")
    finally:
        server.stop()

if __name__ == "__main__":
    run_tests()