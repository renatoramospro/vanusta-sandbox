import time

class TransientError(Exception):
    """Erro temporário que pode ser resolvido com retentativa."""
    pass

class PermanentError(Exception):
    """Erro estrutural/definitivo que nunca funcionará (Poison Pill)."""
    pass

class Message:
    def __init__(self, payload, retry_count=0):
        self.payload = payload
        self.retry_count = retry_count

class ResilientConsumer:
    def __init__(self, max_retries=3, base_delay=0.001):
        self.max_retries = max_retries
        self.base_delay = base_delay  # Atraso curto para fins de teste rápido
        self.dlq = []

    def calculate_backoff(self, retry_count):
        # Backoff exponencial estrito: base_delay * (2 ^ retry_count)
        return self.base_delay * (2 ** retry_count)

    def process_message(self, message):
        try:
            # Simulação de comportamento baseada no payload
            if message.payload == "payload_valido":
                print(f"[SUCESSO] Mensagem processada com sucesso: {message.payload}")
                return "SUCCESS"
            
            elif message.payload == "transient_recoverable":
                # Simula falha nas primeiras 2 tentativas e sucesso na 3ª
                if message.retry_count < 2:
                    raise TransientError("Banco de dados momentaneamente indisponível.")
                else:
                    print(f"[SUCESSO APÓS RETENTATIVA] Mensagem recuperada na tentativa {message.retry_count}")
                    return "SUCCESS"

            elif message.payload == "transient_exhausted":
                # Sempre falha transitoriamente para testar o esgotamento para DLQ
                raise TransientError("Serviço externo fora do ar.")

            elif message.payload == "poison_pill":
                raise PermanentError("Erro de schema / dados corrompidos.")
            
            else:
                raise PermanentError("Payload desconhecido.")

        except TransientError as e:
            if message.retry_count < self.max_retries:
                message.retry_count += 1
                delay = self.calculate_backoff(message.retry_count)
                # CORREÇÃO CRUCIAL: Substituído '.4s' por '.4f' para evitar ValueError
                print(f"[RETENTATIVA] {e} | Tentativa {message.retry_count}/{self.max_retries} | Aguardando {delay:.4f}s")
                time.sleep(delay)  # Simula a espera antes de reprocessar
                return self.process_message(message)
            else:
                print(f"[DLQ] Tentativas esgotadas ({message.retry_count}/{self.max_retries}). Enviando para a DLQ.")
                self.dlq.append(message)
                return "DLQ"

        except PermanentError as e:
            print(f"[DLQ - PERMANENTE] Erro definitivo detectado ({e}). Enviando diretamente para a DLQ sem retentativas.")
            self.dlq.append(message)
            return "DLQ"

# --- Bloco de Testes e Validação ---
if __name__ == "__main__":
    consumer = ResilientConsumer(max_retries=3, base_delay=0.001)

    print("=== TESTE 1: Sucesso na primeira tentativa ===")
    msg1 = Message("payload_valido")
    res1 = consumer.process_message(msg1)
    assert res1 == "SUCCESS"

    print("\n=== TESTE 2: Falha transitória recuperada com sucesso após retentativas ===")
    msg2 = Message("transient_recoverable")
    res2 = consumer.process_message(msg2)
    assert res2 == "SUCCESS"

    print("\n=== TESTE 3: Esgotamento de retentativas transitórias (vai para DLQ) ===")
    msg3 = Message("transient_exhausted")
    res3 = consumer.process_message(msg3)
    assert res3 == "DLQ"
    assert len(consumer.dlq) == 1
    assert consumer.dlq[0].retry_count == consumer.max_retries

    print("\n=== TESTE 4: Falha definitiva (Poison Pill) vai direto para DLQ ===")
    msg4 = Message("poison_pill")
    res4 = consumer.process_message(msg4)
    assert res4 == "DLQ"
    assert len(consumer.dlq) == 2
    assert consumer.dlq[1].retry_count == 0  # Não incrementou tentativas

    print("\n[VEREDITO DO EXPERIMENTO] Todos os testes passaram com 100% de conformidade e sem exceções de formatação!")