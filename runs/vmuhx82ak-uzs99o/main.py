import os
import socket
import threading
import time
import urllib.request
from urllib.parse import unquote_to_bytes

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

            # Tratamento tolerante a quebras de linha (\r\n ou apenas \n)
            request_line = request_data.split(b"\n")[0].rstrip(b"\r")
            parts = request_line.split(b" ")
            if len(parts) < 2:
                break

            method, raw_path = parts[0], parts[1]
            if method != b"GET":
                response = (
                    b"HTTP/1.1 405 Method Not Allowed\r\n"
                    b"Content-Length: 0\r\n"
                    b"Connection: close\r\n\r\n"
                )
                client_socket.sendall(response)
                break

            # Decodificação segura de URI
            decoded_path = unquote_to_bytes(raw_path).decode("utf-8", errors="ignore")
            if decoded_path == "/":
                decoded_path = "/index.html"

            # Resolução de caminho e prevenção contra Path Traversal
            requested_path = os.path.abspath(os.path.join(STATIC_DIR, decoded_path.lstrip("/")))
            
            try:
                common = os.path.commonpath([STATIC_DIR, requested_path])
                is_safe = (common == STATIC_DIR)
            except ValueError:
                is_safe = False

            if not is_safe or not os.path.exists(requested_path) or os.path.isdir(requested_path):
                not_found_path = os.path.join(STATIC_DIR, "404.html")
                if os.path.exists(not_found_path):
                    with open(not_found_path, "rb") as f:
                        content = f.read()
                    response = (
                        b"HTTP/1.1 404 Not Found\r\n"
                        b"Content-Type: text/html; charset=utf-8\r\n"
                        + f"Content-Length: {len(content)}\r\n".encode("utf-8")
                        + b"Connection: keep-alive\r\n\r\n"
                    ) + content
                else:
                    response = (
                        b"HTTP/1.1 404 Not Found\r\n"
                        b"Content-Length: 0\r\n"
                        b"Connection: keep-alive\r\n\r\n"
                    )
                client_socket.sendall(response)
                continue

            # Servir arquivo estático com sucesso
            with open(requested_path, "rb") as f:
                content = f.read()

            response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/html; charset=utf-8\r\n"
                + f"Content-Length: {len(content)}\r\n".encode("utf-8")
                + b"Connection: keep-alive\r\n\r\n"
            ) + content

            client_socket.sendall(response)

            # Verifica se o cliente solicitou fechar a conexão
            if b"Connection: close" in request_data:
                break

    except Exception:
        pass
    finally:
        client_socket.close()


def run_server(server_socket):
    global server_running
    server_socket.settimeout(1.0)
    while server_running:
        try:
            client_socket, addr = server_socket.accept()
            t = threading.Thread(target=handle_client, args=(client_socket, addr))
            t.daemon = True
            t.start()
        except socket.timeout:
            continue
        except Exception:
            break


# 3. Inicialização do Servidor em Porta Dinâmica
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("127.0.0.1", 0))
server_socket.listen(128)
port = server_socket.getsockname()[1]

server_running = True
server_thread = threading.Thread(target=run_server, args=(server_socket,))
server_thread.daemon = True
server_thread.start()

time.sleep(0.2)  # Aguarda subida do servidor


# 4. Testes Automatizados Concorrentes e de Persistência (Keep-Alive)
def test_concurrent_requests():
    url = f"http://127.0.0.1:{port}/index.html"
    num_requests = 20
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
    ), f"Nem todas as requisições retornaram 200: {results}"
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