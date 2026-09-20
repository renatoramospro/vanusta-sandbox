import unittest

class VoidRunnerEngine:
    """Simula o motor de jogo com loops interconectados."""
    def __init__(self):
        # Atributos do Meta-Loop (Permanentes)
        self.meta_damage_level = 0
        self.permanent_damage_modifier = 1.0
        self.energy_fragments = 0

        # Atributos do Core-Loop (Temporários da sessão)
        self.session_damage = 10.0

    def upgrade_meta_damage(self):
        """Simula o investimento no Meta-Loop."""
        if self.energy_fragments >= 50:
            self.meta_damage_level += 1
            self.permanent_damage_modifier += 0.5  # Aumenta 50% o dano base
            self.energy_fragments -= 50
            return True
        return False

    def run_combat_session(self):
        """Simula o Core-Loop: Combate contra um inimigo com 100 HP."""
        # Sincronia: O Core-Loop recebe o modificador do Meta-Loop
        current_damage = 10.0 * self.permanent_damage_modifier
        enemy_hp = 100.0
        
        hits = 0
        while enemy_hp > 0:
            enemy_hp -= current_damage
            hits += 1
        
        # O Core-Loop alimenta o Meta-Loop
        session_reward = hits * 5 # Ganha fragmentos baseados na performance
        self.energy_fragments += session_reward
        
        return hits, session_reward

class TestLoopCausality(unittest.TestCase):
    def setUp(self):
        self.game = VoidRunnerEngine()

    def test_causality_flow(self):
        """
        Testa se: Core -> Meta -> Core funciona.
        1. Core gera fragmentos.
        2. Meta usa fragmentos para upgrade.
        3. Core responde com menos hits necessários.
        """
        # --- FASE 1: Core Loop inicial ---
        hits_initial, reward_initial = self.game.run_combat_session()
        print(f"[CORE] Hits iniciais: {hits_initial}, Fragmentos ganhos: {reward_initial}")
        
        self.assertEqual(hits_initial, 10, "No nível 0, 10 hits de 10 de dano são necessários para 100 HP.")

        # --- FASE 2: Meta Loop (Upgrade) ---
        # Precisamos de 50 fragmentos. Vamos rodar mais uma vez.
        self.game.run_combat_session() 
        print(f"[META] Fragmentos atuais: {self.game.energy_fragments}")
        
        upgrade_success = self.game.upgrade_meta_damage()
        self.assertTrue(upgrade_success, "O upgrade no Meta-Loop deveria ter funcionado.")
        print(f"[META] Upgrade realizado! Novo modificador: {self.game.permanent_damage_modifier}")

        # --- FASE 3: Core Loop com feedback do Meta ---
        hits_after, _ = self.game.run_combat_session()
        print(f"[CORE] Hits após upgrade: {hits_after}")

        # VALIDAÇÃO DA CAUSALIDADE:
        # Se o dano subiu para 15 (10 * 1.5), os hits devem cair de 10 para 7.
        # (100 / 15 = 6.66 -> 7 hits)
        self.assertLess(hits_after, hits_initial, "FALHA: O upgrade no Meta-Loop não afetou o Core-Loop (Loop de Vaidade!)")
        self.assertEqual(hits_after, 7, f"Esperado 7 hits, mas obteve {hits_after}")
        print("[RESULTADO] CAUSALIDADE VALIDADA: O Meta-Loop alterou o Core-Loop com sucesso.")

if __name__ == "__main__":
    # Execução direta para observação de saída
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLoopCausality)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Garantir que o script termine com código 0 se passar, ou 1 se falhar
    import sys
    sys.exit(0 if result.wasSuccessful() else 1)