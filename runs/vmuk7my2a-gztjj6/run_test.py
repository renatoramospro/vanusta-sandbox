import urllib.request
import urllib.error
import ssl
import pytest
from experiment_zerotrust import run_server

@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    server = run_server(8443)
    yield
    server.server_close()

def make_request(client_type):
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="certs/ca.pem")
    ctx.load_cert_chain(
        certfile=f"certs/{client_type}.pem",
        keyfile=f"certs/{client_type}-key.pem"
    )
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    try:
        resp = opener.open("https://127.0.0.1:8443/")
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def test_authorized_client_access():
    status, body = make_request("client_authorized")
    assert status == 200
    assert "Access Granted" in body
    print(f"[TESTE APROVADO] Cliente legítimo autenticado com sucesso: {body}")

def test_unauthorized_client_blocked():
    status, body = make_request("client_unauthorized")
    assert status == 403
    assert "Access Denied by PDP" in body
    print(f"[TESTE APROVADO] Cliente malicioso bloqueado corretamente pelo PEP/PDP: {body}")