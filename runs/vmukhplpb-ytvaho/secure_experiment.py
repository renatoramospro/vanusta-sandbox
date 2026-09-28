import json
import re
import time

# --- 1. VALIDAÇÃO DE ENTRADA E SEGURANÇA ---
def validate_input(user_id, tenant_id):
    """Valida estritamente o formato de user_id e tenant_id para prevenir injeções."""
    if not isinstance(user_id, str) or not re.match(r"^USR-[0-9]+$", user_id):
        raise ValueError("ID de usuário inválido ou malformado.")
    if not isinstance(tenant_id, str) or not re.match(r"^[a-zA-Z0-9_-]+$", tenant_id):
        raise ValueError("Tenant ID inválido ou malformado.")
    return True

# --- 2. SIMULAÇÃO DO BACKEND CORE COM ISOLAMENTO DE TENANT ---
class SecureBackendCore:
    def get_user_profile(self, user_id, tenant_id):
        # Simula consulta ao banco com isolamento de tenant
        time.sleep(0.01) # Simulação de latência de rede
        return {
            "id": user_id,
            "tenant_id": tenant_id,
            "name": "Ana Silva",
            "email": "ana.silva@example.com", # PII sensível
            "bio": "Engenheira de Software sênior apaixonada por arquitetura limpa.",
            "avatar_url": "https://example.com/avatars/ana.jpg",
            "internal_metadata": {"db_version": "v2.4", "cluster": "us-east-1", "legacy_id": 99823},
            "preferences": {"theme": "dark", "notifications_enabled": True}
        }

    def get_user_orders(self, user_id, tenant_id):
        return [
            {"order_id": "ORD-101", "total": 150.50, "status": "DELIVERED", "shipping_address": "Rua A, 123, SP"},
            {"order_id": "ORD-102", "total": 89.90, "status": "PROCESSING", "shipping_address": "Rua A, 123, SP"}
        ]

    def get_user_notifications(self, user_id, tenant_id):
        # Simula falha esporádica para testar degradação graciosa (Circuit Breaker)
        # Neste cenário retorna com sucesso dados fictícios
        return [
            {"id": "NOT-1", "title": "Bem-vinda!", "body": "Obrigado por usar nosso app."}
        ]

# --- 3. MOBILE BFF SEGURO, AGREGADOR E RESILIENTE ---
class SecureMobileBFF:
    def __init__(self, core_backend):
        self.core = core_backend

    def _mask_pii(self, email):
        """Mascaramento de PII (Ex: a***@example.com)"""
        parts = email.split("@")
        if len(parts) == 2:
            name, domain = parts
            masked_name = name[0] + "***" if len(name) > 1 else "***"
            return f"{masked_name}@{domain}"
        return "***@***.com"

    def authenticate_and_authorize(self, auth_header, target_user_id):
        """Valida token Bearer simulado e autorização de acesso ao recurso (BOLA prevention)."""
        if not auth_header or not auth_header.startswith("Bearer "):
            raise PermissionError("Autenticação requerida: Token ausente ou inválido.")
        
        token_payload = auth_header.replace("Bearer token-", "")
        # O token deve corresponder ao usuário requisitado (garantindo acesso horizontal seguro)
        if token_payload != target_user_id:
            raise PermissionError("Acesso negado: Tentativa de acesso horizontal não autorizado.")
        return True

    def get_mobile_home_view(self, auth_header, user_id, tenant_id):
        # 1. Validação de Entrada
        validate_input(user_id, tenant_id)

        # 2. Autenticação e Autorização (RBAC/BOLA)
        self.authenticate_and_authorize(auth_header, user_id)

        # 3. Chamadas agregadas ao Backend Core com isolamento de contexto (Tenant + User)
        profile = self.core.get_user_profile(user_id, tenant_id)
        orders = self.core.get_user_orders(user_id, tenant_id)
        
        # Simulação de tolerância a falhas (Circuit Breaker / Degradação Graciosa para notificações)
        try:
            notifications = self.core.get_user_notifications(user_id, tenant_id)
        except Exception:
            notifications = [] # Degradação graciosa: retorna lista vazia se o serviço falhar

        # 4. Projeção e mascaramento de PII para Mobile
        mobile_profile = {
            "name": profile["name"],
            "email_masked": self._mask_pii(profile["email"]),
            "avatar_url": profile["avatar_url"],
            "theme": profile["preferences"]["theme"]
        }

        mobile_orders = [
            {"id": o["order_id"], "total": o["total"], "status": o["status"]}
            for o in orders
        ]

        # 5. Resposta agregada final otimizada
        return {
            "profile": mobile_profile,
            "recent_orders": mobile_orders,
            "notifications_summary": {"unread_count": len(notifications)}
        }

# --- 4. EXECUÇÃO DO TESTE DE COMPROVAÇÃO DE SEGURANÇA E REDUÇÃO ---
core = SecureBackendCore()
bff = SecureMobileBFF(core)

valid_token = "Bearer token-USR-12345"
target_user = "USR-12345"
tenant = "tenant-alpha"

# A. Execução bem-sucedida (Usuário autorizado)
response_data = bff.get_mobile_home_view(valid_token, target_user, tenant)
payload_json = json.dumps(response_data)
payload_size = len(payload_json.encode('utf-8'))

print("--- RESULTADOS DA IMPLEMENTAÇÃO SEGURA DO BFF ---")
print(f"Payload Segregado e Mascarado (Mobile BFF): {payload_size} bytes")
print(f"Dados retornados: {json.dumps(response_data, indent=2)}")

# B. Teste de Violação de Autorização Horizontal (BOLA Attack)
print("\n--- TESTE DE SEGURANÇA: Bloqueio de Acesso Horizontal ---")
try:
    # Token do usuário USR-12345 tentando acessar dados de USR-99999
    bff.get_mobile_home_view("Bearer token-USR-12345", "USR-99999", tenant)
    assert False, "Deveria ter bloqueado o acesso horizontal!"
except PermissionError as e:
    print(f"[SUCESSO DE SEGURANÇA] Acesso barrado corretamente: {e}")

# C. Teste de Validação de Entrada Maliciosa
print("\n--- TESTE DE SEGURANÇA: Validação de Entrada (Injection/Malformatted ID) ---")
try:
    bff.get_mobile_home_view(valid_token, "USR-12345; DROP TABLE users;", tenant)
    assert False, "Deveria ter validado a entrada!"
except ValueError as e:
    print(f"[SUCESSO DE SEGURANÇA] Entrada maliciosa rejeitada corretamente: {e}")

# Validação final de assertividade
assert payload_size < 500, f"Payload muito grande: {payload_size} bytes"
print("\n[SUCESSO] Todas as verificações de segurança, autorização e payload foram aprovadas!")