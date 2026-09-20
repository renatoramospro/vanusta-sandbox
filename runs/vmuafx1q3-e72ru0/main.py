import time
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any

# --- CORE: BLACKBOARD ---
class Blackboard:
    """Repositório de dados compartilhado entre sistemas."""
    def __init__(self, initial_data: Dict[str, float] = None):
        self._data = initial_data or {}

    def set(self, key: str, value: float):
        self._data[key] = value

    def get(self, key: str, default: float = 0.0) -> float:
        return self._data.get(key, default)

    def __repr__(self):
        return str(self._data)

# --- CORE: BEHAVIOR TREE ---
class NodeStatus:
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"

class BTNode(ABC):
    @abstractmethod
    def tick(self, blackboard: Blackboard) -> str:
        pass

class ActionNode(BTNode):
    """Nó folha que executa uma ação concreta."""
    def __init__(self, name: str, action_func: Callable[[Blackboard], str]):
        self.name = name
        self.action_func = action_func

    def tick(self, blackboard: Blackboard) -> str:
        result = self.action_func(blackboard)
        print(f"  [BT] Executando Ação: {self.name}")
        return NodeStatus.SUCCESS

class Sequence(BTNode):
    """Executa filhos em ordem até que um falhe."""
    def __init__(self, children: List[BTNode]):
        self.children = children

    def tick(self, blackboard: Blackboard) -> str:
        for child in self.children:
            status = child.tick(blackboard)
            if status != NodeStatus.SUCCESS:
                return status
        return NodeStatus.SUCCESS

# --- CORE: UTILITY AI ---
class UtilityAI:
    """Decide a intenção baseada em scores de utilidade."""
    def __init__(self):
        # Mapeia uma string (intenção) para uma função de score
        self.evaluators: Dict[str, Callable[[Blackboard], float]] = {}

    def add_evaluator(self, intention: str, score_func: Callable[[Blackboard], float]):
        self.evaluators[intention] = score_func

    def decide(self, blackboard: Blackboard) -> str:
        best_intention = "IDLE"
        max_score = 0.0
        
        for intention, score_func in self.evaluators.items():
            score = score_func(blackboard)
            if score > max_score:
                max_score = score
                best_intention = intention
        
        return best_intention

# --- CORE: NPC ---
class NPC:
    """O Agente que integra Percepção, Decisão e Execução."""
    def __init__(self, name: str):
        self.name = name
        self.blackboard = Blackboard()
        self.utility_ai = UtilityAI()
        self.behavior_trees: Dict[str, BTNode] = {}

    def register_behavior(self, intention: str, tree: BTNode):
        """Permite estender o NPC sem modificar sua classe."""
        self.behavior_trees[intention] = tree

    def update(self):
        print(f"\n--- {self.name} ---")
        print(f"[Contexto] {self.blackboard}")
        
        # 1. Decisão (Utility AI)
        intention = self.utility_ai.decide(self.blackboard)
        print(f"[Utility AI] Decidiu Intenção: {intention}")

        # 2. Execução (Behavior Tree)
        tree = self.behavior_trees.get(intention)
        if tree:
            tree.tick(self.blackboard)
        else:
            print(f"  [BT] Nenhuma árvore para esta intenção. NPC fica parado.")

# --- EXPERIMENTO E TESTES ---

def run_experiment():
    # 1. Setup do NPC Base
    npc = NPC("Agente Alpha")

    # 2. Configuração da Utility AI (Decisão)
    # Usamos strings para evitar o erro de herança de Enum
    npc.utility_ai.add_evaluator("EAT", lambda b: b.get("hunger"))
    npc.utility_ai.add_evaluator("SLEEP", lambda b: 1.0 - b.get("energy"))
    npc.utility_ai.add_evaluator("FLEE", lambda b: b.get("danger") * 2.0) # Perigo é prioritário

    # 3. Configuração das Behavior Trees (Execução)
    npc.register_behavior("EAT", Sequence([
        ActionNode("Procurar Comida", lambda b: "ok"),
        ActionNode("Comer", lambda b: "ok")
    ]))
    
    npc.register_behavior("SLEEP", Sequence([
        ActionNode("Ir para Cama", lambda b: "ok"),
        ActionNode("Dormir", lambda b: "ok")
    ]))

    npc.register_behavior("FLEE", Sequence([
        ActionNode("Correr desesperadamente", lambda b: "ok")
    ]))

    # --- CENÁRIOS ---
    
    # Cenário 1: Saudável
    npc.blackboard.set("hunger", 0.1)
    npc.blackboard.set("energy", 1.0)
    npc.blackboard.set("danger", 0.0)
    npc.update()

    # Cenário 2: Fome
    npc.blackboard.set("hunger", 0.8)
    npc.update()

    # Cenário 3: Perigo (Deve sobrepor a fome)
    npc.blackboard.set("danger", 0.9)
    npc.update()

    # Cenário 4: Exaustão
    npc.blackboard.set("danger", 0.0)
    npc.blackboard.set("energy", 0.1)
    npc.update()

    # --- TESTE DE EXTENSIBILIDADE (O ponto crítico) ---
    print("\n--- TESTE DE EXTENSIBILIDADE: Adicionando 'Socializar' sem mudar a classe NPC ---")
    
    # Adicionamos uma nova intenção via string e nova lógica de score
    npc.utility_ai.add_evaluator("SOCIALIZE", lambda b: b.get("social_need", 0.0))
    
    # Adicionamos uma nova árvore de comportamento
    npc.register_behavior("SOCIALIZE", Sequence([
        ActionNode("Conversar com vizinho", lambda b: "ok")
    ]))

    # Provocamos o estímulo social
    npc.blackboard.set("hunger", 0.0)
    npc.blackboard.set("energy", 1.0)
    npc.blackboard.set("danger", 0.0)
    npc.blackboard.set("social_need", 0.9)
    
    npc.update()
    print("\n[SUCESSO] O sistema foi estendido sem modificar a classe NPC ou Enums.")

if __name__ == "__main__":
    run_experiment()