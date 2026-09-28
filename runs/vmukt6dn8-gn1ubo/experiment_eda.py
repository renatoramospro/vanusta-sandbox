import json

# ==========================================
# SIMULAÇÃO DE COREOGRAFIA (Descentralizada)
# ==========================================
# Na coreografia, cada serviço escuta eventos e publica novos eventos.
# Não há um "cérebro" central. O acoplamento é via contratos de eventos.

class ChoreographyEventBus:
    def __init__(self):
        self.subscribers = {}
        self.dependencies_count = 0  # Métrica de acoplamento direto

    def subscribe(self, event_type, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        print(f"[EventBus Choreography] Evento publicado: {event_type} com dados {data}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

class ChoreographyOrderService:
    def __init__(self, bus):
        self.bus = bus
        # Order reage a OrderCreated
        bus.subscribe("OrderCreated", self.on_order_created)

    def create_order(self, order_id):
        print(f"\n[Choreography] OrderService: Criando pedido {order_id}")
        self.bus.publish("OrderCreated", {"order_id": order_id})

    def on_order_created(self, data):
        print(f"[Choreography] OrderService: Pedido {data['order_id']} registrado internamente.")

class ChoreographyPaymentService:
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe("OrderCreated", self.on_order_created)

    def on_order_created(self, data):
        print(f"[Choreography] PaymentService: Processando pagamento para {data['order_id']}")
        # Publica evento de sucesso de pagamento
        self.bus.publish("PaymentProcessed", {"order_id": data['order_id']})

class ChoreographyInventoryService:
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe("PaymentProcessed", self.on_payment_processed)

    def on_payment_processed(self, data):
        print(f"[Choreography] InventoryService: Reservando estoque para {data['order_id']}")
        self.bus.publish("InventoryReserved", {"order_id": data['order_id']})


# ==========================================
# SIMULAÇÃO DE ORQUESTRAÇÃO (Centralizada)
# ==========================================
# Na orquestração, o Saga Orchestrator conhece todos os passos e chama
# explicitamente cada serviço, mantendo um estado centralizado visível.

class MockOrderClient:
    def create_order(self, order_id):
        print(f"[Orchestration] OrderService: Pedido {order_id} criado.")

class MockPaymentClient:
    def process_payment(self, order_id):
        print(f"[Orchestration] PaymentService: Pagamento processado para {order_id}.")
        return True

class MockInventoryClient:
    def reserve_inventory(self, order_id):
        print(f"[Orchestration] InventoryService: Estoque reservado para {order_id}.")
        return True

class SagaOrchestrator:
    def __init__(self):
        self.order_client = MockOrderClient()
        self.payment_client = MockPaymentClient()
        self.inventory_client = MockInventoryClient()
        # Visibilidade de estado centralizada
        self.state_store = {}

    def execute_flow(self, order_id):
        print(f"\n[Orchestration] Iniciando fluxo centralizado para o pedido {order_id}")
        self.state_store[order_id] = "STARTED"

        # Passo 1
        self.order_client.create_order(order_id)
        self.state_store[order_id] = "ORDER_CREATED"

        # Passo 2
        success_pay = self.payment_client.process_payment(order_id)
        if success_pay:
            self.state_store[order_id] = "PAYMENT_PROCESSED"

        # Passo 3
        success_inv = self.inventory_client.reserve_inventory(order_id)
        if success_inv:
            self.state_store[order_id] = "COMPLETED"

    def get_status(self, order_id):
        return self.state_store.get(order_id, "NOT_FOUND")


# ==========================================
# EXECUÇÃO E COMPROVAÇÃO DOS RESULTADOS
# ==========================================
if __name__ == "__main__":
    print("--- 1. EXECUTANDO COREOGRAFIA ---")
    bus = ChoreographyEventBus()
    ord_svc = ChoreographyOrderService(bus)
    pay_svc = ChoreographyPaymentService(bus)
    inv_svc = ChoreographyInventoryService(bus)

    ord_svc.create_order("ORD-999")

    print("\n--- 2. EXECUTANDO ORQUESTRAÇÃO ---")
    orchestrator = SagaOrchestrator()
    orchestrator.execute_flow("ORD-888")
    
    # Demonstração da visibilidade de estado centralizada
    status = orchestrator.get_status("ORD-888")
    print(f"\n[Orchestration Visibility] Estado atual do pedido ORD-888 via API/Dashboard: {status}")
    assert status == "COMPLETED", "O estado final do pedido orquestrado deve ser COMPLETED"

    print("\n[SUCESSO] Experimento executado e validado sem erros!")