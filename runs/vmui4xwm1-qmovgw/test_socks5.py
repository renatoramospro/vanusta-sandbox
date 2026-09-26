import socket
import threading
import time
import pytest
from socks5_server import SOCKS5Server, PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS

# Servidor Echo simples para testar o tráfego passando pelo proxy
class EchoServer:
    def __init__(self, host='127.0.0.1', port=0):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(5)
        self.port = self.socket.getsockname()[1]
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.is_running:
            try:
                conn, _ = self.socket.accept()
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
            except Exception:
                break

    def _handle(self, conn):
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)
        except Exception:
            pass
        finally:
            conn.close()

    def stop(self):
        self.is_running = False
        self.socket.close()

def socks5_connect(host, port, user, passwd, dest_host, dest_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    
    # Handshake
    s.sendall(b'\x05\x01\x02')
    resp = s.recv(2)
    if resp != b'\x05\x02':
        s.close()
        raise Exception("Handshake falhou ou autenticação recusada")

    # Autenticação RFC 1929
    auth_payload = b'\x01' + bytes([len(user)]) + user.encode() + bytes([len(passwd)]) + passwd.encode()
    s.sendall(auth_payload)
    auth_resp = s.recv(2)
    if auth_resp != b'\x01\x00':
        s.close()
        raise Exception("Autenticação falhou com credenciais inválidas")

    # Comando CONNECT
    dest_ip = socket.gethostbyname(dest_host)
    req = b'\x05\x01\x00\x01' + socket.inet_aton(dest_ip) + dest_port.to_bytes(2, 'big')
    s.sendall(req)
    
    reply = s.recv(10)
    if len(reply) < 2 or reply[1] != 0x00:
        s.close()
        raise Exception("Conexão de destino recusada pelo proxy")

    return s

def test_consecutive_requests():
    # Iniciar servidor proxy
    proxy = SOCKS5Server(PROXY_HOST, PROXY_PORT)
    proxy.start()
    time.sleep(0.2)

    # Iniciar servidor echo de teste
    echo = EchoServer('127.0.0.1', 0)
    time.sleep(0.2)

    total_requests = 50
    success_count = 0

    try:
        for i in range(total_requests):
            try:
                conn = socks5_connect(PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS, '127.0.0.1', echo.port)
                message = f"Ping {i}".encode()
                conn.sendall(message)
                data = conn.recv(len(message))
                conn.close()
                if data == message:
                    success_count += 1
            except Exception as e:
                print(f"Erro na requisição {i}: {e}")
    finally:
        proxy.stop()
        echo.stop()

    print(f"Requisições bem-sucedidas: {success_count}/{total_requests}")
    assert success_count == total_requests, f"Taxa de sucesso abaixo de 100%: {success_count}/{total_requests}"
    print("Teste concluído com 100% de sucesso!")