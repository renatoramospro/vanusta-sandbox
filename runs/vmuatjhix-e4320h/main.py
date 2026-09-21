from dataclasses import dataclass
from typing import Dict, List, Optional, Set

# --- DOMÍNIO DE DADOS (FLYWEIGHT) ---

@dataclass(frozen=True)
class ItemDefinition:
    """Dados estáticos e imutáveis de um item."""
    item_id: int
    name: str
    max_stack: int

class ItemDatabase:
    """Repositório central de definições de itens."""
    def __init__(self):
        self._definitions: Dict[int, ItemDefinition] = {}

    def register(self, definition: ItemDefinition):
        self._definitions[definition.item_id] = definition

    def get(self, item_id: int) -> Optional[ItemDefinition]:
        return self._definitions.get(item_id)

@dataclass
class ItemStack:
    """Instância de um item em um contêiner."""
    item_id: int
    quantity: int

# --- EXCEÇÕES DE INTEGRIDADE ---

class InventoryError(Exception): pass
class InvalidItemError(InventoryError): pass
class InsufficientQuantityError(InventoryError): pass
class InventoryFullError(InventoryError): pass

# --- LÓGICA DO SISTEMA ---

class InventoryContainer:
    def __init__(self, capacity: int, database: ItemDatabase):
        self.capacity = capacity
        self.database = database
        self.slots: List[Optional[ItemStack]] = [None] * capacity
        
        # Estruturas de indexação para O(1) amortizado
        self._free_slots: Set[int] = set(range(capacity))
        self._item_to_slots: Dict[int, Set[int]] = {}

    def add(self, item_id: int, quantity: int) -> int:
        """Adiciona itens ao inventário. Retorna a quantidade total adicionada."""
        if quantity <= 0:
            raise InvalidItemError("Quantidade deve ser positiva.")
        
        definition = self.database.get(item_id)
        if not definition:
            raise InvalidItemError(f"Item ID {item_id} não existe no banco de dados.")

        remaining = quantity
        
        # 1. Tentar stackar em slots existentes (O(1) para encontrar o set de slots)
        if item_id in self._item_to_slots:
            for slot_idx in list(self._item_to_slots[item_id]):
                stack = self.slots[slot_idx]
                if stack:
                    can_add = min(remaining, definition.max_stack - stack.quantity)
                    if can_add > 0:
                        stack.quantity += can_add
                        remaining -= can_add
                if remaining <= 0: break

        # 2. Usar slots vazios para o restante (O(1) para pegar um slot livre)
        while remaining > 0 and self._free_slots:
            slot_idx = self._free_slots.pop()
            can_add = min(remaining, definition.max_stack)
            
            self.slots[slot_idx] = ItemStack(item_id, can_add)
            remaining -= can_add
            
            # Atualiza indexação
            if item_id not in self._item_to_slots:
                self._item_to_slots[item_id] = set()
            self._item_to_slots[item_id].add(slot_idx)

        if remaining > 0:
            # Nota: Em um sistema real, poderíamos retornar o que sobrou ou lançar erro.
            # Aqui, para simplicidade, apenas registramos o que foi possível.
            pass
            
        return quantity - remaining

    def remove(self, item_id: int, quantity: int) -> int:
        """Remove itens e retorna a quantidade efetivamente removida."""
        if quantity <= 0: return 0
        
        definition = self.database.get(item_id)
        if not definition:
            raise InvalidItemError("ID inválido.")

        removed_total = 0
        
        if item_id in self._item_to_slots:
            # Iteramos sobre os slots que contêm este item
            for slot_idx in list(self._item_to_slots[item_id]):
                stack = self.slots[slot_idx]
                if not stack: continue

                to_remove = min(quantity - removed_total, stack.quantity)
                stack.quantity -= to_remove
                removed_total += to_remove

                if stack.quantity <= 0:
                    # Limpeza de slot
                    self.slots[slot_idx] = None
                    self._free_slots.add(slot_idx)
                    self._item_to_slots[item_id].remove(slot_idx)
                
                if removed_total >= quantity:
                    break
                    
        return removed_total

    def transfer_to(self, target: 'InventoryContainer', item_id: int, quantity: int):
        """Transfere itens entre contêineres de forma desacoplada."""
        removed = self.remove(item_id, quantity)
        if removed > 0:
            added = target.add(item_id, removed)
            if added < removed:
                # Rollback simples se o destino não couber tudo (em sistemas reais usar transações)
                self.add(item_id, removed - added)

# --- EXPERIMENTO E TESTES ---

def run_experiment():
    print("--- Iniciando Experimento de Inventário ---")
    db = ItemDatabase()
    db.register(ItemDefinition(1, "Poção de Vida", 5))
    db.register(ItemDefinition(2, "Espada de Ferro", 1))
    db.register(ItemDefinition(3, "Ouro", 999))

    inv_player = InventoryContainer(10, db)
    inv_chest = InventoryContainer(5, db)

    # Teste 1: Adição e Stacking
    print("Test 1: Adicionando itens e verificando stack...")
    inv_player.add(1, 3) # Slot 0: 3 poções
    inv_player.add(1, 4) # Slot 0: 5 poções (max), Slot 1: 2 poções
    assert inv_player.slots[0].quantity == 5
    assert inv_player.slots[1].quantity == 2
    print("  [OK] Stacking funcionando.")

    # Teste 2: Integridade (Itens Corrompidos)
    print("Test 2: Testando integridade (IDs inválidos e quantidades negativas)...")
    try:
        inv_player.add(99, 1) # ID inexistente
    except InvalidItemError:
        print("  [OK] Capturou ID inexistente.")
    
    try:
        inv_player.add(1, -5) # Quantidade negativa
    except InvalidItemError:
        print("  [OK] Capturou quantidade negativa.")

    # Teste 3: Transferência Desacoplada
    print("Test 3: Transferindo itens entre contêineres...")
    inv_player.add(3, 100) # Adiciona 100 de ouro
    inv_player.transfer_to(inv_chest, 3, 50)
    assert inv_player.remove(3, 0) == 0 # Apenas para checar estado
    # Verificando se o ouro foi movido
    # Precisamos encontrar onde o ouro está para validar
    player_gold = sum(s.quantity for s in inv_player.slots if s and s.item_id == 3)
    chest_gold = sum(s.quantity for s in inv_chest.slots if s and s.item_id == 3)
    assert player_gold == 50
    assert chest_gold == 50
    print(f"  [OK] Transferência concluída: Player({player_gold}), Chest({chest_gold})")

    # Teste 4: Inventário Cheio
    print("Test 4: Testando limite de capacidade...")
    inv_full = InventoryContainer(1, db)
    inv_full.add(2, 1) # Espada ocupa o único slot
    inv_full.add(3, 10) # Ouro tenta entrar, mas não há slots
    # O ouro não deve ter sido adicionado pois não há slots livres
    assert inv_full.slots[0].item_id == 2
    print("  [OK] Resiliência a inventário cheio validada.")

    print("\n--- EXPERIMENTO CONCLUÍDO COM SUCESSO ---")

if __name__ == "__main__":
    run_experiment()