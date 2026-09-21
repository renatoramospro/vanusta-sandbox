py
import time
import hmac
import hashlib
import uuid
from typing import Dict, Tuple

# --- Servidor de Atestação e Jogo ---
class GameAttestationServer:
    def __init__(self, server_secret_key: bytes, nonce_ttl_seconds: float = 2.0):
        self.secret_key = server_secret_key
        self.nonce_ttl = nonce_ttl_seconds
        # Armazena nonces pendentes: nonce -> timestamp de criação
        self.pending_nonces: Dict[str, float] = {}

    def generate_nonce(self) -> str:
        """Gera um nonce criptográfico único e registra seu tempo de vida."""
        nonce = uuid.uuid4().hex
        self.pending_nonces[nonce] = time.time()
        return nonce

    def _verify_platform_signature(self, client_payload: str, signature: str) -> bool:
        """Simula a verificação da assinatura digital emitida pelo enclave de hardware (Google/Apple)."""
        expected_sig = hmac.new(self.secret_key, client_payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    def authenticate_client(self, nonce: str, client_payload: str, signature: str, is_binary_tampered: bool) -> Tuple[bool, str]:
        """
        Valida o pedido de conexão do cliente verificando:
        1. Frescura do Nonce (TTL < 2 segundos e existência).
        2. Assinatura criptográfica válida do token.
        3. Integridade do binário reportada pelo enclave.
        """
        start_time = time.time()

        # 1. Validação de Nonce e Tempo (Deadline < 2s)
        if nonce not in self.pending_nonces:
            return False, "REJECTED: Invalid or already used nonce (Replay Attack Prevention)."
        
        creation_time = self.pending_nonces.pop(nonce) # Consome o nonce imediatamente (one-time use)
        elapsed = time.time() - creation_time

        if elapsed > self.nonce_ttl:
            return False, f"REJECTED: Attestation timeout ({elapsed:.3f}s > {self.nonce_ttl}s limit)."

        # 2. Verificação Criptográfica da Assinatura
        if not self._verify_platform_signature(client_payload, signature):
            return False, "REJECTED: Cryptographic signature mismatch."

        # 3. Verificação de Integridade do Binário (Simulada pelo Enclave)
        if is_binary_tampered:
            return False, "REJECTED: Binary tampering detected by hardware enclave (>95% accuracy rule)."

        # Garantia final de latência global do processo de verificação
        total_latency = time.time() - start_time
        if total_latency > 2.0:
            return False, f"REJECTED: Server processing latency exceeded 2s ({total_latency:.3f}s)."

        return True, "ACCEPTED: Client integrity verified successfully."

# --- Simulação de Execução e Testes ---
if __name__ == "__main__":
    SERVER_SECRET = b"hardware_root_of_trust_secret_key"
    server = GameAttestationServer(server_secret_key=SERVER_SECRET, nonce_ttl_seconds=2.0)

    print("=== INICIANDO TESTES DE ATESTAÇÃO REMOTA ===")

    # Teste 1: Cliente Legítimo (Deve ser Aprovado)
    nonce_legit = server.generate_nonce()
    payload_legit = f"app_package=com.game.mobile;nonce={nonce_legit};integrity=PASS"
    sig_legit = hmac.new(SERVER_SECRET, payload_legit.encode(), hashlib.sha256).hexdigest()

    success, msg = server.authenticate_client(nonce_legit, payload_legit, sig_legit, is_binary_tampered=False)
    print(f"[Teste 1 - Legítimo] -> Resultado: {success} | Mensagem: {msg}")
    assert success == True, "Erro: Cliente legítimo foi rejeitado incorretamente (Falso Positivo)!"

    # Teste 2: Cliente com Binário Adulterado (Deve ser Rejeitado)
    nonce_cheater = server.generate_nonce()
    payload_cheater = f"app_package=com.game.mobile;nonce={nonce_cheater};integrity=FAIL"
    sig_cheater = hmac.new(SERVER_SECRET, payload_cheater.encode(), hashlib.sha256).hexdigest()

    success, msg = server.authenticate_client(nonce_cheater, payload_cheater, sig_cheater, is_binary_tampered=True)
    print(f"[Teste 2 - Adulterado] -> Resultado: {success} | Mensagem: {msg}")
    assert success == False, "Erro crítico: Cliente com binário adulterado foi aceito!"

    # Teste 3: Ataque de Repetição / Replay (Nonce reutilizado deve falhar)
    # Tentando reutilizar o nonce_legit que já foi consumido
    success, msg = server.authenticate_client(nonce_legit, payload_legit, sig_legit, is_binary_tampered=False)
    print(f"[Teste 3 - Replay Attack] -> Resultado: {success} | Mensagem: {msg}")
    assert success == False, "Erro crítico: Ataque de repetição não foi detectado!"

    # Teste 4: Estouro de Tempo / Timeout (> 2 segundos)
    nonce_slow = server.generate_nonce()
    # Simula atraso na rede/geração do token simulando passagem de tempo
    server.pending_nonces[nonce_slow] = time.time() - 2.5 # Força criação no passado
    success, msg = server.authenticate_client(nonce_slow, payload_legit, sig_legit, is_binary_tampered=False)
    print(f"[Teste 4 - Timeout] -> Resultado: {success} | Mensagem: {msg}")
    assert success == False, "Erro crítico: Cliente lento (>2s) não foi rejeitado!"

    print("\nTodos os testes executados com sucesso absoluto e conformidade estrita com os critérios!")