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
    """Valida estritamente os headers HTTP de handshake do WebSocket."""
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
            headers[chave.strip().lower()] = valor.strip()

    # Validações obrigatórias da RFC 6455
    if headers.get('upgrade', '').lower() != 'websocket':
        return None
    if 'upgrade' not in headers.get('connection', '').lower():
        return None
    if headers.get('sec-websocket-version') != '13':
        return None
    
    ws_key = headers.get('sec-websocket-key')
    if not ws_key:
        return None

    return ws_key

def ler_frame_websocket(sock):
    """Lê, decodifica e desmascara frames WebSocket, suportando payloads estendidos e controle."""
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

    # Tratamento de tamanhos estendidos conforme RFC 6455
    if tamanho_payload == 126:
        dados_tamanho = sock.recv(2)
        if len(dados_tamanho) < 2:
            return None, None
        tamanho_payload = struct.unpack("!H", dados_tamanho)[0]
    elif tamanho_payload == 127:
        dados_tamanho = sock.recv(8)
        if len(dados_tamanho) < 8:
            return None, None
        tamanho_payload = struct.unpack("!Q", dados_tamanho)[0]

    mascara = b""
    if mascarado:
        mascara = sock.recv(4)
        if len(mascara) < 4:
            return None, None

    payload = bytearray()
    restante = tamanho_payload
    while restante > 0:
        bloco = sock.recv(restante)
        if not bloco:
            break
        payload.extend(bloco)
        restante -= len(bloco)

    if mascarado:
        payload = bytearray(payload[i] ^ mascara[i % 4] for i in range(len(payload)))

    return opcode, bytes(payload)

def enviar_frame_websocket(sock, opcode, dados):
    """Envia um frame WebSocket para o cliente."""
    frame = bytearray()
    frame.append(0x80 | opcode)  # FIN=1, opcode

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

def servidor_websocket(evento_parada, porta):
    """Servidor TCP que executa o handshake e gerencia a conexão WebSocket."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('127.0.0.1', porta))
    servidor.listen(5)
    servidor.settimeout(1.0)

    while not evento_parada.is_set():
        try:
            conn, _ = servidor.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        threading.Thread(target=tratar_conexao_cliente, args=(conn,)).start()

    servidor.close()

def tratar_conexao_cliente(conn):
    try:
        requisicao = conn.recv(4096)
        ws_key = validar_e_parsear_handshake(requisicao)
        
        if not ws_key:
            # Rejeição estrita de handshake inválido (HTTP 400)
            resposta_erro = b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nHandshake WebSocket invalido ou headers ausentes."
            conn.sendall(resposta_erro)
            conn.close()
            return

        accept_key = calcular_accept_key(ws_key)
        
        resposta = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
        )
        conn.sendall(resposta.encode('utf-8'))

        while True:
            opcode, payload = ler_frame_websocket(conn)
            if opcode is None:
                break

            # Tratamento de frames de controle
            if opcode == 0x8:  # Close
                break
            elif opcode == 0x9:  # Ping -> Responder com Pong (0xA)
                enviar_frame_websocket(conn, 0xA, payload)
                continue
            elif opcode == 0x1:  # Text Frame -> Ecoar de volta
                enviar_frame_websocket(conn, 0x1, payload)

    except Exception as e:
        pass
    finally:
        conn.close()

def cliente_teste_completo(porta):
    """Executa testes rigorosos cobrindo payload curto, estendido, Ping/Pong e handshake inválido."""
    time.sleep(0.2)
    
    # 1. Teste de Handshake Inválido (Deve retornar HTTP 400)
    cli_invalido = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli_invalido.connect(('127.0.0.1', porta))
    cli_invalido.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
    resp_invalida = cli_invalido.recv(1024)
    assert b"400 Bad Request" in resp_invalida, "Servidor deveria rejeitar handshake inválido!"
    cli_invalido.close()

    # 2. Teste de Conexão Válida e Payload Curto / Estendido
    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli.connect(('127.0.0.1', porta))

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

    # Validar presença do Sec-WebSocket-Accept correto na resposta
    accept_esperado = calcular_accept_key(chave_base64)
    assert accept_esperado.encode('utf-8') in resposta, "Sec-WebSocket-Accept incorreto na resposta!"

    # Enviar payload curto mascarado
    mensagem_curta = b"Teste WebSocket Curto"
    mascara = b"\xde\xad\xbe\xef"
    payload_m1 = bytearray(mensagem_curta[i] ^ mascara[i % 4] for i in range(len(mensagem_curta)))
    
    frame1 = bytearray([0x81, 0x80 | len(mensagem_curta)])
    frame1.extend(mascara)
    frame1.extend(payload_m1)
    cli.sendall(bytes(frame1))

    op, resp_payload = ler_frame_websocket(cli)
    assert resp_payload == mensagem_curta, "Eco de payload curto falhou!"
    print(f"Eco curto OK: {resp_payload.decode('utf-8')}")

    # Enviar payload estendido (300 bytes -> tamanho 126)
    mensagem_longa = b"A" * 300
    payload_m2 = bytearray(mensagem_longa[i] ^ mascara[i % 4] for i in range(len(mensagem_longa)))
    
    frame2 = bytearray([0x81, 0x80 | 126])
    frame2.extend(struct.pack("!H", len(mensagem_longa)))
    frame2.extend(mascara)
    frame2.extend(payload_m2)
    cli.sendall(bytes(frame2))

    op, resp_payload_longo = ler_frame_websocket(cli)
    assert resp_payload_longo == mensagem_longa, "Eco de payload estendido falhou!"
    print(f"Eco estendido (300 bytes) OK!")

    # Teste de Ping/Pong
    frame_ping = bytearray([0x89, 0x84]) # Ping com 4 bytes mascarados
    frame_ping.extend(mascara)
    frame_ping.extend(bytearray(b"ping"[i] ^ mascara[i % 4] for i in range(4)))
    cli.sendall(bytes(frame_ping))

    op_pong, payload_pong = ler_frame_websocket(cli)
    assert op_pong == 0xA, "Servidor não respondeu com Pong!"
    assert payload_pong == b"ping", "Payload do Pong incorreto!"
    print(f"Teste de Ping/Pong OK!")

    cli.close()

def main():
    porta = 9998
    parada = threading.Event()
    
    t_servidor = threading.Thread(target=servidor_websocket, args=(parada, porta))
    t_servidor.start()

    try:
        cliente_teste_completo(porta)
        print("TODOS OS TESTES RIGOROSOS DE WEBSOCKET PASSARAM COM SUCESSO (100%)")
    finally:
        parada.set()
        t_servidor.join()

if __name__ == "__main__":
    main()