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

def parsear_handshake(requisicao_bytes):
    """Extrai a chave Sec-WebSocket-Key de uma requisição HTTP."""
    linhas = requisicao_bytes.decode('utf-8', errors='ignore').split('\r\n')
    chave = None
    for linha in linhas:
        if linha.lower().startswith('sec-websocket-key:'):
            chave = linha.split(':', 1)[1].strip()
            break
    return chave

def ler_frame_websocket(sock):
    """Lê, decodifica e desmascara um frame WebSocket enviado pelo cliente."""
    cabecalho1 = sock.recv(1)
    if not cabecalho1:
        return None, None
    
    b1 = cabecalho1[0]
    fin = (b1 & 0x80) != 0
    opcode = b1 & 0x0F

    cabecalho2 = sock.recv(1)
    if not cabecalho2:
        return None, None
    
    b2 = cabecalho2[0]
    mascarado = (b2 & 0x80) != 0
    tamanho_payload = b2 & 0x7F

    # Leitura de comprimentos estendidos
    if tamanho_payload == 126:
        ext = sock.recv(2)
        tamanho_payload = struct.unpack("!H", ext)[0]
    elif tamanho_payload == 127:
        ext = sock.recv(8)
        tamanho_payload = struct.unpack("!Q", ext)[0]

    # Leitura da máscara (obrigatória para clientes)
    mascara = b""
    if mascarado:
        mascara = sock.recv(4)

    # Leitura do payload
    payload = b""
    lido = 0
    while lido < tamanho_payload:
        bloco = sock.recv(tamanho_payload - lido)
        if not bloco:
            break
        payload += bloco
        lido += len(bloco)

    # Desmascaramento XOR
    if mascarado and len(mascara) == 4:
        payload_desmascarado = bytearray(
            payload[i] ^ mascara[i % 4] for i in range(len(payload))
        )
    else:
        payload_desmascarado = bytearray(payload)

    return opcode, bytes(payload_desmascarado)

def enviar_frame_websocket(sock, opcode, dados):
    """Envia um frame WebSocket do servidor para o cliente (sem máscara)."""
    frame = bytearray()
    b1 = 0x80 | (opcode & 0x0F) # FIN=1, Opcode
    frame.append(b1)

    tamanho = len(dados)
    if tamanho <= 125:
        frame.append(tamanho)
    elif tamanho <= 65535:
        frame.append(126)
        frame.extend(struct.pack("!H", tamanho))
    else:
        frame.append(127)
        frame.extend(struct.pack("!Q", tamanho))

    frame.extend(dados)
    sock.sendall(bytes(frame))

def servidor_websocket(parada_evento, porta):
    """Servidor TCP ouvindo conexões WebSocket."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('127.0.0.1', porta))
    servidor.listen(1)
    servidor.settimeout(1.0)

    while not parada_evento.is_set():
        try:
            conn, _ = servidor.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        with conn:
            # 1. Ler requisição HTTP do handshake
            req = conn.recv(1024)
            chave = parsear_handshake(req)
            if not chave:
                conn.close()
                continue

            accept_key = calcular_accept_key(chave)

            # 2. Enviar resposta de Upgrade HTTP 101
            resposta = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
            )
            conn.sendall(resposta.encode('utf-8'))

            # 3. Ler frame de eco do cliente
            opcode, payload = ler_frame_websocket(conn)
            if opcode == 0x1: # Texto
                # 4. Enviar de volta (Echo)
                enviar_frame_websocket(conn, 0x1, payload)
        break
    servidor.close()

def cliente_teste(porta):
    """Simula um cliente WebSocket enviando um frame mascarado."""
    time.sleep(0.2) # Aguarda o servidor subir
    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli.connect(('127.0.0.1', porta))

    # Handshake de cliente
    chave_base64 = base64.b64encode(b"1234567890123456").decode('utf-8')
    requisicao = (
        "GET /chat HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        f"Sec-WebSocket-Key: {chave_base64}\r\n\r\n"
    )
    cli.sendall(requisicao.encode('utf-8'))
    resposta = cli.recv(1024)
    assert b"101 Switching Protocols" in resposta, "Handshake falhou!"

    # Enviar frame mascarado (como exige a RFC para clientes)
    mensagem = b"Teste WebSocket do Zero"
    opcode = 0x1 # Texto
    mascara = b"\xde\xad\xbe\xef"
    
    # Aplicar máscara XOR no payload simulado
    payload_mascarado = bytearray(mensagem[i] ^ mascara[i % 4] for i in range(len(mensagem)))

    # Montar frame do cliente
    frame = bytearray()
    frame.append(0x80 | opcode) # FIN=1, Text
    # Bit MASK (0x80) + tamanho
    tamanho = len(mensagem)
    frame.append(0x80 | tamanho)
    frame.extend(mascara)
    frame.extend(payload_mascarado)

    cli.sendall(bytes(frame))

    # Receber eco do servidor
    resp_opcode, resp_payload = ler_frame_websocket(cli)
    print(f"Servidor ecoou com sucesso: {resp_payload.decode('utf-8')}")
    assert resp_payload == mensagem, "O eco recebido não confere com a mensagem enviada!"
    cli.close()

def main():
    porta = 9999
    parada = threading.Event()
    
    t_servidor = threading.Thread(target=servidor_websocket, args=(parada, porta))
    t_servidor.start()

    try:
        cliente_teste(porta)
        print("TESTE DE ECO WEBSOCKET BEM-SUCEDIDO (100%)")
    finally:
        parada.set()
        t_servidor.join()

if __name__ == "__main__":
    main()