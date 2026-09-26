import os
import socket
import threading
import time
import urllib.request

# 1. Criação de um ambiente de arquivos estáticos para teste
STATIC_DIR = os.path.abspath("./www_test")
os.makedirs(STATIC_DIR, exist_ok=True)
INDEX_FILE = os.path.join(STATIC_DIR, "index.html")
with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.write("<html><body><h1>Hello, HTTP/1.1!</h1></body></html>")

NOT_FOUND_FILE = os.path.join(STATIC_DIR, "404.html")
with open(NOT_FOUND_FILE, "w", encoding="utf-8") as f:
    f.write("<html><body><h1>404 Not Found</h1></body></html>")


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

            request_text = request_data.decode("utf-8", errors="ignore")
            lines = request_text.split("\r\n")
            if not lines or not lines[0]:
                break

            request_line = lines[0]
            parts = request_line.split(" ")
            if len(parts) < 2:
                response = (
                    b"HTTP/1.1 400 Bad Request\r\nContent-Length: 11\r\n\r\nBad Request"
                )
                client_socket.sendall(response)
                break

            method, path = parts[0], parts[1]
            if method != "GET":
                response = b"HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 18\r\n\r\nMethod Not Allowed"
                client_socket.sendall(response)
                break

            # Normalização e segurança de caminho (Path Traversal prevention)
            if path == "/":
                path = "/index.html"

            requested_path = os.path.abspath(
                os.path.join(STATIC_DIR, path.lstrip("/"))
            )
            if not requested_path.startswith(STATIC_DIR) or not os.path.exists(
                requested_path
            ):
                # Serve 404
                content = b"<html><body>404 Not Found</body></html>"
                response = (
                    b"HTTP/1.1 404 Not Found\r\n"
                    b"Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    b"Connection: keep-alive\r\n\r\n"
                ) + content
                client_socket.sendall(response)
                continue

            # Lê arquivo estático
            with open(requested_path, "rb") as file_to_send:
                content = file_to_send.read()

            content_type = "text/html"
            if requested_path.endswith(".css"):
                content_type = "text/css"
            elif requested_path.endswith(".js"):
                content_type = "application/javascript"

            # Verifica cabeçalho Connection
            keep_alive = True
            for line in lines:
                if line.lower().startswith("connection:"):
                    if "close" in line.lower():
                        keep_alive = False

            connection_header = (
                b"Connection: keep-alive\r\n"
                if keep_alive
                else b"Connection: close\r\n"
            )

            response = (
                b"HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}; charset=utf-8\r\n"
                f"Content-Length: {len(content)}\r\n"
                + connection_header
                + b"\r\n"
            ) + content

            client_socket.sendall(response)

            if not keep_alive:
                break
    except Exception as e:
        print(f"[Server Error] {e}")
    finally:
        client_socket.close()


def run_server(server_socket):
    while server_running:
        try:
            client_socket, addr = server_socket.accept()
            t = threading.Thread(
                target=handle_client, args=(client_socket, addr), daemon=True
            )
            t.start()
        except socket.timeout:
            continue
        except Exception:
            break


# Configuração e inicialização do servidor em porta dinâmica livre
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, SO_REUSEADDR := socket.SO_REUSEADDR, 1)
server_socket.bind(("127.0.0.1", 0))
server_socket.listen(128)
port = server_socket.getsockname()[1]
server_socket.settimeout(1.0)

server_running = True
server_thread = threading.Thread(
    target=run_server, args=(server_socket,), daemon=True
)
server_thread.start()
time.sleep(0.1)  # Aguarda subida do servidor

print(f"Servidor HTTP rodando na porta {port}")


# 3. Testes Automatizados e Concorrentes
def test_concurrent_requests():
    url = f"http://127.0.0.1:{port}/index.html"
    results = []

    def make_request():
        try:
            req = urllib.request.urlopen(url, timeout=2)
            results.append((req.status, req.read()))
        except Exception as e:
            results.append((str(e), None))

    # Dispara 20 requisições simultâneas (concorrência)
    threads = [threading.Thread(target=make_request) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Total de requisições concorrentes concluídas: {len(results)}")
    for status, data in results:
        assert status == 200, f"Falha no status: {status}"
    print("Sucesso: Todas as requisições concorrentes retornaram HTTP 200!")


def test_keep_alive():
    # Testa persistência de conexão enviando múltiplas requisições no mesmo socket TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))

    # Primeira requisição
    req1 = b"GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive\r\n\r\n"
    s.sendall(req1)
    resp1 = s.recv(4096)
    assert b"HTTP/1.1 200 OK" in resp1
    assert b"Hello, HTTP/1.1!" in resp1

    # Segunda requisição na mesma conexão TCP (Keep-Alive)
    req2 = b"GET /404.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
    s.sendall(req2)
    resp2 = s.recv(4096)
    assert b"HTTP/1.1 404 Not Found" in resp2

    s.close()
    print("Sucesso: Teste de Keep-Alive executado com múltiplas requisições na mesma conexão TCP!")


# Executa os testes
try:
    test_concurrent_requests()
    test_keep_alive()
finally:
    server_running = False
    server_socket.close()
    server_thread.join(timeout=2)
    print("Servidor encerrado com sucesso.")