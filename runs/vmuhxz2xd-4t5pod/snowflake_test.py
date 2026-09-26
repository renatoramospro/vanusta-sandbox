import time
import threading
from concurrent.futures import ThreadPoolExecutor

class ClockSkewException(Exception):
    """Lançado quando o relógio do sistema retrocede."""
    pass

class SnowflakeGenerator:
    def __init__(self, worker_id: int, epoch: int = 1704067200000): # 2024-01-01 00:00:00 UTC
        self.worker_id_bits = 10
        self.sequence_bits = 12
        
        # Limites máximos
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)
        
        if worker_id > self.max_worker_id or worker_id < 0:
            raise ValueError(f"Worker ID deve estar entre 0 e {self.max_worker_id}")
            
        self.worker_id = worker_id
        self.epoch = epoch
        
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

    def _current_time_ms(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        timestamp = self._current_time_ms()
        while timestamp <= last_timestamp:
            timestamp = self._current_time_ms()
        return timestamp

    def generate_id(self) -> int:
        with self.lock:
            timestamp = self._current_time_ms()

            # Tratamento de Clock Skew
            if timestamp < self.last_timestamp:
                skew = self.last_timestamp - timestamp
                raise ClockSkewException(f"Relógio retrocedeu em {skew}ms. Geração recusada para evitar colisões.")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    # Esgotou a sequência no mesmo milissegundo, espera o próximo
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # Montagem do ID de 64 bits
            # (timestamp - epoch) << 22 | worker_id << 12 | sequence
            new_id = (
                ((timestamp - self.epoch) << (self.worker_id_bits + self.sequence_bits)) |
                (self.worker_id << self.sequence_bits) |
                self.sequence
            )
            return new_id

# --- TESTES E DEMONSTRAÇÕES ---

def test_performance_and_uniqueness():
    print("Iniciando teste de performance (alvo: 100.000 IDs/s) e unicidade...")
    generator = SnowflakeGenerator(worker_id=1)
    
    num_ids = 100_000
    ids = set()
    
    start_time = time.time()
    
    # Geração concorrente usando ThreadPoolExecutor
    def worker_task(count):
        local_ids = []
        for _ in range(count):
            local_ids.append(generator.generate_id())
        return local_ids

    num_threads = 10
    batch_size = num_ids // num_threads
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_task, batch_size) for _ in range(num_threads)]
        for future in futures:
            ids.update(future.result())
            
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Total gerado: {len(ids)} IDs únicos.")
    print(f"Tempo decorrido: {duration:.4f} segundos.")
    print(f"Taxa: {len(ids) / duration:.2f} IDs/segundo.")
    
    assert len(ids) == num_ids, f"Colisão detectada! Esperado {num_ids}, obtido {len(ids)}"
    print("Sucesso: 100.000 IDs gerados sem nenhuma colisão sob concorrência total!")

def test_temporal_ordering():
    print("\nTestando ordenação temporal estrita...")
    generator = SnowflakeGenerator(worker_id=2)
    prev_id = 0
    for _ in range(1000):
        curr_id = generator.generate_id()
        assert curr_id > prev_id, f"Violação de ordenação: {curr_id} não é maior que {prev_id}"
        prev_id = curr_id
    print("Sucesso: Todos os IDs gerados em sequência respeitam rigorosamente a ordem temporal.")

def test_clock_skew_handling():
    print("\nTestando tratamento de Clock Skew (recuo de relógio)...")
    generator = SnowflakeGenerator(worker_id=3)
    generator.generate_id()
    
    # Força artificialmente o last_timestamp para o futuro para simular recuo do relógio do sistema
    generator.last_timestamp = generator._current_time_ms() + 10000
    
    try:
        generator.generate_id()
        raise AssertionError("Deveria ter lançado ClockSkewException!")
    except ClockSkewException as e:
        print(f"Comportamento esperado capturado com sucesso: {e}")

if __name__ == "__main__":
    test_performance_and_uniqueness()
    test_temporal_ordering()
    test_clock_skew_handling()
    print("\Todos os testes do Snowflake passaram com êxito!")