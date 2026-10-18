import unittest

class MockLDAPServer:
    def __init__(self):
        # DIT estruturado hierarquicamente
        self.directory = {
            "cn=admin,dc=empresa,dc=com": {
                "userPassword": "admin_secure_password",
                "objectClass": ["inetOrgPerson", "top"],
                "memberOf": ["cn=administrators,ou=groups,dc=empresa,dc=com"]
            },
            "uid=johndoe,ou=users,dc=empresa,dc=com": {
                "userPassword": "secret_password",
                "objectClass": ["inetOrgPerson", "top"],
                "memberOf": [
                    "cn=developers,ou=groups,dc=empresa,dc=com",
                    "cn=contractors,ou=groups,dc=empresa,dc=com" # Múltiplos grupos
                ]
            },
            "uid=janedoe,ou=users,dc=empresa,dc=com": {
                "userPassword": "wrong_hash_example",
                "objectClass": ["inetOrgPerson", "top"]
                # ATRIBUTO memberOf AUSENTE de propósito para testar KeyError/robustez
            }
        }
        
        # Mapeamento de Permissões baseado em Grupos LDAP
        self.group_permissions = {
            "cn=administrators,ou=groups,dc=empresa,dc=com": ["read", "write", "delete", "execute"],
            "cn=developers,ou=groups,dc=empresa,dc=com": ["read", "write", "execute"],
            "cn=contractors,ou=groups,dc=empresa,dc=com": ["read", "audit"],
            "cn=users,ou=groups,dc=empresa,dc=com": ["read"]
        }

    def bind(self, dn: str, password: str) -> bool:
        """
        Simula a operação LDAP Bind (Autenticação).
        """
        if dn not in self.directory:
            return False
        return self.directory[dn]["userPassword"] == password

    def authorize(self, dn: str) -> list:
        """
        Calcula as permissões agregadas do usuário com base em seus grupos (memberOf).
        CORREÇÃO: Realiza a união de permissões de múltiplos grupos e trata
        a ausência do atributo memberOf para evitar KeyError.
        """
        if dn not in self.directory:
            return []
        
        user_data = self.directory[dn]
        # Usa .get para evitar KeyError se memberOf não existir no DIT do usuário
        groups = user_data.get("memberOf", [])
        
        permissions = set()
        for group in groups:
            if group in self.group_permissions:
                permissions.update(self.group_permissions[group])
                
        return list(permissions)


class TestLDAPAuthSystem(unittest.TestCase):
    def setUp(self):
        self.ldap = MockLDAPServer()

    def test_successful_bind_and_single_group_permissions(self):
        dn = "cn=admin,dc=empresa,dc=com"
        self.assertTrue(self.ldap.bind(dn, "admin_secure_password"))
        perms = self.ldap.authorize(dn)
        self.assertCountEqual(perms, ["read", "write", "delete", "execute"])

    def test_multiple_groups_permission_union(self):
        """Testa o cenário onde o usuário pertence a múltiplos grupos (developers + contractors)."""
        dn = "uid=johndoe,ou=users,dc=empresa,dc=com"
        self.assertTrue(self.ldap.bind(dn, "secret_password"))
        perms = self.ldap.authorize(dn)
        # União de developers (read, write, execute) com contractors (read, audit) -> sem duplicatas de 'read'
        self.assertCountEqual(perms, ["read", "write", "execute", "audit"])

    def test_missing_memberof_attribute_robustness(self):
        """Testa se o sistema lida com segurança com a ausência do atributo memberOf (sem KeyError)."""
        dn = "uid=janedoe,ou=users,dc=empresa,dc=com"
        self.assertTrue(self.ldap.bind(dn, "wrong_hash_example"))
        perms = self.ldap.authorize(dn)
        # Como memberOf está ausente, deve retornar lista vazia de permissões, sem quebrar com KeyError
        self.assertEqual(perms, [])

    def test_failed_bind_invalid_password(self):
        dn = "uid=johndoe,ou=users,dc=empresa,dc=com"
        self.assertFalse(self.ldap.bind(dn, "senha_errada"))


if __name__ == "__main__":
    unittest.main()