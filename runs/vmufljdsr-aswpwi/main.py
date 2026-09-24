import time
from enum import Enum
from typing import Dict, List, Any

# ==========================================
# 1. Definições de Estados e Tipos
# ==========================================
class SagaState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMPENSATING = "COMPENSATING"
    COMPENSATED = "COMPENSATED"

# ==========================================
# 2. Microsserviços Independentes
# ==========================================
class OrderService:
    def __init__(self):
        self.orders = {}

    def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_id = payload["order_id"]
        self.orders[order_id] = "CREATED"
        print(f"[OrderService] Pedido {order_id} criado com sucesso.")
        return {"status": "SUCCESS", "order_id": order_id}

    def cancel_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_id = payload["order_id"]
        # Idempotência: se já estiver cancelado ou não existir, opera sem falhar
        self.orders[order_id] = "CANCELLED"
        print(f"[OrderService] [COMPENSAÇÃO] Pedido {order_id} cancelado/estornado.")
        return {"status": "SUCCESS", "order_id": order_id}


class PaymentService:
    def __init__(self):
        self.payments = {}

    def process_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_id = payload["order_id"]
        self.payments[order_id] = "PAID"
        print(f"[PaymentService] Pagamento para o pedido {order_id} processado com sucesso.")
        return {"status": "SUCCESS", "order_id": order_id}

    _refund_processed = set()
    def refund_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_id = payload["order_id"]
        # Demonstração de idempotência em compensação
        if order_id in self._refund_processed:
            print(f"[PaymentService] [COMPENSAÇÃO-IDEMPOTENTE] Reembolso para {order_id} já havia sido efetuado.")
            return {"status": "SUCCESS", "order_id": order_id}
        
        self._refund_processed.add(order_id)
        self.payments[order_id] = "REFUNDED"
        print(f"[PaymentService] [COMPENSAÇÃO] Reembolso processado para o pedido {order_id}.")
        return {"status": "SUCCESS", "order_id": order_id}


class InventoryService:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.reservations = {}

    def reserve_stock(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_id = payload["order_id"]
        if self.should_fail:
            print(f"[InventoryService] ERRO: Falha ao reservar estoque para o pedido {order_id} (Estoque Insuficiente).")
            return {"status": "FAILURE", "error": "Insufficient Stock"}
        
        self.reservations[order_id] = "RESERVED"
        print(f"[InventoryService] Estoque reservado com sucesso para o pedido {order_id}.")
        return {"status": "SUCCESS", "order_id": order_id}

    def release_stock(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_id = payload["order_id"]
        self.reservations[order_id] = "RELEASED"
        print(f"[InventoryService] [COMPENSAÇÃO] Estoque liberado para o pedido {order_id}.")
        return {"status": "SUCCESS", "order_id": order_id}


# ==========================================
# 3. Orquestrador de Saga (Máquina de Estados)
# ==========================================
class OrchestratorStep:
    def __init__(self, name: str, action, compensation):
        self.name = name
        self.action = action
        self.compensation = compensation

class SagaOrchestrator:
    def __init__(self, saga_id: str, steps: List[OrchestratorStep]):
        self.saga_id = saga_id
        self.steps = steps
        self.state = SagaState.PENDING
        self.completed_steps: List[OrchestratorStep] = []

    def execute(self, payload: Dict[str, Any]) -> SagaState:
        print(f"\n--- Iniciando Saga {self.saga_id} ---")
        self.state = SagaState.RUNNING

        for step in self.steps:
            print(f"[Orchestrator] Executando passo: {step.name}")
            result = step.action(payload)

            if result.get("status") == "SUCCESS":
                self.completed_steps.append(step)
            else:
                print(f"[Orchestrator] Falha detectada no passo {step.name}. Iniciando compensação...")
                self.state = SagaState.FAILED
                self._compensate(payload)
                return self.state

        self.state = SagaState.COMPLETED
        print(f"[Orchestrator] Saga {self.saga_id} concluída com SUCESSO.")
        return self.state

    def _compensate(self, payload: Dict[str, Any]):
        self.state = SagaState.COMPENSATING
        # Executa compensação em ordem inversa (LIFO) dos passos que completaram com sucesso
        for step in reversed(self.completed_steps):
            print(f"[Orchestrator] Compensando passo: {step.name}")
            step.compensation(payload)
        
        self.state = SagaState.COMPENSATED
        print(f"[Orchestrator] Saga {self.saga_id} compensada com sucesso após falha.")


# ==========================================
# 4. Testes e Execução dos Cenários
# ==========================================
if __name__ == "__main__":
    payload = {"order_id": "ORD-999", "items": [{"sku": "SKU-1", "qty": 2}]}

    print("=== CENÁRIO 1: FLUXO FELIZ (TODOS OS PASSOS SUCEDEM) ===")
    order_svc = OrderService()
    payment_svc = PaymentService()
    inventory_svc = InventoryService(should_fail=False)

    steps = [
        OrchestratorStep("OrderStep", order_svc.create_order, order_svc.cancel_order),
        OrchestratorStep("PaymentStep", payment_svc.process_payment, payment_svc.refund_payment),
        OrchestratorStep("InventoryStep", inventory_svc.reserve_stock, inventory_svc.release_stock)
    ]

    orchestrator_success = SagaOrchestrator("SAGA-01", steps)
    final_state_1 = orchestrator_success.execute(payload)
    assert final_state_1 == SagaState.COMPLETED

    print("\n" + "="*50 + "\n")

    print("=== CENÁRIO 2: FLUXO DE FALHA E COMPENSAÇÃO (INVENTORY FALHA) ===")
    order_svc_2 = OrderService()
    payment_svc_2 = PaymentService()
    inventory_svc_2 = InventoryService(should_fail=True) # Força falha no estoque

    steps_fail = [
        OrchestratorStep("OrderStep", order_svc_2.create_order, order_svc_2.cancel_order),
        OrchestratorStep("PaymentStep", payment_svc_2.process_payment, payment_svc_2.refund_payment),
        OrchestratorStep("InventoryStep", inventory_svc_2.reserve_stock, inventory_svc_2.release_stock)
    ]

    orchestrator_failure = SagaOrchestrator("SAGA-02", steps_fail)
    final_state_2 = orchestrator_failure.execute(payload)
    assert final_state_2 == SagaState.COMPENSATED

    # Teste explícito de idempotência na compensação do pagamento
    print("\n--- Testando Idempotência Adicional da Compensação ---")
    payment_svc_2.refund_payment(payload) # Deve lidar graciosamente se chamado duas vezes

    print("\nTodos os testes e cenários executados com sucesso!")