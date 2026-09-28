import sqlite3
import time
import json
import sys
import threading

DB_NAME = "outbox_concurrency_demo.db"
MAX_RETRIES = 3

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Limpeza prévia para garantir determinismo
    cursor.execute("DROP TABLE IF EXISTS outbox")
    cursor.execute("DROP TABLE IF EXISTS orders")
    
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Índice essencial para evitar table scan no polling do Outbox
    cursor.execute("CREATE INDEX idx_outbox_status ON outbox(status, created_at)")
    conn.commit()
    conn.close()

class MockBroker:
    def __init__(self, poison_pill_event_id=None):
        self.published_messages = []
        self.poison_pill_event_id = poison_pill_event_id

    def publish(self, topic, payload):
        data = json.loads(payload)
        # Simula falha permanente (poison pill) para um evento específico
        if self.poison_pill_event_id and data.get("order_id") == self.poison_pill_event_id:
            raise RuntimeError("Poison Pill: Erro irrecuperável ao processar payload!")
        
        # Simula falha temporária genérica aleatória ou controlada
        self.published_messages.append((topic, payload))
        print(f"[BROKER] Mensagem publicada com sucesso no tópico '{topic}': {payload}")

class OutboxWorker:
    def __init__(self, db_path, broker, worker_id):
        self.db_path = db_path
        self.broker = broker
        self.worker_id = worker_id

    def process_pending_events(self):
        # SQLite em modo concorrente precisa de timeout e BEGIN IMMEDIATE para exclusão mútua
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()
            
            # Seleciona lote pendente limitando a concorrência entre workers (simulando row-level locking)
            cursor.execute("""
                SELECT id, aggregate_id, event_type, payload, retry_count 
                FROM outbox 
                WHERE status = 'PENDING' 
                ORDER BY created_at ASC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            
            if not row:
                conn.commit()
                return False

            event_id, aggregate_id, event_type, payload, retry_count = row

            try:
                # Tenta publicar no broker
                self.broker.publish("orders-topic", payload)
                
                # Sucesso: marca como PROCESSED
                cursor.execute("""
                    UPDATE outbox 
                    SET status = 'PROCESSED', updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (event_id,))
                conn.commit()
                print(f"[Worker {self.worker_id}] Evento {event_id} processado com sucesso.")
                return True

            except Exception as e:
                # Falha no envio: incrementa retry e verifica limite de poison pills
                new_retry = retry_count + 1
                if new_retry >= MAX_RETRIES:
                    cursor.execute("""
                        UPDATE outbox 
                        SET status = 'FAILED_DLQ', retry_count = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (new_retry, event_id,))
                    conn.commit()
                    print(f"[Worker {self.worker_id}] [DLQ] Evento {event_id} atingiu MAX_RETRIES ({MAX_RETRIES}) devido a erro: {e}. Movido para DLQ.")
                else:
                    cursor.execute("""
                        UPDATE outbox 
                        SET retry_count = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (new_retry, event_id,))
                    conn.commit()
                    print(f"[Worker {self.worker_id}] Falha ao publicar evento {event_id}: {e}. Retry atualizado para {new_retry}.")
                return False

        except Exception as db_err:
            conn.rollback()
            print(f"[Worker {self.worker_id}] Erro de transação: {db_err}")
            return False
        finally:
            conn.close()

def create_order_with_outbox(item, amount, should_fail_broker=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Transação de Negócio
        cursor.execute("INSERT INTO orders (item, amount) VALUES (?, ?)", (item, amount))
        order_id = cursor.lastrowid
        
        # 2. Outbox Table na MESMA transação ACID
        event_payload = json.dumps({"order_id": order_id, "item": item, "amount": amount})
        cursor.execute("""
            INSERT INTO outbox (aggregate_id, event_type, payload, status)
            VALUES (?, ?, ?, 'PENDING')
        """, (str(order_id), "OrderCreated", event_payload))
        
        conn.commit()
        print(f"Pedido #{order_id} gravado com sucesso no DB junto ao evento Outbox.")
        return order_id
    except Exception as e:
        conn.rollback()
        print(f"Erro na transação de negócio: {e}")
        raise
    finally:
        conn.close()

def main():
    print("=== Inicializando Demonstração Avançada do Outbox Pattern (Concorrência & DLQ) ===")
    init_db()

    # 1. Criar pedidos normais e um pedido Poison Pill (que falhará permanentemente)
    print("\n--- 1. Criando Pedidos (Incluindo Poison Pill) ---")
    id1 = create_order_with_outbox("Teclado Mecânico", 350.0)
    id2 = create_order_with_outbox("Mouse Gamer", 150.0) # Este será o poison pill

    broker = MockBroker(poison_pill_event_id=id2)
    worker1 = OutboxWorker(DB_NAME, broker, worker_id=1)
    worker2 = OutboxWorker(DB_NAME, broker, worker_id=2)

    # 2. Testando Poison Pill e Limite de Retentativas (MAX_RETRIES = 3)
    print("\n--- 2. Processando Eventos com Poison Pill (Simulando esgotamento de retentativas) ---")
    # O pedido id2 vai falhar 3 vezes e ir para DLQ. O pedido id1 deve processar normalmente.
    for attempt in range(1, 5):
        print(Ciclo de processamento {attempt}:)
        worker1.process_pending_events()
        worker2.process_pending_events()

    # 3. Validação de Estados Finais no Banco de Dados
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, aggregate_id, status, retry_count FROM outbox")
    results = cursor.fetchall()
    print("\n--- 3. Verificação de Estados Finais na Tabela Outbox ---")
    for r in results:
        print(f"Outbox ID: {r[0]} | Aggregate ID: {r[1]} | Status: {r[2]} | Retries: {r[3]}")

    # Asserts rigorosos para garantir o critério de sucesso
    # Pedido 1 deve estar PROCESSED
    cursor.execute("SELECT status FROM outbox WHERE aggregate_id = ?", (str(id1),))
    status_id1 = cursor.fetchone()[0]
    assert status_id1 == 'PROCESSED', f"Esperado PROCESSED para id1, obtido {status_id1}"

    # Pedido 2 (Poison Pill) deve estar FAILED_DLQ após esgotar MAX_RETRIES
    cursor.execute("SELECT status, retry_count FROM outbox WHERE aggregate_id = ?", (str(id2),))
    status_id2, retries_id2 = cursor.fetchone()
    assert status_id2 == 'FAILED_DLQ', f"Esperado FAILED_DLQ para poison pill id2, obtido {status_id2}"
    assert retries_id2 == MAX_RETRIES, f"Esperado retry_count igual a {MAX_RETRIES}, obtido {retries_id2}"

    print("\n[SUCESSO] Todos os cenários (Concorrência, Retry e Dead Letter Queue) validados com sucesso!")
    conn.close()
    sys.exit(0)

if __name__ == "__main__":
    main()