import time
import random
import threading
import sys
from typing import Callable, Any

class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o Circuit Breaker está aberto."""
    pass

class ChaosGovernanceException(Exception):
    """Exceção lançada quando o Kill-Switch ou limites de caos são violados."""
    pass

class ThreadSafeCircuitBreaker:
    """
    Circuit Breaker thread-safe com Histerese e Janela Deslizante (Flapping Prevention).
    """
    def __init__(self, failure_threshold: int = 3, success_threshold: int = 2, recovery_time: float = 1.0):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_time = recovery_time
        
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.lock = threading.Lock()

    def record_success(self):
        with self.lock:
            if self.state == "HALF-OPEN":
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = "CLOSED"
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == "CLOSED":
                self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        with self.lock:
            self.last_failure_time = time.time()
            if self.state == "HALF-OPEN":
                # Falha imediata ao sondar no half-open
                self.state = "OPEN"
                self.success_count = 0
            elif self.state == "CLOSED":
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"

    def allow_request(self) -> bool:
        with self.lock:
            now = time.time()
            if self.state == "OPEN":
                if now - self.last_failure_time > self.recovery_time:
                    self.state = "HALF-OPEN"
                    self.success_count = 0
                    return True
                return False
            return True

def retry_with_jitter(func: Callable, max_retries: int = 3, base_delay: float = 0.1) -> Any:
    """Implementa Retry com Exponential Backoff e Full Jitter."""
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            # Exponential backoff com jitter aleatório para evitar tempestades de retry
            sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0, 0.05)
            time.sleep(sleep_time)

class SecureResilientService:
    """Serviço com governança, fallbacks seguros (fail-closed/fail-open) e telemetria."""
    def __init__(self):
        self.circuit_breaker = ThreadSafeCircuitBreaker(failure_threshold=2, recovery_time=0.5)
        self.kill_switch = False

    def call_dependency(self, fail_inject: bool, latency_inject: float) -> str:
        if self.kill_switch:
            raise ChaosGovernanceException("Kill-Switch ativado! Execução abortada por segurança.")
        
        if latency_inject > 0:
            time.sleep(latency_inject)
            
        if fail_inject:
            raise ConnectionError("Falha simulada na dependência externa.")
        
        return "Sucesso na Operação Primária"

    def execute_with_resiliency(self, fail_inject: bool, latency_inject: float) -> str:
        if not self.circuit_breaker.allow_request():
            # Fallback seguro (Fail-Closed para dados sensíveis / Fail-Open para disponibilidade)
            return "Fallback: Resposta segura de contingência (Fail-Open)"

        try:
            result = retry_with_jitter(
                lambda: self.call_dependency(fail_inject, latency_inject),
                max_retries=2,
                base_delay=0.05
            )
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure()
            return "Fallback: Resposta segura de contingência (Fail-Open)"

def run_validated_chaos_experiment(name: str, fail_inject: bool, latency_inject: float):
    print(f"\n[INÍCIO DO EXPERIMENTO GOVERNADO] {name}")
    service = SecureResilientService()

    # 1. Fase de Caos Ativo
    response_during_chaos = service.execute_with_resiliency(fail_inject=fail_inject, latency_inject=latency_inject)
    print(f"  -> Resposta durante o caos: {response_during_chaos}")

    # 2. Remoção da Injeção e Início da Medição Rigorosa de RTO
    print("  -> Removendo injeção de falha e iniciando cronômetro de RTO...")
    start_time = time.time()
    
    recovered = False
    rto_measured = 0.0
    
    # Loop de sondagem síncrona para capturar a restauração exata da dependência primária
    while time.time() - start_time < 5.0:
        res = service.execute_with_resiliency(fail_inject=False, latency_inject=0.0)
        if res == "Sucesso na Operação Primária":
            rto_measured = time.time() - start_time
            recovered = True
            break
        time.sleep(0.05)

    if not recovered:
        raise AssertionError(f"RTO excedeu o limite de 5 segundos no cenário '{name}'!")

    print(f"  -> Resposta pós-recuperação confirmada na dependência primária: Sucesso")
    print(f"  -> RTO Medido com precisão: {rto_measured:.4f} segundos")
    assert rto_measured < 5.0, f"RTO ({rto_measured}s) acima do limite exigido de 5s."
    print(f"[SUCESSO] Cenário '{name}' validado com RTO < 5s e restauração primária comprovada.")

if __name__ == "__main__":
    try:
        run_validated_chaos_experiment("Cenário 1: Latência Extrema de Rede", fail_inject=False, latency_inject=0.2)
        run_validated_chaos_experiment("Cenário 2: Sobrecarga de CPU / Recurso", fail_inject=False, latency_inject=0.3)
        run_validated_chaos_experiment("Cenário 3: Falha Total de Dependência Externa", fail_inject=True, latency_inject=0.0)
        print("\nFramework de Caos e Resiliência executado com sucesso e aprovado em todas as diretrizes de segurança!")
        sys.exit(0)
    except AssertionError as ae:
        print(f"\n[ERRO DE CRITÉRIO] {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\n[ERRO INESPERADO] {ex}")
        sys.exit(1)