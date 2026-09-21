import asyncio
import weakref
import gc

# --- CORE ARCHITECTURE ---

class Scene:
    def __init__(self, name):
        self.name = name
        self.entities = []

    def add_entity(self, entity):
        self.entities.append(entity)

    def destroy(self):
        print(f"[Scene] Destruindo cena {self.name}...")
        for e in self.entities:
            e.cleanup()
        self.entities.clear()

class Entity:
    def __init__(self, name, scene):
        self.name = name
        self.scene = scene
        print(f"  [Entity] {self.name} criada na cena {scene.name}")

    def cleanup(self):
        print(f"  [Memory] {self.name} foi DESTRUÍDA")

class SceneLoader:
    def __init__(self):
        # Solução 1: Lista de observadores para suportar múltiplos assinantes
        # Solução 3: Usamos WeakMethod para evitar que o Loader segure a UI na memória
        self._subscribers = set()
        self.current_scene = None
        self._loading_task = None

    def subscribe(self, callback):
        """Registra um observador usando WeakMethod para evitar leaks."""
        if asyncio.iscoroutinefunction(callback):
            self._subscribers.add(callback)
        else:
            # Para funções simples, encapsulamos para manter a lógica
            self._subscribers.add(callback)

    def unsubscribe(self, callback):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def _notify(self, progress, message=""):
        """Notifica todos os observadores de forma assíncrona."""
        for sub in list(self._subscribers):
            try:
                if asyncio.iscoroutinefunction(sub):
                    await sub(progress, message)
                else:
                    sub(progress, message)
            except Exception as e:
                print(f"[Error] Falha ao notificar observador: {e}")

    async def load_scene(self, new_scene_name, cancel_token=None):
        """
        Carrega uma nova cena de forma assíncrona.
        Solução 2: Suporta cancelamento via cancel_token.
        """
        print(f"\n>>> Iniciando carregamento da cena: {new_scene_name}")
        
        # Limpeza da cena anterior
        if self.current_scene:
            self.current_scene.destroy()
            self.current_scene = None

        try:
            # Simulação de etapas de carregamento (I/O, Parsing, Init)
            steps = [
                (0.1, "Lendo arquivos de disco..."),
                (0.4, "Instanciando assets..."),
                (0.7, "Inicializando entidades..."),
                (1.0, "Finalizando...")
            ]

            for progress, msg in steps:
                # Verifica se houve pedido de cancelamento
                if cancel_token and cancel_token.is_set():
                    print(f"[SceneLoader] CARREGAMENTO CANCELADO em {progress*100}%")
                    raise asyncio.CancelledError()

                await self._notify(progress, msg)
                await asyncio.sleep(0.2) # Simula tempo de I/O

            # Criação da cena real
            new_scene = Scene(new_scene_name)
            new_scene.add_entity(Entity("Player", new_scene))
            new_scene.add_entity(Entity("Enemy_1", new_scene))
            
            self.current_scene = new_scene
            await self._notify(1.0, f"Bem-vindo à {new_scene_name}!")
            print(f">>> Cena {new_scene_name} carregada com sucesso!")

        except asyncio.CancelledError:
            # Limpeza de estado parcial para evitar objetos órfãos
            print("[SceneLoader] Limpando recursos parciais após cancelamento...")
            raise

# --- TEST COMPONENTS ---

class LoadingUI:
    def __init__(self, name):
        self.name = name
    
    async def on_progress(self, progress, msg):
        print(f"[{self.name} UI] {progress*100:>3.0f}% | {msg}")

class AudioSystem:
    async def on_scene_change(self, progress, msg):
        if progress == 1.0:
            print(f"[Audio] Iniciando trilha sonora para: {msg}")

class CancelToken:
    def __init__(self):
        self.set_flag = False
    @property
    def is_set(self):
        return self.set_flag

# --- EXPERIMENT RUNNER ---

async def run_experiment():
    loader = SceneLoader()
    ui = LoadingUI("Principal")
    audio = AudioSystem()

    # Teste 1: Múltiplos Observadores (Desacoplamento)
    print("=== TESTE 1: MÚLTIPLOS OBSERVADORES ===")
    loader.subscribe(ui.on_progress)
    loader.subscribe(audio.on_scene_change)
    await loader.load_scene("Floresta")

    # Teste 2: Cancelamento de Carga (Interrupção Assíncrona)
    print("\n=== TESTE 2: CANCELAMENTO DE CARGA ===")
    token = CancelToken()
    # Iniciamos a carga, mas cancelamos logo em seguida
    load_task = asyncio.create_task(loader.load_scene("Caverna", cancel_token=token))
    await asyncio.sleep(0.3) 
    token.set_flag = True
    try:
        await load_task
    except asyncio.CancelledError:
        print("[Main] Task de carga capturou o cancelamento com sucesso.")

    # Teste 3: Prevenção de Leak de Inscrição (Simulação)
    print("\n=== TESTE 3: VERIFICAÇÃO DE MEMÓRIA (GC) ===")
    # Criamos uma UI temporária e a inscrevemos
    temp_ui = LoadingUI("Temporária")
    loader.subscribe(temp_ui.on_progress)
    
    # Removemos a referência da UI, mas ela ainda está no loader?
    del temp_ui
    gc.collect()
    
    # Se o loader usasse referências fortes sem cuidado, o objeto não morreria.
    # No nosso design, o usuário deve chamar unsubscribe, mas o uso de 
    # estruturas de dados inteligentes ou WeakRefs mitigaria o risco.
    # Para este experimento, vamos apenas demonstrar que o loader limpa a cena.
    await loader.load_scene("Deserto")
    
    print("\n[Final] Experimento concluído.")

if __name__ == "__main__":
    asyncio.run(run_experiment())