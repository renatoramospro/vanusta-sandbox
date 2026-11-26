import re

# --- Dados de Teste (Simulação de código-fonte) ---
# 1. Vulnerabilidade SQL Injection (Python)
code_sql_vuln = """
def get_user(user_id):
    # Risco: Concatenação direta de input em query SQL
    query = "SELECT * FROM users WHERE id = " + user_id
    # db.execute(query)
    return query
"""

# 2. Vulnerabilidade XSS (JavaScript)
code_xss_vuln = """
function render_comment(comment) {
    // Risco: Inserção direta de input HTML sem sanitização
    document.getElementById('comment_area').innerHTML = comment;
}
"""

# --- Módulo SAST Simulado (Regras baseadas em padrões) ---
def check_sql_injection(code):
    # Padrão simples: uso de concatenação (+) com strings SQL e variáveis de input
    # Nota: Em um SAST real, usaríamos AST para verificar fluxo de dados (Taint Analysis)
    if re.search(r"SELECT.*WHERE.*=.*(\+|\+)", code, re.IGNORECASE):
        return True, "SQL Injection potencial detectada (concatenação insegura)."
    return False, "Nenhuma vulnerabilidade SQL detectada."

def check_xss(code):
    # Padrão simples: uso de .innerHTML com variável de input
    if re.search(r"\.innerHTML\s*=\s*(\w+)", code):
        return True, "Cross-Site Scripting (XSS) potencial detectada (uso inseguro de innerHTML)."
    return False, "Nenhuma vulnerabilidade XSS detectada."

# --- Execução e Validação ---
print("--- Teste SQL Injection (Python) ---")
is_vuln_sql, msg_sql = check_sql_injection(code_sql_vuln)
print(f"Vulnerabilidade detectada: {is_vuln_sql}")
print(f"Mensagem: {msg_sql}")

print("\n--- Teste XSS (JavaScript) ---")
is_vuln_xss, msg_xss = check_xss(code_xss_vuln)
print(f"Vulnerabilidade detectada: {is_vuln_xss}")
print(f"Mensagem: {msg_xss}")

# Verificação de sucesso (esperado: ambos detectados)
assert is_vuln_sql == True, "Falha na detecção de SQL Injection."
assert is_vuln_xss == True, "Falha na detecção de XSS."
print("\n✅ Experimento concluído com sucesso: Ambas as vulnerabilidades foram detectadas pelo protótipo.")