import json
import copy

# --- FRAMEWORK CORE ---

class SkillRegistry:
    """Registry para mapear strings de dados para classes de comportamento."""
    _registry = {}

    @classmethod
    def register(cls, skill_type):
        def wrapper(wrapped_class):
            cls._registry[skill_type] = wrapped_class
            return wrapped_class
        return wrapper

    @classmethod
    def get_behavior(cls, skill_type):
        if skill_type not in cls._registry:
            raise ValueError(f"Comportamento '{skill_type}' não registrado.")
        return cls._registry[skill_type]

class SkillBehavior:
    """Classe base para todos os comportamentos de habilidades."""
    def execute(self, caster, target, params):
        raise NotImplementedError

@SkillRegistry.register("damage")
class DamageBehavior(SkillBehavior):
    def execute(self, caster, target, params):
        # Suporte a atributos dinâmicos: dano pode ser baseado na força do caster
        base_damage = params.get("value", 0)
        scaling = params.get("scaling_attr", None)
        if scaling:
            base_damage += caster.attributes.get(scaling, 0) * params.get("scaling_factor", 0)
        
        target.attributes["hp"] -= base_damage
        print(f"  [Skill] {caster.name} causou {base_damage} de dano em {target.name}. (HP de {target.name}: {target.attributes['hp']})")

@SkillRegistry.register("heal")
class HealBehavior(SkillBehavior):
    def execute(self, caster, target, params):
        amount = params.get("value", 0)
        target.attributes["hp"] += amount
        print(f"  [Skill] {caster.name} curou {amount} de {target.name}. (HP de {target.name}: {target.attributes['hp']})")

@SkillRegistry.register("buff")
class BuffBehavior(SkillBehavior):
    def execute(self, caster, target, params):
        attr = params.get("attribute")
        amount = params.get("value", 0)
        if attr in target.attributes:
            target.attributes[attr] += amount
            print(f"  [Skill] {caster.name} deu buff de {amount} em {target.name}. ({attr} de {target.name}: {target.attributes[attr]})")

class DataManager:
    """Gerencia o carregamento e a validação de dados externos."""
    def __init__(self):
        self.data = {"attributes": {}, "skills": {}, "entities": {}}

    def load_from_dict(self, raw_data):
        """Simula o carregamento de um arquivo JSON com validação básica."""
        try:
            # Validação de estrutura mínima
            if not isinstance(raw_data, dict):
                raise ValueError("Dados devem ser um dicionário.")
            
            # Fallback para chaves inexistentes (Evita crash 1)
            self.data["attributes"] = raw_data.get("attributes", {})
            self.data["skills"] = raw_data.get("skills", {})
            self.data["entities"] = raw_data.get("entities", {})
            return True
        except Exception as e:
            print(f"[Erro DataManager] Falha ao carregar dados: {e}")
            return False

class Entity:
    """Representa um objeto no jogo com atributos e habilidades dinâmicas."""
    def __init__(self, name, data_manager):
        self.name = name
        self.dm = data_manager
        self.attributes = {}
        self.skills = [] # Lista de dicionários de configuração de habilidades
        self.sync()

    def sync(self):
        """Sincroniza a entidade com os dados atuais do DataManager (Hot-Reload)."""
        # 1. Sincroniza Atributos
        entity_data = self.dm.data["entities"].get(self.name, {})
        if not entity_data:
            print(f"[Aviso] Dados para {self.name} não encontrados. Usando padrão vazio.")
            self.attributes = {"hp": 10, "attack": 1}
        else:
            # Mescla atributos base do sistema com os específicos da entidade
            base_attrs = self.dm.data["attributes"].get(entity_data.get("type", "default"), {})
            self.attributes = copy.deepcopy(base_attrs)
            self.attributes.update(entity_data.get("stats", {}))

        # 2. Sincroniza Composição de Habilidades (Resolve Problema 2)
        self.skills = []
        entity_skills_config = entity_data.get("skills", [])
        for s_conf in entity_skills_config:
            skill_def_id = s_conf.get("skill_id")
            skill_def = self.dm.data["skills"].get(skill_def_id)
            
            if skill_def:
                # Combina parâmetros da instância com a definição global
                combined_params = copy.deepcopy(skill_def.get("params", {}))
                combined_params.update(s_conf.get("overrides", {}))
                self.skills.append({
                    "type": skill_def["type"],
                    "params": combined_params
                })
            else:
                print(f"[Aviso] Skill ID '{skill_def_id}' não encontrada em 'skills'.")

    def use_skill(self, skill_index, target):
        if 0 <= skill_index < len(self.skills):
            skill_info = self.skills[skill_index]
            try:
                behavior = SkillRegistry.get_behavior(skill_info["type"])
                behavior.execute(self, target, skill_info["params"])
            except Exception as e:
                print(f"[Erro Execução] Falha ao usar habilidade: {e}")
        else:
            print("[Erro] Índice de habilidade inválido.")

