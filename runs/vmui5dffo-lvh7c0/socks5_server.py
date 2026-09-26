import socket
import threading
import select
import sys
import os

# Configurações seguras e dinâmicas (com fallbacks seguros)
PROXY_HOST = os.getenv('PROXY_HOST', '127.0.0.1')
PROXY_PORT = int(os.getenv('PROXY_PORT', 1080))
VALID_USER = os.getenv('PROXY_USER', 'admin')
VALID_PASS = os.getenv('PROXY_PASS', 'secret123')

# Lista de redes/destinos proibidos para mitigar SSRF / Open Proxy em ambientes de produção
BLOCKED_NETWORKS = ['169.254.169.254'] # Exemplo: metadados de nuvem

class SOCKS5Server:
    def __init__(self, host=PROXY_HOST, port=PROXY_PORT, user=VALID_USER, passwd=VALID_PASS, allowed_ports=None):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.allowed_ports = allowed_ports # None significa todas as portas permitidas (exceto restrições)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False
        self.server_thread = None

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(128)
        self.server_socket.settimeout(1.0) # Permite encerrar o accept gracefully
        self.is_running = True
        self.server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.server_thread.start()

    def stop(self):
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        try:
            self.server_socket.close()
        except Exception:
            pass

    def _accept_loop(self):
        while self.is_running:
            try:
                client_sock, addr = self.server_socket.accept()
                client_sock.settimeout(10.0) # Timeout defensivo contra slowloris / conexões travadas
                client_thread = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
            except Exception:
                if not self.is_running:
                    break
                continue

    def _handle_client(self, client_sock):
        try:
            # 1. Negociação de Métodos
            header = client_sock.recv(2)
            if len(header) < 2:
                client_sock.close()
                return
            
            ver, nmethods = header[0], header[1]
            if ver != 0x05:
                client_sock.close()
                return

            methods = client_sock.recv(nmethods)
            if len(methods) < nmethods:
                client_sock.close()
                return

            # Exigir autenticação por usuário/senha (0x02)
            if b'\x02' in methods:
                client_sock.sendall(b'\x05\x02')
                if not self._authenticate(client_sock):
                    client_sock.close()
                    return
            else:
                # Nenhum método de autenticação suportado comum
                client_sock.sendall(b'\x05\xff')
                client_sock.close()
                return

            # 2. Requisição de Comando (RFC 1928)
            req = client_sock.recv(4)
            if len(req) < 4:
                client_sock.close()
                return

            ver, cmd, rsv, atyp = req[0], req[1], req[2], req[3]
            if ver != 0x05 or cmd != 0x01: # Apenas CONNECT (0x01) é suportado nesta implementação TCP
                client_sock.sendall(b'\x05\x07\x00\x01\x00\x00\x00\x00\x00\x00') # Command not supported
                client_sock.close()
                return

            # Ler endereço de destino com base no tipo (atyp)
            if atyp == 0x01: # IPv4
                addr_bytes = client_sock.recv(4)
                if len(addr_bytes) < 4:
                    client_sock.close()
                    return
                dest_addr = socket.inet_ntoa(addr_bytes)
            elif atyp == 0x03: # Domínio
                addr_len_byte = client_sock.recv(1)
                if not addr_len_byte:
                    client_sock.close()
                    return
                addr_len = addr_len_byte[0]
                addr_bytes = client_sock.recv(addr_len)
                if len(addr_bytes) < addr_len:
                    client_sock.close()
                    return
                dest_addr = addr_bytes.decode('utf-8', errors='ignore')
            elif atyp == 0x04: # IPv6
                addr_bytes = client_sock.recv(16)
                if len(addr_bytes) < 16:
                    client_sock.close()
                    return
                dest_addr = socket.inet_ntop(socket.AF_INET6, addr_bytes)
            else:
                client_sock.sendall(b'\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00') # Address type not supported
                client_sock.close()
                return

            port_bytes = client_sock.recv(2)
            if len(port_bytes) < 2:
                client_sock.close()
                return
            dest_port = int.from_bytes(port_bytes, 'big')

            # Validação de segurança de destino (Proteção contra SSRF e IPs bloqueados)
            if dest_addr in BLOCKED_NETWORKS:
                client_sock.sendall(b'\x05\x02\x00\x01\x00\x00\x00\x00\x00\x00') # Connection not allowed
                client_sock.close()
                return

            if self.allowed_ports and dest_port not in self.allowed_ports:
                client_sock.sendall(b'\x05\x02\x00\x01\x00\x00\x00\x00\x00\x00')
                client_sock.close()
                return

            # Conectar ao destino real
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(10.0)
            try:
                remote_sock.connect((dest_addr, dest_port))
            except Exception:
                client_sock.sendall(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00') # Host unreachable
                client_sock.close()
                return

            # Responder sucesso ao cliente SOCKS5
            bind_addr = remote_sock.getsockname()
            bind_ip = socket.inet_aton(bind_addr[0])
            bind_port = bind_addr[1].to_bytes(2, 'big')
            client_sock.sendall(b'\x05\x00\x00\x01' + bind_ip + bind_port)

            # 3. Túnel Bidirecional TCP
            self._relay_traffic(client_sock, remote_sock)

        except Exception:
            try:
                client_sock.close()
            except Exception:
                pass

    def _authenticate(self, client_sock):
        try:
            auth_header = client_sock.recv(2)
            if len(auth_header) < 2:
                return False
            sub_ver, ulen = auth_header[0], auth_header[1]
            if sub_ver != 0x01:
                return False

            username = client_sock.recv(ulen).decode('utf-8', errors='ignore')
            
            plen_byte = client_sock.recv(1)
            if not plen_byte:
                return False
            plen = plen_byte[0]
            
            password = client_sock.recv(plen).decode('utf-8', errors='ignore')

            if username == self.user and password == self.passwd:
                client_sock.sendall(b'\x01\x00') # Sucesso na autenticação
                return True
            else:
                client_sock.sendall(b'\x01\x01') # Falha na autenticação
                return False
        except Exception:
            return False

    def _relay_traffic(self, client_sock, remote_sock):
        sockets = [client_sock, remote_sock]
        client_sock.settimeout(None)
        remote_sock.settimeout(None)

        while True:
            rlist, _, _ = select.select(sockets, [], [], 300) # Timeout de ociosidade de 5 minutes
            if not rlist:
                break
            
            for sock in rlist:
                other = remote_sock if sock is client_sock else client_sock
                data = sock.recv(4096)
                if not data:
                    break
                other.sendall(data)
            else:
                continue
            break

        try:
            client_sock.close()
        except Exception:
            pass
        try:
            remote_sock.close()
        except Exception:
            pass