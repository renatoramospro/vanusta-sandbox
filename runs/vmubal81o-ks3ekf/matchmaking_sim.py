import time
import math
import random

class Player:
    def __init__(self, player_id, mmr, latency):
        self.id = player_id
        self.mmr = mmr
        self.latency = latency
        self.entry_time = time.time()

    def wait_time(self):
        return time.time() - self.entry_time

class Matchmaker:
    def __init__(self, base_mmr_diff=50, base_latency_diff=30):
        self.queue = []
        self.base_mmr_diff = base_mmr_diff
        self.base_latency_diff = base_latency_diff
        # Coeficientes de relaxamento
        self.alpha = 0.5  # Relaxamento de MMR (logarítmico)
        self.beta = 0.2   # Relaxamento de Latência (linear)

    def add_player(self, player):
        self.queue.append(player)

    def get_thresholds(self, wait_time):
        """Calcula os limites de tolerância baseados no tempo de espera."""
        mmr_diff = self.base_mmr_diff * (1 + self.alpha * math.log1p(wait_time))
        lat_diff = self.base_latency_diff * (1 + self.beta * wait_time)
        return mmr_diff, lat_diff

    def attempt_match(self):
        """Tenta encontrar pares na fila usando relaxamento de critérios."""
        if len(self.queue) < 2:
            return None

        # Ordenar por tempo de espera para priorizar quem está há mais tempo (FIFO-ish)
        self.queue.sort(key=lambda p: p.entry_time)
        
        matched_indices = set()
        matches_found = []

        for i in range(len(self.queue)):
            if i in matched_indices:
                continue
            
            p1 = self.queue[i]
            wait_p1 = p1.wait_time()
            mmr_limit, lat_limit = self.get_thresholds(wait_p1)

            for j in range(i + 1, len(self.queue)):
                if j in matched_indices:
                    continue
                
                p2 = self.queue[j]
                
                # Verifica se o p2 também está dentro de um limite razoável 
                # ou se o p1 (que espera há mais) aceita o p2
                mmr_gap = abs(p1.mmr - p2.mmr)
                lat_gap = abs(p1.latency - p2.latency)

                if mmr_gap <= mmr_limit and lat_gap <= lat_limit:
                    matches_found.append((p1, p2, mmr_gap, lat_gap, wait_p1))
                    matched_indices.add(i)
                    matched_indices.add(j)
                    break
            
            if i in matched_indices:
                continue

        # Remove os jogadores que deram match da fila
        new_queue = [p for idx, p in enumerate(self.queue) if idx not in matched_indices]
        self.queue = new_queue
        return matches_found

def run_simulation():
    print("--- Iniciando Simulação de Matchmaking ---")
    mm = Matchmaker(base_mmr_diff=30, base_latency_diff=20)

    # Criando jogadores com perfis variados
    # Jogador 1: Pro (MMR alto, Ping baixo)
    # Jogador 2: Noob (MMR baixo, Ping alto)
    # Jogador 3: Mid (MMR médio, Ping médio)
    players = [
        Player("Pro_Player", 2500, 15),
        Player("Noob_Player", 1000, 150),
        Player("Mid_Player", 1500, 50),
        Player("Average_1", 1520, 45),
        Player("Average_2", 1480, 55),
    ]

    for p in players:
        mm.add_player(p)
        print(f"Jogador {p.id} entrou na fila (MMR: {p.mmr}, Ping: {p.latency}ms)")

    print("\nSimulando ciclos de matchmaking...\n")
    
    for cycle in range(1, 6):
        print(f"Ciclo {cycle} (Tempo decorrido: {cycle}s)")
        # Simulamos o passar do tempo artificialmente para o experimento
        # Em um sistema real, o tempo passa naturalmente.
        # Aqui, vamos 'envelhecer' os jogadores na fila para testar o relaxamento.
        for p in mm.queue:
            p.entry_time -= cycle # Força o tempo de espera a aumentar

        matches = mm.attempt_match()
        
        if matches:
            for m in matches:
                p1, p2, m_gap, l_gap, w_time = m
                print(f"  [MATCH ENCONTRADO] {p1.id} <-> {p2.id}")
                print(f"    Qualidade: ΔMMR={m_gap:.1f}, ΔPing={l_gap:.1f}ms")
                print(f"    Tempo de espera do pioneiro: {w_time:.1f}s")
        else:
            print("  Nenhum match encontrado com os critérios atuais.")
        
        time.sleep(0.1)

if __name__ == "__main__":
    run_simulation()