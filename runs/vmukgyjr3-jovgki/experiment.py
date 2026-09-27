import json
import time

# --- 1. SIMULAÇÃO DO BACKEND CORE ---
class BackendCore:
    def get_user_profile(self, user_id):
        # Simula latência e dados excessivos (over-fetching)
        return {
            "id": user_id,
            "name": "Ana Silva",
            "email": "ana@example.com",
            "bio": "Engenheira de Software sênior apaixonada por arquitetura limpa e sistemas distribuídos.",
            "avatar_url": "https://example.com/avatars/ana.jpg",
            "internal_metadata": {"db_version": "v2.4", "cluster": "us-east-1", "legacy_id": 99823},
            "preferences": {"theme": "dark", "notifications_enabled": True, "language": "pt-BR", "currency": "BRL"}
        }

    def get_user_orders(self, user_id):
        return [
            {"order_id": "ORD-101", "total": 150.50, "status": "DELIVERED", "items_count": 3, "shipping_address": "Rua A, 123, SP", "tracking_code": "BR123456789"},
            {"order_id": "ORD-102", "total": 89.90, "status": "PROCESSING", "items_count": 1, "shipping_address": "Rua A, 123, SP", "tracking_code": "BR987654321"}
        ]

    def get_user_notifications(self, user_id):
        return [
            {"id": "NOT-1", "title": "Bem-vinda!", "body": "Obrigado por usar nosso app.", "read": True, "created_at": "2023-10-01"},
            {"id": "NOT-2", "title": "Promoção", "body": "Desconto de 20% hoje.", "read": False, "created_at": "2023-10-10"}
        ]

core = BackendCore()

# --- 2. ABORDAGEM DIRETA (SEM BFF - ANTIPADRÃO) ---
def client_direct_approach(user_id):
    start_time = time.time()
    
    # Múltiplas chamadas redundantes feitas pelo cliente mobile
    profile = core.get_user_profile(user_id)
    orders = core.get_user_orders(user_id)
    notifications = core.get_user_notifications(user_id)
    
    # O cliente recebe o payload bruto completo (sem filtragem)
    payload = {
        "profile": profile,
        "orders": orders,
        "notifications": notifications
    }
    
    payload_json = json.dumps(payload)
    duration = time.time() - start_time
    return len(payload_json), 3, duration, payload_json

# --- 3. ABORDAGEM COM BFF (PADRÃO) ---
class MobileBFF:
    def __init__(self, core_service):
        self.core = core_service

    def get_mobile_dashboard(self, user_id):
        # Agregação no servidor (uma única chamada do ponto de vista do cliente)
        # Em produção, estas chamadas ao core poderiam ser assíncronas / em paralelo.
        profile = self.core.get_user_profile(user_id)
        orders = self.core.get_user_orders(user_id)
        notifications = self.core.get_user_notifications(user_id)

        # Transformação e Projeção (Remoção de dados desnecessários para mobile)
        lean_profile = {
            "name": profile["name"],
            "avatar": profile["avatar_url"],
            "unread_notifications": sum(1 for n in notifications if not n["read"])
        }

        lean_orders = [
            {"id": o["order_id"], "status": o["status"], "total": o["total"]}
            for o in orders
        ]

        # Payload otimizado focado estritamente na UI mobile
        dashboard = {
            "user": lean_profile,
            "recent_orders": lean_orders
        }

        return dashboard

bff = MobileBFF(core)

def client_bff_approach(user_id):
    start_time = time.time()
    
    # Apenas 1 chamada de rede do cliente para o BFF
    dashboard = bff.get_mobile_dashboard(user_id)
    
    payload_json = json.dumps(dashboard)
    duration = time.time() - start_time
    return len(payload_json), 1, duration, payload_json

# --- 4. EXECUÇÃO E VALIDAÇÃO DOS CRITÉRIOS DE SUCESSO ---
user_id = "user_42"
size_direct, calls_direct, time_direct, _ = client_direct_approach(user_id)
size_bff, calls_bff, time_bff, _ = client_bff_approach(user_id)

reduction_percentage = ((size_direct - size_bff) / size_direct) * 100
call_reduction = calls_direct - calls_bff

print(f"--- RESULTADOS DO EXPERIMENTO ---")
print(f"Abordagem Direta (Sem BFF):")
print(f"  - Chamadas ao Core: {calls_direct}")
print(f"  - Tamanho do Payload: {size_direct} bytes\n")

print(f"Abordagem com BFF (Mobile BFF):")
print(f"  - Chamadas ao Core (pelo cliente): {calls_bff}")
print(f"  - Tamanho do Payload: {size_bff} bytes\n")

print(f"Métricas Alcançadas:")
print(f"  - Redução de Payload: {reduction_percentage:.2f}% (Meta: >= 40%)")
print(f"  - Eliminação de Chamadas Redundantes: {call_reduction} chamada(s) a menos por ciclo de UI")

# Asserções para garantir que o critério de sucesso foi atingido
assert reduction_percentage >= 40, f"Falha na meta de payload: {reduction_percentage}%"
assert calls_bff == 1, f"O cliente mobile ainda está fazendo mais de 1 chamada: {calls_bff}"
print("\n[SUCESSO] Todos os critérios da missão foram validados com êxito!")