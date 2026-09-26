import time

# --- Serviços Participantes simulados ---
class OrderService:
    def execute(self):
        print("[OrderService] Pedido criado com sucesso.")
        return "order_123"
    def compensate(self, ref):
        print(f"[OrderService] Compensando pedido {ref} (Cancelando pedido)...")

class PaymentService:
    def execute(self):
        print("[PaymentService] Pagamento processado com sucesso.")
        return "pay_456"
    def compensate(self, ref):
        print(f"[PaymentService] Compensando pagamento {ref} (Estornando valor)...")

class InventoryService:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self._compensated = False

    def execute(self):
        if self.should_fail:
            print("[InventoryService] FALHA: Estoque indisponível!")
            raise RuntimeError("Falha de negócio no Inventário")
        print("[InventoryService] Estoque reservado com sucesso.")
        return "inv_789"

    def compensate(self, ref):
        # Garantindo Idempotência
        if self._compensated:
            print(f"[InventoryService] AVISO: Compensação para {ref} já havia sido executada (Idempotência tratada).")
            return
        print(f"[InventoryService] Compensando inventário {ref} (Liberando estoque)...")
        self._compensated = True


# --- Orquestrador de Sagas ---
class Orchestrator:
    def __init__(self, order_svc, payment_svc, inventory_svc):
        self.order_svc = order_svc
        self.payment_svc = payment_svc
        self.inventory_svc = inventory_svc

    def run_saga(self):
        state = "STARTED"
        completed_steps = []
        print("\n--- Iniciando Nova Saga ---")

        try:
            # Etapa 1: Pedido
            ref_order = self.order_svc.execute()
            completed_steps.append(("order", ref_order))

            # Etapa 2: Pagamento
            ref_payment = self.payment_svc.execute()
            completed_steps.append(("payment", ref_payment))

            # Etapa 3: Inventário
            ref_inv = self.inventory_svc.execute()
            completed_steps.append(("inventory", ref_inv))

            state = "COMPLETED"
            print("--- Saga concluída com sucesso! ---\n")
            return state

        except Exception as e:
            print(f"[Orchestrator] Erro detectado: {e}. Iniciando compensação...")
            state = "COMPENSATING"
            self._compensate(completed_steps)
            state = "FAILED"
            print("--- Saga revertida com sucesso (Consistência Eventual Alcançada) ---\n")
            return state

    def _compensate(self, completed_steps):
        # Executa compensação na ordem inversa
        for step_name, ref in reversed(completed_steps):
            if step_name == "inventory":
                self.inventory_svc.compensate(ref)
                # Testando idempotência chamando novamente de propósito
                self.inventory_svc.compensate(ref)
            elif step_name == "payment":
                self.payment_svc.compensate(ref)
            elif step_name == "order":
                self.order_svc.compensate(ref)


if __name__ == "__main__":
    print("=== TESTE 1: Fluxo Completo Bem-Sucedido ===")
    orch_success = Orchestrator(OrderService(), PaymentService(), InventoryService(should_fail=False))
    res1 = orch_success.run_saga()
    assert res1 == "COMPLETED"

    print("=== TESTE 2: Fluxo com Falha na Etapa 3 e Compensação ===")
    orch_failure = Orchestrator(OrderService(), PaymentService(), InventoryService(should_fail=True))
    res2 = orch_failure.run_saga()
    assert res2 == "FAILED"

    print("Todos os testes executados com sucesso!")