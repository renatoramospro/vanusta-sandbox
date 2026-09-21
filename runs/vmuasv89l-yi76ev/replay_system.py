import hashlib
import json
import random

class GameState:
    """Representa o estado crítico do jogo que deve ser idêntico no replay."""
    def __init__(self, player_pos, score, rng_seed):
        self.player_pos = player_pos  # [x, y]
        self.score = score
        self.rng_seed = rng_seed

    def compute_checksum(self):
        """Gera um hash único do estado para validação de desvio zero."""
        state_str = f"{self.player_pos}:{self.score}:{self.rng_seed}"
        return hashlib.sha256(state_str.encode()).hexdigest()

    def __repr__(self):
        return f"Pos: {self.player_pos}, Score: {self.score}"

class DeterministicEngine:
    def __init__(self, seed):
        self.seed = seed
        self.rng = random.Random(seed)
        self.player_pos = [0.0, 0.0]
        self.score = 0
        self.frame = 0
        self.dt = 0.016  # 60 FPS fixo

    def step(self, input_vector):
        """
        Processa um único frame de simulação.
        input_vector: [dx, dy]
        """
        # 1. Aplicar Input
        self.player_pos[0] += input_vector[0] * self.dt
        self.player_pos[1] += input_vector[1] * self.dt

        # 2. Lógica Determinística (ex: bônus aleatório baseado na semente)
        # Usamos o RNG interno para garantir que o 'aleatório' seja igual no replay
        if self.frame % 10 == 0:
            bonus = self.rng.randint(1, 10)
            self.score += bonus

        self.frame += 1

    def get_state(self):
        return GameState(list(self.player_pos), self.score, self.seed)

class ReplayRecorder:
    def __init__(self, seed):
        self.seed = seed
        self.inputs = [] # Lista de (frame, input_vector)

    def record(self, frame, input_vector):
        self.inputs.append((frame, input_vector))

    def save(self):
        return json.dumps({
            "seed": self.seed,
            "inputs": self.inputs
        })

class ReplayPlayer:
    def __init__(self, replay_data):
        data = json.loads(replay_data)
        self.seed = data["seed"]
        self.inputs_map = {f: vec for f, vec in data["inputs"]}

    def play(self, total_frames, speed_multiplier=1):
        engine = DeterministicEngine(self.seed)
        checksums = []

        # Simulação com aceleração
        # Para manter o determinismo, a aceleração pula frames de renderização,
        # mas processa TODOS os frames de simulação.
        for f in range(total_frames):
            input_vec = self.inputs_map.get(f, [0.0, 0.0])
            engine.step(input_vec)
            
            # Registra checksum a cada 10 frames para validação
            if f % 10 == 0:
                checksums.append(engine.get_state().compute_checksum())
        
        return engine.get_state(), checksums

def run_experiment():
    print("--- Iniciando Experimento de Replay Determinístico ---")
    
    # Configurações
    SEED = 42
    TOTAL_FRAMES = 100
    
    # 1. SIMULAÇÃO ORIGINAL (Gravação)
    print(f"[1] Executando Simulação Original (Seed: {SEED})...")
    original_engine = DeterministicEngine(SEED)
    recorder = ReplayRecorder(SEED)
    
    original_checksums = []
    
    for f in range(TOTAL_FRAMES):
        # Simula um input: movimento diagonal constante
        input_vec = [1.0, 0.5] 
        original_engine.step(input_vec)
        recorder.record(f, input_vec)
        
        if f % 10 == 0:
            original_checksums.append(original_engine.get_state().compute_checksum())

    final_state_orig = original_engine.get_state()
    print(f"Estado Final Original: {final_state_orig}")

    # 2. REPRODUÇÃO (Replay)
    print(f"\n[2] Iniciando Replay (Simulando aceleração 16x)...")
    replay_data = recorder.save()
    player = ReplayPlayer(replay_data)
    
    # O player executa a simulação. A aceleração de 16x em um motor real
    # significaria processar 16 frames de lógica para cada 1 frame de renderização.
    final_state_replay, replay_checksums = player.play(TOTAL_FRAMES)
    
    print(f"Estado Final Replay:    {final_state_replay}")

    # 3. VALIDAÇÃO (O critério de sucesso: Desvio Zero)
    print(f"\n[3] Validando Determinismo...")
    
    # Checksum do estado final
    match_final = final_state_orig.compute_checksum() == final_state_replay.compute_checksum()
    
    # Checksum da trajetória (todos os pontos intermediários)
    match_trajectory = original_checksums == replay_checksums
    
    # Tamanho do arquivo (Eficiência)
    file_size_kb = len(replay_data.encode()) / 1024

    print(f"Match Estado Final: {match_final}")
    print(f"Match Trajetória (Checksums): {match_trajectory}")
    print(f"Tamanho do Replay: {file_size_kb:.4f} KB")

    # Verificação de erro (Contraexemplo: Se mudarmos a semente no replay)
    print(f"\n[4] Testando Falha (Mudando semente no replay)...")
    corrupted_data = json.dumps({"seed": 99, "inputs": recorder.inputs})
    player_corrupted = ReplayPlayer(corrupted_data)
    state_corrupted, _ = player_corrupted.play(TOTAL_FRAMES)
    
    if state_corrupted.compute_checksum() != final_state_orig.compute_checksum():
        print("SUCESSO: O sistema detectou a corrupção (desvio de estado) corretamente.")
    else:
        print("FALHA: O sistema não detectou a mudança de semente!")

    # Assertions para o ambiente de teste
    assert match_final, "O estado final do replay deve ser idêntico ao original!"
    assert match_trajectory, "A trajetória do replay deve ser idêntica à original!"
    assert file_size_kb < 1.0, "O arquivo de replay deve ser extremamente pequeno."
    print("\n--- EXPERIMENTO CONCLUÍDO COM SUCESSO ---")

if __name__ == "__main__":
    run_experiment()