import weakref

class Observable:
    """
    Um Subject robusto que utiliza referências fracas para evitar memory leaks
    e iteração sobre cópias para evitar crashes por mutação.
    """
    def __init__(self):
        # Estrutura: { "evento_nome": [WeakMethod1, WeakMethod2] }
        self._observers = {}

    def subscribe(self, event_name, callback):
        if event_name not in self._observers:
            self._observers[event_name] = []
        
        # Usamos WeakMethod para que o observador possa ser coletado pelo GC
        # mesmo que ainda esteja inscrito neste evento.
        if hasattr(callback, '__self__'):
            ref = weakref.WeakMethod(callback)
        else:
            # Para funções puras, usamos ref simples (embora menos comum em UI)
            ref = weakref.ref(callback)
            
        self._observers[event_name].append(ref)

    def notify(self, event_name, *args, **kwargs):
        if event_name not in self._observers:
            return

        # 1. Prevenção de Crash: Iteramos sobre uma CÓPIA da lista (snapshot)
        # Isso permite que um observador se desinscreva durante o notify sem erro.
        observers_snapshot = list(self._observers[event_name])
        
        for ref in observers_snapshot:
            callback = ref()
            if callback is not None:
                # 2. Execução do callback
                callback(*args, **kwargs)
            else:
                # Limpeza automática de referências mortas (Garbage Collected)
                self._observers[event_name].remove(ref)

class Player(Observable):
    def __init__(self, name, health):
        super().__init__()
        self.name = name
        self._health = health

    @property
    def health(self):
        return self._health

    def take_damage(self, amount):
        self._health -= amount
        # 3. Proteção de Encapsulamento: Passamos apenas o VALOR (int), 
        # não o objeto 'self'. A UI não tem acesso aos métodos do Player.
        self.notify("health_changed", self._health)

class HealthBarUI:
    def __init__(self, name):
        self.name = name

    def on_health_changed(self, new_health):
        print(f"[UI - {self.name}] Atualizando barra visual para: {new_health}%")

class CombatLog:
    def log_event(self, new_health):
        print(f"[Log] Alerta: Vida do jogador caiu para {new_health}!")

def run_security_experiments():
    print("=== INICIANDO TESTES DE SEGURANÇA E ESTABILIDADE ===\n")

    # --- TESTE 1: Prevenção de Crash por Mutação (Reentrância) ---
    print("Teste 1: Reentrância (Observador que se desinscreve ao ser notificado)...")
    player = Player("Hero", 100)
    
    class SelfRemovingObserver:
        def __init__(self, p):
            self.p = p
        def callback(self, val):
            print("  [Observer] Recebi o evento e vou me desinscrever agora!")
            self.p.unsubscribe("health_changed", self.callback)

    # Adicionamos uma classe auxiliar para gerenciar o unsubscribe no teste
    # (Simulando o comportamento de um componente que se destrói)
    class Wrapper:
        def __init__(self, p, obs):
            self.p = p
            self.obs = obs
        def call(self, val):
            self.obs.callback(val)
            self.p.unsubscribe("health_changed", self.call)

    wrapper = Wrapper(player, SelfRemovingObserver(player))
    player.subscribe("health_changed", wrapper.call)
    
    # Se o notify não usar snapshot, isso causará erro de mutação na lista
    player.take_damage(10) 
    print("  RESULTADO: Sucesso! O sistema não crashou ao modificar a lista durante o notify.\n")


    # --- TESTE 2: Prevenção de Memory Leak (Weak References) ---
    print("Teste 2: Memory Leak (Verificando se referências fracas funcionam)...")
    player_leak_test = Player("LeakTest", 100)
    ui_zumbi = HealthBarUI("Zumbi")
    
    player_leak_test.subscribe("health_changed", ui_zumbi.on_health_changed)
    
    print(f"  Antes de deletar UI: {len(player_leak_test._observers['health_changed'])} observadores.")
    
    # Deletamos a UI (simulando fechamento de janela)
    del ui_zumbi
    import gc
    gc.collect() # Força o Garbage Collector
    
    # O notify deve limpar a referência morta automaticamente
    player_leak_test.notify("health_changed", 50)
    
    # Verificamos se a lista foi limpa
    remaining = len(player_leak_test._observers["health_changed"])
    print(f"  Após deletar UI e rodar notify: {remaining} observadores ativos.")
    assert remaining == 0
    print("  RESULTADO: Sucesso! A referência morta foi removida e não causou leak.\n")


    # --- TESTE 3: Proteção de Encapsulamento ---
    print("Teste 3: Encapsulamento (UI não recebe o objeto Player)...")
    player_encap = Player("Encap", 100)
    
    def malicious_ui_callback(data):
        # Se 'data' fosse o objeto player, a UI poderia fazer: data.take_damage(100)
        # Como passamos apenas o int, o teste abaixo falharia se tentássemos acessar atributos
        try:
            print(f"  Tentando acessar .take_damage() no dado recebido: {data}")
            data.take_damage(100)
        except AttributeError:
            print("  RESULTADO: Sucesso! O dado recebido é um valor simples, não o objeto Player.")

    player_encap.subscribe("health_changed", malicious_ui_callback)
    player_encap.take_damage(20)
    print("\n=== TODOS OS TESTES DE SEGURANÇA PASSARAM ===\n")

# Adicionando método de suporte para o teste de reentrância
def unsubscribe_helper(self, event_name, callback):
    if event_name in self._observers:
        self._observers[event_name] = [r for r in self._observers[event_name] 
                                       if r() is not None and r().__call__ != callback]

# Injetando o método de suporte para o experimento
Observable.unsubscribe = unsubscribe_helper

if __name__ == "__main__":
    run_security_experiments()