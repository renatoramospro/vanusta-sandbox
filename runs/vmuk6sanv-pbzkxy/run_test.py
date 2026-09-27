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
import socket

def generate_ca():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ZeroTrust Root CA")])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        private_key.public_key()
    ).serial_number(x509.random_serial_number()).not_valid_before(
        datetime.datetime.utcnow() - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    ).add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).sign(private_key, hashes.SHA256())
    return private_key, cert

def generate_service_cert(ca_priv, ca_cert, spiffe_id):
    priv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, spiffe_id.split('/')[-1])])
    alt_name = x509.GeneralName(x509.UniformResourceIdentifier(spiffe_id))
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(ca_cert.subject).public_key(
        priv_key.public_key()
    ).serial_number(x509.random_serial_number()).not_valid_before(
        datetime.datetime.utcnow() - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=1)
    ).add_extension(x509.SubjectAlternativeName([alt_name]), critical=False).sign(ca_priv, hashes.SHA256())
    return priv_key, cert

def save_pem(path, private_key, cert):
    with open(path + "_key.pem", "wb") as f:
        f.write(private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
    with open(path + "_cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

ca_key, ca_cert = generate_ca()
save_pem("ca", ca_key, ca_cert)

pay_key, pay_cert = generate_service_cert(ca_key, ca_cert, "spiffe://cluster.local/ns/prod/sa/payment-service")
save_pem("client_authorized", pay_key, pay_cert)

mal_key, mal_cert = generate_service_cert(ca_key, ca_cert, "spiffe://cluster.local/ns/default/sa/malicious-service")
save_pem("client_unauthorized", mal_key, mal_cert)

srv_key, srv_cert = generate_service_cert(ca_key, ca_cert, "spiffe://cluster.local/ns/prod/sa/order-service")
save_pem("server", srv_key, srv_cert)

class ZeroTrustHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        client_cert_bin = self.connection.getpeercert(binary_form=True)
        if not client_cert_bin:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        client_cert = x509.load_der_x509_certificate(client_cert_bin)
        spiffe_id = None
        try:
            ext = client_cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            for name in ext.value:
                if isinstance(name.value, str) and name.value.startswith("spiffe://"):
                    spiffe_id = name.value
        except x509.ExtensionNotFound:
            pass

        allowed_identity = "spiffe://cluster.local/ns/prod/sa/payment-service"
        print(f"[PEP/PDP Server Log] Identidade SPIFFE extraida: {spiffe_id}")

        if spiffe_id != allowed_identity:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden: Unauthorized SPIFFE ID")
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Success: Zero-Trust Verified")

    def log_message(self, format, *args):
        pass

class ThreadedHTTPServer(http.server.HTTPServer):
    allow_reuse_address = True

def run():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server_cert.pem", keyfile="server_key.pem")
    context.load_verify_locations(cafile="ca_cert.pem")
    context.verify_mode = ssl.CERT_REQUIRED

    server = ThreadedHTTPServer(('127.0.0.1', 8443), ZeroTrustHandler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    return server

if __name__ == "__main__":
    server = run()
    print("=== TESTANDO ARQUITETURA ZERO-TRUST (mTLS + SPIFFE) ===")

    def test_client(prefix, name):
        print(f"\n[Cliente] Tentativa de conexao: {name}")
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="ca_cert.pem")
        ctx.load_cert_chain(certfile=f"{prefix}_cert.pem", keyfile=f"{prefix}_key.pem")
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        try:
            resp = opener.open("https://127.0.0.1:8443/")
            print(f"-> Resposta: {resp.status} ({resp.read().decode()})")
        except urllib.error.HTTPError as e:
            print(f"-> Bloqueado pelo PEP/PDP: {e.code} ({e.read().decode()})")

    test_client("client_authorized", "Payment Service (Legitimo)")
    test_client("client_unauthorized", "Malicious Service (Comprometido/Namespace Invalido)")
    server.shutdown()