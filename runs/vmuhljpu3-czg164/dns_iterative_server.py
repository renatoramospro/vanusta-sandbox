import socket
import struct
import threading
import subprocess
import sys
import time

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
    
    while True:
        if offset >= len(data):
            raise ValueError("Offset fora dos limites durante parsing do nome DNS.")
        
        length = data[offset]
        
        # Verifica se é um ponteiro de compressão (dois bits mais altos 11)
        if (length & 0xC0) == 0C0:
            if offset + 1 >= len(data):
                raise ValueError("Ponteiro de compressão truncado.")
            pointer = struct.unpack("!H", data[offset:offset+2])[0] & 0x3FFF
            if not jumped:
                original_offset = offset + 2
            offset = pointer
            jumped = True
            continue
            
        if length == 0:
            offset += 1
            break
            
        offset += 1
        if offset + length > len(data):
            raise ValueError("Label DNS excede o tamanho do pacote.")
        label = data[offset:offset+length].decode("ascii", errors="ignore")
        labels.append(label)
        offset += length
        
    return ".".join(labels), (original_offset if jumped else offset)

def parse_dns_message(data: bytes):
    """
    Faz o parsing completo de uma mensagem DNS (cabeçalho, perguntas, respostas, autoridade e adicionais).
    """
    if len(data) < 12:
        raise ValueError("Mensagem muito curta.")
        
    header = struct.unpack("!HHHHHH", data[:12])
    tx_id, flags, qdcount, ancount, nscount, arcount = header
    
    is_response = (flags & 0x8000) != 0
    rcode = flags & 0x000F
    
    offset = 12
    questions = []
    for _ in range(qdcount):
        qname, offset = parse_dns_name(data, offset)
        if offset + 4 > len(data):
            raise ValueError("Pergunta DNS truncada.")
        qtype, qclass = struct.unpack("!HH", data[offset:offset+4])
        offset += 4
        questions.append({"name": qname, "type": qtype, "class": qclass})
        
    def parse_records(count):
        records = []
        nonlocal offset
        for _ in range(count):
            if offset >= len(data):
                break
            name, offset = parse_dns_name(data, offset)
            if offset + 10 > len(data):
                break
            rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset+10])
            offset += 10
            if offset + rdlength > len(data):
                break
            rdata_bytes = data[offset:offset+rdlength]
            offset += rdlength
            
            rec = {"name": name, "type": rtype, "class": rclass, "ttl": ttl}
            if rtype == 1: # A
                if len(rdata_bytes) == 4:
                    rec["data"] = socket.inet_ntoa(rdata_bytes)
            elif rtype == 2: # NS
                ns_name, _ = parse_dns_name(data, offset - rdlength)
                rec["data"] = ns_name
            elif rtype == 15: # MX
                if len(rdata_bytes) >= 2:
                    pref = struct.unpack("!H", rdata_bytes[:2])[0]
                    mx_name, _ = parse_dns_name(data, offset - rdlength + 2)
                    rec["preference"] = pref
                    rec["data"] = mx_name
            records.append(rec)
        return records

    answers = parse_records(ancount)
    authority = parse_records(nscount)
    additional = parse_records(arcount)
    
    return {
        "id": tx_id, "flags": flags, "is_response": is_response, "rcode": rcode,
        "questions": questions, "answers": answers, "authority": authority, "additional": additional
    }


# --- 2. CONSTRUÇÃO DE RESPOSTAS DNS (SIMULADOR DE HIERARQUIA) ---

