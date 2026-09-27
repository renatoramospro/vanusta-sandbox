import os
import ssl
import socket
import threading
import http.server
import urllib.request
import subprocess

def generate_certs():
    """Gera certificados autoassinados de teste usando openssl do sistema com SAN adequado."""
    os.makedirs("certs", exist_ok=True)
    
    # Criar arquivo de configuração OpenSSL para SAN (Subject Alternative Name)
    openssl_cnf_content = """
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
CN = Test-Root-CA

[v3_ca]
subjectAltName = @alt_names

[server_req]
distinguished_name = server_distinguished_name
x509_extensions = v3_server
prompt = no

[server_distinguished_name]
CN = server

[v3_server]
subjectAltName = @alt_names

[alt_names]
IP.1 = 127.0.0.1
DNS.1 = localhost
"""
    cnf_path = "certs/openssl.cnf"
    with open(cnf_path, "w") as f:
        f.write(openssl_cnf_content.strip())

    # 1. CA Root
    if not os.path.exists("certs/ca.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/ca-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-x509", "-new", "-nodes", "-key", "certs/ca-key.pem",
            "-sha256", "-days", "1", "-out", "certs/ca.pem", "-config", cnf_path, "-extensions", "v3_ca"
        ], check=True)

    # 2. Server Cert com SAN IP:127.0.0.1
    if not os.path.exists("certs/server.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/server-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-new", "-key", "certs/server-key.pem", "-out", "certs/server.csr",
            "-config", cnf_path
        ], check=True)
        subprocess.run([
            "openssl", "x509", "-req", "-in", "certs/server.csr", "-CA", "certs/ca.pem",
            "-CAkey", "certs/ca-key.pem", "-CAcreateserial", "-out", "certs/server.pem",
            "-days", "1", "-sha256", "-extfile", cnf_path, "-extensions", "v3_server"
        ], check=True)

    # 3. Authorized Client (SPIFFE ID legítimo)
    if not os.path.exists("certs/client_authorized.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/client_authorized-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-new", "-key", "certs/client_authorized-key.pem", "-out", "certs/client_authorized.csr",
            "-subj", "/CN=spiffe://example.org/ns/prod/sa/payment-service"
        ], check=True)
        subprocess.run([
            "openssl", "x509", "-req", "-in", "certs/client_authorized.csr", "-CA", "certs/ca.pem",
            "-CAkey", "certs/ca-key.pem", "-CAcreateserial", "-out", "certs/client_authorized.pem",
            "-days", "1", "-sha256"
        ], check=True)

    # 4. Unauthorized Client (SPIFFE ID não autorizado ou desconhecido)
    if not os.path.exists("certs/client_unauthorized.pem"):
        subprocess.run(["openssl", "genrsa", "-out", "certs/client_unauthorized-key.pem", "2048"], check=True)
        subprocess.run([
            "openssl", "req", "-new", "-key", "certs/client_unauthorized-key.pem", "-out", "certs/client_unauthorized.csr",
            "-subj", "/CN=spiffe://example.org/ns/prod/sa/malicious-service"
        ], check=True)
        subprocess.run([
            "openssl", "x509", "-req", "-in", "certs/client_unauthorized.csr", "-CA", "certs/ca.pem",
            "-CAkey", "certs/ca-key.pem", "-CAcreateserial", "-out", "certs/client_unauthorized.pem",
            "-days", "1", "-sha256"
        ], check=True)

class ZeroTrustHandler(http.server.BaseHTTPRequestHandler):
    """PEP (Policy Enforcement Point): Intercepta requisições e valida identidade mTLS via PDP."""
    def do_GET(self):
        # Extrair certificado do cliente do contexto TLS da conexão
        client_cert = self.connection.getpeercert()
        
        if not client_cert:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Access Denied: No client certificate provided")
            return

        # PDP (Policy Decision Point): Avaliar identidade (SPIFFE ID simulado no Subject DN / CN)
        subject = client_cert.get('subject', ())
        cn = next((value for subst in subject for key, value in subst if key == 'commonName'), None)
        
        allowed_spiffe_id = "spiffe://example.org/ns/prod/sa/payment-service"
        
        if cn == allowed_spiffe_id:
            # Acesso Autorizado
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Access Granted: Zero-Trust mTLS Policy Verified")
        else:
            # Acesso Negado (Princípio Fail-Closed)
            self.send_response(403)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Access Denied by PDP: Unauthorized Identity")

    def log_message(self, format, *args):
        # Silenciar logs HTTP padrão para clareza da execução
        pass

def run_server(port=8443):
    generate_certs()
    server_address = ('127.0.0.1', port)
    httpd = http.server.HTTPServer(server_address, ZeroTrustHandler)
    
    # Configurar mTLS estrito no servidor
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="certs/server.pem", keyfile="certs/server-key.pem")
    context.load_verify_locations(cafile="certs/ca.pem")
    context.verify_mode = ssl.CERT_REQUIRED
    
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd