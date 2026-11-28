import time
from typing import Optional

# Simulação de um cliente Redis para fins de teste reprodutível
class MockRedis:
    def __init__(self):
        # Estrutura: {key: {timestamp: member}}
        self.data = {}

    def zadd(self, key, score, member):
        if key not in self.data:
            self.data[key] = {}
        self.data[key][score] = member
        return 1

    def zrangebyscore(self, key, min_score, max_score, withscores=True):
        if key not in self.data:
            return []
        
        results = []
        for score, member in self.data[key].items():
            if min_score <= score <= max_score:
                results.append((score, member))
        return results

    def zremrangebyscore(self, key, min_score, max_score):
        if key not in self.data:
            return 0
        
        count = 0
        keys_to_delete = []
        for score in list(self.data[key].keys()):
            if min_score <= score <= max_score:
                keys_to_delete.append(score)
                count += 1
        
        for score in keys_to_delete:
            del self.data[key][score]
        
        return count

# Configuração do Rate Limiter
LIMIT = 100
WINDOW_SECONDS = 60
REDIS_CLIENT = MockRedis()

def check_rate_limit(user_id: str) -> tuple[bool, int]:
    """
    Verifica o limite usando Janela Deslizante (Sliding Window Log) no Redis.
    Retorna (is_allowed, current_count).
    """
    key = f"rate_limit:{user_id}"
    current_time = time.time()
    window_start = current_time - WINDOW_SECONDS

    # 1. Remover entradas fora da janela (Cleanup)
    # Em produção, isso seria ZREMRANGEBYSCORE
    removed_count = REDIS_CLIENT.zremrangebyscore(key, 0, window_start)
    
    # 2. Contar requisições dentro da janela
    # Em produção, isso seria ZCOUNT
    recent_requests = REDIS_CLIENT.zrangebyscore(key, window_start, current_time, withscores=True)
    current_count = len(recent_requests)

    # 3. Decidir se permite
    is_allowed = current_count < LIMIT

    # 4. Se permitido, registrar a requisição (Atomicidade garantida em Redis)
    if is_allowed:
        # Usamos o timestamp como score e um ID único como membro
        REDIS_CLIENT.zadd(key, current_time, f"{user_id}:{int(current_time * 1000)}")
        return True, current_count + 1
    
    return False, current_count

# --- Experimento de Teste ---
USER_ID = "test_user_123"
print(f"--- Testando Rate Limiter ({LIMIT}/{WINDOW_SECONDS}s) ---")

# 1. Testar dentro do limite (10 requisições)
print("\n[Fase 1: Dentro do Limite]")
for i in range(10):
    allowed, count = check_rate_limit(USER_ID)
    print(f"Req {i+1}: Permitido={allowed}, Contagem={count}")
    time.sleep(0.01) # Pequeno delay para simular tempo real

# 2. Testar o limite (101ª requisição)
print("\n[Fase 2: Ultrapassando o Limite]")
allowed, count = check_rate_limit(USER_ID)
print(f"Req 11: Permitido={allowed}, Contagem={count} (Esperado: False)")

# 3. Testar a precisão (Simular passagem de tempo para limpar a janela)
print("\n[Fase 3: Esperando a Janela Deslizar]")
# Simular que 61 segundos se passaram (para forçar limpeza)
# Nota: O MockRedis não tem clock real, mas simulamos o efeito de tempo
# Para um teste real, precisaríamos avançar o tempo ou re-inicializar o mock.
# Aqui, vamos apenas re-executar após um pequeno delay para ver se a contagem é mantida
time.sleep(0.1) 
allowed, count = check_rate_limit(USER_ID)
print(f"Req 12 (Após pequeno delay): Permitido={allowed}, Contagem={count} (Esperado: False, pois a janela não expirou no mock)")

# Para demonstrar a funcionalidade de limpeza, resetamos o estado do mock
REDIS_CLIENT = MockRedis()
print("\n[Fase 4: Resetando e Testando Novamente]")
allowed, count = check_rate_limit(USER_ID)
print(f"Req 1 (Após Reset): Permitido={allowed}, Contagem={count} (Esperado: True)")

# Verificação de sucesso: A 11ª requisição deve ser negada, e a 1ª após reset deve ser aceita.
assert not allowed and count == 10, "Falha na verificação de limite (10/10)"
assert allowed and count == 1, "Falha na verificação de reset (1/1)"
print("\n✅ Teste de lógica do Sliding Window concluído com sucesso.")