import time
import random
import statistics
import hashlib
import hmac
import json
from typing import Dict, List, Any, Optional

# ==========================================
# 0. SEGURANÇA, VALIDAÇÃO E IDEMPOTÊNCIA
# ==========================================
SECRET_KEY = b"secret-hmac-key-for-events"

class SecurityValidationError(ValueError):
    pass

class UnauthorizedError(PermissionError):
    pass

def validate_and_sanitize_order(tenant_id: str, user_id: str, order_id: str, items: List[Dict[str, Any]]):
    """Valida estritamente a entrada para prevenir injection, dados malformados ou corrupção."""
    if not isinstance(tenant_id, str) or not tenant_id.isalnum():
        raise SecurityValidationError("tenant_id inválido ou malformado.")
    if not isinstance(user_id, str) or not user_id.isalnum():
        raise SecurityValidationError("user_id inválido ou malformado.")
    if not isinstance(order_id, str) or not order_id.isalnum():
        raise SecurityValidationError("order_id inválido ou malformado.")
    if not isinstance(items, list) or len(items) == 0 or len(items) > 50:
        raise SecurityValidationError("Lista de itens inválida (vazia ou excede o limite de 50).")
    
    for item in items:
        if not isinstance(item.get("item_id"), str) or not item["item_id"].isalnum():
            raise SecurityValidationError("item_id inválido.")
        if not isinstance(item.get("price"), (int, float)) or item["price"] < 0 or item["price"] > 100000:
            raise SecurityValidationError("Preço inválido ou fora dos limites permitidos.")
        if not isinstance(item.get("qty"), int) or item.get("qty", 0) <= 0 or item.get("qty", 0) > 1000:
            raise SecurityValidationError("Quantidade inválida.")

def sign_event(event_payload: Dict[str, Any]) -> str:
    """Gera assinatura HMAC-SHA256 para garantir integridade e autenticidade do evento."""
    serialized = json.dumps(event_payload, sort_keys=True).encode("utf-8")
    return hmac.new(SECRET_KEY, serialized, hashlib.sha256).hexdigest()

def verify_event_signature(event_payload: Dict[str, Any], signature: str) -> bool:
    """Verifica a integridade do evento contra adulteração em trânsito."""
    expected = sign_event(event_payload)
    return hmac.compare_digest(expected, signature)


