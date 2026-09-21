class Attribute:
    def __init__(self, base_value: float):
        self.base_value = base_value
        self.modifiers = []

    def add_modifier(self, modifier):
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier):
        if modifier in self.modifiers:
            self.modifiers.remove(modifier)

    @property
    def value(self) -> float:
        flat_sum = sum(m.value for m in self.modifiers if m.is_flat)
        percent_sum = sum(m.value for m in self.modifiers if not m.is_flat)
        
        final = (self.base_value + flat_sum) * (1.0 + percent_sum)
        return max(0.0, final)


class AttributeModifier:
    def __init__(self, value: float, is_flat: bool = True):
        self.value = value
        self.is_flat = is_flat


class StatusEffect:
    def __init__(self, name: str, duration: int):
        self.name = name
        self.duration = duration
        self.target = None

    def apply(self, target):
        self.target = target
        self.on_apply()

    def update(self):
        if self.duration > 0:
            self.on_tick()
            self.duration -= 1
        if self.duration == 0:
            self.remove()

    def on_apply(self):
        pass

    def on_tick(self):
        pass

    def on_remove(self):
        pass

    def remove(self):
        self.on_remove()
        if self in self.target.status_effects:
            self.target.status_effects.remove(self)


class StatModifierEffect(StatusEffect):
    def __init__(self, name: str, duration: int, stat_name: str, modifier: AttributeModifier):
        super().__init__(name, duration)
        self.stat_name = stat_name
        self.modifier = modifier

    def on_apply(self):
        attr = self.target.attributes.get(self.stat_name)
        if attr:
            attr.add_modifier(self.modifier)

    def on_remove(self):
        attr = self.target.attributes.get(self.stat_name)
        if attr:
            attr.remove_modifier(self.modifier)


class DamageOverTimeEffect(StatusEffect):
    def __init__(self, name: str, duration: int, damage_per_tick: float):
        super().__init__(name, duration)
        self.damage_per_tick = damage_per_tick

    def on_tick(self):
        hp_attr = self.target.attributes.get("hp")
        if hp_attr:
            new_hp = hp_attr.base_value - self.damage_per_tick
            hp_attr.base_value = max(0.0, new_hp)


class Entity:
    def __init__(self, name: str):
        self.name = name
        self.attributes = {
            "hp": Attribute(100.0),
            "attack": Attribute(10.0),
            "speed": Attribute(5.0)
        }
        self.status_effects = []

    def add_effect(self, effect: StatusEffect):
        self.status_effects.append(effect)
        effect.apply(self)

    def update(self):
        # Cria uma cópia para evitar erro de mutação durante a iteração
        for effect in list(self.status_effects):
            effect.update()


# --- Teste Automatizado do Experimento ---
if __name__ == "__main__":
    hero = Entity("Guerreiro")
    print(f"Estado inicial - Ataque: {hero.attributes['attack'].value}, HP: {hero.attributes['hp'].value}")

    # 1. Aplica buff de ataque plano (+5) por 2 turnos
    buff_ataque = StatModifierEffect("Fúria", 2, "attack", AttributeModifier(5.0, is_flat=True))
    hero.add_effect(buff_ataque)
    print(f"Turno 0 (Após Fúria) - Ataque: {hero.attributes['attack'].value}")

    # 2. Aplica DoT (Veneno) de 10 de dano por 3 turnos
    veneno = DamageOverTimeEffect("Veneno", 3, 10.0)
    hero.add_effect(veneno)

    # Simulação de passagem de turnos
    hero.update()
    print(f"Turno 1 - HP: {hero.attributes['hp'].value}, Ataque: {hero.attributes['attack'].value}")

    hero.update()
    print(f"Turno 2 - HP: {hero.attributes['hp'].value}, Ataque (buff deve ter expirado): {hero.attributes['attack'].value}")

    hero.update()
    print(f"Turno 3 - HP: {hero.attributes['hp'].value}")

    # Validações asserções
    assert hero.attributes['attack'].value == 10.0, "O buff de ataque deveria ter expirado!"
    assert hero.attributes['hp'].value == 70.0, f"HP esperado 70.0, obtido {hero.attributes['hp'].value}"
    print("Sucesso: Todos os testes do framework de status passaram corretamente!")