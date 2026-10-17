path=main.py
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

# --- 3. FLUXO 1: AUTHORIZATION CODE FLOW COM PKCE (Ex: Mobile App) ---
print("\n--- [TESTE 1] Authorization Code Flow com PKCE (Mobile App) ---")
client_id = "mobile_app"
redirect_uri = DATABASE["clients"][client_id]["redirect_uri"]

# Passo A: Cliente gera o code_verifier e o code_challenge
verifier = generate_code_verifier()
challenge = generate_code_challenge(verifier)
print(f"1. Cliente Mobile gerou Code Verifier e Code Challenge (S256).")

# Passo B: Usuário se autentica e autoriza o app (Simulação)
auth_code = secrets.token_hex(16)
DATABASE["authorization_codes"][auth_code] = {
    "client_id": client_id,
    "code_challenge": challenge,
    "expires_at": time.time() + 60,
    "used": False
}
print(f"2. Authorization Code emitido: {auth_code}")

# Passo C: Cliente troca o code pelo token enviando o code_verifier original
def exchange_code_for_token(code, sent_verifier):
    if code not in DATABASE["authorization_codes"]:
        raise ValueError("Código de autorização inválido.")
    
    code_data = DATABASE["authorization_codes"][code]
    if code_data["used"]:
        raise ValueError("Código já foi utilizado (Replay Attack prevenido!).")
    
    if time.time() > code_data["expires_at"]:
        raise ValueError("Código expirado.")
    
    # Validação do PKCE
    expected_challenge = generate_code_challenge(sent_verifier)
    if expected_challenge != code_data["code_challenge"]:
        raise ValueError("Falha na validação do PKCE: Code Verifier incorreto.")
    
    code_data["used"] = True
    
    # Emissão de Access Token e Refresh Token
    access_token = f"at_{secrets.token_hex(16)}"
    refresh_token = f"rt_{secrets.token_hex(16)}"
    
    DATABASE["tokens"][access_token] = {
        "client_id": code_data["client_id"],
        "scope": "read:profile",
        "expires_at": time.time() + 2  # Expira rápido para teste
    }
    
    return access_token, refresh_token

access_token_mobile, refresh_token_mobile = exchange_code_for_token(auth_code, verifier)
print(f"3. Sucesso! Access Token emitido: {access_token_mobile}")
print(f"4. Sucesso! Refresh Token emitido: {refresh_token_mobile}")

# --- 4. PROTECTED RESOURCE & SCOPES ---
print("\n--- [TESTE 2] Acesso ao Resource Server com Token Válido e Escopo ---")
def access_resource_server(token, required_scope):
    if token in DATABASE["token_blacklist"]:
        return 401, {"error": "token_revoked", "message": "O token foi revogado."}
    
    if token not in DATABASE["tokens"]:
        return 401, {"error": "invalid_token", "message": "Token não encontrado."}
    
    token_data = DATABASE["tokens"][token]
    if time.time() > token_data["expires_at"]:
        return 401, {"error": "expired_token", "message": "Token expirado."}
    
    if required_scope not in token_data["scope"]:
        return 403, {"error": "insufficient_scope", "message": "Escopo insuficiente."}
    
    return 200, {"data": "Informações confidenciais do perfil do usuário."}

status, response = access_resource_server(access_token_mobile, "read:profile")
print(f"Status HTTP: {status} | Resposta: {response}")
assert status == 200, "Deveria ter acessado com sucesso o recurso protegido."

# --- 5. ATAQUE DE REPLAY (Contraexemplo / Mitigação) ---
print("\n--- [TESTE 3] Contraexemplo: Tentativa de Reutilização de Authorization Code ---")
try:
    # Tentando trocar o mesmo auth_code novamente
    exchange_code_for_token(auth_code, verifier)
except ValueError as e:
    print(f"Bloqueio bem-sucedido contra Replay Attack: {e}")

# --- 6. REVOGAÇÃO DE TOKEN (Blacklist) ---
print("\n--- [TESTE 4] Revogação de Refresh Token e Access Token ---")
# Revogando o token
DATABASE["token_blacklist"].add(access_token_mobile)
print("Token adicionado à Blacklist (Revogado).")

status_revoked, response_revoked = access_resource_server(access_token_mobile, "read:profile")
print(f"Status HTTP após revogação: {status_revoked} | Resposta: {response_revoked}")
assert status_revoked == 401, "Token revogado deve retornar 401 Unauthorized."

print("\n=== TODOS OS TESTES EXECUTADOS COM SUCESSO ===")