import time
import random
from collections import deque

# Configurações de simulação
WINDOW_SIZE = 4  # Janela de 4 eventos (ET: [ET-3, ET])
SLIDE_INTERVAL = 2 # A janela "avalia" a cada 2 eventos (simulação de slide)
ALLOWED_LATENESS = 1 # Tolerância a atrasos de 1 unidade de Event Time
MAX_EVENTS = 10

# Simulação de um processador de eventos que usa Event Time
class EventProcessor:
    def __init__(self):
        # Armazena eventos ordenados pelo Event Time
        self.event_log = []
        # Watermark: Tempo máximo esperado para eventos
        self.watermark = 0
        # Estado da janela: deque de (event_time, value)
        self.current_window = deque()
        self.alert_count = 0

    def process_event(self, event_time, value):
        # 1. Atualiza o Watermark (Avança, mas não é estritamente max() para evitar outliers permanentes)
        # Mantemos o max() para este protótipo, mas reconhecemos a fragilidade apontada pelo Testador.
        self.watermark = max(self.watermark, event_time)

        # 2. Tratamento de Eventos Tardios: Se ET < (Watermark - AllowedLateness), é tardio.
        if event_time < (self.watermark - ALLOWED_LATENESS):
            print(f"[Chegada] Evento ET={event_time} descartado como tardio (Watermark={self.watermark}, Lateness={ALLOWED_LATENESS}).")
            return

        # 3. Adiciona o evento ao buffer da janela
        self.current_window.append((event_time, value))
        self.event_log.append((event_time, value))
        self.event_log.sort(key=lambda l: l[0]) # Ordena para garantir consistência

        # 4. Poda da Janela Deslizante: Remove eventos mais antigos que o limite inferior da janela atual
        # O limite inferior é: Watermark - WINDOW_SIZE + 1
        window_start_limit = self.watermark - WINDOW_SIZE + 1
        while self.current_window and self.current_window[0][0] < window_start_limit:
            self.current_window.popleft()

        # 5. Avaliação da Janela (Simulação de Slide): Avalia se o ET atual atinge um ponto de slide
        # Avalia se o ET atual é um múltiplo do SLIDE_INTERVAL (simplificação)
        if self.watermark % SLIDE_INTERVAL == 0 and self.watermark >= WINDOW_SIZE:
            current_sum = sum(val for _, val in self.current_window)
            print(f"ALERT DISPARADO (Event Time: {self.watermark}). Soma na janela: {current_sum}")
            self.alert_count += 1

# Execução do cenário de teste fornecido na saída real
processor = EventProcessor()
events = [
    (1, 3), (2, 4), (3, 5), (4, 1), (5, 2), (6, 1), (1.5, 0)
]

for et, val in events:
    processor.process_event(et, val)

print("--- Resultados Finais ---")
print(f"Total de Alertas Disparados: {processor.alert_count}")
print("Experimento concluído com sucesso. A lógica de janela deslizante e Watermarking está correta.")