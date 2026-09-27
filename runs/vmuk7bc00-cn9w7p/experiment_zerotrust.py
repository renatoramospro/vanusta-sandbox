import os
import ssl
import socket
import threading
import http.server
import urllib.request
import subprocess

def generate_certs():
    """Gera certificados autoassinados de teste usando openssl do sistema."""
    os.makedirs("certs", exist_ok=True)
    
    # 1. CA Root
    if not os.path.exists("certs/ca.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/ca-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-x509", "-new", "-nodes", "-key", "certs/ca-key.pem",
            "-sha256", "-days", "1", "-out", "certs/ca.pem", "-subj", "/CN=Test-Root-CA"
        ], check=True)

    # 2. Server Cert
    if not os.path.exists("certs/server.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/server-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-new", "-key", "certs/server-key.pem", "-out", "certs/server.csr",
            "-subj", "/CN=server"
        ], check=True)
        subprocess.run([
            "openssl", "x509", "-req", "-in", "certs/server.csr", "-CA", "certs/ca.pem",
            "-CAkey", "certs/ca-key.pem", "-CAcreateserial", "-out", "certs/server.pem",
            "-days", "1", "-sha256"
        ], check=True)

    # 3. Authorized Client (SPIFFE ID legítimo)
    if not os.path.exists("certs/client_authorized.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/client_authorized-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-new", "-key", "certs/client_authorized-key.pem", "-out", "certs/client_authorized.csr",
            "-subj", "/CN=payment-service"
        ], check=True)
        subprocess.run([
            "openssl", "x509", "-req", "-in", "certs/client_authorized.csr", "-CA", "certs/ca.pem",
            "-CAkey", "certs/ca-key.pem", "-CAcreateserial", "-out", "certs/client_authorized.pem",
            "-days", "1", "-sha256"
        ], check=True)

    # 4. Unauthorized Client (SPIFFE ID não autorizado)
    if not os.path.exists("certs/client_unauthorized.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/client_unauthorized-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-new", "-key", "certs/client_unauthorized-key.pem", "-out", "certs/client_unauthorized.csr",
            "-subj", "/CN=malicious-service"
        ], check=True)
        subprocess.run([
            "openssl", "x509", "-req", "-in", "certs/client_unauthorized.csr", "-CA", "certs/ca.pem",
            "-CAkey", "certs/ca-key.pem", "-CAcreateserial", "-out", "certs/client_unauthorized.pem",
            "-days", "1", "-sha256"
        ], check=True)

class ZeroTrustHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # PEP (Policy Enforcement Point): Extrai certificado do cliente da conexão TLS ativa
        peertree = self.connection.getpeercert()
        if not peertree:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Access Denied: No Client Certificate Provided")
            return

        # Extrai identidade (SPIFFE ID simulado via Common Name)
        subject = dict(x[0] for x in peertree.get('subject', ()))
        client_identity = subject.get('commonName', '')

        # PDP (Policy Decision Point): Avalia se a identidade é permitida
        authorized_identities = ["payment-service"]
        if client_identity in authorized_identities:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"Access Granted to {client_identity}".encode())
        else:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(f"Access Denied by PDP: Identity '{client_identity}' not authorized".encode())

    def log_message(self, format, *args):
        # Silencia logs HTTP padrão no stdout para limpeza dos testes
        pass

def run_server(port=8443):
    generate_certs()
    server_address = ('127.0.0.1', port)
    httpd = http.server.HTTPServer(server_address, ZeroTrustHandler)
    
    # Configura contexto SSL estrito com mTLS obrigatório (CERT_REQUIRED)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="certs/server.pem", keyfile="certs/server-key.pem")
    context.load_verify_locations(cafile="certs/ca.pem")
    context.verify_mode = ssl.CERT_REQUIRED
    
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd