from enum import Enum, auto
from typing import List, Protocol, Optional
from dataclasses import dataclass

# --- 1. DEFINIÇÕES DE DOMÍNIO ---

class DamageType(Enum):
    PHYSICAL = auto()
    FIRE = auto()
    MAGIC = auto()

class IDamageable(Protocol):
    """Interface que garante que qualquer objeto possa receber dano."""
    def take_damage(self, amount: float, damage_type: DamageType) -> None:
        ...

@dataclass
class HitboxData:
    """Dados contidos em uma Hitbox."""
    damage: float
    damage_type: DamageType

# --- 2. COMPONENTES DO SISTEMA ---

class Hurtbox:
    """Representa a área de vulnerabilidade de um objeto."""
    def __init__(self, owner: IDamageable):
        self.owner = owner

class Hitbox:
    """Representa a área de ataque de um objeto."""
    def __init__(self, data: HitboxData):
        self.data = data
        self.is_active = False

class AttackAnimation:
    """Gerencia o timing do ataque baseado em frames."""
    def __init__(self, hitbox: Hitbox, active_frames: List[int]):
        self.hitbox = hitbox
        self.active_frames = active_frames
        self.current_frame = 0
        self.is_finished = False

    def update(self):
        """Simula o avanço de um frame de animação."""
        self.current_frame += 1
        if self.current_frame in self.active_frames:
            self.hitbox.is_active = True
        else:
            self.hitbox.is_active = False
        
        if self.current_frame > 5: # Simulação de fim de animação
            self.is_finished = True

# --- 3. IMPLEMENTAÇÕES CONCRETAS (ENTIDADES) ---

class Enemy:
    def __init__(self, name: str, health: float):
        self.name = name
        self.health = health

    def take_damage(self, amount: float, damage_type: DamageType):
        self.health -= amount
        print(f"  [HIT] {self.name} recebeu {amount} de {damage_type.name}. HP: {self.health}")

class DestructibleBarrel:
    def __init__(self):
        self.is_broken = False

    def take_damage(self, amount: float, damage_type: DamageType):
        # Barris só quebram com fogo ou dano físico alto
        if damage_type == DamageType.FIRE or amount > 50:
            self.is_broken = True
            print(f"  [BREAK] O barril explodiu com {damage_type.name}!")
        else:
            print(f"  [MISS] O barril resistiu ao dano {damage_type.name}.")

# --- 4. O MOTOR DE COMBATE (CORE) ---

class CombatEngine:
    """Orquestra a detecção de colisão entre Hitboxes e Hurtboxes."""
    def process_combat(self, hitbox: Hitbox, targets: List[Hurtbox]):
        if not hitbox.is_active:
            return # Se a hitbox não está no frame ativo, não processa nada

        for target in targets:
            # O motor não sabe o que é 'Enemy' ou 'Barrel', apenas 'IDamageable'
            target.owner.take_damage(hitbox.data.damage, hitbox.data.damage_type)

# --- 5. EXECUÇÃO DO TESTE ---

def run_experiment():
    print("=== INICIANDO EXPERIMENTO DE ARQUITETURA DE COMBATE ===\n")

    # Setup de Entidades
    orc = Enemy("Orc", 100)
    barrel = DestructibleBarrel()
    
    # Setup de Hurtboxes (O que pode ser atingido)
    hurtboxes = [Hurtbox(orc), Hurtbox(barrel)]

    # Setup de Ataque (Hitbox de Fogo)
    fire_hitbox = Hitbox(HitboxData(damage=30, damage_type=DamageType.FIRE))
    # O ataque só é perigoso nos frames 2 e 3
    attack = AttackAnimation(fire_hitbox, active_frames=[2, 3])
    
    engine = CombatEngine()

    # Simulação de Loop de Animação
    for frame in range(1, 7):
        print(f"Frame {frame}: ", end="")
        attack.update()
        
        if attack.hitbox.is_active:
            print(f"(Hitbox ATIVA) -> ", end="")
        else:
            print(f"(Hitbox INATIVA) -> ", end="")
            
        engine.process_combat(attack.hitbox, hurtboxes)
        
        if not attack.hitbox.is_active:
            print("Nada aconteceu.")

    print("\n=== RESULTADO FINAL ===")
    print(f"Orc HP: {orc.health}")
    print(f"Barril Quebrado: {barrel.is_broken}")

    # --- TESTE DE EQUÍVOCO COMUM (CONTRAEXEMPLO) ---
    print("\n=== TESTE DE EQUÍVOCO: Hitbox sem controle de frame ===")
    # Se o programador apenas ativar a hitbox e esquecer de desligar (ou não usar frames)
    bad_hitbox = Hitbox(HitboxData(damage=10, damage_type=DamageType.PHYSICAL))
    bad_hitbox.is_active = True # Erro: Ativada permanentemente
    
    print("Tentando aplicar dano com hitbox 'viciada' (sem controle de frame):")
    # Em um loop real, isso causaria dano infinito por frame
    engine.process_combat(bad_hitbox, hurtboxes)
    print("ERRO: O dano foi aplicado mesmo sem uma animação de ataque ativa!")

if __name__ == "__main__":
    run_experiment()