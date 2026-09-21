import time

class AssetStreamer:
    """Simula o sistema de streaming de assets do motor."""
    def __init__(self):
        self.assets_loaded = 0
        self.is_running = True

    def update(self):
        if self.is_running:
            self.assets_loaded += 1  # Simula o carregamento contínuo de texturas/LODs

class PhysicsSystem:
    """Simula a física do jogo."""
    def __init__(self):
        self.position = 0.0
        self.is_frozen = False

    def update(self, dt):
        if not self.is_frozen:
            self.position += dt * 10.0

class PhotoModeManager:
    """Gerencia o Modo Foto e o protocolo de fallback de VRAM."""
    def __init__(self, physics, streamer):
        self.physics = physics
        self.streamer = streamer
        self.vram_available_mb = 1024 # Simulação de memória disponível

    def enter_photo_mode(self):
        print("[Modo Foto] Ativando...")
        self.physics.is_frozen = True

    def exit_photo_mode(self):
        print("[Modo Foto] Saindo...")
        self.physics.is_frozen = False

    def capture_image(self, requested_res_mb):
        print(f"[Captura] Solicitando {requested_res_mb}MB de VRAM...")
        
        # Protocolo de Fallback
        if requested_res_mb <= self.vram_available_mb:
            return "SUCESSO: Renderização GPU-Native (Alta Resolução)"
        elif requested_res_mb <= self.vram_available_mb * 2:
            return "FALLBACK: Tiled Rendering (Processamento em blocos para poupar VRAM)"
        else:
            return "FALLBACK CRÍTICO: Downsampling + Upscaling via CPU (Resolução Nativa)"

def run_experiment():
    physics = PhysicsSystem()
    streamer = AssetStreamer()
    photo_manager = PhotoModeManager(physics, streamer)

    print("--- FASE 1: Gameplay Normal ---")
    for _ in range(3):
        physics.update(0.1)
        streamer.update()
    print(f"Física: {physics.position:.1f} | Assets Carregados: {streamer.assets_loaded}")

    print("\n--- FASE 2: Modo Foto (Teste de Isolamento) ---")
    photo_manager.enter_photo_mode()
    
    # Durante o modo foto, a física deve parar, mas o streamer deve continuar
    for _ in range(3):
        physics.update(0.1) # dt simulação é 0.1, mas physics.is_frozen deve impedir
        streamer.update()   # Engine time continua
    
    print(f"Física (Esperado parado): {physics.position:.1f}")
    print(f"Assets Carregados (Esperado aumentar): {streamer.assets_loaded}")
    
    assert physics.position == 3.0, "ERRO: A física não foi congelada!"
    assert streamer.assets_loaded > 3, "ERRO: O streaming de assets foi congelado indevidamente!"

    print("\n--- FASE 3: Teste de Protocolo de Fallback de VRAM ---")
    # Caso 1: Resolução suportada
    print(f"Resultado 1: {photo_manager.capture_image(512)}")
    # Caso 2: Resolução exige Tiled Rendering
    print(f"Resultado 2: {photo_manager.capture_image(1536)}")
    # Caso 3: Resolução excede limites (Fallback Crítico)
    print(f"Resultado 3: {photo_manager.capture_image(5000)}")

    print("\n--- FASE 4: Retorno ao Gameplay ---")
    photo_manager.exit_photo_mode()
    physics.update(0.1)
    print(f"Física (Esperado retomar): {physics.position:.1f}")
    assert physics.position > 3.0, "ERRO: A física não retomou após o modo foto!"

    print("\n[SUCESSO] Arquitetura corrigida validada com êxito!")

if __name__ == "__main__":
    run_experiment()