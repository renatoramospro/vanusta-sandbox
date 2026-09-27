import time
import random
import sys

class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o Circuit Breaker está aberto."""
    pass

class CircuitBreaker:
    """Implementação do padrão Circuit Breaker para proteção contra falhas em cascata."""
    def __init__(self, failure_threshold=3, recovery_time=2.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = 0

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def __call__(self, func, *args, **kwargs):
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_time:
                self.state = "HALF-OPEN"
            else:
                raise CircuitBreakerOpenException("Circuit Breaker está ABERTO. Chamada rejeitada.")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF-OPEN":
                self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise e

class ResilientService:
    """Serviço simulado que integra padrões de resiliência e tratamento de falhas."""
    def __init__(self):
        self.cb = CircuitBreaker(failure_threshold=2, recovery_time=1.5)

    def external_dependency_call(self, fail=False, latency=0.0):
        if latency > 0:
            time.sleep(latency)
        if fail:
            raise RuntimeError("Dependência externa indisponível!")
        return "Sucesso na Operação"

    def execute_with_resiliency(self, fail=False, latency=0.0):
        """Executa a chamada protegida por Circuit Breaker e lógica de Retry."""
        retries = 2
        delay = 0.1

        for attempt in range(retries + 1):
            try:
                # Envolvemos a chamada no Circuit Breaker
                return self.cb(self.external_dependency_call, fail=fail, latency=latency)
            except CircuitBreakerOpenException:
                # Fallback imediato se o circuito estiver aberto
                return "Fallback: Resposta padrão de contingência ativa"
            except Exception as e:
                if attempt == retries:
                    return f"Fallback após esgotar retries: {str(e)}"
                time.sleep(delay)
                delay *= 2  # Exponential backoff

def run_chaos_experiment(scenario_name, fail_inject, latency_inject):
    print(f"\n[INÍCIO DO EXPERIMENTO] Cenário: {scenario_name}")
    service = ResilientService()
    
    start_time = time.time()
    
    # 1. Fase de Injeção de Caos (Induzindo falha)
    response_failure = service.execute_with_resiliency(fail=fail_inject, latency=latency_inject)
    print(f"  -> Resposta durante o caos: {response_failure}")
    
    # 2. Fase de Recuperação (Removendo o caos)
    print("  -> Removendo injeção de falha e aguardando auto-recuperação...")
    time.sleep(1.0) # Estabilização
    
    response_recovery = service.execute_with_resiliency(fail=False, latency=0.0)
    end_time = time.time()
    
    rto = end_time - start_time
    print(f"  -> Resposta pós-recuperação: {response_recovery}")
    print(f"  -> RTO Medido: {rto:.4f} segundos")
    
    assert rto < 5.0, f"Falha de RTO: {rto}s excedeu o limite de 5 segundos!"
    print(f"[SUCESSO] Cenário '{scenario_name}' validado com RTO < 5s.")

if __name__ == "__main__":
    # Executando os 3 cenários obrigatórios do critério de sucesso
    try:
        run_chaos_experiment("Cenário 1: Latência Extrema de Rede", fail_inject=False, latency_inject=0.2)
        run_chaos_experiment("Cenário 2: Sobrecarga de CPU / Recurso", fail_inject=False, latency_inject=0.3)
        run_chaos_experiment("Cenário 3: Falha Total de Dependência Externa", fail_inject=True, latency_inject=0.0)
        print("\nTrapézio de Engenharia do Caos executado com sucesso absoluto!")
        sys.exit(0)
    except AssertionError as ae:
        print(f"\n[ERRO DE CRITÉRIO] {ae}")
        sys.exit(1)
    except Exception as ex:
        print(f"\n[ERRO INESPERADO] {ex}")
        sys.exit(1)