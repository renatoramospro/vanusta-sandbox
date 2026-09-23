import json
import unittest

# ==========================================
# 1. Representação Intermediária (IR) do Fluxo
# ==========================================
def extrair_fluxo_oidc() -> dict:
    """
    Simula a extração estática de configurações de OIDC e rotas do código-fonte,
    produzindo uma Representação Intermediária (IR) estruturada.
    """
    return {
        "client_id": "app-financeiro-01",
        "grant_type": "authorization_code",
        "use_pkce": True,
        "response_type": "code",
        "scopes_required": ["openid", "profile", "finance:read"],
        "endpoints": {
            "authorization": "https://auth.vanusta.com/oauth/authorize",
            "token": "https://auth.vanusta.com/oauth/token",
            "userinfo": "https://auth.vanusta.com/oauth/userinfo"
        },
        "atores": ["Browser", "Client (RP)", "Authorization Server (OP)", "Resource Server"]
    }

# ==========================================
# 2. Geradores a partir da IR
# ==========================================
def gerar_diagrama_mermaid(ir: dict) -> str:
    """Gera um diagrama de sequência em Mermaid a partir da IR estruturada."""
    mermaid = "sequenceDiagram\n"
    mermaid += "    autonumber\n"
    mermaid += "    participant Browser as Browser\n"
    mermaid += "    participant RP as Client (RP)\n"
    mermaid += "    participant OP as Authorization Server (OP)\n\n"
    
    if ir["grant_type"] == "authorization_code":
        mermaid += "    Browser->>RP: 1. Acessa rota protegida\n"
        mermaid += "    RP-->>Browser: 2. Redireciona com code_challenge (PKCE)\n"
        mermaid += "    Browser->>OP: 3. Autenticação e Consentimento\n"
        mermaid += "    OP-->>Browser: 4. Retorna Authorization Code\n"
        mermaid += "    Browser->>RP: 5. Envia Authorization Code\n"
        mermaid += "    RP->>OP: 6. Troca Code por Tokens (com code_verifier)\n"
        mermaid += "    OP-->>RP: 7. Retorna ID Token e Access Token\n"
    
    return mermaid

# ==========================================
# 3. Testes de Conformidade (Assertion Testing)
# ==========================================
class TestConformidadeOIDC(unittest.TestCase):
    
    def setUp(self):
        self.ir = extrair_fluxo_oidc()

    def test_obrigatoriedade_pkce(self):
        """Valida se o fluxo de autorização obrigatoriamente utiliza PKCE."""
        self.assertTrue(
            self.ir.get("use_pkce", False),
            "FALHA DE SEGURANÇA: O fluxo Authorization Code deve exigir PKCE obrigatoriamente."
        )

    def test_proibicao_implicit_grant(self):
        """Valida que o sistema não expõe endpoints com grant_type implicit (response_type=token)."""
        self.assertNotEqual(
            self.ir.get("response_type"), "token",
            "FALHA DE SEGURANÇA: Uso de Implicit Grant (response_type=token) é estritamente proibido."
        )

    def test_escopos_minimos_oidc(self):
        """Valida se o escopo 'openid' está presente, garantindo conformidade com o protocolo OIDC."""
        self.assertIn(
            "openid", self.ir.get("scopes_required", []),
            "FALHA DE CONFORMIDADE: O escopo 'openid' é obrigatório para autenticação federada."
        )

# ==========================================
# Execução e Demonstração Observável
# ==========================================
if __name__ == "__main__":
    print("=== 1. Extração da Representação Intermediária (IR) ==")
    ir_dados = extrair_fluxo_oidc()
    print(json.dumps(ir_dados, indent=2))
    
    print("\n=== 2. Geração Automática do Diagrama Mermaid ==")
    diagrama = gerar_diagrama_mermaid(ir_dados)
    print(diagrama)
    
    print("=== 3. Execução dos Testes de Conformidade de Segurança ==")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConformidadeOIDC)
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    
    if not resultado.wasSuccessful():
        exit(1)