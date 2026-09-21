import collections

# --- CAMADA 1: INFRAESTRUTURA DE COMUNICAÇÃO (EVENT BUS) ---

class EventBus:
    """O mediador que permite o desacoplamento total."""
    def __init__(self):
        self._subscribers = collections.defaultdict(list)

    def subscribe(self, event_type, callback):
        self._subscribers[event_type].append(callback)

    def emit(self, event_type, data=None):
        for callback in self._subscribers[event_type]:
            callback(data)

# --- CAMADA 2: PERSISTÊNCIA DE APRENDIZADO (INDEPENDENTE) ---

class LearningStore:
    """Armazena o progresso de aprendizado separado do save do jogo."""
    def __init__(self):
        self._learned_skills = set()

    def mark_learned(self, skill_id):
        self._learned_skills.add(skill_id)

    def has_learned(self, skill_id):
        return skill_id in self._learned_skills

# --- CAMADA 3: CORE DE TUTORIAL (ABSTRAÇÕES E TIPOS) ---

class Tutorial:
    """Interface base para todos os tipos de tutorial."""
    def __init__(self, tutorial_id):
        self.tutorial_id = tutorial_id
        self.is_active = False

    def start(self): self.is_active = True
    def complete(self): self.is_active = False

class LinearTutorial(Tutorial):
    """Tutorial que segue uma sequência de passos (Ex: Pular -> Atacar)."""
    def __init__(self, tutorial_id, steps, learning_store):
        super().__init__(tutorial_id)
        self.steps = steps  # Lista de eventos necessários
        self.current_step_idx = 0
        self.learning_store = learning_store

    def handle_event(self, event_type, data):
        if not self.is_active: return
        
        if event_type == self.steps[self.current_step_idx]:
            print(f"[Tutorial Linear] Passo '{event_type}' concluído!")
            self.current_step_idx += 1
            if self.current_step_idx >= len(self.steps):
                print(f"[Tutorial Linear] {self.tutorial_id} FINALIZADO.")
                self.learning_store.mark_learned(self.tutorial_id)
                self.complete()

class ContextualTutorial(Tutorial):
    """Tutorial que só aparece quando um contexto específico é atingido."""
    def __init__(self, tutorial_id, trigger_event, message, learning_store):
        super().__init__(tutorial_id)
        self.trigger_event = trigger_event
        self.message = message
        self.learning_store = learning_store

    def handle_event(self, event_type, data):
        if not self.is_active: return
        
        if event_type == self.trigger_event:
            print(f"[Tutorial Contextual] MENSAGEM: {self.message}")
            self.learning_store.mark_learned(self.tutorial_id)
            self.complete()

class TutorialManager:
    """Orquestrador que conecta o EventBus aos Tutoriais."""
    def __init__(self, event_bus, learning_store):
        self.event_bus = event_bus
        self.learning_store = learning_store
        self.active_tutorials = []

    def register_tutorial(self, tutorial):
        if not self.learning_store.has_learned(tutorial.tutorial_id):
            self.active_tutorials.append(tutorial)
            # O Manager escuta o bus e repassa para os tutoriais ativos
            # Em um sistema real, o Manager assinaria eventos específicos para performance
            self.event_bus.subscribe("ANY", lambda data: self._dispatch(data))

    def _dispatch(self, event_data):
        # event_data deve ser um tupla (event_type, payload)
        event_type, payload = event_data
        for tutorial in self.active_tutorials[:]:
            if tutorial.is_active:
                tutorial.handle_event(event_type, payload)
            if not tutorial.is_active:
                self.active_tutorials.remove(tutorial)

    def activate_tutorial(self, tutorial_id):
        for t in self.active_tutorials:
            if t.tutorial_id == tutorial_id:
                t.start()
                print(f"[Manager] Tutorial '{tutorial_id}' ATIVADO.")

# --- CAMADA 4: GAMEPLAY CORE (EMISSORES) ---

class Player:
    """O Player não conhece o TutorialManager. Ele apenas emite eventos."""
    def __init__(self, event_bus):
        self.event_bus = event_bus

    def jump(self):
        print("-> Player pulou.")
        self.event_bus.emit("ANY", ("PLAYER_JUMP", None))

    def attack(self):
        print("-> Player atacou.")
        self.event_bus.emit("ANY", ("PLAYER_ATTACK", None))

# --- TESTE DE EXECUÇÃO ---

def run_experiment():
    bus = EventBus()
    store = LearningStore()
    manager = TutorialManager(bus, store)
    player = Player(bus)

    # 1. Configurando um Tutorial Linear (Pular -> Atacar)
    linear_tut = LinearTutorial("BASIC_MOVEMENT", ["PLAYER_JUMP", "PLAYER_ATTACK"], store)
    manager.register_tutorial(linear_tut)
    manager.activate_tutorial("BASIC_MOVEMENT")

    # 2. Configurando um Tutorial Contextual (Aparece quando entra em combate)
    context_tut = ContextualTutorial("COMBAT_TIP", "ENEMY_SPAWNED", "Use o botão de ataque!", store)
    manager.register_tutorial(context_tut)
    # O tutorial contextual começa inativo, esperando o gatilho
    context_tut.is_active = True 

    print("\n--- Iniciando Simulação de Gameplay ---")
    
    # Passo 1: Jogador pula
    player.jump()

    # Passo 2: Um inimigo aparece (Gatilho Contextual)
    print("\n[Mundo] Um inimigo apareceu!")
    bus.emit("ANY", ("ENEMY_SPAWNED", None))

    # Passo 3: Jogador ataca (Finaliza o Linear)
    player.attack()

    print("\n--- Verificação de Estado ---")
    print(f"Aprendizado registrado: {store._learned_skills}")
    
    # Teste de Independência: Se tentarmos registrar o mesmo tutorial, ele não deve ser reativado
    print(f"Tutorial 'BASIC_MOVEMENT' já aprendido? {store.has_learned('BASIC_MOVEMENT')}")

if __name__ == "__main__":
    run_experiment()