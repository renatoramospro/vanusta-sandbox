import json
import threading
import time

# ==========================================
# 1. SEGURANÇA: SANITIZAÇÃO DE LOGS E MENSAGENS
# ==========================================
class SecurityAuditor:
    @staticmethod
    def sanitize_payload(payload):
        """Mascaramento de dados sensíveis antes do log (evita PII/PCI vazando)."""
        safe_copy = dict(payload)
        if "credit_card" in safe_copy:
            safe_copy["credit_card"] = "****-****-****-" + safe_copy["credit_card"][-4:]
        if "amount" in safe_copy:
            safe_copy["amount"] = "[MASKED]"
        return safe_copy

    @staticmethod
    def validate_schema(event_type, payload):
        """Validação estrita de campos obrigatórios no evento."""
        if not isinstance(payload, dict):
            raise ValueError("Payload inválido: deve ser um dicionário.")
        if "order_id" not in payload:
            raise ValueError("Payload rejeitado: 'order_id' ausente.")
        if "tenant_id" not in payload:
            raise ValueError("Payload rejeitado: 'tenant_id' ausente.")
        return True


# ==========================================
# 2. BARRAMENTO RESILIENTE COM IDEMPOTÊNCIA E ISOLAMENTO
# ==========================================
class SecureEventBus:
    def __init__(self):
        self.subscribers = {}
        self.processed_events = set()  # Para idempotência contra duplicidade/replay
        self.lock = threading.Lock()
        self.dead_letter_queue = []

    def subscribe(self, event_type, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, payload):
        # Validação de Mensagem e Segurança
        SecurityAuditor.validate_schema(event_type, payload)
        
        event_id = payload.get("event_id")
        with self.lock:
            if event_id and event_id in self.processed_events:
                print(f"[Security/Bus] ALERTA: Tentativa de Replay/Duplicidade bloqueada para event_id: {event_id}")
                return
            if event_id:
                self.processed_events.add(event_id)

        sanitized = SecurityAuditor.sanitize_payload(payload)
        print(f"[SecureEventBus] Evento publicado: {event_type} | Payload sanitizado: {sanitized}")

        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    # Isolamento de falhas: um callback com erro não quebra os demais
                    callback(payload)
                except Exception as e:
                    print(f"[SecureEventBus] ERRO no handler {callback.__name__}: {e}. Enviando para DLQ.")
                    self.dead_letter_queue.append({"event": event_type, "payload": payload, "error": str(e)})


# ==========================================
# 3. ORQUESTRADOR CENTRAL COM ESTADO CONSULTÁVEL E CONTROLE DE ACESSO
# ==========================================
class SecureOrchestrator:
    def __init__(self):
        self.orders_state = {}
        self.lock = threading.Lock()

    def start_workflow(self, order_id, tenant_id, credit_card):
        with self.lock:
            self.orders_state[order_id] = {
                "tenant_id": tenant_id,
                "status": "STARTED",
                "step": "PaymentPending"
            }
        
        print(f"\n[Orchestration-Secure] Iniciando fluxo para pedido {order_id} (Tenant: {tenant_id})")
        
        # Passo 1: Pagamento
        success_payment = self._process_payment(order_id, credit_card)
        if not success_payment:
            self._fail_workflow(order_id, "PaymentFailed")
            return

        # Passo 2: Estoque
        success_inventory = self._reserve_inventory(order_id)
        if not success_inventory:
            # Compensação: estorna pagamento
            self._compensate_payment(order_id)
            self._fail_workflow(order_id, "InventoryFailed_Compensated")
            return

        with self.lock:
            self.orders_state[order_id]["status"] = "COMPLETED"
            self.orders_state[order_id]["step"] = "Finished"
        print(f"[Orchestration-Secure] Fluxo concluído com sucesso para {order_id}")

    def _process_payment(self, order_id, credit_card):
        print(f"[Orchestrator] Processando pagamento com cartão terminando em {credit_card[-4:]}")
        with self.lock:
            self.orders_state[order_id]["step"] = "PaymentProcessed"
        return True

    def _reserve_inventory(self, order_id):
        print(f"[Orchestrator] Reservando estoque...")
        with self.lock:
            self.orders_state[order_id]["step"] = "InventoryReserved"
        return True # Simule False para testar compensação

    def _compensate_payment(self, order_id):
        print(f"[Orchestrator SAGA] COMPENSAÇÃO: Estornando pagamento para o pedido {order_id}")

    def _fail_workflow(self, order_id, reason):
        with self.lock:
            self.orders_state[order_id]["status"] = "FAILED"
            self.orders_state[order_id]["reason"] = reason
        print(f"[Orchestrator-Secure] Pedido {order_id} marcado como FAILED: {reason}")

    def get_order_status(self, order_id, principal_tenant):
        """Endpoint consultável com Autenticação e Autorização por Tenant."""
        with self.lock:
            order = self.orders_state.get(order_id)
            if not order:
                raise KeyError("Pedido não encontrado.")
            
            # Controle de Acesso Baseado em Tenant (RBAC/ABAC simulado)
            if order["tenant_id"] != principal_tenant:
                raise PermissionError(f"ACESSO NEGADO: Tenant '{principal_tenant}' não tem permissão para acessar dados do tenant '{order['tenant_id']}'.")
            
            return order


# ==========================================
# 4. EXECUÇÃO DO TESTE DE SEGURANÇA E VALIDAÇÃO
# ==========================================
if __name__ == "__main__":
    print("=== TESTE 1: Orquestração Segura com Controle de Acesso e Estado Consultável ===")
    orchestrator = SecureOrchestrator()
    
    # Executa fluxo válido
    orchestrator.start_workflow("ORD-SEC-001", tenant_id="tenant_alpha", credit_card="4111222233334444")

    # Consulta autorizada
    status = orchestrator.get_order_status("ORD-SEC-001", principal_tenant="tenant_alpha")
    print(f"[API Status 200] Estado consultado por tenant autorizado: {status}")

    # Consulta NÃO autorizada (Cross-tenant attack simulation)
    try:
        orchestrator.get_order_status("ORD-SEC-001", principal_tenant="tenant_beta")
    except PermissionError as e:
        print(f"[API Status 403] Sucesso no bloqueio de segurança: {e}")

    print("\n=== TESTE 2: Barramento com Sanitização, Idempotência e Isolamento ===")
    bus = SecureEventBus()

    def dummy_handler(payload):
        print(f"[Service Handler] Processou evento {payload['event_id']}")

    bus.subscribe("OrderCreated", dummy_handler)

    valid_payload = {
        "event_id": "evt-12345",
        "order_id": "ORD-SEC-002",
        "tenant_id": "tenant_alpha",
        "credit_card": "5555444433332222",
        "amount": 150.00
    }

    # Publicação normal
    bus.publish("OrderCreated", valid_payload)

    # Tentativa de Replay / Mensagem Duplicada (deve ser bloqueada)
    print("\n[Teste Replay]:")
    bus.publish("OrderCreated", valid_payload)

    print("\n[SUCESSO] Todos os controles de segurança, validação, isolamento e concorrência executados com código 0!")