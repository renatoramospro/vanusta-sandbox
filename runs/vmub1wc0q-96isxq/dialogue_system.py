import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# --- CORE: O Blackboard (Desacoplamento) ---

class Blackboard:
    """
    Repositório de estados. O sistema de diálogo interage APENAS com este objeto.
    Ele não sabe o que é um 'Player' ou 'Quest', apenas chaves e valores.
    """
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return self._data

# --- ABSTRAÇÃO: Condições de Ramificação ---

class Condition(ABC):
    """Interface para condições de ramificação."""
    @abstractmethod
    def is_met(self, blackboard: Blackboard) -> bool:
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

class AttributeCondition(Condition):
    """Verifica se um atributo (ex: força) é >= valor."""
    def __init__(self, attribute: str, min_value: int):
        self.attribute = attribute
        self.min_value = min_value

    def is_met(self, blackboard: Blackboard) -> bool:
        return blackboard.get(self.attribute, 0) >= self.min_value

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "attribute", "attr": self.attribute, "min": self.min_value}

class ItemCondition(Condition):
    """Verifica se um item está no inventário."""
    def __init__(self, item_id: str):
        self.item_id = item_id

    def is_met(self, blackboard: Blackboard) -> bool:
        inventory = blackboard.get("inventory", [])
        return self.item_id in inventory

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "item", "item_id": self.item_id}

class QuestCondition(Condition):
    """Verifica se uma missão foi concluída."""
    def __init__(self, quest_id: str):
        self.quest_id = quest_id

    def is_met(self, blackboard: Blackboard) -> bool:
        completed_quests = blackboard.get("completed_quests", [])
        return self.quest_id in completed_quests

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "quest", "quest_id": self.quest_id}

# --- ESTRUTURA: Nós de Diálogo ---

class DialogueOption:
    def __init__(self, text: str, next_node_id: Optional[str], conditions: List[Condition] = None):
        self.text = text
        self.next_node_id = next_node_id
        self.conditions = conditions or []

    def is_available(self, blackboard: Blackboard) -> bool:
        return all(c.is_met(blackboard) for c in self.conditions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "next_node_id": self.next_node_id,
            "conditions": [c.to_dict() for c in self.conditions]
        }

class DialogueNode:
    def __init__(self, node_id: str, text: str, options: List[DialogueOption]):
        self.node_id = node_id
        self.text = text
        self.options = options

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "text": self.text,
            "options": [opt.to_dict() for opt in self.options]
        }

# --- MOTOR: Dialogue Engine ---

class DialogueEngine:
    def __init__(self, nodes: Dict[str, DialogueNode], blackboard: Blackboard):
        self.nodes = nodes
        self.blackboard = blackboard
        self.current_node_id: Optional[str] = None

    def start(self, start_node_id: str):
        self.current_node_id = start_node_id

    def get_current_node(self) -> Optional[DialogueNode]:
        if not self.current_node_id:
            return None
        return self.nodes.get(self.current_node_id)

    def select_option(self, option_index: int):
        node = self.get_current_node()
        if not node:
            return

        # Filtramos apenas as opções que o jogador REALMENTE pode ver/escolher
        available_options = [opt for opt in node.options if opt.is_available(self.blackboard)]
        
        if 0 <= option_index < len(available_options):
            selected = available_options[option_index]
            self.current_node_id = selected.next_node_id
        else:
            print("Opção inválida!")

# --- TESTE E DEMONSTRAÇÃO ---

def run_experiment():
    # 1. Setup do Estado do Jogador (Blackboard)
    bb = Blackboard()
    bb.set("strength", 15)
    bb.set("inventory", ["old_key", "map"])
    bb.set("completed_quests", ["tutorial_done"])

    # 2. Construção da Árvore de Diálogo (Data-Driven)
    # Nó 0: Início
    # Nó 1: Sucesso (tem força e chave)
    # Nó 2: Falha (não tem requisitos)
    # Nó 3: Fim
    
    nodes = {
        "start": DialogueNode("start", "Olá viajante. Você parece forte. Tem a chave?", [
            DialogueOption("Sim, aqui está a chave!", "success", [
                AttributeCondition("strength", 10),
                ItemCondition("old_key")
            ]),
            DialogueOption("Não tenho nada...", "fail", [
                QuestCondition("tutorial_done") # Só pode responder isso se fez o tutorial
            ]),
            DialogueOption("Eu sou um fraco...", "fail") # Opção padrão sem condição
        ]),
        "success": DialogueNode("success", "Excelente! A porta está aberta.", []),
        "fail": DialogueNode("fail", "Então não posso te ajudar.", []),
    }

    engine = DialogueEngine(nodes, bb)
    engine.start("start")

    print("--- INÍCIO DO DIÁLOGO ---")
    
    # Simulação de interação
    curr = engine.get_current_node()
    print(f"NPC: {curr.text}")
    
    available = [opt for opt in curr.options if opt.is_available(bb)]
    for i, opt in enumerate(available):
        print(f"{i}: {opt.text}")

    # Escolhendo a opção 0 (Sucesso)
    print("\n> Escolhendo opção 0...")
    engine.select_option(0)
    
    curr = engine.get_current_node()
    if curr:
        print(f"NPC: {curr.text}")
    
    print("\n--- SERIALIZAÇÃO JSON DO ESTADO ---")
    # Serialização do Blackboard (Estado do mundo)
    print("Blackboard JSON:", json.dumps(bb.to_dict(), indent=2))
    
    # Serialização da Árvore (Estrutura do diálogo)
    dialogue_data = {nid: n.to_dict() for nid, n in nodes.items()}
    print("\nDialogue Tree JSON (Fragmento):")
    print(json.dumps(dialogue_data["start"], indent=2))

if __name__ == "__main__":
    run_experiment()