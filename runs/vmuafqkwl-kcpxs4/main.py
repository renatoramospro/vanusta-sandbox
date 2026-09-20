import enum

# --- 1. FUNDAMENTOS: BLACKBOARD ---
class Blackboard:
    """Repositório de dados compartilhado entre os sistemas."""
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key, default=0.0):
        return self.data.get(key, default)

# --- 2. FUNDAMENTOS: BEHAVIOR TREE (EXECUÇÃO) ---
class NodeStatus(enum.Enum):
    SUCCESS = 1
    FAILURE = 2
    RUNNING = 3

class BTNode:
    def tick(self, context) -> NodeStatus:
        raise NotImplementedError

class Selector(BTNode):
    """Executa filhos até que um retorne SUCCESS."""
    def __init__(self, children):
        self.children = children
    def tick(self, context):
        for child in self.children:
            status = child.tick(context)
            if status != NodeStatus.FAILURE:
                return status
        return NodeStatus.FAILURE

class Sequence(BTNode):
    """Executa filhos até que um retorne FAILURE."""
    def __init__(self, children):
        self.children = children
    def tick(self, context):
        for child in self.children:
            status = child.tick(context)
            if status != NodeStatus.SUCCESS:
                return status
        return NodeStatus.SUCCESS

class ActionNode(BTNode):
    """Folha da árvore que executa uma ação concreta."""
    def __init__(self, name, action_func):
        self.name = name
        self.action_func = action_func
    def tick(self, context):
        print(f"  [BT] Executando Ação: {self.name}")
        return self.action_func(context)

# --- 3. FUNDAMENTOS: UTILITY AI (DECISÃO) ---
class Intention(enum.Enum):
    IDLE = 0
    EAT = 1
    SLEEP = 2
    FLEE = 3

class UtilityAI:
    """Avalia o contexto e decide a intenção de maior utilidade."""
    def __init__(self):
        self.evaluators = []

    def add_evaluator(self, intention, score_func):
        self.evaluators.append((intention, score_func))

    def decide(self, blackboard: Blackboard) -> Intention:
        best_intention = Intention.IDLE
        highest_score = 0.0

        for intention, score_func in self.evaluators:
            score = score_func(blackboard)
            if score > highest_score:
                highest_score = score
                best_intention = intention
        
        return best_intention

# --- 4. O AGENTE (NPC) ---
class NPC:
    """O Agente é apenas um container que orquestra os sistemas."""
    def __init__(self, blackboard, utility_ai, behavior_tree_map):
        self.blackboard = blackboard
        self.utility_ai = utility_ai
        self.bt_map = behavior_tree_map # Mapeia Intention -> BT Root

    def update(self):
        print(f"\n[Contexto] {self.blackboard.data}")
        
        # Passo 1: Decisão (Utility AI)
        intention = self.utility_ai.decide(self.blackboard)
        print(f"[Utility AI] Decidiu Intenção: {intention.name}")

        # Passo 2: Execução (Behavior Tree)
        bt_root = self.bt_map.get(intention)
        if bt_root:
            bt_root.tick(self.blackboard)
        else:
            print("  [BT] Nenhuma árvore para esta intenção. NPC fica parado.")

# --- 5. EXPERIMENTO E TESTES ---

def test_npc_behavior():
    bb = Blackboard()
    bb.set("hunger", 0.0)
    bb.set("energy", 1.0)
    bb.set("danger", 0.0)

    # Configurando Utility AI
    ua = UtilityAI()
    ua.add_evaluator(Intention.EAT, lambda b: b.get("hunger"))
    ua.add_evaluator(Intention.SLEEP, lambda b: 1.0 - b.get("energy"))
    ua.add_evaluator(Intention.FLEE, lambda b: b.get("danger"))

    # Configurando Behavior Trees (Ações concretas)
    # Árvore de Comer: [Encontrar Comida -> Comer]
    eat_bt = Sequence([
        ActionNode("Procurar Comida", lambda b: NodeStatus.SUCCESS),
        ActionNode("Comer", lambda b: NodeStatus.SUCCESS)
    ])

    # Árvore de Dormir: [Ir para Cama -> Dormir]
    sleep_bt = Sequence([
        ActionNode("Ir para Cama", lambda b: NodeStatus.SUCCESS),
        ActionNode("Dormir", lambda b: NodeStatus.SUCCESS)
    ])

    # Árvore de Fugir: [Correr]
    flee_bt = ActionNode("Correr desesperadamente", lambda b: NodeStatus.SUCCESS)

    # Mapeamento de Intenção para Árvore
    bt_map = {
        Intention.EAT: eat_bt,
        Intention.SLEEP: sleep_bt,
        Intention.FLEE: flee_bt
    }

    npc = NPC(bb, ua, bt_map)

    # --- CENÁRIOS ---
    
    print("--- CENÁRIO 1: NPC Saudável ---")
    npc.update()

    print("\n--- CENÁRIO 2: NPC com Fome ---")
    bb.set("hunger", 0.8)
    npc.update()

    print("\n--- CENÁRIO 3: NPC em Perigo (Perigo sobrepõe fome) ---")
    bb.set("danger", 0.9)
    npc.update()

    print("\n--- CENÁRIO 4: NPC Exausto (Após fugir) ---")
    bb.set("danger", 0.0)
    bb.set("energy", 0.1)
    npc.update()

    # --- TESTE DE EXTENSIBILIDADE (Ataque ao equívoco) ---
    print("\n--- TESTE DE EXTENSIBILIDADE: Adicionando 'Socializar' sem mudar a classe NPC ---")
    
    # 1. Nova Intenção
    class IntentionExtended(Intention):
        SOCIALIZE = 4

    # 2. Nova Árvore
    social_bt = ActionNode("Conversar com vizinho", lambda b: NodeStatus.SUCCESS)
    
    # 3. Injeção de nova lógica na Utility AI e no Mapa de BTs
    # (Simulando que o sistema de jogo adicionou esse módulo)
    ua.add_evaluator(IntentionExtended.SOCIALIZE, lambda b: b.get("social_need", 0.0))
    bt_map[IntentionExtended.SOCIALIZE] = social_bt
    
    bb.set("social_need", 0.9)
    bb.set("hunger", 0.0)
    bb.set("energy", 1.0)
    bb.set("danger", 0.0)
    
    npc.update()

if __name__ == "__main__":
    test_npc_behavior()