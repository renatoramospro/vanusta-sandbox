import time
import hashlib
import base64
import secrets

print("=== INICIALIZANDO SIMULAÇÃO DE OAUTH 2.0 ===")

# --- 1. SIMULAÇÃO DE BANCO DE DADOS E ESTADO GLOBAL ---
DATABASE = {
    "clients": {
        "web_app": {"redirect_uri": "https://webapp.com/callback", "type": "confidential"},
        "mobile_app": {"redirect_uri": "app://callback", "type": "public"},
        "spa_app": {"redirect_uri": "https://spa.com/callback", "type": "public"}
    },
    "authorization_codes": {},
    "tokens": {},
    "token_blacklist": set()
}

# --- 2. FUNÇÕES AUXILIARES DE PKCE E HASH ---
def generate_code_verifier():
    return secrets.token_urlsafe(64)

def generate_code_challenge(verifier):
    sha256_hash = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(sha256_hash).rstrip(b'=').decode('utf-8')

# --- 3. SUPORTE AOS TRÊS TIPOS DE CLIENTES E FLUXOS ---

# CLIENTE 1: Mobile App (Authorization Code com PKCE)
print("\n--- [TESTE 1] Authorization Code Flow com PKCE (Mobile App) ---")
client_id_mobile = "mobile_app"
verifier = generate_code_verifier()
challenge = generate_code_challenge(verifier)
print(f"1. Cliente Mobile gerou Code Verifier e Code Challenge (S256).")

auth_code_mobile = secrets.token_hex(16)
DATABASE["authorization_codes"][auth_code_mobile] = {
    "client_id": client_id_mobile,
    "code_challenge": challenge,
    "expires_at": time.time() + 60,
    "used": False
}
print(f"2. Authorization Code emitido para o Mobile App: {auth_code_mobile}")

# Troca do código por tokens validando o PKCE
def exchange_code_for_token(auth_code, verifier_sent):
    if auth_code not in DATABASE["authorization_codes"]:
        raise ValueError("Authorization code inválido.")
    
    code_data = DATABASE["authorization_codes"][auth_code]
    if code_data["used"]:
        raise ValueError("Replay Attack detectado: Código já utilizado!")
    if time.time() > code_data["expires_at"]:
        raise ValueError("Authorization code expirado.")
    
    # Validação do PKCE
    expected_challenge = code_data["code_challenge"]
    calculated_challenge = generate_code_challenge(verifier_sent)
    if expected_challenge != calculated_challenge:
        raise ValueError("Falha na validação do PKCE (Code Verifier incorreto).")
    
    code_data["used"] = True
    
    access_token = secrets.token_hex(32)
    refresh_token = secrets.token_hex(32)
    DATABASE["tokens"][access_token] = {
        "client_id": code_data["client_id"],
        "scope": "read:profile write:profile",
        "expires_at": time.time() + 300
    }
    return access_token, refresh_token

access_token_mobile, refresh_token_mobile = exchange_code_for_token(auth_code_mobile, verifier)
print(f"3. Sucesso! Access Token emitido: {access_token_mobile[:10]}...")


# CLIENTE 2: Web App Tradicional (Authorization Code sem PKCE, mas com Client Secret simulado)
print("\n--- [TESTE 2] Authorization Code Flow Tradicional (Web App) ---")
client_id_web = "web_app"
auth_code_web = secrets.token_hex(16)
DATABASE["authorization_codes"][auth_code_web] = {
    "client_id": client_id_web,
    "code_challenge": None,
    "expires_at": time.time() + 60,
    "used": False
}
print(f"1. Web App recebeu Authorization Code: {auth_code_web}")

# Simulação de troca de código por token para app confidencial
code_data_web = DATABASE["authorization_codes"][auth_code_web]
code_data_web["used"] = True
access_token_web = secrets.token_hex(32)
DATABASE["tokens"][access_token_web] = {
    "client_id": "web_app",
    "scope": "read:profile",
    "expires_at": time.time() + 300
}
print(f"2. Sucesso! Web App autenticado com sucesso. Token: {access_token_web[:10]}...")


# CLIENTE 3: SPA App (Simulação de Implicit Grant e seus riscos)
print("\n--- [TESTE 3] Implicit Grant (SPA App) [Demonstração de Risco] ---")
# No fluxo implícito, o token é retornado diretamente na URL, expondo-o a scripts XSS.
access_token_spa = secrets.token_hex(32)
DATABASE["tokens"][access_token_spa] = {
    "client_id": "spa_app",
    "scope": "read:profile",
    "expires_at": time.time() + 120
}
print(f"ALERTA: Token emitido diretamente via Implicit Grant (vulnerável a XSS): {access_token_spa[:10]}...")


# --- 4. VALIDAÇÃO DE RECURSOS NO RESOURCE SERVER E ESCOPOS ---
print("\n--- [TESTE 4] Acesso a Recursos Protegidos e Scopes ---")

def access_resource_server(token, required_scope):
    if token in DATABASE["token_blacklist"]:
        return 401, {"error": "token_revoked"}
    if token not in DATABASE["tokens"]:
        return 401, {"error": "invalid_token"}
    
    token_data = DATABASE["tokens"][token]
    if time.time() > token_data["expires_at"]:
        return 401, {"error": "token_expired"}
    
    if required_scope not in token_data["scope"]:
        return 403, {"error": "insufficient_scope"}
        
    return 200, {"data": "Informação sensível do perfil do usuário"}

# Testando acesso com escopo válido
status, response = access_resource_server(access_token_mobile, "read:profile")
print(f"Mobile acessando com escopo 'read:profile' -> Status: {status} | Resposta: {response}")
assert status == 200

# Testando acesso com escopo insuficiente
status_fail, response_fail = access_resource_server(access_token_web, "write:profile")
print(f"Web App tentando acessar 'write:profile' sem permissão -> Status: {status_fail} | Resposta: {response_fail}")
assert status_fail == 403


# --- 5. REVOGAÇÃO DE TOKENS (Blacklist) ---
print("\n--- [TESTE 5] Revogação de Token (Blacklist) ---")
DATABASE["token_blacklist"].add(access_token_mobile)
print("Access Token do Mobile App adicionado à Blacklist (Revogado).")

status_revoked, response_revoked = access_resource_server(access_token_mobile, "read:profile")
print(f"Tentativa de acesso após revogação -> Status: {status_revoked} | Resposta: {response_revoked}")
assert status_revoked == 401, "Token revogado deve retornar 401 Unauthorized."

print("\n=== TODOS OS TESTES EXECUTADOS COM SUCESSO ===")