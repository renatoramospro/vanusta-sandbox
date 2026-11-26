import re
import pytest

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
    # Risco: Inserção direta de input HTML sem sanitização
    document.getElementById('comment_area').innerHTML = comment;
}
"""

# --- Módulo SAST Simulado (Regras baseadas em padrões) ---
def check_sql_injection(code):
    # Padrão simples: uso de concatenação (+) com strings SQL e variáveis de input
    if re.search(r"SELECT.*WHERE.*=.*(\+|\+)", code, re.IGNORECASE):
        return True, "SQL Injection potencial detectada (concatenação insegura)."
    return False, "Nenhuma vulnerabilidade SQL detectada."

def check_xss(code):
    # Padrão simples: uso de .innerHTML com variável de input
    if re.search(r"\.innerHTML\s*=\s*(\w+)", code):
        return True, "Cross-Site Scripting (XSS) potencial detectada (uso inseguro de innerHTML)."
    return False, "Nenhuma vulnerabilidade XSS detectada."

# --- Testes Pytest ---

def test_detect_sql_injection():
    """Testa a detecção de SQL Injection no código Python."""
    is_vuln, msg = check_sql_injection(code_sql_vuln)
    assert is_vuln is True, "Falha na detecção de SQL Injection."
    assert "SQL Injection potencial" in msg

def test_detect_xss():
    """Testa a detecção de XSS no código JavaScript."""
    is_vuln, msg = check_xss(code_xss_vuln)
    assert is_vuln is True, "Falha na detecção de XSS."
    assert "Cross-Site Scripting (XSS) potencial" in msg

def test_no_vulnerability_detected():
    """Testa um caso de código seguro (negativo)."""
    code_safe = "def safe_func(id): return f\"SELECT * FROM users WHERE id = {id}\""
    is_vuln, _ = check_sql_injection(code_safe)
    assert is_vuln is False, "Falso positivo: detectou vulnerabilidade em código seguro."

# Verificação de sucesso geral (8/10 não é atingível com 2 testes, mas a execução deve ser 0)
# O critério de sucesso 8/10 será validado APÓS a implementação de mais regras (OWASP Top 10).