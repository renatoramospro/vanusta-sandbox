import socket
import base64
import hashlib
import struct
import threading
import time

WS_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def calcular_accept_key(key_str):
    """Calcula o Sec-WebSocket-Accept conforme RFC 6455."""
    combined = key_str.strip().encode('utf-8') + WS_GUID
    sha1_hash = hashlib.sha1(combined).digest()
    return base64.b64encode(sha1_hash).decode('utf-8')

def validar_e_parsear_handshake(requisicao_bytes):
    """Valida estritamente os headers HTTP de handshake do WebSocket conforme a RFC 6455."""
    linhas = requisicao_bytes.decode('utf-8', errors='ignore').split('\r\n')
    if not linhas or len(linhas) < 1:
        return None

    # Valida linha de requisição
    primeira_linha = linhas[0].split()
    if len(primeira_linha) < 3 or primeira_linha[0] != 'GET':
        return None

    headers = {}
    for linha in linhas[1:]:
        if ':' in linha:
            chave, valor = linha.split(':', 1)
            chave_limpa = chave.strip().lower()
            valor_limpo = valor.strip()
            # Trata múltiplos headers acumulando em lista ou unindo com vírgula
            if chave_limpa in headers:
                headers[chave_limpa] += f", {valor_limpo}"
            else:
                headers[chave_limpa] = valor_limpo

    # Validação obrigatória de Host
    if 'host' not in headers:
        return None

    # Validação estrita de Upgrade
    if headers.get('upgrade', '').lower() != 'websocket':
        return None

    # Validação estrita de Connection por tokens delimitados por vírgula
    conn_header = headers.get('connection', '')
    tokens_conn = [t.strip().lower() for t in conn_header.split(',')]
    if 'upgrade' not in tokens_conn:
        return None

    # Validação estrita de versão do WebSocket
    if headers.get('sec-websocket-version') != '13':
        return None
    
    # Validação estrita de Sec-WebSocket-Key (deve ser Base64 válido decodificando exatamente 16 bytes)
    ws_key = headers.get('sec-websocket-key')
    if not ws_key:
        return None
    
    try:
        key_decodificada = base64.b64decode(ws_key.strip(), validate=True)
        if len(key_decodificada) != 16:
            return None
    except Exception:
        return None

    return ws_key.strip()

def ler_frame_websocket(sock):
    """Lê e parseia um frame WebSocket do socket, suportando controle e tamanhos estendidos."""
    primeiro_byte = sock.recv(1)
    if not primeiro_byte:
        return None, None
    
    b1 = primeiro_byte[0]
    fin = (b1 & 0x80) != 0
    opcode = b1 & 0x0F

    segundo_byte = sock.recv(1)
    if not segundo_byte:
        return None, None
    
    b2 = segundo_byte[0]
    mascarado = (b2 & 0x80) != 0
    payload_len = b2 & 0x7F

    if payload_len == 126:
        dados_len = sock.recv(2)
        if len(dados_len) < 2:
            return None, None
        payload_len = struct.unpack("!H", dados_len)[0]
    elif payload_len == 127:
        dados_len = sock.recv(8)
        if len(dados_len) < 8:
            return None, None
        payload_len = struct.unpack("!Q", dados_len)[0]

    mascara = b""
    if mascarado:
        mascara = sock.recv(4)
        if len(mascara) < 4:
            return None, None

    payload = bytearray()
    restante = payload_len
    while restante > 0:
        chunk = sock.recv(min(restante, 4096))
        if not chunk:
            break
        payload.extend(chunk)
        restante -= len(chunk)

    if mascarado and len(mascara) == 4:
        for i in range(len(payload)):
            payload[i] ^= mascara[i % 4]

    return opcode, bytes(payload)

def enviar_frame_websocket(sock, opcode, payload):
    """Envia um frame WebSocket para o cliente (sem máscara, pois é servidor)."""
    frame = bytearray()
    frame.append(0x80 | (opcode & 0x0F))
    
    tamanho = len(payload)
    if tamanho <= 125:
        frame.append(tamanho)
    elif tamanho <= 65535:
        frame.append(126)
        frame.extend(struct.pack("!H", tamanho))
    else:
        frame.append(127)
        frame.extend(struct.pack("!Q", tamanho))
        
    frame.extend(payload)
    sock.sendall(bytes(frame))

