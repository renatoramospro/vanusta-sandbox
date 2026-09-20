import time
import random

class SagaError(Exception):
    """Exceção base para falhas na Saga."""
    pass

class ServiceResponse:
    def __init__(self, success, message):
        self.success = success
        self.message = message

# --- MOCKS DE SERVIÇOS ---

class PaymentService:
    def __init__(self):
        self.processed_payments = set()
        self.refunded_payments = set()

    def charge(self, transaction_id, amount):
        print(f"[PaymentService] Cobrando R${amount} para {transaction_id}...")
        self.processed_payments.add(transaction_id)
        return ServiceResponse(True, "Pagamento realizado")

    def refund(self, transaction_id):
        # Demonstração de IDEMPOTÊNCIA
        if transaction_id in self.refunded_payments:
            print(f"[PaymentService] AVISO: Reembolso para {transaction_id} já foi processado (Idempotência aplicada).")
            return ServiceResponse(True, "Já reembolsado")
        
        print(f"[PaymentService] Reembolsando {transaction_id}...")
        self.refunded_payments.add(transaction_id)
        return ServiceResponse(True, "Reembolso realizado")

class InventoryService:
    def __init__(self, fail_on_id=None):
        self.reserved_items = set()
        self.fail_on_id = fail_on_id

    def reserve(self, transaction_id, item_id):
        if transaction_id == self.fail_on_id:
            print(f"[InventoryService] ERRO: Item {item_id} indisponível para {transaction_id}!")
            return ServiceResponse(False, "Estoque insuficiente")
        
        print(f"[InventoryService] Item {item_id} reservado para {transaction_id}.")
        self.reserved_items.add(item_id)
        return ServiceResponse(True, "Estoque reservado")

    def release(self, item_id):
        if item_id in self.reserved_items:
            print(f"[InventoryService] Liberando item {item_id}...")
            self.reserved_items.remove(item_id)
        return ServiceResponse(True, "Estoque liberado")

# --- ORQUESTRADOR ---

class SagaStep:
    def __init__(self, name, action, compensate, args):
        self.name = name
        self.action = action
        self.compensate = compensate
        self.args = args
        self.completed = False

class SagaOrchestrator:
    def __init__(self):
        self.steps = []
        self.executed_steps = []

    def add_step(self, step: SagaStep):
        self.steps.append(step)

    def execute(self):
        print("\n--- Iniciando Saga ---")
        for step in self.steps:
            try:
                print(f"Executando etapa: {step.name}")
                response = step.action(*step.args)
                if not response.success:
                    print(f"Falha na etapa {step.name}: {response.message}")
                    self._compensate()
                    return False
                step.completed = True
                self.executed_steps.append(step)
            except Exception as e:
                print(f"Erro inesperado na etapa {step.name}: {e}")
                self._compensate()
                return False
        print("--- Saga Concluída com Sucesso! ---")
        return True

    def _compensate(self):
        print("\n--- Iniciando Compensação (Rollback Lógico) ---")
        # Compensamos na ordem inversa das que foram concluídas
        for step in reversed(self.executed_steps):
            print(f"Compensando etapa: {step.name}")
            # Em um sistema real, aqui haveria retentativas (retries)
            step.compensate(*step.args)
        print("--- Compensação Finalizada. Sistema em estado consistente. ---")

# --- TESTES ---

def run_test_scenario(name, fail_id=None, duplicate_refund=False):
    print(f"\n{'='*20}\nTESTE: {name}\n{'='*20}")
    
    payment_svc = PaymentService()
    inventory_svc = InventoryService(fail_on_id=fail_id)
    orchestrator = SagaOrchestrator()

    tx_id = "TX_123"
    item_id = "ITEM_ABC"

    # Passo 1: Pagamento
    orchestrator.add_step(SagaStep(
        "Pagamento", 
        payment_svc.charge, 
        payment_svc.refund, 
        (tx_id, 100.0)
    ))

    # Passo 2: Estoque
    orchestrator.add_step(SagaStep(
        "Estoque", 
        inventory_svc.reserve, 
        inventory_svc.release, 
        (tx_id, item_id)
    ))

    success = orchestrator.execute()

    # Simulação do Ataque ao Equívoco: Se houver falha, o orquestrador pode tentar 
    # compensar o mesmo passo duas vezes (ex: timeout de rede na primeira tentativa)
    if not success and duplicate_refund:
        print("\n[Simulação] Tentando compensação duplicada (erro de rede/retry)...")
        payment_svc.refund(tx_id)

    return success, payment_svc, inventory_svc

if __name__ == "__main__":
    # 1. Sucesso Total
    run_test_scenario("Fluxo de Sucesso")

    # 2. Falha no Estoque (Gatilha compensação do pagamento)
    run_test_scenario("Falha no Estoque (Gatilha Compensação)", fail_id="TX_FAIL")

    # 3. Falha + Idempotência (Gatilha compensação duplicada)
    run_test_scenario("Falha + Teste de Idempotência", fail_id="TX_FAIL", duplicate_refund=True)
