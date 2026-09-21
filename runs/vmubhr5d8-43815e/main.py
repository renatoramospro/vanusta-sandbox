import unittest

class AuthSystem:
    def __init__(self):
        self.sessions = {}

    def login(self, username, password):
        # Simula validação de senha
        if username == "admin" and password == "secret":
            self.sessions[username] = {"status": "pending_mfa"}
            return True
        return False

    def verify_totp(self, username, code):
        # Simula validação TOTP (code 123456 é o correto)
        if username in self.sessions and code == "123456":
            self.sessions[username]["status"] = "fully_authenticated"
            return True
        return False

    def access_resource(self, username):
        # Middleware de proteção
        session = self.sessions.get(username)
        if not session or session["status"] != "fully_authenticated":
            return 403
        return 200

class TestMFA(unittest.TestCase):
    def test_admin_mfa_enforcement(self):
        auth = AuthSystem()
        auth.login("admin", "secret")
        
        # Tenta acessar sem TOTP
        status = auth.access_resource("admin")
        print(f"Acesso sem TOTP: {status}")
        self.assertEqual(status, 403, "Erro: Administrador acessou sem MFA!")

        # Valida TOTP
        auth.verify_totp("admin", "123456")
        
        # Tenta acessar com TOTP
        status = auth.access_resource("admin")
        print(f"Acesso com TOTP: {status}")
        self.assertEqual(status, 200)

if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)