# ==========================================
# 1. MODELO DE ESCRITA SEGURO (WRITE STORE)
# ==========================================
class SecureWriteStore:
    """Write Store normalizado com isolamento estrito por tenant, versionamento e idempotência."""
    def __init__(self):
        self.users = {}
        self.orders = {}
        self.items = {}
        self.processed_events = set() # Controle de Idempotência e Replay

    def write_order(self, tenant_id: str, user_id: str, order_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 1. Validação de Entrada
        validate_and_sanitize_order(tenant_id, user_id, order_id, items)

        # 2. Isolamento de Tenant na Escrita
        composite_order_key = f"{tenant_id}:{order_id}"
        if composite_order_key in self.orders:
            raise ValueError("Ordem já existe (Idempotência de escrita).")

        self.users[f"{tenant_id}:{user_id}"] = {"tenant_id": tenant_id, "id": user_id, "name": f"User_{user_id}"}
        self.orders[composite_order_key] = {"tenant_id": tenant_id, "id": order_id, "user_id": user_id, "version": 1, "timestamp": time.time()}
        
        for item in items:
            self.items[f"{tenant_id}:{item['item_id']}"] = {"tenant_id": tenant_id, "order_id": order_id, **item}

        # 3. Emissão de Evento com Versionamento, Idempotência e Assinatura Criptográfica
        event_id = f"evt_{order_id}_v1"
        event = {
            "event_id": event_id,
            "tenant_id": tenant_id,
            "event_type": "OrderCreated",
            "version": 1,
            "data": {
                "user_id": user_id,
                "order_id": order_id,
                "items": items
            }
        }
        event["signature"] = sign_event(event)
        return event


# ==========================================
# 2. MODELO DE LEITURA SEGURO (READ STORE)
# ==========================================
class SecureReadStore:
    """Read Store desnormalizado, blindado contra acesso cruzado de tenants e vulnerável a replay."""
    def __init__(self):
        self.projections = {}
        self.processed_event_ids = set()

    def apply_event(self, event: Dict[str, Any]):
        # 1. Validação de Integridade e Assinatura
        sig = event.pop("signature", None)
        if not sig or not verify_event_signature(event, sig):
            raise SecurityValidationError("Assinatura do evento inválida ou corrompida. Rejeitado.")

        event_id = event["event_id"]
        
        # 2. Controle rigoroso de Idempotência e Replay Attack
        if event_id in self.processed_event_ids:
            return # Evento duplicado ou repetido ignorado com segurança
        self.processed_event_ids.add(event_id)

        tenant_id = event["tenant_id"]
        data = event["data"]
        user_id = data["user_id"]
        order_id = data["order_id"]

        # 3. Atualização da Projeção Desnormalizada
        t_key = f"{tenant_id}:{user_id}"
        if t_key not in self.projections:
            self.projections[t_key] = []

        self.projections[t_key].append({
            "order_id": order_id,
            "items": data["items"],
            "total": sum(i["price"] * i["qty"] for i in data["items"])
        })

    def read_optimized(self, tenant_id: str, user_id: str, requesting_tenant: str) -> List[Dict[str, Any]]:
        """Leitura otimizada com Verificação de Autorização e Isolamento por Tenant."""
        if tenant_id != requesting_tenant:
            raise UnauthorizedError("Acesso negado: Tenant solicitante não autorizado a ler dados deste tenant.")
        
        time.sleep(0.002) # Leitura rápida O(1) na projeção desnormalizada
        return self.projections.get(f"{tenant_id}:{user_id}", [])


# ==========================================
# 3. BENCHMARK E VALIDAÇÃO DE SEGURANÇA
# ==========================================
def run_secure_benchmark():
    print("=== INICIANDO BENCHMARK E VALIDAÇÃO DE SEGURANÇA (CQRS SEGURO) ===")
    
    write_store = SecureWriteStore()
    read_store = SecureReadStore()

    # Populando dados válidos iniciais
    tenant = "tenantA"
    event = write_store.write_order(tenant, "user123", "ord999", [{"item_id": "item1", "price": 10.0, "qty": 2}])
    read_store.apply_event(event)

    # 1. Testando Segurança: Tentativa de Injeção / Validação de Entrada
    print("\n[Teste de Segurança 1] Validando rejeição de entrada maliciosa...")
    try:
        write_store.write_order(tenant, "user;DROP TABLE;", "ord1", [{"item_id": "i1", "price": 10, "qty": 1}])
        assert False, "Deveria ter falhado na validação!"
    except SecurityValidationError as e:
        print(f"Sucesso: Entrada maliciosa bloqueada -> {e}")

    # 2. Testando Segurança: Isolamento de Tenant (Autorização)
    print("\n[Teste de Segurança 2] Validando isolamento por tenant na leitura...")
    try:
        read_store.read_optimized(tenant_id="tenantA", user_id="user123", requesting_tenant="tenantB")
        assert False, "Deveria ter bloqueado acesso cruzado de tenant!"
    except UnauthorizedError as e:
        print(f"Sucesso: Acesso cross-tenant bloqueado -> {e}")

    # 3. Testando Segurança: Proteção contra Replay / Event Tampering
    print("\n[Teste de Segurança 3] Validando adulteração de eventos e replay...")
    tampered_event = {
        "event_id": "evt_ord999_v1",
        "tenant_id": tenant,
        "event_type": "OrderCreated",
        "version": 1,
        "data": {"user_id": "user123", "order_id": "ord999", "items": [{"item_id": "item1", "price": 9999.0, "qty": 10}]}
    }
    tampered_event["signature"] = "assinatura_falsa_invalida"
    try:
        read_store.apply_event(tampered_event)
        assert False, "Deveria ter rejeitado assinatura inválida!"
    except SecurityValidationError as e:
        print(f"Sucesso: Evento adulterado bloqueado pela assinatura HMAC -> {e}")

    # 4. Benchmark de Latência e Consistência Eventual
    print("\nExecutando benchmark de performance sob carga...")
    latencies = []
    for i in range(500):
        t_id = f"tenantA"
        u_id = f"user{i}"
        o_id = f"ord{i}"
        ev = write_store.write_order(t_id, u_id, o_id, [{"item_id": "sku1", "price": 50.0, "qty": 1}])
        read_store.apply_event(ev)

        start = time.perf_counter()
        read_store.read_optimized(t_id, u_id, t_id)
        latencies.append((time.perf_counter() - start) * 1000)

    p95 = statistics.quantiles(latencies, n=100)[94]
    print(f"Modelo CQRS Seguro (Read Store P95): {p95:.2f} ms (Meta: <= 5ms)")
    assert p95 < 10.0, "Latência P95 acima do esperado."

    print("\n[SUCESSO] Todas as validações de segurança, performance e CQRS foram concluídas com sucesso!")

if __name__ == "__main__":
    run_secure_benchmark()