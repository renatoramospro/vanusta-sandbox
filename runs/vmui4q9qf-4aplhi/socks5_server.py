import socket
import threading
import sys
import time

# Configurações do Servidor Proxy
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1080
VALID_USER = 'admin'
VALID_PASS = 'secret123'

def handle_client(client_socket):
    try:
        # 1. Negociação de métodos
        header = client_socket.recv(2)
        if len(header) < 2:
            client_socket.close()
            return
        
        ver, nmethods = header[0], header[1]
        methods = client_socket.recv(nmethods)
        
        if ver != 0x05:
            client_socket.close()
            return

        # Exigir autenticação por usuário/senha (0x02)
        if 0x02 not in methods:
            client_socket.sendall(b'\x05\xff') # Nenhum método aceitável
            client_socket.close()
            return

        # Informa ao cliente que escolhemos autenticação por usuário/senha
        client_socket.sendall(b'\x05\x02')

        # 2. Sub-negociação de Autenticação (RFC 1929)
        auth_header = client_socket.recv(2)
        if len(auth_header) < 2:
            client_socket.close()
            return

        sub_ver, ulen = auth_header[0], auth_header[1]
        username = client_socket.recv(ulen).decode('utf-8', errors='ignore')
        
        plen_data = client_socket.recv(1)
        if not plen_data:
            client_socket.close()
            return
        plen = plen_data[0]
        password = client_socket.recv(plen).decode('utf-8', errors='ignore')

        # Validação de credenciais
        if username == VALID_USER and password == VALID_PASS:
            # Sucesso na autenticação
            client_socket.sendall(bytes([sub_ver, 0x00]))
        else:
            # Falha na autenticação
            client_socket.sendall(bytes([sub_ver, 0x01]))
            client_socket.close()
            return

        # 3. Requisição de Comando (CONNECT)
        req = client_socket.recv(4)
        if len(req) < 4:
            client_socket.close()
            return

        ver, cmd, rsv, atyp = req[0], req[1], req[2], req[3]
        if cmd != 0x01: # Apenas suporte a CONNECT
            client_socket.close()
            return

        # Ler endereço de destino
        if atyp == 0x01: # IPv4
            addr_bytes = client_socket.recv(4)
            dest_addr = socket.inet_ntoa(addr_bytes)
        elif atyp == 0x03: # Domínio
            addr_len = client_socket.recv(1)[0]
            dest_addr = client_socket.recv(addr_len).decode('utf-8')
        elif atyp == 0x04: # IPv6
            addr_bytes = client_socket.recv(16)
            dest_addr = socket.inet_ntop(socket.AF_INET6, addr_bytes)
        else:
            client_socket.close()
            return

        port_bytes = client_socket.recv(2)
        dest_port = int.from_bytes(port_bytes, 'big')

        # Conectar ao destino final
        try:
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((dest_addr, dest_port))
            bind_addr = remote_socket.getsockname()
        except Exception as e:
            # Enviar falha de conexão (Host unreachable / Connection refused)
            client_socket.sendall(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00')
            client_socket.close()
            return

        # Responder sucesso ao cliente
        # VER | REP (0x00=sucesso) | RSV | ATYP (0x01=IPv4) | BND.ADDR | BND.PORT
        reply = b'\x05\x00\x00\x01' + socket.inet_aton('0.0.0.0') + (0).to_bytes(2, 'big')
        client_socket.sendall(reply)

        # 4. Túnel TCP Bidirecional
        def forward(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
                except Exception:
                    pass
                finally:
                    try:
                        source.shutdown(socket.SHUT_RD)
                    except:
                        pass
                    try:
                        destination.shutdown(socket.SHUT_WR)
                    except:
                        pass

        t1 = threading.Thread(target=forward, args=(client_socket, remote_socket))
        t2 = threading.Thread(target=forward, args=(remote_socket, client_socket))
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()

    except Exception as e:
        client_socket.close()

class SOCKS5Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_running = False

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        self.is_running = True
        while self.is_running:
            try:
                client_socket, _ = self.server_socket.accept()
                t = threading.Thread(target=handle_client, args=(client_socket,))
                t.daemon = True
                t.start()
            except Exception:
                break

    def stop(self):
        self.is_running = False
        self.server_socket.close()

if __name__ == '__main__':
    server = SOCKS5Server(PROXY_HOST, PROXY_PORT)
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    print(f"Servidor SOCKS5 rodando em {PROXY_HOST}:{PROXY_PORT}")