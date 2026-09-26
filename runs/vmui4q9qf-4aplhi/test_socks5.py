import socket
import threading
import time
import struct
from socks5_server import SOCKS5Server, PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS

# Servidor TCP de Eco Dummy para testar o túnel do proxy
class EchoServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.running = True

    def start(self):
        def run():
            while self.running:
                try:
                    conn, _ = self.sock.accept()
                    data = conn.recv(1024)
                    conn.sendall(data) # Eco
                    conn.close()
                except:
                    break
        self.thread = threading.Thread(target=run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.sock.close()

def socks5_client_request(target_host, target_port, payload):
    # Conectar ao Proxy
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((PROXY_HOST, PROXY_PORT))

    # 1. Handshake inicial (suporta métodos sem auth e com auth, mas escolhemos 0x02)
    s.sendall(b'\x05\x01\x02')
    resp = s.recv(2)
    assert resp == b'\x05\x02', f"Método de autenticação rejeitado: {resp}"

    # 2. Autenticação por usuário e senha
    username_bytes = VALID_USER.encode('utf-8')
    password_bytes = VALID_PASS.encode('utf-8')
    auth_packet = bytes([0x01, len(username_bytes)]) + username_bytes + bytes([len(password_bytes)]) + password_bytes
    s.sendall(auth_packet)
    
    auth_resp = s.recv(2)
    assert auth_resp == b'\x01\x00', f"Falha na autenticação SOCKS5: {auth_resp}"

    # 3. Comando CONNECT
    # ATYP 0x01 = IPv4
    ip_bytes = socket.inet_aton(target_host)
    port_bytes = target_port.to_bytes(2, 'big')
    connect_packet = b'\x05\x01\x00\x01' + ip_bytes + port_bytes
    s.sendall(connect_packet)

    conn_resp = s.recv(10)
    assert conn_resp[1] == 0x00, f"Falha na conexão CONNECT: {conn_resp[1]}"

    # 4. Enviar dados pelo túnel e receber eco
    s.sendall(payload)
    received = s.recv(len(payload))
    s.close()
    return received

def test_consecutive_requests():
    # Iniciar servidor proxy
    proxy = SOCKS5Server(PROXY_HOST, PROXY_PORT)
    p_thread = threading.Thread(target=proxy.start)
    p_thread.daemon = True
    p_thread.start()

    # Iniciar servidor de eco de teste
    echo_port = 9090
    echo_server = EchoServer('127.0.0.1', echo_port)
    echo_server.start()
    time.sleep(0.5)

    total_requests = 50
    success_count = 0

    print(f"Iniciando teste de {total_requests} requisições consecutivas via Proxy SOCKS5...")
    
    for i in range(1, total_requests + 1):
        test_payload = f"Ping-SOCKS5-{i}".encode('utf-8')
        try:
            result = socks5_client_request('127.0.0.1', echo_port, test_payload)
            if result == test_payload:
                success_count += 1
        except Exception as e:
            print(f"Erro na requisição {i}: {e}")

    proxy.stop()
    echo_server.stop()

    print(f"Requisições bem-sucedidas: {success_count}/{total_requests}")
    assert success_count == total_requests, f"Taxa de sucesso abaixo de 100%: {success_count}/{total_requests}"
    print("Teste concluído com 100% de sucesso!")

if __name__ == '__main__':
    test_consecutive_requests()