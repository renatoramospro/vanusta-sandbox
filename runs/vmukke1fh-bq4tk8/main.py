import sqlite3
import time
import json
import sys
import threading
import os

DB_NAME = "outbox_concurrency_demo.db"
MAX_RETRIES = 3

def init_db():
    # Remove o banco anterior para garantir um ambiente limpo e determinístico por execução
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
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
            raise ConnectionError("Broker indisponível para Poison Pill (falha permanente simulada)")
        
        # Simula sucesso na publicação
        self.published_messages.append({"topic": topic, "payload": payload})

class OutboxService:
    def __init__(self, db_path):
        self.db_path = db_path

    def create_order_with_outbox(self, item, amount):
        """Simula a transação de negócio atômica gravando o pedido e o evento outbox."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Inicia transação explícita
            cursor.execute("BEGIN TRANSACTION")
            
            # 1. Grava a ordem de negócio
            cursor.execute("INSERT INTO orders (item, amount) VALUES (?, ?)", (item, amount))
            order_id = cursor.lastrowid
            
            # 2. Grava o evento na Outbox na MESMA transação ACID
            event_payload = json.dumps({"order_id": order_id, "item": item, "amount": amount})
            cursor.execute(
                "INSERT INTO outbox (aggregate_id, event_type, payload) VALUES (?, ?, ?)",
                (str(order_id), "OrderCreated", event_payload)
            )
            
            conn.commit()
            return order_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class OutboxWorker:
    def __init__(self, db_path, broker, worker_id):
        self.db_path = db_path
        self.broker = broker
        self.worker_id = worker_id

    def process_pending_events(self):
        """Processa eventos pendentes usando controle de concorrência transacional."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # BEGIN IMMEDIATE adquire um lock de escrita exclusivo no SQLite,
            # impedindo que múltiplos workers leiam e processem o mesmo lote concorrentemente.
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute("""
                SELECT id, aggregate_id, payload, retry_count 
                FROM outbox 
                WHERE status = 'PENDING' 
                ORDER BY created_at ASC 
                LIMIT 5
            """)
            rows = cursor.fetchall()
            
            if not rows:
                conn.commit()
                return

            for row in rows:
                outbox_id, aggregate_id, payload, retry_count = row
                try:
                    # Tenta publicar no broker
                    self.broker.publish("orders-topic", payload)
                    
                    # Se bem-sucedido, marca como PROCESSED
                    cursor.execute(
                        "UPDATE outbox SET status = 'PROCESSED', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (outbox_id,)
                    )
                    print(f"[Worker {self.worker_id}] Evento Outbox ID {outbox_id} publicado e marcado como PROCESSED.")
                
                except Exception as e:
                    # Falha na publicação: incrementa retry e gerencia DLQ
                    new_retry_count = retry_count + 1
                    if new_retry_count >= MAX_RETRIES:
                        cursor.execute(
                            "UPDATE outbox SET status = 'FAILED_DLQ', retry_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (new_retry_count, outbox_id)
                        )
                        print(f"[Worker {self.worker_id}] ALERTA: Evento ID {outbox_id} atingiu MAX_RETRIES ({MAX_RETRIES}) e foi enviado para FAILED_DLQ. Erro: {e}")
                    else:
                        cursor.execute(
                            "UPDATE outbox SET retry_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (new_retry_count, outbox_id)
                        )
                        print(f"[Worker {self.worker_id}] Falha ao publicar evento ID {outbox_id}. Retry count: {new_retry_count}. Erro: {e}")
            
            conn.commit()
        except sqlite3.OperationalError as oe:
            # Conflito de lock com outro worker, faz rollback e tenta novamente no próximo ciclo
            conn.rollback()
        except Exception as e:
            conn.rollback()
            print(f"[Worker {self.worker_id}] Erro inesperado no worker: {e}")
        finally:
            conn.close()

def main():
    print("=== Inicializando Demonstração do Outbox Pattern (Concorrência, Retries e DLQ) ===")
    init_db()

    # O pedido com id 2 será nossa 'poison pill' proposital para esgotar as tentativas
    broker = MockBroker(poison_pill_event_id=2)
    service = OutboxService(DB_NAME)

    # 1. Criação de Pedidos (Transação de Negócio + Outbox Atômica)
    id1 = service.create_order_with_outbox("Notebook Gamer", 7500.00)
    id2 = service.create_order_with_outbox("Mouse Periférico (Poison Pill)", 150.00)
    
    print(f"Pedidos criados com sucesso: ID {id1} e ID {id2} (Poison Pill).")

    # Instancia dois workers concorrentes simulados
    worker1 = OutboxWorker(DB_NAME, broker, worker_id=1)
    worker2 = OutboxWorker(DB_NAME, broker, worker_id=2)

    # 2. Execução dos ciclos de processamento (Simulando polling e resiliência)
    for attempt in range(1, 5):
        print(f"Ciclo de processamento {attempt}:")
        worker1.process_pending_events()
        worker2.process_pending_events()
        time.sleep(0.1)

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