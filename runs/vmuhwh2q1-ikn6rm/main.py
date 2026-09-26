import os
import socket
import threading
import time
import urllib.request

# 1. Criação de um ambiente de arquivos estáticos para teste
STATIC_DIR = os.path.abspath("./www_test")
os.makedirs(STATIC_DIR, exist_ok=True)
INDEX_FILE = os.path.join(STATIC_DIR, "index.html")
with open(INDEX_FILE, "wb") as f:
    f.write(b"<html><body><h1>Hello, HTTP/1.1!</h1></body></html>")

NOT_FOUND_FILE = os.path.join(STATIC_DIR, "404.html")
with open(NOT_FOUND_FILE, "wb") as f:
    f.write(b"<html><body><h1>404 Not Found</h1></body></html>")


# 2. Implementação do Servidor HTTP/1.1 com Sockets TCP Puros e Keep-Alive
def handle_client(client_socket, address):
    client_socket.settimeout(2.0)  # Timeout de ociosidade para Keep-Alive
    try:
        while True:
            try:
                request_data = client_socket.recv(4096)
            except socket.timeout:
                break  # Encerra conexão ociosa

            if not request_data:
                break

            request_line = request_data.split(b"\r\n")[0]
            parts = request_line.split(b" ")
            if len(parts) < 2:
                break

            method, path = parts[0], parts[1]
            if method != b"GET":
                response = (
                    b"HTTP/1.1 405 Method Not Allowed\r\n"
                    b"Content-Length: 0\r\n"
                    b"Connection: close\r\n\r\n"
                )
                client_socket.sendall(response)
                break

            # Normalização e resolução segura de caminhos contra Path Traversal
            path_str = path.decode("utf-8")
            if path_str == "/":
                path_str = "/index.html"

            requested_path = os.path.realpath(
                os.path.join(STATIC_DIR, path_str.lstrip("/"))
            )
            real_base = os.path.realpath(STATIC_DIR)

            # Verifica se o caminho está estritamente dentro da raiz
            if (
                os.path.commonpath([requested_path, real_base]) != real_base
                or not os.path.exists(requested_path)
                or os.path.isdir(requested_path)
            ):
                not_found_path = os.path.join(STATIC_DIR, "404.html")
                with open(not_found_path, "rb") as f:
                    content = f.read()
                response = (
                    b"HTTP/1.1 404 Not Found\r\n"
                    b"Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(content)}\r\n".encode("utf-8")
                    + b"Connection: keep-alive\r\n\r\n"
                    + content
                )
                client_socket.sendall(response)
                continue

            with open(requested_path, "rb") as f:
                content = f.read()

            # Checa cabeçalho de conexão para Keep-Alive ou Close
            connection_header = b"keep-alive"
            if b"Connection: close" in request_data:
                connection_header = b"close"

            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(content)}\r\n".encode("utf-8")
                + f"Connection: {connection_header.decode('utf-8')}\r\n\r\n".encode(
                    "utf-8"
                )
                + content
            )
            client_socket.sendall(response)

            if connection_header == b"close":
                break

    except Exception as e:
        print(f"Erro no cliente {address}: {e}")
    finally:
        client_socket.close()


def run_server(server_socket):
    global server_running
    while server_running:
        try:
            server_socket.settimeout(1.0)
            client_socket, address = server_socket.accept()
            t = threading.Thread(
                target=handle_client, args=(client_socket, address)
            )
            t.daemon = True
            t.start()
        except socket.timeout:
            continue
        except Exception:
            break


# Inicialização do Servidor TCP Puro
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("127.0.0.1", 0))
port = server_socket.getsockname()[1]
server_socket.listen(128)

server_running = True
server_thread = threading.Thread(target=run_server, args=(server_socket,))
server_thread.daemon = True
server_thread.start()

print(f"Servidor HTTP/1.1 ouvindo na porta {port}...")


# 3. Testes Automatizados Concorrentes e de Persistência (Keep-Alive)
def test_concurrent_requests():
    url = f"http://127.0.0.1:{port}/index.html"
    num_requests = 10
    results = []

    def fetch():
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                results.append(resp.status)
        except Exception as e:
            results.append(e)

    threads = [threading.Thread(target=fetch) for _ in range(num_requests)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Resultados das requisições concorrentes: {results}")
    assert all(
        status == 200 for status in results
    ), fNem todas as requisições retornaram 200: {results}"
    print("Sucesso: Todas as requisições concorrentes retornaram HTTP 200!")


def test_keep_alive():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))

    # Primeira requisição mantendo conexão aberta
    req1 = b"GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n"
    s.sendall(req1)
    resp1 = s.recv(4096)
    assert b"HTTP/1.1 200 OK" in resp1
    assert b"Hello, HTTP/1.1!" in resp1

    # Segunda requisição na mesma conexão TCP (Keep-Alive ativo)
    req2 = b"GET /404.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
    s.sendall(req2)
    resp2 = s.recv(4096)
    assert b"HTTP/1.1 404 Not Found" in resp2

    s.close()
    print("Sucesso: Teste de Keep-Alive executado com múltiplas requisições na mesma conexão TCP!")


# Executa os testes e encerra o servidor de forma limpa
try:
    test_concurrent_requests()
    test_keep_alive()
finally:
    server_running = False
    server_socket.close()
    server_thread.join(timeout=2)
    print("Servidor encerrado com sucesso.")