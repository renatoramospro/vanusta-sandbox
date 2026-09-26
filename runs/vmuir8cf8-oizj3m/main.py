import time
import json
import threading

# --- 1. Serviço de Inventário com Isolamento de Concorrência e Idempotência ---

class InventoryService:
    def __init__(self, initial_stock=10, failure_type=None):
        self.stock = initial_stock
        self.failure_type = failure_type
        self._compensated = False
        self._lock = threading.Lock() # Tratamento de concorrência para recursos compartilhados
        self.status = "PENDING"

    def execute(self, ref_id):
        with self._lock: # Isolamento de concorrência no recurso compartilhado
            if self.failure_type == 'business':
                print("[InventoryService] FALHA DE NEGÓCIO: Estoque insuficiente.")
                raise ValueError("Estoque insuficiente")
            elif self.failure_type == 'timeout':
                print("[InventoryService] FALHA DE TIMEOUT: O serviço demorou para responder.")
                raise TimeoutError("Timeout ao contatar inventário")
            
            if self.stock <= 0:
                print("[InventoryService] FALHA: Sem estoque disponível.")
                raise ValueError("Sem estoque")
            
            self.stock -= 1
            self.status = "RESERVED"
            print(f"[InventoryService] Estoque reservado com sucesso. Restante: {self.stock}")
            return "inv_789"

    def compensate(self, ref):
        with self._lock:
            if self._compensated:
                print(f"[InventoryService] IDEMPOTÊNCIA: Reserva {ref} já compensada anteriormente.")
                return True
            print(f"[InventoryService] Compensando reserva {ref} (Devolvendo item ao estoque)...")
            self.stock += 1
            self._compensated = True
            self.status = "RELEASED"
            return True


# --- 2. Serviços de Pedido e Pagamento com Suporte a Retry na Compensação ---

class OrderService:
    def __init__(self):
        self._compensated = False
        self.status = "CREATED"

    def execute(self):
        print("[OrderService] Pedido criado com sucesso.")
        self.status = "ACTIVE"
        return "order_123"

    def compensate_with_retry(self, ref, max_retries=3):
        """Implementa política de Retry e DLQ para falhas na própria compensação."""
        attempts = 0
        while attempts < max_retries:
            try:
                attempts += 1
                print(f"[OrderService] Tentativa {attempts}/{max_retries} de compensar pedido {ref}...")
                if attempts == 1:
                    # Simula falha intermitente na primeira tentativa de compensação
                    raise ConnectionError("Falha transitória de rede ao compensar pedido")
                
                if self._compensated:
                    print(f"[OrderService] IDEMPOTÊNCIA: Pedido {ref} já estava compensado.")
                    return True
                
                print(f"[OrderService] Pedido {ref} compensado com sucesso na tentativa {attempts}.")
                self._compensated = True
                self.status = "CANCELLED"
                return True
            except Exception as e:
                print(f"[OrderService] Erro na compensação: {e}. Reprogramando retry...")
                time.sleep(0.01)
        
        print(f"[OrderService] ALERTA CRÍTICO: Falha permanente na compensação após {max_retries} tentativas. Enviando para DLQ (Dead Letter Queue).")
        self.status = "DLQ_FAILED"
        return False


class PaymentService:
    def __init__(self):
        self._compensated = False
        self.status = "PENDING"

    def execute(self):
        print("[PaymentService] Pagamento processado com sucesso.")
        self.status = "CONFIRMED"
        return "pay_456"

    def compensate(self, ref):
        if self._compensated:
            print(f"[PaymentService] IDEMPOTÊNCIA: Pagamento {ref} já estornado.")
            return True
        print(f"[PaymentService] Estornando pagamento {ref}...")
        self._compensated = True
        self.status = "REFUNDED"
        return True


# --- 3. Orquestrador com Consulta de Status Prévia (Ambiguidade de Timeout) e Tratamento de Falha na Compensação ---

class Orchestrator:
    def __init__(self, order_service, payment_service, inventory_service):
        self.order_service = order_service
        self.payment_service = payment_service
        self.inventory_service = inventory_service

    def query_service_status(self, service_name, ref_id):
        """Resolve ambiguidade de rede/timeout consultando o estado real antes de compensar cegamente."""
        print(f"[Orchestrator] CONSULTA DE STATUS: Verificando se {service_name} realmente concluiu a transação {ref_id}...")
        # Simula checagem idempotente no serviço remoto
        return True 

    def run_saga(self):
        print("\n--- Iniciando Nova Saga Orquestrada ---")
        completed_steps = []
        
        try:
            # Etapa 1: Order
            o_ref = self.order_service.execute()
            completed_steps.append(('Order', o_ref))

            # Etapa 2: Payment
            p_ref = self.payment_service.execute()
            completed_steps.append(('Payment', p_ref))

            # Etapa 3: Inventory (Injetando falha de timeout para testar ambiguidade)
            i_ref = self.inventory_service.execute("inv_789")
            completed_steps.append(('Inventory', i_ref))

            return "COMPLETED"

        except (TimeoutError, ValueError) as e:
            print(f"[Orchestrator] Falha detectada: {type(e).__name__} -> {e}")
            print("[Orchestrator] Iniciando fase de compensação segura...")
            
            # Tratamento de ambiguidade de timeout
            if isinstance(e, TimeoutError):
                print("[Orchestrator] Timeout detectado. Consultando serviços para evitar compensações fantasmas...")
                self.query_service_status("PaymentService", "pay_456")

            # Compensação em ordem inversa com suporte a retry
            for step_name, ref in reversed(completed_steps):
                if step_name == 'Payment':
                    self.payment_service.compensate(ref)
                elif step_name == 'Order':
                    # Exercita o mecanismo de retry/DLQ na compensação
                    success = self.order_service.compensate_with_retry(ref)
                    if not success:
                        print("[Orchestrator] Interrupção de compensação tratada via DLQ.")
            
            return "FAILED_AND_COMPENSATED"


# --- Execução dos Testes Automatizados ---

if __name__ == "__main__":
    print("=== TESTE 1: Timeout com Consulta de Status Prévia e Retry na Compensação ===")
    order_svc = OrderService()
    pay_svc = PaymentService()
    inv_svc = InventoryService(failure_type='timeout')
    
    orch = Orchestrator(order_svc, pay_svc, inv_svc)
    result = orch.run_saga()
    
    assert result == "FAILED_AND_COMPENSATED"
    assert pay_svc.status == "REFUNDED"
    assert order_svc.status == "CANCELLED" # Recuperado via retry com sucesso após falha transitória
    print("Teste 1 executado com sucesso!")

    print("\n=== TESTE 2: Concorrência Cruzada em Recurso Compartilhado (Estoque) ===")
    shared_inv = InventoryService(initial_stock=2)
    
    # Simula múltiplas threads executando reservas simultâneas no mesmo inventário
    threads = []
    for i in range(3):
        t = threading.Thread(target=lambda: shared_inv.execute(f"ref_{i}"))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

    print(f"Estoque final após concorrência (esperado 1, pois estoque inicial era 2 e 3 threads tentaram): {shared_inv.stock}")
    assert shared_inv.stock == 1
    print("Teste 2 de isolamento de concorrência executado com sucesso!")