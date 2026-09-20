import logging

# Configuração de log para visibilidade clara do fluxo
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class SagaError(Exception):
    """Exceção customizada para falhas em etapas da Saga."""
    pass

class SagaStep:
    """Interface para uma etapa da Saga."""
    def execute(self, transaction_id: str):
        raise NotImplementedError
    
    def compensate(self, transaction_id: str):
        raise NotImplementedError

class PaymentService(SagaStep):
    def __init__(self):
        self.processed_payments = {}  # Simula DB: {tx_id: amount}
        self.refunded_payments = set() # Para testar idempotência

    def execute(self, transaction_id: str):
        amount = 100.0
        logger.info(f"[PaymentService] Cobrando R$ {amount} para {transaction_id}...")
        self.processed_payments[transaction_id] = amount
        return True

    def compensate(self, transaction_id: str):
        if transaction_id in self.refunded_payments:
            logger.info(f"[PaymentService] REEMBOLSO IGNORADO (Idempotência): {transaction_id} já foi reembolsado.")
            return
        
        if transaction_id in self.processed_payments:
            amount = self.processed_payments.pop(transaction_id)
            self.refunded_payments.add(transaction_id)
            logger.info(f"[PaymentService] REEMBOLSO REALIZADO: R$ {amount} devolvidos para {transaction_id}.")
        else:
            logger.info(f"[PaymentService] NADA PARA REEMBOLSAR para {transaction_id}.")

class InventoryService(SagaStep):
    def __init__(self, fail_next=False):
        self.fail_next = fail_next
        self.reserved_items = set()

    def execute(self, transaction_id: str):
        if self.fail_next:
            logger.error(f"[InventoryService] FALHA CRÍTICA: Item indisponível para {transaction_id}!")
            raise SagaError("Estoque insuficiente")
        
        logger.info(f"[InventoryService] Item reservado para {transaction_id}.")
        self.reserved_items.add(transaction_id)
        return True

    def compensate(self, transaction_id: str):
        if transaction_id in self.reserved_items:
            self.reserved_items.remove(transaction_id)
            logger.info(f"[InventoryService] ESTOQUE LIBERADO para {transaction_id}.")
        else:
            logger.info(f"[InventoryService] NADA PARA LIBERAR para {transaction_id}.")

class SagaOrchestrator:
    def __init__(self):
        self.steps = []
        self.executed_steps = []

    def add_step(self, step: SagaStep):
        self.steps.append(step)

    def run(self, transaction_id: str):
        logger.info(f"\n--- Iniciando Saga para {transaction_id} ---")
        self.executed_steps = []
        
        try:
            for step in self.steps:
                step.execute(transaction_id)
                self.executed_steps.append(step)
            logger.info("--- Saga Concluída com Sucesso! ---")
            return True
        except SagaError as e:
            logger.warning(f"--- Falha detectada: {e}. Iniciando Compensação... ---")
            self._rollback(transaction_id)
            logger.info("--- Saga Rollback Concluído (Estado Consistente) ---")
            return False

    def _rollback(self, transaction_id: str):
        # Executa a compensação em ordem reversa (LIFO)
        for step in reversed(self.executed_steps):
            try:
                step.compensate(transaction_id)
            except Exception as e:
                logger.error(f"ERRO CRÍTICO NA COMPENSAÇÃO: {e}. Requer intervenção manual!")

def run_experiment():
    # 1. TESTE DE SUCESSO
    logger.info(">>> TESTE 1: Fluxo de Sucesso")
    payment_svc = PaymentService()
    inventory_svc = InventoryService()
    
    orchestrator = SagaOrchestrator()
    orchestrator.add_step(payment_svc)
    orchestrator.add_step(inventory_svc)
    
    success = orchestrator.run("TX_SUCESSO")
    assert success is True

    # 2. TESTE DE FALHA E COMPENSAÇÃO
    logger.info("\n>>> TESTE 2: Falha no Estoque (Gatilha Rollback)")
    payment_svc_fail = PaymentService()
    inventory_svc_fail = InventoryService(fail_next=True)
    
    orchestrator_fail = SagaOrchestrator()
    orchestrator_fail.add_step(payment_svc_fail)
    orchestrator_fail.add_step(inventory_svc_fail)
    
    success_fail = orchestrator_fail.run("TX_FALHA")
    assert success_fail is False
    # Verifica se o pagamento foi de fato reembolsado
    assert "TX_FALHA" not in payment_svc_fail.processed_payments
    assert "TX_FALHA" in payment_svc_fail.refunded_payments

    # 3. TESTE DE IDEMPOTÊNCIA
    logger.info("\n>>> TESTE 3: Idempotência na Compensação")
    # Simulamos o orquestrador chamando a compensação duas vezes para a mesma TX
    payment_svc_fail.compensate("TX_FALHA") 

    logger.info("\n[EXPERIMENTO FINALIZADO COM SUCESSO]")

if __name__ == "__main__":
    run_experiment()