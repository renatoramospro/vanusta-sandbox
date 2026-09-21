import time
import threading

class AudioLayer:
    def __init__(self, name, bpm):
        self.name = name
        self.bpm = bpm
        self.beat_duration = 60.0 / bpm
        self.is_playing = False
        self.volume = 0.0

    def set_volume(self, vol):
        self.volume = vol

class AdaptiveAudioSystem:
    def __init__(self, bpm):
        self.bpm = bpm
        self.beat_duration = 60.0 / bpm
        self.layers = {
            "base": AudioLayer("Base", bpm),
            "percussion": AudioLayer("Percussion", bpm)
        }
        self.intensity = 0.0
        self.running = True

    def update_intensity(self, value):
        self.intensity = max(0.0, min(1.0, value))

    def audio_thread_loop(self):
        start_time = time.time()
        while self.running:
            elapsed = time.time() - start_time
            current_beat = elapsed / self.beat_duration
            
            # Vertical Layering: Volume da percussão segue a intensidade
            self.layers["base"].set_volume(1.0)
            self.layers["percussion"].set_volume(self.intensity)
            
            # Print para demonstrar sincronia de beat e volume
            beat_int = current_beat - int(current_beat)
            print(f"[Audio Engine] Beat: {int(current_beat)} | Fase: {beat_int:.2f} | "
                  f"Percussion Vol: {self.layers['percussion'].volume:.2f}", end='\r')
            
            time.sleep(0.05)

    def stop(self):
        self.running = False

def run_experiment():
    system = AdaptiveAudioSystem(bpm=120)
    engine_thread = threading.Thread(target=system.audio_thread_loop)
    engine_thread.start()

    try:
        # Simulação de Gameplay
        time.sleep(1)
        system.update_intensity(0.0)
        time.sleep(2)
        
        print("\n[Gameplay] Evento: Combate Iniciado!")
        system.update_intensity(1.0)
        time.sleep(3)

    finally:
        system.stop()
        engine_thread.join()
        print("\n[Sistema] Finalizado.")

if __name__ == "__main__":
    run_experiment()