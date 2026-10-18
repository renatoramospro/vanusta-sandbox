import unittest

# --- Simulação do Servidor LDAP (Directory Information Tree - DIT) ---
class MockLDAPServer:
    def __init__(self):
        # DIT estruturado hierarquicamente (Equívoco Comum: tratar como SQL)
        self.directory = {
            "cn=admin,dc=empresa,dc=com": {
                "userPassword": "admin_secure_password",
                "objectClass": ["inetOrgPerson", "top"],
                "memberOf": ["cn=administrators,ou=groups,dc=empresa,dc=com"]
            },
            "uid=johndoe,ou=users,dc=empresa,dc=com": {
                "userPassword": "secret_password",
                "objectClass": ["inetOrgPerson", "top"],
                "memberOf": ["cn=developers,ou=groups,dc=empresa,dc=com"]
            },
            "uid=janedoe,ou=users,dc=empresa,dc=com": {
                "userPassword": "wrong_hash_example", # Equívoco: senha em texto plano sem hash adequado no backend
                "objectClass": ["inetOrgPerson", "top"],
                "memberOf": ["cn=users,ou=groups,dc=empresa,dc=com"]
            }
        }
        
        # Mapeamento de Permissões baseado em Grupos LDAP
        self.group_permissions = {
            "cn=administrators,ou=groups,dc=empresa,dc=com": ["read", "write", "delete", "execute"],
            "cn=developers,ou=groups,dc=empresa,dc=com": ["read", "write", "execute"],
            "cn=users,ou=groups,dc=empresa,dc=com": ["read"]
        }

    def bind(self, dn: str, password: str) -> bool:
        """
        Simula a operação LDAP Bind (Autenticação).
        Equívoco comum: Acreditar que o bind sem TLS é seguro.
        """
        if dn not in self.directory:
            return False
        # Simula verificação de credenciais
        return self.directory[dn]["userPassword"] == password

    def search_user_attributes(self, dn: str, attribute: str):
        """
        Simula a busca (Search) de atributos em um nó da árvore DIT.
        """
        if dn not in self.directory:
            return None
        return self.directory[dn].get(attribute)

    def get_permissions(self, dn: str) -> list:
        """
        Mapeia os grupos do usuário (memberOf) para permissões do sistema.
        Atende ao critério de gerenciamento de permissões.
        """
        groups = self.search_user_attributes(dn, "memberOf")
        if not groups:
            return []
        
        permissions = set()
        for group in groups:
            if group in self.group_permissions:
                permissions.update(self.group_permissions[group])
        return list(permissions)


# --- Testes Automatizados para Validar Autenticação e Permissões ---
class TestLDAPAuthenticationSystem(unittest.TestCase):
    
    def setUp(self):
        self.ldap_server = MockLDAPServer()

    def test_successful_authentication_and_permissions(self):
        """Testa o fluxo completo: Bind bem-sucedido e atribuição correta de permissões."""
        user_dn = "uid=johndoe,ou=users,dc=empresa,dc=com"
        password = "secret_password"
        
        # 1. Autenticação (Bind)
        is_authenticated = self.ldap_server.bind(user_dn, password)
        self.assertTrue(is_authenticated, "O usuário deveria autenticar com sucesso.")
        
        # 2. Autorização (Permissões baseadas em grupos)
        permissions = self.ldap_server.get_permissions(user_dn)
        expected_permissions = {"read", "write", "execute"}
        self.assertEqual(set(permissions), expected_permissions, "As permissões do desenvolvedor estão incorretas.")
        print(f"[SUCESSO] Usuário {user_dn} autenticado e autorizado com permissões: {permissions}")

    def test_failed_authentication_invalid_password(self):
        """Testa falha de autenticação com senha incorreta."""
        user_dn = "uid=johndoe,ou=users,dc=empresa,dc=com"
        wrong_password = "wrong_password"
        
        is_authenticated = self.ldap_server.bind(user_dn, wrong_password)
        self.assertFalse(is_authenticated, "A autenticação deve falhar com senha incorreta.")
        print("[SUCESSO] Falha de autenticação tratada corretamente para senha inválida.")

    def test_failed_authentication_nonexistent_user(self):
        """Testa tentativa de bind com DN inexistente."""
        fake_dn = "uid=hacker,ou=users,dc=empresa,dc=com"
        is_authenticated = self.ldap_server.bind(fake_dn, "any_password")
        self.assertFalse(is_authenticated, "A autenticação deve falhar para usuários inexistentes.")
        print("[SUCESSO] Tentativa de bind com usuário inexistente rejeitada.")

    def test_counterexample_insecure_simple_bind_warning(self):
        """
        Demonstra o porquê do equívoco comum: 'TLS é opcional'.
        O Simple Bind transmite credenciais em texto plano se LDAPS/TLS não for ativado na camada de transporte.
        """
        # Demonstração conceitual do risco
        insecure_transport = True # Simulando rede sem TLS
        user_dn = "uid=johndoe,ou=users,dc=empresa,dc=com"
        password = "secret_password"
        
        if insecure_transport:
            # Em rede sem TLS, um sniffer captura exatamente isto:
            intercepted_packet = {"dn": user_dn, "password": password}
            self.assertEqual(intercepted_packet["password"], "secret_password")
            print(f"[ALERTA DE SEGURANÇA] O Simple Bind enviou a senha em texto plano pela rede: {intercepted_packet}")


if __name__ == "__main__":
    unittest.main()