import time

class Player:
    def __init__(self):
        # Atributos Base (Core Loop)
        self.base_damage = 10
        self.base_health = 100
        
        # Recursos de Meta-Game
        self.void_fragments = 0
        
        # Árvore de Habilidades (Meta-Loop)
        self.damage_upgrade_level = 0

    def upgrade_damage(self):
        if self.void_fragments >= 50:
            self.void_fragments -= 50
            self.damage_upgrade_level += 1
            print(f"--- META-UPGRADE: Dano aumentado para nível {self.damage_upgrade_level}! ---")
        else:
            print("--- META-UPGRADE FALHOU: Fragmentos insuficientes. ---")

    def get_current_damage(self):
        # A CAUSALIDADE: O dano atual é o base + o multiplicador do meta-game
        return self.base_damage + (self.damage_upgrade_level * 5)

def simulate_core_loop(player, enemy_health):
    """Simula o Core Loop: Ação -> Recompensa -> Resultado"""
    print(f"\n[RUN START] Atributos: Dano={player.get_current_damage()}, HP={player.base_health}")
    
    current_enemy_hp = enemy_health
    damage = player.get_current_damage()
    
    # Simulação de combate simplificada
    while current_enemy_hp > 0:
        current_enemy_hp -= damage
        if current_enemy_hp > 0:
            print(f"  Inimigo atingido! HP restante: {current_enemy_hp}")
        else:
            print(f"  Inimigo derrotado!")

    # Recompensa do Secondary/Core Loop para o Meta-Loop
    reward = 30 # Fragmentos por vitória
    player.void_fragments += reward
    print(f"[RUN END] Vitória! Ganhou {reward} fragmentos. Total: {player.void_fragments}")
    return True

def run_experiment():
    player = Player()
    enemy_hp = 50

    print("=== INICIANDO TESTE DE ARQUITETURA DE LOOPS ===")
    
    # RUN 1: Sem upgrades
    print("\n--- RUN 1: Estado Inicial ---")
    simulate_core_loop(player, enemy_hp)

    # TENTATIVA DE UPGRADE (Deve falhar, pois só tem 30 fragmentos)
    print("\n--- TENTATIVA DE UPGRADE (Esperado: Falha) ---")
    player.upgrade_damage()

    # RUN 2: Acumulando mais recursos
    print("\n--- RUN 2: Acumulando Recursos ---")
    simulate_core_loop(player, enemy_hp)

    # TENTATIVA DE UPGRADE (Agora deve funcionar: 30 + 30 = 60)
    print("\n--- TENTATIVA DE UPGRADE (Esperado: Sucesso) ---")
    player.upgrade_damage()

    # RUN 3: Com o impacto do Meta-Loop no Core-Loop
    print("\n--- RUN 3: Testando Causalidade (Dano deve ser maior) ---")
    simulate_core_loop(player, enemy_hp)

    # VALIDAÇÃO FINAL
    expected_damage = 15 # 10 (base) + 5 (1 upgrade)
    actual_damage = player.get_current_damage()
    
    print("\n=== RESULTADO DO TESTE ===")
    print(f"Dano esperado após upgrade: {expected_damage}")
    print(f"Dano real no Core Loop: {actual_damage}")
    
    if actual_damage == expected_damage:
        print("VEREDITO: CAUSALIDADE VALIDADA (O Meta-Loop alterou o Core-Loop)")
    else:
        print("VEREDITO: FALHA NA CAUSALIDADE (O Meta-Loop é apenas cosmético)")

if __name__ == "__main__":
    run_experiment()