# --- EXPERIMENTO ---

def run_experiment():
    dm = DataManager()

    # 1. Configuração Inicial (Simulando Arquivo JSON)
    initial_config = {
        "attributes": {
            "hero": {"hp": 100, "attack": 10, "defense": 5},
            "monster": {"hp": 50, "attack": 5, "defense": 2}
        },
        "skills": {
            "slash": {"type": "damage", "params": {"value": 15, "scaling_attr": "attack", "scaling_factor": 1.0}},
            "heal_spell": {"type": "heal", "params": {"value": 20}},
            "power_up": {"type": "buff", "params": {"attribute": "attack", "value": 5}}
        },
        "entities": {
            "Player": {
                "type": "hero",
                "stats": {"hp": 100},
                "skills": [
                    {"skill_id": "slash"},
                    {"skill_id": "heal_spell"}
                ]
            },
            "Slime": {
                "type": "monster",
                "stats": {"hp": 50},
                "skills": []
            }
        }
    }

    print("--- INICIANDO JOGO (CONFIG 1) ---")
    dm.load_from_dict(initial_config)
    player = Entity("Player", dm)
    slime = Entity("Slime", dm)

    print(f"Player: {player.attributes} | Slime: {slime.attributes}")
    
    # Teste de Atributo Dinâmico (Slash usa o 'attack' do player)
    player.use_skill(0, slime) # Slash: 15 + (10 * 1.0) = 25 dano

    # 2. Simulação de HOT-RELOAD com mudança de perfil e valores
    print("\n--- SIMULANDO RELOAD (CONFIG 2: Player vira Mago e Slime fica forte) ---")
    
    new_config = {
        "attributes": {
            "hero": {"hp": 100, "attack": 10, "defense": 5},
            "mage": {"hp": 70, "attack": 20, "defense": 2}, # Novo tipo
            "monster": {"hp": 200, "attack": 20, "defense": 10} # Monster buffado
        },
        "skills": {
            "slash": {"type": "damage", "params": {"value": 15}},
            "heal_spell": {"type": "heal", "params": {"value": 50}}, # Cura buffada
            "fireball": {"type": "damage", "params": {"value": 40}} # Nova skill
        },
        "entities": {
            "Player": {
                "type": "mage", # Mudança de tipo (Perfil)
                "stats": {"hp": 70},
                "skills": [
                    {"skill_id": "heal_spell"}, # Mudou a skill
                    {"skill_id": "fireball", "overrides": {"value": 60}} # Skill nova com override
                ]
            },
            "Slime": {
                "type": "monster",
                "stats": {"hp": 200},
                "skills": []
            }
        }
    }

    dm.load_from_dict(new_config)
    player.sync() # Sincroniza composição e atributos
    slime.sync()

    print(f"Player (Mago): {player.attributes} | Slime (Buffado): {slime.attributes}")
    
    # Teste de nova composição e override
    player.use_skill(1, slime) # Fireball com override (60)
    player.use_skill(0, player) # Heal buffado (50)

    # 3. Teste de Robustez (Dados Corrompidos/Inexistentes)
    print("\n--- TESTANDO ROBUSTEZ (DADOS CORROMPIDOS) ---")
    corrupt_config = {"entities": {"Player": {"skill_id": "inexistente"}}} # Falta chaves essenciais
    dm.load_from_dict(corrupt_config)
    player.sync()
    print(f"Player após dados corrompidos (deve manter estado anterior ou fallback): {player.attributes}")

if __name__ == "__main__":
    run_experiment()