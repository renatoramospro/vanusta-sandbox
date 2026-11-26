import unittest
from rbac import RBACEngine, Permission

class TestRBACScenarios(unittest.TestCase):
    def setUp(self):
        self.engine = RBACEngine()
        
        # Criando Papéis
        self.viewer = self.engine.create_role("Viewer")
        self.editor = self.engine.create_role("Editor")
        self.admin = self.engine.create_role("Admin")
        
        # Configurando Permissões básicas
        self.viewer.add_permission(Permission("read", "document"))
        self.editor.add_permission(Permission("write", "document"))
        
        # Herança: Editor herda de Viewer
        self.editor.add_parent(self.viewer)
        
        # Admin herda de Editor
        self.admin.add_parent(self.editor)
        self.admin.add_permission(Permission("delete", "*"))

        # Criando Usuários de Teste
        self.alice = self.engine.create_user("alice") # Apenas Viewer
        self.bob = self.engine.create_user("bob")     # Editor (herda Viewer)
        self.charlie = self.engine.create_user("charlie") # Admin (herda Editor e Viewer)
        self.dave = self.engine.create_user("dave")   # Editor com Negação Explícita

        self.alice.assign_role(self.viewer)
        self.bob.assign_role(self.editor)
        self.charlie.assign_role(self.admin)
        self.dave.assign_role(self.editor)

    def test_scenario_1_viewer_can_read(self):
        """Cenário 1: Viewer pode ler documentos."""
        self.assertTrue(self.alice.has_permission("read", "document"))

    def test_scenario_2_viewer_cannot_write(self):
        """Cenário 2: Viewer NÃO pode escrever documentos."""
        self.assertFalse(self.alice.has_permission("write", "document"))

    def test_scenario_3_editor_inherits_viewer_permissions(self):
        """Cenário 3: Editor herda permissão de leitura do Viewer."""
        self.assertTrue(self.bob.has_permission("read", "document"))

    def test_scenario_4_editor_can_write(self):
        """Cenário 4: Editor pode escrever documentos."""
        self.assertTrue(self.bob.has_permission("write", "document"))

    def test_scenario_5_admin_has_global_delete(self):
        """Cenário 5: Admin possui permissão global de exclusão."""
        self.assertTrue(self.charlie.has_permission("delete", "qualquer_recurso"))

    def test_scenario_6_admin_inherits_all_lower_permissions(self):
        """Cenário 6: Admin herda leitura e escrita via hierarquia."""
        self.assertTrue(self.charlie.has_permission("read", "document"))
        self.assertTrue(self.charlie.has_permission("write", "document"))

    def test_scenario_7_explicit_denial_overrides_role_permission(self):
        """Cenário 7: Negação explícita bloqueia escrita mesmo tendo o papel Editor."""
        self.dave.deny_permission(Permission("write", "document"))
        self.assertFalse(self.dave.has_permission("write", "document"))

    def test_scenario_8_explicit_denial_does_not_block_other_actions(self):
        """Cenário 8: Negação explícita de escrita não afeta a leitura."""
        self.dave.deny_permission(Permission("write", "document"))
        self.assertTrue(self.dave.has_permission("read", "document"))

    def test_scenario_9_unassigned_user_has_no_permissions(self):
        """Cenário 9: Usuário sem papéis não tem nenhuma permissão."""
        guest = self.engine.create_user("guest")
        self.assertFalse(guest.has_permission("read", "document"))

    def test_scenario_10_resource_specific_scoping(self):
        """Cenário 10: Restrição de escopo de recurso específico."""
        custom_role = self.engine.create_role("DocOwner")
        custom_role.add_permission(Permission("read", "doc_123"))
        
        user_eve = self.engine.create_user("eve")
        user_eve.assign_role(custom_role)
        
        # Deve poder ler doc_123, mas não doc_456
        self.assertTrue(user_eve.has_permission("read", "doc_123"))
        self.assertFalse(user_eve.has_permission("read", "doc_456"))

if __name__ == "__main__":
    unittest.main()