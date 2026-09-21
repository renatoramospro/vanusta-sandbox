import time
import hmac
import hashlib
import uuid

# Configurações de Segurança e Performance
NONCE_TTL_SECONDS = 2.0
MAX_LATENCY_SECONDS = 2.0

class GameServer:
    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key
        self.active_nonces = {} # nonce -> timestamp de criação

    def generate_nonce(self) -> str:
        """Gera um nonce criptografado/único com TTL estrito."""
        nonce = uuid.uuid4().hex
        self.active_nonces[nonce] = time.time()
        return nonce

    def verify_attestation(self, nonce: str, client_token: str, signature: str, arrival_time: float) -> bool:
        """
        Valida a atestação remota enviada pelo cliente.
        Verifica:
        1. Existência e validade temporal do nonce (frescura / TTL < 2s).
        2. Integridade criptográfica do token assinado pelo enclave do hardware.
        """
        # Verifica se o nonce existe
        if nonce not in self.active_nonces:
            return False

        # Verifica o TTL do nonce (Prevenção contra Replay e atrasos)
        creation_time = self.active_nonces.pop(nonce) # Nonce é de uso único (consume-once)
        elapsed_time = arrival_time - creation_time

        if elapsed_time > NONCE_TTL_SECONDS:
            return False # Nonce expirado

        # Validação criptográfica do token usando HMAC (simulando chave assimétrica do OS)
        expected_signature = hmac.new(
            self.secret_key,
            f"{nonce}:{client_token}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature):
            return False

        return True

class MobileClient:
    def __init__(self, client_id: str, is_tampered: bool = False):
        self.client_id = client_id
        self.is_tampered = is_tampered

    def request_attestation_token(self, nonce: str, secret_key: bytes) -> tuple:
        """
        Simula a API nativa da plataforma (Google Play Integrity / Apple App Attest).
        O binário adulterado é detectado pelo enclave e resulta em um veredito inválido ou assinatura incorreta.
        """
        token = f"token_payload_{self.client_id}"
        
        if self.is_tampered:
            # Cliente adulterado produz um token corrompido ou assinatura inválida
            fake_key = b"wrong_key_simulation"
            signature = hmac.new(
                fake_key,
                f"{nonce}:{token}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        else:
            # Cliente legítimo assina corretamente usando a raiz de confiança do hardware
            signature = hmac.new(
                secret_key,
                f"{nonce}:{token}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

        return token, signature

# --- Testes Automatizados de Validação ---
def run_tests():
    server_secret = b"hardware_root_of_trust_secret"
    server = GameServer(server_secret)

    print("=== Iniciando Testes de Atestação Remota ===")

    # Teste 1: Cliente Legítimo (Deve passar com latência < 2s)
    start_time = time.time()
    nonce = server.generate_nonce()
    
    client_legit = MobileClient(client_id="user_1001", is_tampered=False)
    token, signature = client_legit.request_attestation_token(nonce, server_secret)
    
    arrival_time = time.time()
    latency = arrival_time - start_time

    assert latency < MAX_LATENCY_SECONDS, f"Latência excedida: {latency}s"
    
    success = server.verify_attestation(nonce, token, signature, arrival_time)
    assert success is True, "Cliente legítimo foi rejeitado incorretamente (falso positivo)!"
    print(f"[SUCESSO] Cliente legítimo validado em {latency:.4f}s (Abaixo do limite de 2s).")

    # Teste 2: Cliente Adulterado (Deve ser rejeitado com precisão)
    nonce_tampered = server.generate_nonce()
    client_hacker = MobileClient(client_id="hacker_666", is_tampered=True)
    hacker_token, hacker_signature = client_hacker.request_attestation_token(nonce_tampered, server_secret)
    
    success_hacker = server.verify_attestation(nonce_tampered, hacker_token, hacker_signature, time.time())
    assert success_hacker is False, "Falha de segurança: Binário adulterado foi aceito!"
    print("[SUCESSO] Cliente adulterado detectado e rejeitado com sucesso.")

    # Teste 3: Ataque de Repetição / Nonce Expirado (Replay Attack Protection)
    nonce_replay = server.generate_nonce()
    time.sleep(2.1) # Simula estouro do TTL de 2 segundos
    
    success_replay = server.verify_attestation(nonce_replay, token, signature, time.time())
    assert success_replay is False, "Falha de segurança: Ataque de repetição (replay) não foi bloqueado!"
    print("[SUCESSO] Ataque de repetição bloqueado por expiração de Nonce (TTL).")

    print("Todos os testes executados com sucesso!")

if __name__ == "__main__":
    run_tests()