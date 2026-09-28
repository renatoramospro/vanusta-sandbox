import sqlite3
import time
import json
import sys

DB_NAME = "outbox_demo.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabela de negócio
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    # Tabela Outbox com campos para controle de estado e retry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aggregate_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            retry_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

class MockBroker:
    def __init__(self, failure_rate=0.0):
        self.published_messages = []
        self.failure_rate = failure_rate
        self.attempts = 0

    def publish(self, topic, payload):
        self.attempts += 1
        # Simula falha intermitente do broker (ex: queda de rede)
        if self.attempts <= 1 and self.failure_rate > 0:
            raise ConnectionError("Broker indisponível temporariamente!")
        self.published_messages.append((topic, payload))
        return True

def business_operation_with_outbox(item, amount, broker_payload):
    """Executa a transação atômica de negócio + outbox."""
    conn = sqlite3.connect(DB_NAME)
    try:
        cursor = conn.cursor()
        
        # 1. Operação de Negócio
        cursor.execute("INSERT INTO orders (item, amount) VALUES (?, ?)", (item, amount))
        order_id = cursor.lastrowid
        
        # 2. Gravação na Outbox dentro da MESMA transação
        event_data = json.dumps({"order_id": order_id, **broker_payload})
        cursor.execute("""
            INSERT INTO outbox (aggregate_type, aggregate_id, event_type, payload)
            VALUES (?, ?, ?, ?)
        """, ("Order", str(order_id), "OrderCreated", event_data))
        
        # Commit atômico: ou os dois entram, ou nenhum entra
        conn.commit()
        return order_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def outbox_processor(broker):
    """Processa a outbox simulando o padrão de leitura at-least-once com retry."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Seleciona eventos pendentes
    cursor.execute("""
        SELECT id, event_type, payload, retry_count 
        FROM outbox 
        WHERE status = 'PENDING' 
        ORDER BY created_at ASC
    """)
    events = cursor.fetchall()
    
    processed_count = 0
    for event_id, event_type, payload, retry_count in events:
        try:
            # Tenta publicar no broker
            broker.publish("orders-topic", payload)
            
            # Se teve sucesso, marca como PROCESSADO
            cursor.execute("""
                UPDATE outbox SET status = 'PROCESSED' WHERE id = ?
            """, (event_id,))
            conn.commit()
            processed_count += 1
        except Exception as e:
            # Em caso de falha, incrementa o retry e mantém pendente (At-Least-Once)
            new_retry = retry_count + 1
            cursor.execute("""
                UPDATE outbox SET retry_count = ? WHERE id = ?
            """, (new_retry, event_id))
            conn.commit()
            print(f"[AVISO] Falha ao publicar evento {event_id}: {e}. Tentativa {new_retry}.")
            
    conn.close()
    return processed_count

if __name__ == "__main__":
    print("Inicializando ambiente de teste do Outbox Pattern...")
    init_db()

    # Instancia um broker que falha na primeira tentativa para testar resiliência
    broker = MockBroker(failure_rate=1.0)

    print("\n--- 1. Executando Transação de Negócio (DB + Outbox) ---")
    order_id = business_operation_with_outbox("Notebook Gamer", 4500.00, {"item": "Notebook Gamer", "amount": 4500.00})
    print(f"Pedido #{order_id} gravado com sucesso no banco junto ao evento Outbox.")

    # Valida que o evento está pendente
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status, retry_count FROM outbox WHERE aggregate_id = ?", (str(order_id),))
    status, retries = cursor.fetchone()
    print(f"Estado inicial no DB -> Status: {status}, Retries: {retries}")
    assert status == 'PENDING'

    print("\n--- 2. Tentativa 1 de Processamento (Broker simula queda) ---")
    outbox_processor(broker)
    
    cursor.execute("SELECT status, retry_count FROM outbox WHERE aggregate_id = ?", (str(order_id),))
    status, retries = cursor.fetchone()
    print(f"Estado após falha do broker -> Status: {status}, Retries: {retries}")
    assert status == 'PENDING'
    assert retries == 1
    assert len(broker.published_messages) == 0
    print("-> Comportamento validado: O evento NÃO foi perdido, manteve-se pendente com retry incrementado.")

    print("\n--- 3. Tentativa 2 de Processamento (Broker recuperado) ---")
    # Desliga a taxa de falha do broker simulando recuperação
    broker.failure_rate = 0.0
    outbox_processor(broker)

    cursor.execute("SELECT status, retry_count FROM outbox WHERE aggregate_id = ?", (str(order_id),))
    status, retries = cursor.fetchone()
    print(f"Estado após recuperação -> Status: {status}, Retries: {retries}")
    assert status == 'PROCESSED'
    assert len(broker.published_messages) == 1
    print(f"Mensagens publicadas no broker: {broker.published_messages}")

    print("\n[SUCESSO] Demonstração concluída: Garantia de entrega At-Least-Once comprovada sem perda de eventos.")
    sys.exit(0)