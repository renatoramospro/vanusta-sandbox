import time
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class ContextManager:
    """Interface base para gerenciamento de contexto."""
    def set(self, key, value, owner_id): raise NotImplementedError
    def get(self, key, requester_id): raise NotImplementedError

class BaselineContext(ContextManager):
    """Contexto inseguro: qualquer um lê qualquer coisa (Baseline)."""
    def __init__(self):
        self.storage = {}

    def set(self, key, value, owner_id):
        self.storage[key] = value

    def get(self, key, requester_id):
        # No baseline, não há verificação de quem pede
        return self.storage.get(key)

class SecureContext(ContextManager):
    """Contexto seguro: Criptografia por agente (Proposta)."""
    def __init__(self):
        self.storage = {}  # Armazena {key: (encrypted_blob, nonce, owner_id)}
        self.agent_keys = {} # Armazena {agent_id: key}

    def register_agent(self, agent_id):
        key = AESGCM.generate_key(bit_length=128)
        self.agent_keys[agent_id] = AESGCM(key)

    def set(self, key, value, owner_id):
        if owner_id not in self.agent_keys:
            raise ValueError("Agente não registrado")
        
        aesgcm = self.agent_keys[owner_id]
        nonce = os.urandom(12)
        data = value.encode()
        # Criptografa o dado associando o owner_id como contexto de autenticação
        encrypted_blob = aesgcm.encrypt(nonce, data, owner_id.encode())
        self.storage[key] = (encrypted_blob, nonce, owner_id)

    def get(self, key, requester_id):
        if key not in self.storage:
            return None
        
        encrypted_blob, nonce, owner_id = self.storage[key]
        
        # Regra de Segurança: Só permite descriptografar se o solicitante for o dono
        # ou se houver uma política de permissão (aqui simplificada para o dono)
        if requester_id != owner_id:
            return "ACCESS_DENIED"

        try:
            aesgcm = self.agent_keys[requester_id]
            decrypted_data = aesgcm.decrypt(nonce, encrypted_blob, owner_id.encode())
            return decrypted_data.decode()
        except Exception:
            return "DECRYPTION_FAILED"

def run_benchmark(manager, name, iterations=1000):
    start_time = time.perf_counter()
    for i in range(iterations):
        # Simula uma operação de escrita e leitura
        manager.set(f"key_{i}", f"value_{i}", "agent_1")
        manager.get(f"key_{i}", "agent_1")
    end_time = time.perf_counter()
    avg_latency_ms = ((end_time - start_time) / (iterations * 2)) * 1000
    return avg_latency_ms

def run_security_test(manager):
    """Tenta realizar um ataque de vazamento de contexto."""
    # Setup: Agente 1 guarda um segredo
    secret_key = "top_secret_data"
    secret_value = "PASSWORD_123"
    
    if isinstance(manager, SecureContext):
        manager.register_agent("agent_1")
        manager.register_agent("malicious_agent")
        manager.set(secret_key, secret_value, "agent_1")
    else:
        manager.set(secret_key, secret_value, "agent_1")

    # Ataque: Agente Malicioso tenta ler o segredo
    attempt = manager.get(secret_key, "malicious_agent")
    
    # Se o retorno for o valor real, houve vazamento
    return attempt == secret_value

def main():
    print("--- INICIANDO TESTES DE SEGURANÇA E DESEMPENHO ---\n")

    # 1. Teste de Segurança (Red Teaming)
    baseline = BaselineContext()
    secure = SecureContext()

    baseline_leak = run_security_test(baseline)
    secure_leak = run_security_test(secure)

    print(f"[SEGURANÇA] Baseline Leakage: {'SIM' if baseline_leak else 'NÃO'}")
    print(f"[SEGURANÇA] Secure Leakage:   {'SIM' if secure_leak else 'NÃO'}")

    # Cálculo de redução de vazamento
    # Baseline leak = 1 (100%), Secure leak = 0 (0%). Redução = 100%
    reduction = 100.0 if not secure_leak and baseline_leak else 0.0
    print(f"[RESULTADO] Redução de vazamento: {reduction}%")

    # 2. Teste de Latência
    print("\n--- TESTE DE LATÊNCIA (Benchmark) ---")
    # Precisamos registrar agentes para o SecureContext antes do benchmark
    secure.register_agent("agent_1")
    
    baseline_lat = run_benchmark(baseline)
    secure_lat = run_benchmark(secure)

    print(f"Baseline Latência Média: {baseline_lat:.4f} ms")
    print(f"Secure Latência Média:   {secure_lat:.4f} ms")

    # Verificação de Critérios de Sucesso
    success = True
    if reduction < 90:
        print("❌ FALHA: Redução de vazamento abaixo de 90%")
        success = False
    if secure_lat > 5:
        print(f"❌ FALHA: Latência acima de 5ms ({secure_lat:.4f}ms)")
        success = False
    
    if success:
        print("\n✅ MISSÃO CUMPRIDA: Critérios de sucesso atingidos.")
    else:
        print("\n❌ MISSÃO FALHOU: Critérios não atendidos.")

if __name__ == "__main__":
    main()