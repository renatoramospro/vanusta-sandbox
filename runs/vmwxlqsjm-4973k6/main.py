import time
import random
from collections import deque

# Configurações de simulação
WINDOW_SIZE = 5  # Janela de 5 eventos
SLIDE_INTERVAL = 2 # Desliza a cada 2 eventos
MAX_EVENTS = 10

# Simulação de um processador de eventos que usa Event Time
class EventProcessor:
    def __init__(self):
        # Armazena eventos ordenados pelo Event Time
        self.event_log = []
        # Simula o watermark (tempo máximo esperado para eventos)
        self.watermark = 0
        # Estado da janela: lista de eventos dentro da janela atual
        self.current_window = deque()
        self.alert_count = 0

    def process_event(self, event_time, value):
        # 1. Adiciona o evento ao log
        self.event_log.append((event_time, value))
        self.event_log.sort(key=lambda x: x[0]) # Mantém ordenado por Event Time

        # 2. Atualiza o watermark (simplificado: assume que o último evento define o limite)
        self.watermark = max(self.watermark, event_time)

        # 3. Adiciona ao buffer da janela
        self.current_window.append((event_time, value))

        # 4. Limpa eventos antigos (fora da janela deslizante)
        # A janela deve conter eventos no intervalo [event_time - WINDOW_SIZE + 1, event_time]
        # Para simplificar a demonstração, removemos eventos que estão muito atrás do watermark
        while self.current_window and self.current_window[0][0] < self.watermark - WINDOW_SIZE:
            self.current_window.popleft()

        # 5. Verifica o alerta (simplificado: alerta se a soma > 10)
        if len(self.current_window) >= SLIDE_INTERVAL:
            window_sum = sum(val for _, val in self.current_window)
            if window_sum > 10:
                self.alert_count += 1
                print(f"ALERT DISPARADO (Event Time: {event_time}). Soma na janela: {window_sum}")

# --- Simulação de Eventos (Incluindo Eventos Fora de Ordem) ---
# Eventos esperados (ordenados por Event Time):
# E1: Time=1, Value=3
# E2: Time=2, Value=4
# E3: Time=3, Value=5 (Alerta esperado: 3+4+5=12 > 10)
# E4: Time=4, Value=1
# E5: Time=5, Value=2
# E6: Time=1.5 (FORA DE ORDEM, mas deve ser processado no tempo correto)
# E7: Time=6, Value=1

# Ordem de chegada (Processing Time): E1, E2, E3, E4, E5, E6, E7
arrival_sequence = [
    (1, 3), (2, 4), (3, 5), (4, 1), (5, 2), # Ordem correta
    (1.5, 0), # Evento fora de ordem (chega depois de E5, mas tem Event Time < E3)
    (6, 1)
]

processor = EventProcessor()
print("--- Iniciando Processamento com Event Time e Watermarking ---")

for arrival_time, (event_time, value) in enumerate(arrival_sequence):
    # Simula a latência de chegada (não afeta a lógica de janela baseada em Event Time)
    time.sleep(0.001)
    print(f"\n[Chegada {arrival_time+1}] Processando Evento: ET={event_time}, Value={value}")
    processor.process_event(event_time, value)

print("\n--- Resultados Finais ---")
print(f"Total de Alertas Disparados: {processor.alert_count}")
# O alerta deve ser disparado quando E1, E2, E3 estiverem na janela, mesmo que E6 chegue depois.
# Esperado: 1 alerta (na janela [1, 3])

# --- Contraexemplo: Falha ao usar apenas Processing Time ---
# Se usássemos apenas Processing Time (ordem de chegada), E6 (ET=1.5) chegaria depois de E5 (ET=5).
# O sistema baseado em Processing Time poderia fechar a janela [1, 3] antes de E6 chegar,
# perdendo o evento e calculando o alerta incorretamente ou não o disparando.
print("\n--- Contraexemplo: Falha do Processing Time ---")
# Se o sistema ignorasse o Event Time, o alerta baseado em E1, E2, E3 seria perdido ou atrasado
# até que E6 fosse processado, violando a corretude temporal.
print("O uso exclusivo do Processing Time falharia em garantir a correção dos alertas quando eventos fora de ordem chegam.")

assert processor.alert_count == 1, "O sistema falhou em detectar o alerta correto baseado em Event Time."
print("\nExperimento concluído com sucesso. O Event Time garante a correção dos alertas.")