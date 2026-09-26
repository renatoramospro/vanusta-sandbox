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
        self.status = "PENDING"
        self._compensated_attempts = 0

    def execute(self):
        self.status = "CREATED"
        print("[OrderService] Pedido criado com sucesso (order_123).")
        return "order_123"

    def compensate_with_retry(self, ref):
        # Simula falha transitória na primeira tentativa, exigindo política de retry
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"[OrderService] Tentativa {attempt}/{max_attempts} de compensar pedido {ref}...")
            if attempt == 1:
                print("[OrderService] Erro na compensação: Falha transitória de rede ao compensar pedido. Reprogramando retry...")
                continue
            else:
                self.status = "CANCELLED"
                print(f"[OrderService] Pedido {ref} compensado com sucesso na tentativa {attempt}.")
                return True
        print(f"[OrderService] FALHA CRÍTICA: Esgotadas tentativas de compensação para {ref}. Enviando para DLQ.")
        return False

class PaymentService:
    def __init__(self):
        self.status = "PENDING"

    def execute(self):
        self.status = "PAID"
        print("[PaymentService] Pagamento processado com sucesso (pay_456).")
        return "pay_456"

    def get_status(self, ref):
        # Consulta de status prévia para resolver ambiguidade de timeout
        print(f"[PaymentService] CONSULTA DE STATUS: Verificando se transação {ref} foi efetivamente concluída...")
        return "COMPLETED"

    def compensate(self, ref):
        self.status = "REFUNDED"
        print(f"[PaymentService] Estornando pagamento {ref}...")
        return True


# --- 3. Orquestrador Centralizado de Sagas ---

class Orchestrator:
    def __init__(self, order_service, payment_service, inventory_service):
        self.order_service = order_service
        self.payment_service = payment_service
        self.inventory_service = inventory_service
        self.completed_steps = []

    def run_saga(self):
        print("\n--- Iniciando Execução da Saga Orquestrada ---")
        try:
            # Etapa 1: Pedido
            order_ref = self.order_service.execute()
            self.completed_steps.append(('order', order_ref))

            # Etapa 2: Pagamento
            payment_ref = self.payment_service.execute()
            self.completed_steps.append(('payment', payment_ref))

            # Etapa 3: Inventário (com falha injetada simulando timeout)
            try:
                self.inventory_service.execute("inv_ref")
                self.completed_steps.append(('inventory', "inv_789"))
            except TimeoutError:
                print("[Orchestrator] Timeout detectado no Inventário. Resolvendo ambiguidade consultando pagamento anterior...")
                # Resolução de ambiguidade de timeout via consulta de status prévia
                pay_current_status = self.payment_service.get_status(payment_ref)
                if pay_current_status == "COMPLETED":
                    print("[Orchestrator] Status confirmado: Pagamento ocorreu. Disparando compensação em cascata.")
                raise

        except (ValueError, TimeoutError) as e:
            print(f"[Orchestrator] Falha capturada na Saga: {e}. Iniciando compensação em ordem inversa...")
            
            # Executa compensação em ordem inversa
            for step_type, ref in reversed(self.completed_steps):
                if step_type == 'payment':
                    self.payment_service.compensate(ref)
                elif step_type == 'order':
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
    
    results = []
    errors = []
    
    def thread_task(ref_id):
        try:
            res = shared_inv.execute(ref_id)
            results.append(res)
        except Exception as exc:
            errors.append(str(exc))

    threads = [
        threading.Thread(target=thread_task, args=(f"ref_{i}",))
        for i in range(3)
    ]
    
    for t in threads:
        t.start()
        
    for t in threads:
        t.join()

    print(f"Reservas bem-sucedidas: {len(results)}, Falhas de estoque: {len(errors)}")
    print(f"Estoque final após concorrência (esperado 0, pois estoque inicial era 2 e 3 threads tentaram): {shared_inv.stock}")
    
    assert len(results) == 2
    assert len(errors) == 1
    assert shared_inv.stock == 0
    print("Teste 2 de isolamento de concorrência executado com sucesso!")