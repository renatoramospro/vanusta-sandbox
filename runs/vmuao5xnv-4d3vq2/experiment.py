class ObservableProperty:
    """Implementação básica de Property Reativa (Observer Pattern)."""
    def __init__(self, value=None):
        self._value = value
        self._listeners = []

    def subscribe(self, listener):
        self._listeners.append(listener)
        # Notifica imediatamente com o valor atual
        listener(self._value)

    def set(self, value):
        if self._value != value:
            self._value = value
            for listener in self._listeners:
                listener(self._value)

    @property
    def value(self):
        return self._value


# ==========================================
# 1. MODEL (Gameplay Puro - Sem dependência de UI)
# ==========================================
class PlayerModel:
    def __init__(self):
        self.hp = 100
        self.max_hp = 100
        self.inventory = []
        self.is_paused = False

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def add_item(self, item_name):
        self.inventory.append(item_name)

    def toggle_pause(self):
        self.is_paused = not self.is_paused


# ==========================================
# 2. VIEWMODEL (Mediador Reativo)
# ==========================================
class GameViewModel:
    def __init__(self, model: PlayerModel):
        self._model = model
        
        # Propriedades reativas expostas para a View
        self.hp_text = ObservableProperty("100/100")
        self.inventory_list = ObservableProperty([])
        self.pause_menu_active = ObservableProperty(False)

    def process_damage(self, amount):
        self._model.take_damage(amount)
        # Atualiza a propriedade reativa baseada no Model
        self.hp_text.set(f"{self._model.hp}/{self._model.max_hp}")

    def process_pickup(self, item_name):
        self._model.add_item(item_name)
        # Cria uma cópia para disparar a reatividade da lista
        self.inventory_list.set(list(self._model.inventory))

    def process_pause_toggle(self):
        self._model.toggle_pause()
        self.pause_menu_active.set(self._model.is_paused)


# ==========================================
# 3. VIEW (HUD, Inventário e Pausa)
# ==========================================
class GameView:
    def __init__(self):
        self.rendered_hp = ""
        self.rendered_inventory = []
        self.rendered_pause_state = False

    def bind(self, view_model: GameViewModel):
        # A View assina as mudanças no ViewModel (Data Binding / Observer)
        view_model.hp_text.subscribe(lambda val: self._update_hud(val))
        view_model.inventory_list.subscribe(lambda val: self._update_inventory(val))
        view_model.pause_menu_active.subscribe(lambda val: self._update_pause(val))

    def _update_hud(self, hp_str):
        self.rendered_hp = hp_str
        print(f"[HUD Render] HP atualizado na tela: {hp_str}")

    def _update_inventory(self, items):
        self.rendered_inventory = items
        print(f"[Inventário Render] Itens na tela: {items}")

    def _update_pause(self, is_paused):
        self.rendered_pause_state = is_paused
        status = "ABERTO" if is_paused else "FECHADO"
        print(f"[Menu Pausa Render] Menu de Pausa {status}")


# ==========================================
# TESTE DE COMPROVAÇÃO E VALIDAÇÃO
# ==========================================
if __name__ == "__main__":
    print("--- Inicializando Arquitetura Desacoplada ---")
    model = PlayerModel()
    vm = GameViewModel(model)
    view = GameView()
    
    # Vincula a View ao ViewModel
    view.bind(vm)

    print("\n--- Cenário 1: HUD Dinâmico (Recebendo Dano) ---")
    vm.process_damage(25)
    assert view.rendered_hp == "75/100", f"Erro no HUD: esperado 75/100, obtido {view.rendered_hp}"

    print("\n--- Cenário 2: Inventário (Coletando Itens) ---")
    vm.process_pickup("Poção de Cura")
    vm.process_pickup("Espada Longa")
    assert len(view.rendered_inventory) == 2, "Erro no inventário: quantidade incorreta."

    print("\n--- Cenário 3: Menu de Pausa ---")
    vm.process_pause_toggle()
    assert view.rendered_pause_state is True, "Erro no menu de pausa: deveria estar ativo."

    print("\n[SUCESSO] Todos os cenários testados com 0 acoplamento direto entre Model e View!")