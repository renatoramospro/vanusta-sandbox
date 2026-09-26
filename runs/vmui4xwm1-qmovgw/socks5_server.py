import socket
import threading
import select
import sys

# Configurações do Servidor Proxy
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1080
VALID_USER = 'admin'
VALID_PASS = 'secret123'

class SOCKS5Server:
    def __init__(self, host=PROXY_HOST, port=PROXY_PORT):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False
        self.server_thread = None

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(128)
        self.is_running = True
        self.server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.server_thread.start()

    def stop(self):
        self.is_running = False
        self.server_socket.close()
        if self.server_thread:
            self.server_thread.join(timeout=1)

    def _accept_loop(self):
        while self.is_running:
            try:
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, client_socket):
        try:
            # 1. Negociação de métodos (RFC 1928)
            header = client_socket.recv(2)
            if len(header) < 2:
                client_socket.close()
                return

            ver, nmethods = header[0], header[1]
            if ver != 0x05:
                client_socket.close()
                return

            methods = client_socket.recv(nmethods)
            
            # Requer autenticação por usuário/senha (0x02)
            if 0x02 not in methods:
                client_socket.sendall(b'\x05\xff')
                client_socket.close()
                return

            # Responde aceitando o método 0x02
            client_socket.sendall(b'\x05\x02')

            # 2. Autenticação por Usuário/Senha (RFC 1929)
            auth_header = client_socket.recv(2)
            if len(auth_header) < 2 or auth_header[0] != 0x01:
                client_socket.close()
                return

            ulen = auth_header[1]
            username = client_socket.recv(ulen).decode('utf-8', errors='ignore')
            
            plen_bytes = client_socket.recv(1)
            if not plen_bytes:
                client_socket.close()
                return
            plen = plen_bytes[0]
            password = client_socket.recv(plen).decode('utf-8', errors='ignore')

            if username == VALID_USER and password == VALID_PASS:
                # Sucesso na autenticação
                client_socket.sendall(b'\x01\x00')
            else:
                # Falha na autenticação
                client_socket.sendall(b'\x01\x01')
                client_socket.close()
                return

            # 3. Requisição de Conexão (RFC 1928)
            req = client_socket.recv(4)
            if len(req) < 4 or req[0] != 0x05 or req[1] != 0x01:
                client_socket.close()
                return

            atyp = req[3]
            if atyp == 0x01:  # IPv4
                addr = socket.inet_ntoa(client_socket.recv(4))
            elif atyp == 0x03:  # Domínio
                addr_len = client_socket.recv(1)[0]
                addr = client_socket.recv(addr_len).decode('utf-8', errors='ignore')
            elif atyp == 0x04:  # IPv6
                addr = socket.inet_ntop(socket.AF_INET6, client_socket.recv(16))
            else:
                client_socket.close()
                return

            port_bytes = client_socket.recv(2)
            port = int.from_bytes(port_bytes, 'big')

            # 4. Estabelecer conexão com o destino final
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                remote_socket.connect((addr, port))
            except Exception:
                # Falha ao conectar no destino (REP = 0x04 - Host unreachable)
                client_socket.sendall(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00')
                client_socket.close()
                return

            # Sucesso no estabelecimento do túnel (REP = 0x00)
            bind_addr = remote_socket.getsockname()
            reply = b'\x05\x00\x00\x01' + socket.inet_aton(bind_addr[0]) + bind_addr[1].to_bytes(2, 'big')
            client_socket.sendall(reply)

            # 5. Túnel bidirecional TCP
            self._tunnel(client_socket, remote_socket)

        except Exception:
            try:
                client_socket.close()
            except Exception:
                pass

    def _tunnel(self, client, remote):
        sockets = [client, remote]
        try:
            while True:
                readable, _, _ = select.select(sockets, [], [], 60)
                if not readable:
                    break
                for s in readable:
                    data = s.recv(4096)
                    if not data:
                        return
                    if s is client:
                        remote.sendall(data)
                    else:
                        client.sendall(data)
        except Exception:
            pass
        finally:
            client.close()
            remote.close()