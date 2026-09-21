import sys

# --- INFRAESTRUTURA DO FRAMEWORK (O que o desenvolvedor usa) ---

class Observable:
    """Base para objetos que podem ser observados."""
    def __init__(self):
        self._observers = {}

    def subscribe(self, event_name, callback):
        if event_name not in self._observers:
            self._observers[event_name] = []
        self._observers[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        if event_name in self._observers:
            self._observers[event_name].remove(callback)

    def notify(self, event_name, *args, **kwargs):
        if event_name in self._observers:
            for callback in self._observers[event_name]:
                callback(*args, **kwargs)

# --- CENÁRIO 1: O ERRO (ACOPLAMENTO DIRETO) ---

class BadPlayer:
    """Player que possui dependência direta de uma UI específica."""
    def __init__(self, ui_component=None):
        self.health = 100
        self.ui = ui_component  # Referência direta!

    def take_damage(self, amount):
        self.health -= amount
        print(f"[BadPlayer] Recebi {amount} de dano. Vida: {self.health}")
        # ERRO: O Player decide QUANDO e COMO a UI deve ser atualizada.
        # Se a UI não existir ou mudar de nome, o jogo crasha.
        if self.ui:
            self.ui.update_health_bar(self.health)
        else:
            # Simulando o erro de referência nula ou falta de componente
            raise AttributeError("BadPlayer falhou: Tentei atualizar uma UI que não existe!")

# --- CENÁRIO 2: A SOLUÇÃO (DESACOPLAMENTO) ---

class GoodPlayer(Observable):
    """Player que apenas emite sinais de mudança de estado."""
    def __init__(self):
        super().__init__()
        self.health = 100

    def take_damage(self, amount):
        self.health -= amount
        print(f"[GoodPlayer] Recebi {amount} de dano. Vida: {self.health}")
        # O Player não sabe quem está ouvindo. Ele apenas avisa que algo mudou.
        self.notify("health_changed", self.health)

class HealthBarUI:
    """Componente de UI que reage a eventos."""
    def __init__(self, name):
        self.name = name

    def on_health_changed(self, new_health):
        print(f"[UI - {self.name}] Atualizando barra visual para: {new_health}%")

# --- TESTES E DEMONSTRAÇÃO ---

def run_experiment():
    print("=== TESTE 1: O PERIGO DO ACOPLAMENTO DIRETO ===")
    player_bad = BadPlayer(ui_component=None)
    try:
        player_bad.take_damage(20)
    except AttributeError as e:
        print(f"RESULTADO ESPERADO (ERRO): {e}")
    print("-" * 50)

    print("=== TESTE 2: A LIBERDADE DO DESACOPLAMENTO ===")
    player_good = GoodPlayer()
    
    # Cenário A: Sem UI presente (O jogo deve rodar normalmente)
    print("Cenário A: Jogando sem nenhuma UI carregada...")
    player_good.take_damage(10)
    print("RESULTADO: Sucesso! O Player funcionou sem depender de UI.")
    print("-" * 50)

    # Cenário B: Com UI presente
    print("Cenário B: Adicionando uma barra de vida (HUD)...")
    hud_bar = HealthBarUI("HUD_Principal")
    # A UI se inscreve no Player, não o contrário.
    player_good.subscribe("health_changed", hud_bar.on_health_changed)
    
    player_good.take_damage(30)
    print("RESULTADO: Sucesso! A UI reagiu ao evento do Player.")
    print("-" * 50)

    # Cenário C: Múltiplas UIs (Flexibilidade)
    print("Cenário C: Adicionando um segundo observador (Log de Combate)...")
    def combat_log(health):
        print(f"[Log] Alerta: Vida do jogador caiu para {health}!")
    
    player_good.subscribe("health_changed", combat_log)
    player_good.take_damage(50)
    print("RESULTADO: Sucesso! Múltiplos sistemas reagiram ao mesmo evento.")

if __name__ == "__main__":
    run_experiment()