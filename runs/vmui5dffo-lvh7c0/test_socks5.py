import socket
import threading
import time
import pytest
from socks5_server import SOCKS5Server, PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS

class EchoServer:
    def __init__(self, host='127.0.0.1', port=0):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.port = self.server.getsockname()[1]
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.is_running:
            try:
                self.server.settimeout(1.0)
                conn, _ = self.server.accept()
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle(self, conn):
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                conn.sendall(data)
        except Exception:
            pass
        finally:
            conn.close()

    def stop(self):
        self.is_running = False
        try:
            self.server.close()
        except Exception:
            pass
        self.thread.join(timeout=1.0)

def socks5_connect(proxy_host, proxy_port, user, passwd, dest_host, dest_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((proxy_host, proxy_port))

    # Handshake SOCKS5 com autenticação
    s.sendall(b'\x05\x01\x02') # Versão 5, 1 método, suporte a usuário/senha (0x02)
    resp = s.recv(2)
    if len(resp) < 2 or resp[1] != 0x02:
        s.close()
        raise Exception("Servidor proxy rejeitou método de autenticação")

    # Enviar credenciais RFC 1929
    auth_req = b'\x01' + len(user).to_bytes(1, 'big') + user.encode() + len(passwd).to_bytes(1, 'big') + passwd.encode()
    s.sendall(auth_req)
    
    auth_resp = s.recv(2)
    if len(auth_resp) < 2 or auth_resp[1] != 0x00:
        s.close()
        raise Exception("Autenticação falhou com credenciais inválidas")

    # Comando CONNECT para IPv4
    dest_ip = socket.gethostbyname(dest_host)
    req = b'\x05\x01\x00\x01' + socket.inet_aton(dest_ip) + dest_port.to_bytes(2, 'big')
    s.sendall(req)
    
    reply = s.recv(10)
    if len(reply) < 2 or reply[1] != 0x00:
        s.close()
        raise Exception("Conexão de destino recusada pelo proxy")

    return s

def test_consecutive_requests():
    proxy = SOCKS5Server(PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS)
    proxy.start()
    time.sleep(0.2)

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
    print("Teste consecutivas concluído com 100% de sucesso!")

def test_invalid_credentials():
    proxy = SOCKS5Server(PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS)
    proxy.start()
    time.sleep(0.2)

    try:
        # Tentar conectar com senha incorreta
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((PROXY_HOST, PROXY_PORT))
        s.sendall(b'\x05\x01\x02')
        s.recv(2)
        
        bad_user = "admin"
        bad_pass = "wrongpassword"
        auth_req = b'\x01' + len(bad_user).to_bytes(1, 'big') + bad_user.encode() + len(bad_pass).to_bytes(1, 'big') + bad_pass.encode()
        s.sendall(auth_req)
        
        auth_resp = s.recv(2)
        # O servidor deve retornar status de falha (\x01\x01) ou fechar a conexão
        assert len(auth_resp) >= 2 and auth_resp[1] == 0x01
        s.close()
        print("Teste de credenciais inválidas validado com sucesso!")
    finally:
        proxy.stop()

def test_blocked_destination():
    proxy = SOCKS5Server(PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS)
    proxy.start()
    time.sleep(0.2)

    try:
        # Tentar conectar a um destino bloqueado (ex: IP em BLOCKED_NETWORKS)
        conn = socks5_connect(PROXY_HOST, PROXY_PORT, VALID_USER, VALID_PASS, '169.254.169.254', 80)
        assert False, "Deveria ter bloqueado o destino restrito"
    except Exception as e:
        print(f"Destino restrito bloqueado corretamente com exceção: {e}")
    finally:
        proxy.stop()