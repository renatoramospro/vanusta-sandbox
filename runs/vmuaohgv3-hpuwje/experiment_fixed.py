class ObservableProperty:
    """Implementação robusta de Property Reativa com suporte a unsubscribe."""
    def __init__(self, value=None):
        self._value = value
        self._listeners = []

    def subscribe(self, listener):
        """Adiciona um observador e retorna uma função de callback para unsubscribe."""
        if listener not in self._listeners:
            self._listeners.append(listener)
        # Notifica imediatamente com o valor atual (comportamento padrão)
        listener(self._value)
        
        # Retorna função de desinscrição para evitar vazamentos de memória
        def unsubscribe():
            if listener in self._listeners:
                self._listeners.remove(listener)
        return unsubscribe

    def set(self, value):
        if self._value != value:
            self._value = value
            for listener in list(self._listeners): # Cópia para segurança caso modifique durante iteração
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
        self.hp_text = ObservableProperty(f"{model.hp}/{model.max_hp}")
        self.inventory_list = ObservableProperty(list(model.inventory))
        self.pause_state = ObservableProperty(model.is_paused)

    def process_damage(self, amount):
        self._model.take_damage(amount)
        # Atualiza a propriedade reativa (o ViewModel traduz o Model para a View)
        self.hp_text.set(f"{self._model.hp}/{self._model.max_hp}")

    def process_pickup(self, item_name):
        self._model.add_item(item_name)
        self.inventory_list.set(list(self._model.inventory))

    def process_pause_toggle(self):
        self._model.toggle_pause()
        self.pause_state.set(self._model.is_paused)


# ==========================================
# 3. VIEW (Camada Visual / HUD / Inventário / Pausa)
# ==========================================
class GameView:
    def __init__(self):
        self.rendered_hp = ""
        self.rendered_inventory = []
        self.rendered_pause_state = False
        self._unsubscribers = []

    def bind(self, vm: GameViewModel):
        """Realiza o data-binding salvando as funções de unsubscribe."""
        self._unsubscribers.append(
            vm.hp_text.subscribe(lambda val: self.render_hp(val))
        )
        self._unsubscribers.append(
            vm.inventory_list.subscribe(lambda val: self.render_inventory(val))
        )
        self._unsubscribers.append(
            vm.pause_state.subscribe(lambda val: self.render_pause(val))
        )

    def destroy(self):
        """Simula a destruição da View (ex: fechamento de menu ou troca de cena).
        Executa todas as funções de unsubscribe para evitar vazamentos de memória."""
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()

    def render_hp(self, hp_str):
        self.rendered_hp = hp_str
        print(f"[HUD Render] HP atualizado na tela: {hp_str}")

    def render_inventory(self, items):
        self.rendered_inventory = items
        print(f"[Inventário Render] Itens na tela: {items}")

    def render_pause(self, is_paused):
        self.rendered_pause_state = is_paused
        status = "ABERTO" if is_paused else "FECHADO"
        print(f"[Menu Pausa Render] Menu de Pausa {status}")


# ==========================================
# EXECUÇÃO DO EXPERIMENTO E VALIDAÇÃO DE MEMÓRIA
# ==========================================
if __name__ == "__main__":
    print("--- Inicializando Arquitetura Desacoplada com Suporte a Unsubscribe ---")
    model = PlayerModel()
    vm = GameViewModel(model)
    view = GameView()
    
    # Vincula a View ao ViewModel
    view.bind(vm)

    print("\n--- Cenário 1: HUD Dinâmico (Recebendo Dano) ---")
    vm.process_damage(25)
    assert view.rendered_hp == "75/100", f"Erro no HUD: esperado 75/100, obtido {view.rendered_hp}"

    print("\n--- Cenário 2: Teste de Destruição e Prevenção de Vazamento (Memory Leak Test) ---")
    # A view é destruída (ex: fechou a janela ou mudou de fase)
    view.destroy()
    
    # Verificação de segurança: listeners devem estar vazios após o destroy
    assert len(vm.hp_text._listeners) == 0, "Falha: Vazamento de memória detectado, listener de HP ainda inscrito!"
    assert len(vm.inventory_list._listeners) == 0, "Falha: Vazamento de memória detectado, listener de inventário ainda inscrito!"
    
    # Alterações subsequentes no ViewModel não devem afetar a View destruída
    vm.process_damage(25)
    print("[Verificação] View destruída ignorou com sucesso a notificação subsequente.")

    print("\n[SUCESSO] Padrão MVVM reativo corrigido com mecanismo de unsubscribe validado com sucesso!")