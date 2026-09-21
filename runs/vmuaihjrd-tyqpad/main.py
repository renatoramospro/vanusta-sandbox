import asyncio
import gc

# --- CORE ARCHITECTURE ---

class CancelToken:
    def __init__(self):
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

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
        self._subscribers = set()
        self.current_scene = None

    def subscribe(self, callback):
        self._subscribers.add(callback)

    def unsubscribe(self, callback):
        self._subscribers.discard(callback)

    async def _notify(self, event_type, data):
        """Notifica observadores com isolamento de erro e proteção contra mutação."""
        # Solução 3: Iterar sobre uma cópia para evitar RuntimeError se alguém der unsubscribe aqui
        for callback in list(self._subscribers):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                # Solução 2: Isolamento de exceções - um erro na UI não quebra o Loader
                print(f"[SceneLoader ERROR] Falha ao notificar observador: {e}")

    async def load_scene(self, scene_name, cancel_token: CancelToken = None):
        print(f"\n>>> Iniciando carregamento da cena: {scene_name}")
        
        # Limpeza da cena anterior
        if self.current_scene:
            self.current_scene.destroy()
            self.current_scene = None
            gc.collect()

        new_scene = Scene(scene_name)
        
        # Simulação de etapas de carregamento
        steps = [
            (10, "Lendo arquivos de disco..."),
            (40, "Instanciando assets..."),
            (70, "Inicializando entidades..."),
            (100, "Finalizando...")
        ]

        for progress, msg in steps:
            # Solução 1: Verificação correta do CancelToken (propriedade, não método)
            if cancel_token and cancel_token.is_cancelled:
                print(f"[SceneLoader] Carregamento de {scene_name} CANCELADO.")
                return False

            await self._notify("progress", {"percent": progress, "msg": msg})
            await asyncio.sleep(0.1) # Simula I/O

        # Finalização da cena
        new_scene.add_entity(Entity("Player", new_scene))
        new_scene.add_entity(Entity("Enemy_1", new_scene))
        
        self.current_scene = new_scene
        await self._notify("complete", {"scene": scene_name})
        print(f">>> Cena {scene_name} carregada com sucesso!")
        return True

# --- TEST COMPONENTS ---

class LoadingUI:
    def on_progress(self, event, data):
        if event == "progress":
            print(f"[Principal UI] {data['percent']}% | {data['msg']}")
        elif event == "complete":
            print(f"[Principal UI] Carregamento concluído: {data['scene']}")

class AudioSystem:
    def on_event(self, event, data):
        if event == "complete":
            print(f"[Audio] Iniciando trilha sonora para: {data['scene']}")

class BuggyObserver:
    """Simula um sistema que quebra ao receber eventos."""
    def on_error(self, event, data):
        raise RuntimeError("Erro crítico no sistema de partículas!")

# --- EXPERIMENT RUNNER ---

async def run_experiment():
    loader = SceneLoader()
    ui = LoadingUI()
    audio = AudioSystem()
    buggy = BuggyObserver()

    # Configuração de observadores
    loader.subscribe(ui.on_progress)
    loader.subscribe(audio.on_event)
    loader.subscribe(buggy.on_error) # Este observador vai falhar

    print("=== TESTE 1: MÚLTIPLOS OBSERVADORES E ISOLAMENTO DE ERRO ===")
    # O erro do 'buggy' não deve impedir o progresso da UI ou o carregamento
    success = await loader.load_scene("Floresta")
    assert success is True, "O carregamento deveria ter tido sucesso apesar do erro do observador."

    print("\n=== TESTE 2: CANCELAMENTO DE CARGA ===")
    token = CancelToken()
    
    async def delayed_cancel():
        await asyncio.sleep(0.15)
        token.cancel()

    # Inicia o carregamento e o cancelamento simultaneamente
    load_task = asyncio.create_task(loader.load_scene("Caverna", token))
    cancel_task = asyncio.create_task(delayed_cancel())
    
    success_cancel = await load_task
    await cancel_task
    assert success_cancel is False, "O carregamento deveria ter sido cancelado."

    print("\n=== TESTE 3: PROTEÇÃO CONTRA MUTAÇÃO DE LISTA ===")
    # Testar se desinscrever durante o evento causa erro
    class SelfUnsubscriber:
        def __init__(self, loader):
            self.loader = loader
        def on_event(self, event, data):
            print(f"[SelfUnsubscriber] Me desinscrevendo durante o evento...")
            self.loader.unsubscribe(self.on_event)

    su = SelfUnsubscriber(loader)
    loader.subscribe(su.on_event)
    # Se houver erro de mutação, o teste falhará aqui
    await loader.load_scene("Deserto")

    print("\n[Final] Todos os testes passaram com sucesso!")

if __name__ == "__main__":
    asyncio.run(run_experiment())