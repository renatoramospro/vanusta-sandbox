path=retry_jitter_core.py
import time
import random
import logging

# Configuração de logging para observação clara no console
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VanustaCoreRetry")

class RetryConfig:
    def __init__(self, max_attempts=3, base_delay=0.1, max_delay=5.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

class ExternalCallMetrics:
    def __init__(self):
        self.attempts = 0
        self.successes = 0
        self.successes_after_retry = 0
        self.failures = 0

    def reset(self):
        self.attempts = 0
        self.successes = 0
        self.successes_after_retry = 0
        self.failures = 0

class TransientError(Exception):
    """Erro transitório simulado (ex: 503, Timeout)"""
    pass

class PermanentError(Exception):
    """Erro permanente simulado (ex: 400 Bad Request)"""
    pass

def execute_with_retry(service_name: str, config: RetryConfig, metrics: ExternalCallMetrics, func, *args, **kwargs):
    """
    Executa uma chamada externa aplicando Backoff Exponencial com Full Jitter.
    """
    attempt = 0
    while True:
        attempt += 1
        metrics.attempts += 1
        try:
            logger.info(f"[{service_name}] Tentativa {attempt} de {config.max_attempts}")
            result = func(*args, **kwargs)
            if attempt == 1:
                metrics.successes += 1
            else:
                metrics.successes_after_retry += 1
            logger.info(f"[{service_name}] Sucesso na tentativa {attempt}")
            return result
        except TransientError as e:
            if attempt >= config.max_attempts:
                metrics.failures += 1
                logger.error(f"[{service_name}] Falha definitiva após {attempt} tentativas. Erro: {e}")
                raise e
            
            # Cálculo do Backoff Exponencial com Full Jitter
            # teto = min(max_delay, base_delay * 2^(attempt - 1))
            exponential_ceiling = min(config.max_delay, config.base_delay * (2 ** (attempt - 1)))
            sleep_time = random.uniform(0, exponential_ceiling)
            
            logger.warning(f"[{service_name}] Erro transitório: {e}. Aguardando {sleep_time:.3f}s (teto exp: {exponential_ceiling:.3f}s)")
            time.sleep(sleep_time)
        except PermanentError as e:
            metrics.failures += 1
            logger.error(f"[{service_name}] Erro permanente detectado imediatamente. Abortando retries. Erro: {e}")
            raise e

# --- SIMULAÇÃO E TESTES COMPROBATÓRIOS ---
if __name__ == "__main__":
    metrics = ExternalCallMetrics()
    config = RetryConfig(max_attempts=4, base_delay=0.1, max_delay=2.0)

    # Cenário 1: Falha transitória nas 2 primeiras tentativas, sucesso na 3ª
    print("\n--- CENÁRIO 1: Recuperação de Falha Transitória ---")
    call_attempts = 0
    def unstable_service():
        nonlocal call_attempts
        call_attempts += 1
        if call_attempts < 3:
            raise TransientError("503 Service Unavailable")
        return "Dados obtidos com sucesso"

    start_time = time.time()
    res = execute_with_retry("PaymentService", config, metrics, unstable_service)
    duration = time.time() - start_time
    print(res)
    print(f"Tempo total de recuperação: {duration:.3f}s")
    assert duration < 2.0, "O tempo de recuperação excedeu o limite de 2 segundos!"
    assert metrics.successes_after_retry == 1, "Métrica de sucesso após retry incorreta."

    # Cenário 2: Erro permanente (não deve realizar retries)
    print("\n--- CENÁRIO 2: Erro Permanente (Sem Retry) ---")
    def permanent_failure_service():
        raise PermanentError("400 Bad Request - Payload Inválido")

    try:
        execute_with_retry("BillingService", config, metrics, permanent_failure_service)
    except PermanentError:
        print("Erro permanente tratado com sucesso e sem loops de retry desnecessários.")

    assert metrics.attempts == 2 + 1, "Número total de tentativas incorreto."
    print("\nTodas as validações do experimento foram executadas com sucesso absoluto e código de saída 0.")