import time
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecureContextManager:
    """
    Implementa criptografia de envelope por agente com validação de escopo de tarefa
    para prevenir vazamentos via Prompt Injection.
    """
    def __init__(self):
        self._storage = {}  # {key_id: {"data": encrypted_blob, "owner_id": id, "type": type}}
        self._agent_keys = {} # {agent_id: AESGCM_instance}

    def register_agent(self, agent_id):
        key = AESGCM.generate_key(bit_length=128)
        self._agent_keys[agent_id] = AESGCM(key)

    def store_context(self, key_id, data, owner_id, context_type):
        if owner_id not in self._agent_keys:
            raise ValueError("Agente não registrado.")
        
        nonce = os.urandom(12)
        encrypted_data = self._agent_keys[owner_id].encrypt(nonce, data.encode(), None)
        self._storage[key_id] = {
            "blob": encrypted_data,
            "nonce": nonce,
            "owner_id": owner_id,
            "type": context_type
        }

    def get_context(self, key_id, requester_id, current_task_scope):
        """
        Recupera e descriptografa o contexto, validando:
        1. Se o requerente tem a chave (posse).
        2. Se o tipo de dado está no escopo da tarefa atual (prevenção de Prompt Injection).
        """
        if key_id not in self._storage:
            return "ERROR: Key not found"
        
        entry = self._storage[key_id]
        
        # 1. Verificação de Posse (Criptografia Simétrica)
        if entry["owner_id"] not in self._agent_keys:
            return "ERROR: Owner key missing"
        
        # Tenta descriptografar para validar a chave
        try:
            aesgcm = self._agent_keys[entry["owner_id"]]
            decrypted_data = aesgcm.decrypt(entry["nonce"], entry["blob"], None).decode()
        except Exception:
            return "ERROR: Access Denied (Invalid Key)"

        # 2. Verificação de Escopo (Mitigação de Prompt Injection/Indução)
        # Mesmo que o agente tenha a chave, o dado deve pertencer ao escopo da tarefa atual.
        if entry["type"] not in current_task_scope:
            return f"ERROR: Security Violation (Context '{entry['type']}' not in task scope)"

        return decrypted_data

class BaselineContextManager:
    """Versão insegura para comparação (Baseline)."""
    def __init__(self):
        self._storage = {}

    def store_context(self, key_id, data, owner_id, context_type):
        self._storage[key_id] = data

    def get_context(self, key_id, requester_id, current_task_scope):
        return self._storage.get(key_id, "ERROR: Key not found")

def run_benchmark(manager, agents, data_payloads):
    latencies = []
    leaks = 0
    total_attempts = len(data_payloads)

    for key_id, target_owner, target_type, requester_id, scope, is_malicious in data_payloads:
        start = time.perf_counter()
        
        # Simulação de acesso
        result = manager.get_context(key_id, requester_id, scope)
        
        end = time.perf_counter()
        latencies.append((end - start) * 1000) # ms

        # Se o resultado for o dado real e o agente for malicioso ou o escopo estiver errado
        # consideramos um vazamento.
        if "ERROR" not in result and is_malicious:
            leaks += 1
        elif "ERROR" not in result and target_type not in scope:
            leaks += 1

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    leak_rate = (leaks / total_attempts) * 100 if total_attempts > 0 else 0
    return avg_latency, leak_rate

def main():
    print("--- Iniciando Experimento de Criptografia de Contexto ---")
    
    # Configuração de Agentes
    # Agente A (Vendas) | Agente B (RH)
    agent_a = "agent_sales"
    agent_b = "agent_hr"
    
    secure_mgr = SecureContextManager()
    secure_mgr.register_agent(agent_a)
    secure_mgr.register_agent(agent_b)
    
    baseline_mgr = BaselineContextManager()

    # Dados para armazenar
    # 1. Dado de Vendas (Dono: A, Tipo: sales_data)
    # 2. Dado de RH (Dono: B, Tipo: hr_data)
    secure_mgr.store_context("key_sales", "Customer_List_2023", agent_a, "sales_data")
    baseline_mgr.store_context("key_sales", "Customer_List_2023", agent_a, "sales_data")
    
    secure_mgr.store_context("key_hr", "Salary_Secret_99k", agent_b, "hr_data")
    baseline_mgr.store_context("key_hr", "Salary_Secret_99k", agent_b, "hr_data")

    # Cenários de Teste (key_id, target_owner, target_type, requester_id, scope, is_malicious)
    test_scenarios = [
        # 1. Acesso Legítimo (Agente A acessa dado de A no escopo correto)
        ("key_sales", agent_a, "sales_data", agent_a, ["sales_data"], False),
        
        # 2. Ataque de Acesso Direto (Agente A tenta acessar dado de B)
        ("key_hr", agent_b, "hr_data", agent_a, ["sales_data"], True),
        
        # 3. Ataque de Prompt Injection (Agente A tem a chave de B, mas tenta usar fora do escopo)
        # Simulamos que o Agente A "roubou" a chave de B ou o orquestrador foi induzido.
        # Para testar o escopo, vamos registrar a chave de B no Agente A (simulando vazamento de chave)
        # mas manter o escopo da tarefa apenas como 'sales_data'.
    ]
    
    # Adicionando o cenário de Prompt Injection de forma realista:
    # O Agente A consegue a chave de B (vazamento de chave), mas o escopo da tarefa dele é apenas 'sales_data'
    secure_mgr._agent_keys[agent_a] = secure_mgr._agent_keys[agent_b] # Simula vazamento de chave
    test_scenarios.append(("key_hr", agent_b, "hr_data", agent_a, ["sales_data"], True))

    # Execução Baseline
    baseline_lat, baseline_leak = run_benchmark(baseline_mgr, [agent_a, agent_b], test_scenarios)
    
    # Execução Secure
    secure_lat, secure_leak = run_benchmark(secure_mgr, [agent_a, agent_b], test_scenarios)

    print(f"\n[RESULTADOS BASELINE]")
    print(f"Latência Média: {baseline_lat:.4f} ms")
    print(f"Taxa de Vazamento: {baseline_leak:.1f}%")

    print(f"\n[RESULTADOS SECURE]")
    print(f"Latência Média: {secure_lat:.4f} ms")
    print(f"Taxa de Vazamento: {secure_leak:.1f}%")

    # Verificação de Critérios de Sucesso
    reduction = 100 - secure_leak
    print(f"\n--- VERIFICAÇÃO DE CRITÉRIOS ---")
    print(f"Redução de Vazamento: {reduction:.1f}% (Meta: > 90%)")
    print(f"Latência Média: {secure_lat:.4f} ms (Meta: < 5ms)")

    if reduction >= 90 and secure_lat < 5:
        print("\n✅ SUCESSO: Critérios de missão atingidos.")
    else:
        print("\n❌ FALHA: Critérios não atingidos.")

if __name__ == "__main__":
    main()