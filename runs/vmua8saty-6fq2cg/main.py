import sqlite3
import json
import uuid

# --- SIMULAÇÃO DE INFRAESTRUTURA ---

class MockBroker:
    def __init__(self):
        self.messages = []
        self.fail_next = False

    def publish(self, message):
        if self.fail_next:
            self.fail_next = False
            raise ConnectionError("Falha de rede no Broker!")
        self.messages.append(message)
        print(f"  [Broker] Mensagem recebida: {message}")

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.setup()

    def setup(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE orders (id TEXT, amount REAL)")
        cursor.execute("CREATE TABLE outbox (id TEXT, payload TEXT, processed INTEGER)")
        self.conn.commit()

    def execute(self, query, params=()):
        return self.conn.execute(query, params)

    def commit(self):
        self.conn.commit()

# --- IMPLEMENTAÇÕES ---

class DualWriteService:
    """Implementação INCORRETA que sofre de Dual Write."""
    def __init__(self, db, broker):
        self.db = db
        self.broker = broker

    def create_order(self, order_id, amount):
        # Passo 1: Salva no DB
        self.db.execute("INSERT INTO orders VALUES (?, ?)", (order_id, amount))
        self.db.commit()
        
        # Passo 2: Publica no Broker (Pode falhar!)
        event = json.dumps({"order_id": order_id, "amount": amount})
        self.broker.publish(event)

class OutboxService:
    """Implementação CORRETA usando Transactional Outbox."""
    def __init__(self, db):
        self.db = db

    def create_order(self, order_id, amount):
        event_payload = json.dumps({"order_id": order_id, "amount": amount})
        
        # Uma única transação para ambos
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            # Salva o negócio
            cursor.execute("INSERT INTO orders VALUES (?, ?)", (order_id, amount))
            
            # Salva o evento na Outbox
            cursor.execute("INSERT INTO outbox VALUES (?, ?, 0)", (str(uuid.uuid4()), event_payload))
            
            self.db.conn.commit()
            print(f"  [Service] Pedido {order_id} e evento salvos atomicamente.")
        except Exception as e:
            self.db.conn.rollback()
            print(f"  [Service] Erro! Transação revertida: {e}")

class OutboxRelay:
    """O processo que move mensagens da Outbox para o Broker."""
    def __init__(self, db, broker):
        self.db = db
        self.broker = broker
        self.simulate_crash_after_publish = False

    def process(self):
        cursor = self.db.conn.cursor()
        # Busca eventos não processados
        cursor.execute("SELECT id, payload FROM outbox WHERE processed = 0")
        rows = cursor.fetchall()

        for row_id, payload in rows:
            try:
                self.broker.publish(payload)
                
                # Simulação de falha crítica: O broker recebeu, mas o Relay "morreu" 
                # antes de conseguir atualizar o banco de dados.
                if self.simulate_crash_after_publish:
                    print("  [Relay] !!! CRASH SIMULADO APÓS PUBLICAÇÃO !!!")
                    return # Sai do processo sem marcar como processado

                cursor.execute("UPDATE outbox SET processed = 1 WHERE id = ?", (row_id,))
                self.db.conn.commit()
            except Exception as e:
                print(f"  [Relay] Erro ao processar evento {row_id}: {e}")

# --- EXPERIMENTO ---

def run_experiment():
    print("=== CENÁRIO 1: Falha na Escrita Dupla (Dual Write) ===")
    db = Database()
    broker = MockBroker()
    service = DualWriteService(db, broker)
    
    broker.fail_next = True # Simula queda de rede no broker
    try:
        service.create_order("ORD-001", 100.0)
    except Exception:
        pass

    # Verificação de inconsistência
    cursor = db.execute("SELECT COUNT(*) FROM orders").fetchone()
    print(f"  Pedidos no DB: {cursor[0]}")
    print(f"  Mensagens no Broker: {len(broker.messages)}")
    if cursor[0] == 1 and len(broker.messages) == 0:
        print("  RESULTADO: INCONSISTÊNCIA DETECTADA! (Pedido existe, mas evento sumiu)")

    print("\n=== CENÁRIO 2: Sucesso com Transactional Outbox ===")
    db = Database()
    broker = MockBroker()
    service = OutboxService(db)
    relay = OutboxRelay(db, broker)

    service.create_order("ORD-002", 250.0)
    relay.process() # O relay processa o que foi salvo na outbox

    cursor = db.execute("SELECT COUNT(*) FROM orders").fetchone()
    print(f"  Pedidos no DB: {cursor[0]}")
    print(f"  Mensagens no Broker: {len(broker.messages)}")

    print("\n=== CENÁRIO 3: O Equívoco da Entrega Única (At-Least-Once) ===")
    # O Relay garante a entrega, mas se ele falhar após o publish, ele enviará de novo.
    # Isso prova que o sistema é "At-least-once" e não "Exactly-once".
    
    db = Database()
    broker = MockBroker()
    service = OutboxService(db)
    relay = OutboxRelay(db, broker)

    service.create_order("ORD-003", 500.0)
    
    # Primeira tentativa do Relay: ele publica, mas "morre" antes de marcar como processado
    relay.simulate_crash_after_publish = True
    relay.process()

    # Segunda tentativa do Relay: ele lê o mesmo evento e publica de novo
    print("  [Relay] Reiniciando após crash...")
    relay.simulate_crash_after_publish = False
    relay.process()

    print(f"  Mensagens totais no Broker para o mesmo pedido: {len(broker.messages)}")
    if len(broker.messages) > 1:
        print("  RESULTADO: DUPLICIDADE DETECTADA! (O consumidor DEVE ser idempotente)")

if __name__ == "__main__":
    run_experiment()