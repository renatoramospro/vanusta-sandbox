import asyncio
import time

# --- INFRAESTRUTURA DE EVENTOS (Simulando Signals/Events) ---
class Event:
    def __init__(self):
        self._subscribers = []

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def emit(self, *args, **kwargs):
        for callback in self._subscribers:
            callback(*args, **kwargs)

# --- DOMÍNIO DO JOGO ---

class Entity:
    def __init__(self, name, scene):
        self.name = name
        self.scene = scene
        print(f"  [Entity] {self.name} criada na cena {scene.name}")

    def __del__(self):
        # O __del__ no Python é chamado quando o objeto é coletado pelo GC
        print(f"  [Memory] {self.name} foi DESTRUÍDA (limpeza de memória)")

class Scene:
    def __init__(self, name):
        self.name = name
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)

    def dispose(self):
        print(f"[Scene] Descartando cena {self.name}...")
        # Limpa referências para permitir a coleta pelo Garbage Collector
        self.entities.clear()

# --- SISTEMA DE CARREGAMENTO (O CORAÇÃO DA MISSÃO) ---

class SceneLoader:
    def __init__(self):
        self.current_scene = None
        # Eventos para desacoplamento
        self.on_progress = Event()
        self.on_complete = Event()

    async def load_scene(self, scene_name):
        print(f"\n>>> Iniciando carregamento da cena: {scene_name}")
        
        # 1. Limpeza da cena anterior (Evita vazamento)
        if self.current_scene:
            self.current_scene.dispose()
            self.current_scene = None

        # 2. Simulação de I/O (0% a 80%)
        for i in range(1, 5):
            await asyncio.sleep(0.2) # Simula leitura de disco
            progress = (i * 20) / 100
            self.on_progress.emit(progress)

        # 3. Simulação de Inicialização (80% a 100%)
        new_scene = Scene(scene_name)
        # Criando entidades para a nova cena
        new_scene.add_entity(Entity("Player", new_scene))
        new_scene.add_entity(Entity("Enemy_1", new_scene))
        
        await asyncio.sleep(0.3) # Simula setup de memória
        self.on_progress.emit(1.0)
        
        self.current_scene = new_scene
        self.on_complete.emit(new_scene)
        print(f">>> Cena {scene_name} carregada com sucesso!\n")

# --- UI (OBSERVADORA) ---

class LoadingUI:
    def __init__(self, loader: SceneLoader):
        # A UI se inscreve nos eventos do loader (Desacoplamento)
        loader.on_progress.subscribe(self.update_bar)
        loader.on_complete.subscribe(self.show_finished)

    def update_bar(self, progress):
        bar_length = 20
        filled = int(bar_length * progress)
        bar = "█" * filled + "-" * (bar_length - filled)
        print(f"[UI] Progresso: |{bar}| {progress*100:.0f}%")

    def show_finished(self, scene):
        print(f"[UI] Tela de carregamento sumindo... Bem-vindo à {scene.name}!")

# --- TESTES E CONTRAEXEMPLOS ---

async def run_experiment():
    print("=== TESTE 1: ARQUITETURA CORRETA (DESACOPLADA E LIMPA) ===")
    loader = SceneLoader()
    ui = LoadingUI(loader)

    await loader.load_scene("Floresta")
    await loader.load_scene("Caverna") # Deve destruir a Floresta
    
    # Forçar Garbage Collection para demonstrar a limpeza no log
    import gc
    gc.collect()

    print("\n=== TESTE 2: CONTRAEXEMPLO - VAZAMENTO DE MEMÓRIA (LEAK) ===")
    # Simulando o erro: Uma lista global que guarda referências de tudo
    GLOBAL_REGISTRY = []

    class LeakyEntity(Entity):
        def __init__(self, name, scene):
            super().__init__(name, scene)
            GLOBAL_REGISTRY.append(self) # ERRO: Referência presa globalmente

    class LeakyScene(Scene):
        def add_leaky_entity(self, name):
            e = LeakyEntity(name, self)
            self.add_entity(e)

    print("Criando cena com erro de vazamento...")
    leaky_loader = SceneLoader()
    leaky_scene = LeakyScene("Mundo_Bugado")
    leaky_scene.add_leaky_entity("Inimigo_Fantasma")
    
    # Simulando troca de cena
    print("Trocando de cena...")
    leaky_loader.current_scene = None # Simula descarte
    leaky_scene = None
    
    import gc
    gc.collect()
    
    if len(GLOBAL_REGISTRY) > 0:
        print(f"[ALERTA] Vazamento detectado! {len(GLOBAL_REGISTRY)} objeto(s) presos no GLOBAL_REGISTRY.")
    else:
        print("[OK] Memória limpa.")

    print("\n=== TESTE 3: CONTRAEXEMPLO - ACOPLAMENTO (TIGHT COUPLING) ===")
    # Simulando o erro: Loader que precisa saber da UI para funcionar
    class BadLoader:
        def __init__(self, ui_element):
            self.ui = ui_element # ERRO: Loader depende de um objeto de UI específico

        async def load(self):
            print("[BadLoader] Carregando...")
            self.ui.set_text("Carregando...") # Se a UI mudar de nome, o loader quebra
            await asyncio.sleep(0.1)
            self.ui.set_text("Pronto!")

    class MockUI:
        def set_text(self, t): print(f"[MockUI] Texto: {t}")

    bad_ui = MockUI()
    bad_loader = BadLoader(bad_ui)
    await bad_loader.load()

if __name__ == "__main__":
    asyncio.run(run_experiment())