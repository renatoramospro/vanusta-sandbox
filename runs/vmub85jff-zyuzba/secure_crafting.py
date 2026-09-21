import threading
from typing import Dict, List, Set, Optional, Tuple

class Item:
    def __init__(self, item_id: str, tags: Set[str]):
        self.item_id = item_id
        self.tags = tags

class Requirement:
    def __init__(self, target: str, quantity: int, is_tag: bool = False):
        self.target = target  # item_id ou tag
        self.quantity = quantity
        self.is_tag = is_tag

class Recipe:
    def __init__(self, recipe_id: str, inputs: List[Requirement], output_item_id: str, output_quantity: int):
        self.recipe_id = recipe_id
        self.inputs = inputs
        self.output_item_id = output_item_id
        self.output_quantity = output_quantity

class Inventory:
    def __init__(self):
        # Mapeia item_id -> quantidade
        self._items: Dict[str, int] = {}
        # Mapeia item_id -> Objeto Item (metadados e tags)
        self._registry: Dict[str, Item] = {}
        # Lock de exclusão mútua para evitar Race Conditions em ambientes concorrentes
        self._lock = threading.RLock()

    def register_item_meta(self, item: Item):
        with self._lock:
            self._registry[item.item_id] = item

    def add_item(self, item_id: str, quantity: int, tags: Optional[Set[str]] = None):
        with self._lock:
            if quantity <= 0:
                raise ValueError("Quantidade deve ser positiva.")
            if item_id not in self._items:
                self._items[item_id] = 0
                if tags and item_id not in self._registry:
                    self.register_item_meta(Item(item_id, tags))
            self._items[item_id] += quantity

    def get_quantity(self, item_id: str) -> int:
        with self._lock:
            return self._items.get(item_id, 0)

    def get_items_by_tag(self, tag: str) -> List[str]:
        with self._lock:
            matching = []
            for item_id, item in self._registry.items():
                if tag in item.tags and self.get_quantity(item_id) > 0:
                    matching.append(item_id)
            return matching

    def generate_atomic_plan(self, recipe: Recipe) -> Optional[Dict[str, int]]:
        """
        Gera um plano de consumo sem mutar o estado, sob lock.
        """
        with self._lock:
            plan: Dict[str, int] = {}
            temp_inventory = self._items.copy()

            for req in recipe.inputs:
                remaining_needed = req.quantity

                if not req.is_tag:
                    available = temp_inventory.get(req.target, 0)
                    if available < remaining_needed:
                        return None # Falha de requisito
                    plan[req.target] = plan.get(req.target, 0) + remaining_needed
                    temp_inventory[req.target] -= remaining_needed
                else:
                    # Resolução por tag
                    candidate_ids = [iid for iid, item in self._registry.items() if req.target in item.tags]
                    for iid in candidate_ids:
                        if remaining_needed <= 0:
                            break
                        available = temp_inventory.get(iid, 0)
                        if available <= 0:
                            continue
                        take = min(available, remaining_needed)
                        plan[iid] = plan.get(iid, 0) + take
                        temp_inventory[iid] -= take
                        remaining_needed -= take

                    if remaining_needed > 0:
                        return None # Não há itens suficientes para cobrir a tag

            return plan

    def commit_craft(self, recipe: Recipe, plan: Dict[str, int], output_item: Item) -> bool:
        """
        Executa a mutação atômica do inventário com REVALIDAÇÃO sob lock.
        Garante que nenhuma outra thread alterou o inventário entre o planejamento e o commit.
        """
        with self._lock:
            # 1. Revalidação estrita do estado atual (Double-Checked Locking)
            for item_id, qty in plan.items():
                if self._items.get(item_id, 0) < qty:
                    return False # Concorrência detectada: itens foram consumidos por outra transação!

            # 2. Execução atômica do consumo
            for item_id, qty in plan.items():
                self._items[item_id] -= qty
                if self._items[item_id] <= 0:
                    del self._items[item_id]

            # 3. Adição do item produzido
            self.register_item_meta(output_item)
            self.add_item(output_item.item_id, recipe.output_quantity)
            return True

class SecureCraftingEngine:
    @staticmethod
    def craft(recipe: Recipe, inventory: Inventory, output_item: Item) -> bool:
        # AVISO DE SEGURANÇA: Esta função deve ser executada exclusivamente no SERVIDOR.
        # Nunca confie em chamadas diretas vindas do cliente (Client-Authoritative).
        
        # Fase 1: Planejamento
        plan = inventory.generate_atomic_plan(recipe)
        if not plan:
            return False

        # Fase 2: Commit Transacional Atômico com Proteção contra Race Conditions
        success = inventory.commit_craft(recipe, plan, output_item)
        return success

def run_security_tests():
    print("Iniciando testes de segurança e concorrência...")

    # Teste 1: Concorrência de Threads (Race Condition attack simulation)
    inv = Inventory()
    inv.add_item("tora_carvalho", 5, tags={"madeira"})
    
    recipe = Recipe(
        recipe_id="fazer_prancha",
        inputs=[Requirement("madeira", 5, is_tag=True)],
        output_item_id="prancha",
        output_quantity=1
    )
    output_item = Item("prancha", tags={"material_processado"})

    results = []
    def worker():
        res = SecureCraftingEngine.craft(recipe, inv, output_item)
        results.append(res)

    # Dispara duas threads simultâneas tentando consumir os únicos 5 recursos disponíveis
    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exatamente uma thread deve ter sucesso, a outra deve falhar na revalidação atômica
    success_count = sum(1 for r in results if r)
    assert success_count == 1, f"Falha de Concorrência: {success_count} sucessos registrados (esperado exatamente 1)."
    print(f"✅ Teste de Concorrência Passou: Apenas 1 transação teve sucesso, evitando duplicação/race condition.")

    print("\n--- TODOS OS TESTES DE SEGURANÇA PASSARAM ---")

if __name__ == "__main__":
    run_security_tests()