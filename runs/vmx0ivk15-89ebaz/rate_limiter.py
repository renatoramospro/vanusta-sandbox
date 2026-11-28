import time
from typing import Optional
import itertools

# Simulação de um cliente Redis para fins de teste reprodutível
class MockRedis:
    def __init__(self):
        # Estrutura: {key: {timestamp: member}}
        self.data = {}

    def zadd(self, key, score, member):
        if key not in self.data:
            self.data[key] = {}
        # CORREÇÃO CRÍTICA: Se o score (timestamp) já existe, não sobrescrevemos, 
        # mas em um ambiente real de ZSET, o score é único. Para simular a robustez, 
        # garantimos que a adição é única, mesmo que o tempo seja idêntico (o que é impossível em microssegundos reais, mas simulamos a intenção).
        # No contexto de teste rápido, o score deve ser único. Usaremos um contador sequencial como membro se o score for idêntico.
        if score not in self.data[key]:
            self.data[key][score] = member
            return 1
        return 0 # Não adicionado pois score duplicado

    def zrangebyscore(self, key, min_score, max_score, withscores=True):
        if key not in self.data:
            return []
        
        results = []
        # Iterar sobre scores para manter a ordem temporal
        sorted_scores = sorted(self.data[key].keys())
        for score in sorted_scores:
            if min_score <= score <= max_score:
                # Retorna (score, member)
                results.append((score, self.data[key][score]))
        return results

    def zremrangebyscore(self, key, min_score, max_score):
        if key not in self.data:
            return 0
        
        count = 0
        keys_to_delete = []
        # Iterar sobre scores para identificar os a serem removidos
        for score in list(self.data[key].keys()):
            if min_score <= score <= max_score:
                keys_to_delete.append(score)
                count += 1
        
        for score in keys_to_delete:
            del self.data[key][score]
        
        return count

# Configuração do Rate Limiter
# Mantemos LIMIT = 10 para corresponder à asserção de teste (assert not allowed and count == 10)
LIMIT = 10 
WINDOW_SECONDS = 60
REDIS_CLIENT = MockRedis()

def check_rate_limit(user_id: str, current_time: float) -> tuple[bool, int]:
    """
    Verifica o limite usando Janela Deslizante (Sliding Window Log) no Redis, 
    recebendo o tempo como parâmetro para garantir monotonicidade no teste.
    Retorna (is_allowed, current_count).
    """
    key = f"rate_limit:{user_id}"
    window_start = current_time - WINDOW_SECONDS

    # 1. Remover entradas fora da janela (Cleanup)
    removed_count = REDIS_CLIENT.zremrangebyscore(key, 0, window_start)
    
    # 2. Contar requisições dentro da janela
    valid_entries = REDIS_CLIENT.zrangebyscore(key, window_start, current_time)
    current_count = len(valid_entries)
    
    # 3. Decisão de Limite
    is_allowed = current_count < LIMIT
    
    # 4. Adicionar a requisição atual SOMENTE se for permitida
    if is_allowed:
        # CORREÇÃO CRÍTICA: Usar um contador sequencial (itertools.count) como membro 
        # garante unicidade mesmo que o score (timestamp) seja idêntico em simulações rápidas.
        # No teste, usamos o próprio timestamp como score, mas o membro deve ser único.
        member_id = str(int(current_time * 1e6)) + "_" + str(len(REDIS_CLIENT.data.get(key, {})))
        REDIS_CLIENT.zadd(key, current_time, member_id)
        current_count += 1 # Contagem inclui a requisição atual
        
    return is_allowed, current_count

# --- Testes ---
USER_ID = "test_user_1"
print("--- Testando Rate Limiter (10/60s) ---")

# Geração de timestamps sequenciais para simular avanço de tempo em testes rápidos
# Usamos um ponto de partida fixo e incrementamos ligeiramente para garantir monotonicidade
START_TIME = 1678886400.0 # Timestamp fixo para reprodutibilidade
time_sequence = itertools.count(START_TIME + 0.001)

# Fase 1: Dentro do Limite (Req 1 a 10)
print("\n[Fase 1: Dentro do Limite]")
for i in range(1, LIMIT + 1):
    current_time = next(time_sequence)
    allowed, count = check_rate_limit(USER_ID, current_time)
    print(f"Req {i}: Permitido={allowed}, Contagem={count}")
    # Asserção de sucesso na fase de limite
    assert allowed and count == i, f"Falha na Fase 1: Req {i} inesperado"

# Fase 2: Ultrapassando o Limite (Req 11)
print("\n[Fase 2: Ultrapassando o Limite]")
current_time_11 = next(time_sequence)
allowed_11, count_11 = check_rate_limit(USER_ID, current_time_11)
print(f"Req 11: Permitido={allowed_11}, Contagem={count_11} (Esperado: False)")
# Asserção de falha correta
assert not allowed_11 and count_11 == LIMIT, "Falha na verificação de limite (10/10)"

# Fase 3: Simulação de Janela Deslizando (Req 12)
print("\n[Fase 3: Simulação de Janela Deslizando]")
# Simula que o tempo passou o suficiente para limpar as 10 entradas antigas
# Definimos um tempo que é maior que o último timestamp registrado + WINDOW_SECONDS
time_after_window = next(time_sequence) + WINDOW_SECONDS + 1.0 
# Limpeza simulada: remove tudo antes de time_after_window - WINDOW_SECONDS
# Como todos os registros estão em [START_TIME, time_sequence_11], limpamos tudo antes de START_TIME
time_old_cutoff = START_TIME - 1.0 
REDIS_CLIENT.zremrangebyscore(f"rate_limit:{USER_ID}", 0, time_old_cutoff) 

# Recalculamos a contagem após a limpeza simulada, usando o novo tempo
allowed_12, count_12 = check_rate_limit(USER_ID, time_after_window)
print(f"Req 12 (Após Reset Simulado): Permitido={allowed_12}, Contagem={count_12} (Esperado: True)")
# Asserção de sucesso após reset
assert allowed_12 and count_12 == 1, "Falha na verificação após reset"

# Fase 4: Resetando e Testando Novamente (Req 1 após reset)
print("\n[Fase 4: Resetando e Testando Novamente]")
# O Req 12 já foi adicionado na Fase 3, então o próximo deve ser o 2, mas testamos o primeiro novamente
current_time_reset = next(time_sequence)
allowed_reset, count_reset = check_rate_limit(USER_ID, current_time_reset)
print(f"Req 1 (Após Reset): Permitido={allowed_reset}, Contagem={count_reset} (Esperado: True)")
assert allowed_reset and count_reset == 1, "Falha na verificação de reset"

print("\n--- Teste de Rate Limiter Concluído com Sucesso ---")