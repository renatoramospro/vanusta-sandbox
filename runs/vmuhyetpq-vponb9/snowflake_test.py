import time
import threading
from concurrent.futures import ThreadPoolExecutor

class ClockSkewException(Exception):
    """Lançado quando o relógio do sistema retrocede além do limite tolerável."""
    pass

class SnowflakeGenerator:
    def __init__(self, worker_id: int, epoch: int = 1704067200000): # 2024-01-01 00:00:00 UTC
        self.worker_id_bits = 10
        self.sequence_bits = 12
        
        # Limites máximos
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)
        self.max_timestamp_bits = -1 ^ (-1 << 41)
        
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
            
            # Validação explícita do teto de 41 bits do timestamp
            timestamp_delta = timestamp - self.epoch
            if timestamp_delta > self.max_timestamp_bits or timestamp_delta < 0:
                raise ValueError("Timestamp excede o limite de 41 bits do Snowflake (estouro de vida útil ou epoch inválida).")

            # Tratamento de Clock Skew com recuperação automática para pequenos recuos
            if timestamp < self.last_timestamp:
                skew = self.last_timestamp - timestamp
                if skew <= 2000: # Tolerância de até 2 segundos para recuos leves de NTP
                    # Espera ativa segura para alcançar o last_timestamp
                    while timestamp < self.last_timestamp:
                        time.sleep(0.001)
                        timestamp = self._current_time_ms()
                else:
                    raise ClockSkewException(
                        f"Recuo de relógio (clock skew) crítico detectado: {skew}ms. "
                        f"Último timestamp: {self.last_timestamp}, atual: {timestamp}"
                    )

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    # Esgotamento de sequência no mesmo milissegundo: aguarda o próximo ms
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # Montagem do ID de 64 bits:
            # [ 1 bit (sinal 0) ] [ 41 bits timestamp ] [ 10 bits worker_id ] [ 12 bits sequence ]
            new_id = (
                ((timestamp - self.epoch) << (self.worker_id_bits + self.sequence_bits))
                | (self.worker_id << self.sequence_bits)
                | self.sequence
            )
            return new_id

def test_performance_and_uniqueness():
    print("Iniciando teste de performance (>100.000 IDs/s)...")
    generator = SnowflakeGenerator(worker_id=1)
    num_ids = 100000
    ids = set()
    
    start_time = time.time()
    
    def generate_batch(count):
        batch_ids = []
        for _ in range(count):
            batch_ids.append(generator.generate_id())
        return batch_ids

    # Execução concorrente com múltiplas threads
    num_threads = 10
    batch_size = num_ids // num_threads
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(generate_batch, batch_size) for _ in range(num_threads)]
        for future in futures:
            ids.update(future.result())
            
    duration = time.time() - start_time
    rate = len(ids) / duration
    
    print(f"Total gerado: {len(ids)} IDs únicos.")
    print(f"Tempo decorrido: {duration:.4f} segundos.")
    print(f"Taxa alcançada: {rate:.2f} IDs/segundo.")
    
    assert len(ids) == num_ids, f"Colisão detectada! Esperado {num_ids}, obtido {len(ids)}"
    assert rate >= 100000, f"Performance abaixo da meta: {rate} IDs/s"
    print("Sucesso: Mais de 100.000 IDs gerados por segundo sem nenhuma colisão sob concorrência total!")

def test_temporal_ordering():
    print("\nTestando ordenação temporal estrita...")
    generator = SnowflakeGenerator(worker_id=2)
    prev_id = generator.generate_id()
    for _ in range(1000):
        curr_id = generator.generate_id()
        assert curr_id > prev_id, f"Violação de ordenação: {curr_id} não é maior que {prev_id}"
        prev_id = curr_id
    print("Sucesso: Todos os IDs gerados em sequência respeitam rigorosamente a ordem temporal.")

def test_clock_skew_recovery():
    print("\nTestando recuperação automática de Clock Skew leve...")
    generator = SnowflakeGenerator(worker_id=3)
    generator.generate_id()
    
    # Simula um recuo leve de relógio (ex: 50 milissegundos)
    generator.last_timestamp = generator._current_time_ms() + 50
    
    start = time.time()
    generated_id = generator.generate_id()
    elapsed = time.time() - start
    
    print(f"Recuperação bem-sucedida em {elapsed:.4f}s. Novo ID gerado: {generated_id}")
    assert generated_id > 0

def test_clock_skew_critical_failure():
    print("\nTestando falha crítica para Clock Skew severo (>2 segundos)...")
    generator = SnowflakeGenerator(worker_id=4)
    generator.generate_id()
    
    # Simula um recuo severo de 3 segundos no relógio
    generator.last_timestamp = generator._current_time_ms() + 3000
    
    try:
        generator.generate_id()
        raise AssertionError("Deveria ter lançado ClockSkewException para recuo severo!")
    except ClockSkewException as e:
        print(f"Comportamento seguro capturado com sucesso: {e}")

if __name__ == "__main__":
    test_performance_and_uniqueness()
    test_temporal_ordering()
    test_clock_skew_recovery()
    test_clock_skew_critical_failure()
    print("\nTodos os testes do Snowflake passaram com êxito!")