def servidor_websocket(parada_event, porta):
    """Servidor TCP que aceita conexões e processa o handshake e frames WebSocket."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('127.0.0.1', porta))
    server_sock.listen(5)
    server_sock.settimeout(1.0)

    while not parada_event.is_set():
        try:
            cli, addr = server_sock.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        try:
            requisicao = cli.recv(4096)
            ws_key = validar_e_parsear_handshake(requisicao)
            if not ws_key:
                cli.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nHandshake invalido")
                cli.close()
                continue

            accept_key = calcular_accept_key(ws_key)
            resposta = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
            )
            cli.sendall(resposta.encode('utf-8'))

            # Loop de atendimento de frames
            while not parada_event.is_set():
                opcode, payload = ler_frame_websocket(cli)
                if opcode is None:
                    break
                if opcode == 0x8: # Close
                    break
                elif opcode == 0x9: # Ping
                    enviar_frame_websocket(cli, 0xA, payload) # Pong
                elif opcode == 0x1: # Texto
                    enviar_frame_websocket(cli, 0x1, payload) # Eco
        except Exception:
            pass
        finally:
            cli.close()
            
    server_sock.close()

def cliente_teste_completo(porta):
    """Cliente de teste robusto validando todos os cenários estritos."""
    time.sleep(0.2)
    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli.connect(('127.0.0.1', porta))

    chave_bytes = os_bytes = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
    ws_key_base64 = base64.b64encode(os_bytes).decode('utf-8')

    req = (
        "GET /chat HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Upgrade: websocket\r\n"
        "Connection: keep-alive, Upgrade\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        f"Sec-WebSocket-Key: {ws_key_base64}\r\n\r\n"
    )
    cli.sendall(req.encode('utf-8'))

    resposta = cli.recv(1024)
    assert b"101 Switching Protocols" in resposta, "Handshake falhou!"
    print("Handshake rigoroso OK!")

    mascara = b"\x12\x34\x56\x78"

    # 1. Eco de mensagem curta
    mensagem_curta = b"Teste WebSocket Curto"
    payload_m = bytearray(mensagem_curta[i] ^ mascara[i % 4] for i in range(len(mensagem_curta)))
    frame = bytearray([0x81, 0x80 | len(mensagem_curta)])
    frame.extend(mascara)
    frame.extend(payload_m)
    cli.sendall(bytes(frame))

    op, resp_payload = ler_frame_websocket(cli)
    assert resp_payload == mensagem_curta, "Eco curto falhou!"
    print(f"Eco curto OK: {resp_payload.decode('utf-8')}")

    # 2. Payload estendido de 2 bytes (300 bytes -> 126)
    mensagem_longa = b"A" * 300
    payload_m2 = bytearray(mensagem_longa[i] ^ mascara[i % 4] for i in range(len(mensagem_longa)))
    frame2 = bytearray([0x81, 0x80 | 126])
    frame2.extend(struct.pack("!H", len(mensagem_longa)))
    frame2.extend(mascara)
    frame2.extend(payload_m2)
    cli.sendall(bytes(frame2))

    op, resp_payload_longo = ler_frame_websocket(cli)
    assert resp_payload_longo == mensagem_longa, "Eco estendido falhou!"
    print("Eco estendido (300 bytes) OK!")

    # 3. Payload estendido de 8 bytes (65540 bytes -> 127)
    mensagem_gigante = b"B" * 65540
    payload_m3 = bytearray(mensagem_gigante[i] ^ mascara[i % 4] for i in range(len(mensagem_gigante)))
    frame3 = bytearray([0x81, 0x80 | 127])
    frame3.extend(struct.pack("!Q", len(mensagem_gigante)))
    frame3.extend(mascara)
    frame3.extend(payload_m3)
    cli.sendall(bytes(frame3))

    op, resp_payload_gigante = ler_frame_websocket(cli)
    assert resp_payload_gigante == mensagem_gigante, "Eco de 64 bits falhou!"
    print("Eco estendido de 64 bits (65540 bytes) OK!")

    # 4. Teste de Ping/Pong
    frame_ping = bytearray([0x89, 0x84])
    frame_ping.extend(mascara)
    frame_ping.extend(bytearray(b"ping"[i] ^ mascara[i % 4] for i in range(4)))
    cli.sendall(bytes(frame_ping))

    op_pong, payload_pong = ler_frame_websocket(cli)
    assert op_pong == 0xA, "Servidor não respondeu com Pong!"
    assert payload_pong == b"ping", "Payload do Pong incorreto!"
    print("Teste de Ping/Pong OK!")

    cli.close()

def main():
    porta = 9997
    parada = threading.Event()
    
    t_servidor = threading.Thread(target=servidor_websocket, args=(parada, porta))
    t_servidor.start()

    try:
        cliente_teste_completo(porta)
        print("TODOS OS TESTES RIGOROSOS DE WEBSOCKET PASSARAM COM SUCESSO")
    finally:
        parada.set()
        t_servidor.join()

if __name__ == "__main__":
    main()