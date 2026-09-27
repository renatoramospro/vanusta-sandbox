import os
import ssl
import http.server
import threading
import urllib.request
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

# --- 1. Infraestrutura de Criptografia (Simulação SPIFFE / CA) ---

def generate_ca():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "ZeroTrust Root CA"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow() - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(private_key, hashes.SHA256())
    return private_key, cert

def generate_service_cert(ca_priv, ca_cert, spiffe_id):
    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, spiffe_id.split('/')[-1]),
    ])
    
    # Adicionando SPIFFE ID no SAN (Subject Alternative Name)
    alt_name = x509.GeneralName(x509.UniformResourceIdentifier(spiffe_id))
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        priv_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow() - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    ).add_extension(
        x509.SubjectAlternativeName([alt_name]), critical=False,
    ).sign(ca_priv, hashes.SHA256())
    
    return priv_key, cert

def save_pem(path, private_key, cert):
    with open(path + "_key.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(path + "_cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

# Gerando os arquivos de teste
ca_key, ca_cert = generate_ca()
save_pem("ca", ca_key, ca_cert)

# Cliente 1: Autorizado (Payment Service)
pay_key, pay_cert = generate_service_cert(ca_key, ca_cert, "spiffe://cluster.local/ns/prod/sa/payment-service")
save_pem("client_authorized", pay_key, pay_cert)

# Cliente 2: Não Autorizado (Malicious Service)
mal_key, mal_cert = generate_service_cert(ca_key, ca_cert, "spiffe://cluster.local/ns/default/sa/malicious-service")
save_pem("client_unauthorized", mal_key, mal_cert)

# Servidor (Order Service)
srv_key, srv_cert = generate_service_cert(ca_key, ca_cert, "spiffe://cluster.local/ns/prod/sa/order-service")
save_pem("server", srv_key, srv_cert)


# --- 2. Simulação do PEP / PDP e Servidor Zero-Trust ---

class ZeroTrustHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Ponto de Aplicação de Política (PEP): Extração do Certificado do Cliente
        client_cert_bin = self.connection.getpeercert(binary_form=True)
        if not client_cert_bin:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized: No client certificate provided (mTLS required)")
            return

        # 2. Análise do SPIFFE ID no SAN
        client_cert = x509.load_der_x509_certificate(client_cert_bin)
        spiffe_id = None
        try:
            ext = client_cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            for name in ext.value:
                if isinstance(name.value, str) and name.value.startswith("spiffe://"):
                    spiffe_id = name.value
        except x509.ExtensionNotFound:
            pass

        # 3. Motor de Decisão de Política (PDP): RBAC/ABAC baseado em Identidade
        # Política: Apenas spiffe://cluster.local/ns/prod/sa/payment-service pode acessar /orders
        allowed_identity = "spiffe://cluster.local/ns/prod/sa/payment-service"
        
        print(f"[PEP/PDP] Requisição recebida de Identidade SPIFFE: {spiffe_id}")

        if spiffe_id != allowed_identity:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(f"Forbidden: Identity {spiffe_id} is not authorized to access this resource.".encode())
            return

        # Acesso Concedido
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Success: Order service accessed securely via Zero-Trust mTLS!")

    def log_message(self, format, *args):
        # Silenciar logs padrão do servidor HTTP para manter a saída limpa
        return

def run_server(stop_event):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server_cert.pem", keyfile="server_key.pem")
    context.load_verify_locations(cafile="ca_cert.pem")
    # Forçar mTLS estrito (exigir e verificar certificado do cliente)
    context.verify_mode = ssl.CERT_REQUIRED

    server = http.server.HTTPServer(('127.0.0.1', 8443), ZeroTrustHandler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    
    while not stop_event.is_set():
        server.handle_request()
    server.server_close()

# --- 3. Execução dos Cenários de Teste (Validação de Ameaças) ---

if __name__ == "__main__":
    stop_event = threading.Event()
    server_thread = threading.Thread(target=run_server, args=(stop_event,))
    server_thread.start()

    print("=== INICIANDO VALIDAÇÃO DO MODELO DE AMEAÇA ZERO-TRUST ===")

    def make_request(cert_prefix, desc):
        print(f"\n[Cenário] Testando requisição com: {desc}")
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="ca_cert.pem")
        context.load_cert_chain(certfile=f"{cert_prefix}_cert.pem", keyfile=f"{cert_prefix}_key.pem")
        
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
        try:
            response = opener.open("https://127.0.0.1:8443/orders")
            print(f"-> Resultado HTTP: {response.status} - {response.read().decode()}")
        except urllib.error.HTTPError as e:
            print(f"-> Resultado HTTP (Bloqueado): {e.code} - {e.read().decode()}")

    # Cenário 1: Cliente legítimo com identidade autorizada
    make_request("client_authorized", "Payment Service Legítimo")

    # Cenário 2: Cliente comprometido com identidade não autorizada (Ataque de Impersonação/Serviço Malicioso)
    make_request("client_unauthorized", "Serviço Malicioso (Namespace diferente)")

    # Encerrar servidor
    stop_event.set(>