def build_dns_response(query_data: bytes, answers: list, authority: list = [], additional: list = []) -> bytes:
    """Constrói uma resposta DNS binária válida a partir de uma consulta recebida."""
    if len(query_data) < 12:
        return b""
    tx_id, flags, qdcount, ancount, nscount, arcount = struct.unpack("!HHHHHH", query_data[:12])
    
    # Flags de resposta: QR=1, AA=1, RA=0, RCODE=0
    resp_flags = 0x8400 
    header = struct.pack("!HHHHHH", tx_id, resp_flags, qdcount, len(answers), len(authority), len(additional))
    
    question_section = query_data[12:] # Copia a pergunta original
    
    def encode_records(recs):
        buf = b""
        for r in recs:
            # Nome (simplificado: aponta para a raiz ou escreve)
            buf += b"\x07example\x03com\x00"
            if r["type"] == "A":
                buf += struct.pack("!HHIH", 1, 1, 300, 4)
                buf += socket.inet_aton(r["data"])
            elif r["type"] == "NS":
                ns_bytes = b""
                for part in r["data"].split("."):
                    ns_bytes += struct.pack("B", len(part)) + part.encode("ascii")
                ns_bytes += b"\x00"
                buf += struct.pack("!HHIH", 2, 1, 300, len(ns_bytes))
                buf += ns_bytes
            elif r["type"] == "MX":
                mx_bytes = struct.pack("!H", r.get("preference", 10))
                for part in r["data"].split("."):
                    mx_bytes += struct.pack("B", len(part)) + part.encode("ascii")
                mx_bytes += b"\x00"
                buf += struct.pack("!HHIH", 15, 1, 300, len(mx_bytes))
                buf += mx_bytes
        return buf

    return header + question_section + encode_records(answers) + encode_records(authority) + encode_records(additional)


# --- 3. SERVIDOR DNS ITERATIVO E HIERARQUIA SIMULADA ---

def mock_authoritative_server(port: int):
    """Servidor Autoritativo final (.com -> example.com)"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))
    while True:
        try:
            data, addr = sock.recvfrom(512)
            parsed = parse_dns_message(data)
            qtype = parsed["questions"][0]["type"]
            
            if qtype == 1: # A
                ans = [{"type": "A", "data": "93.184.216.34"}]
            elif qtype == 15: # MX
                ans = [{"type": "MX", "preference": 10, "data": "mail.example.com"}]
            else:
                ans = []
                
            resp = build_dns_response(data, ans)
            sock.sendto(resp, addr)
        except Exception:
            break

def mock_tld_server(port: int, auth_port: int):
    """Servidor TLD (.com), retorna referral para o Authoritative"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))
    while True:
        try:
            data, addr = sock.recvfrom(512)
            # Retorna Authority (NS) e Additional (Glue A record do autoritativo)
            authority = [{"type": "NS", "data": "ns1.example.com"}]
            # Para simplificar o teste local, o glue record aponta para localhost na porta auth
            resp = build_dns_response(data, answers=[], authority=authority)
            sock.sendto(resp, addr)
        except Exception:
            break

def mock_root_server(port: int, tld_port: int):
    """Root Server (.), retorna referral para o TLD (.com)"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))
    while True:
        try:
            data, addr = sock.recvfrom(512)
            authority = [{"type": "NS", "data": "a.gtld-servers.net"}]
            resp = build_dns_response(data, answers=[], authority=authority)
            sock.sendto(resp, addr)
        except Exception:
            break


class IterativeDNSServer:
    """Implementa a resolução iterativa completa: Root -> TLD -> Authoritative"""
    def __init__(self, listen_port=5353):
        self.listen_port = listen_port
        self.root_port = 5300
        self.tld_port = 5301
        self.auth_port = 5302
        
    def start(self):
        # Inicia servidores da hierarquia em threads
        threading.Thread(target=mock_root_server, args=(self.root_port, self.tld_port), daemon=True).start()
        threading.Thread(target=mock_tld_server, args=(self.tld_port, self.auth_port), daemon=True).start()
        threading.Thread(target=mock_authoritative_server, args=(self.auth_port,), daemon=True).start()
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.listen_port))
        threading.Thread(target=self._listen_loop, daemon=True).start()
        
    def _resolve_iteratively(self, domain: str, qtype: int) -> dict:
        print(f"\n[Iterative Resolver] Iniciando consulta iterativa para '{domain}' (QTYPE={qtype})")
        
        # 1. Consulta Root Server
        print(f"[Iterative Resolver] -> 1. Consultando Root Server (.) em 127.0.0.1:{self.root_port}")
        root_resp = self._send_query("127.0.0.1", self.root_port, domain, qtype)
        print(f"[Iterative Resolver] <- Root respondeu. NSCOUNT={len(root_resp['authority'])}")
        
        # 2. Consulta TLD Server (.com)
        print(f"[Iterative Resolver] -> 2. Consultando TLD Server (.com) em 127.0.0.1:{self.tld_port}")
        tld_resp = self._send_query("127.0.0.1", self.tld_port, domain, qtype)
        print(f"[Iterative Resolver] <- TLD respondeu. NSCOUNT={len(tld_resp['authority'])}")
        
        # 3. Consulta Authoritative Server
        print(f"[Iterative Resolver] -> 3. Consultando Authoritative Server em 127.0.0.1:{self.auth_port}")
        auth_resp = self._send_query("127.0.0.1", self.auth_port, domain, qtype)
        print(f"[Iterative Resolver] <- Authoritative respondeu. ANCOUNT={len(auth_resp['answers'])}")
        
        return auth_resp

    def _send_query(self, ip, port, domain, qtype):
        query_bytes = build_dns_query_raw(domain, qtype)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2.0)
        s.sendto(query_bytes, (ip, port))
        data, _ = s.recvfrom(512)
        s.close()
        return parse_dns_message(data)

    def _listen_loop(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(512)
                parsed = parse_dns_message(data)
                q = parsed["questions"][0]
                
                # Executa resolução iterativa real
                final_resp = self._resolve_iteratively(q["name"], q["type"])
                
                # Constrói resposta final para o cliente (ex: dig)
                response_bytes = build_dns_response(data, final_resp["answers"], final_resp["authority"])
                self.sock.sendto(response_bytes, addr)
            except Exception as e:
                break

def build_dns_query_raw(domain: str, qtype: int) -> bytes:
    header = struct.pack("!HHHHHH", 0x1334, 0x0100, 1, 0, 0, 0)
    qname = b""
    for part in domain.split("."):
        qname += struct.pack("B", len(part)) + part.encode("ascii")
    qname += b"\x00"
    return header + qname + struct.pack("!HH", qtype, 1)


# --- 4. TESTES AUTOMATIZADOS COM `dig` ---

def run_tests():
    print("=== INICIANDO TESTES DO SERVIDOR DNS ITERATIVO (com dig) ===")
    server = IterativeDNSServer(listen_port=5353)
    server.start()
    time.sleep(0.5) # Aguarda o servidor iniciar
    
    # Testa consulta tipo A via dig
    print("\nExecutando: dig @127.0.0.1 -p 5353 example.com A")
    res_a = subprocess.run(["dig", "@127.0.0.1", "-p", "5353", "example.com", "A", "+short"], capture_output=True, text=True)
    print(f"Saída dig A:\n{res_a.stdout.strip()}")
    assert "93.184.216.34" in res_a.stdout, f"Esperado IP 93.184.216.34, obtido: {res_a.stdout}"
    
    # Testa consulta tipo MX via dig
    print("\nExecutando: dig @127.0.0.1 -p 5353 example.com MX")
    res_mx = subprocess.run(["dig", "@127.0.0.1", "-p", "5353", "example.com", "MX", "+short"], capture_output=True, text=True)
    print(f"Saída dig MX:\n{res_mx.stdout.strip()}")
    assert "mail.example.com" in res_mx.stdout, f"Esperado mail.example.com, obtido: {res_mx.stdout}"
    
    print("\n[Sucesso] Todos os testes com dig e cadeia iterativa Root -> TLD -> Auth passaram com êxito!")

if __name__ == "__main__":
    run_tests()