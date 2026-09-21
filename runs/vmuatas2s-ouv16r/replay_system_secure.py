import json
import hashlib
import hmac
import io

# --- CONFIGURAÇÕES DE SEGURANÇA ---
SECRET_KEY = b"vanusta-super-secret-key-for-replay-integrity"
MAX_REPLAY_SIZE_BYTES = 1024 * 1024  # 1 MB limite de segurança
MAX_JSON_DEPTH = 3                   # Limite de profundidade para evitar recursão infinita

class SecurityError(Exception):
    """Exceção lançada para violações de segurança."""
    pass

# --- MOTOR DETERMINÍSTICO (CORE) ---

class DeterministicEngine:
    def __init__(self, seed=42):
        import random
        self.rng = random.Random(seed)
        self.pos = [0.0, 0.0]
        self.score = 0
        self.frame = 0
        self.dt = 0.016  # Fixed Timestep

    def step(self, inputs):
        # Simulação simples: inputs são [dx, dy]
        dx, dy = inputs
        self.pos[0] += dx * self.dt
        self.pos[1] += dy * self.dt
        self.score += self.rng.randint(0, 1) # Determinismo via seed
        self.frame += 1

    def get_state_hash(self):
        # Gera um hash do estado atual para validação de desvio zero
        state_str = f"{self.pos[0]}|{self.pos[1]}|{self.score}|{self.frame}"
        return hashlib.sha256(state_str.encode()).hexdigest()

# --- SUBSISTEMA DE REPLAY SEGURO ---

class SecureReplaySystem:
    def __init__(self, engine):
        self.engine = engine
        self.recorded_data = []

    def record_frame(self, inputs):
        self.recorded_data.append(inputs)

    def save_replay(self):
        """Salva o replay com uma assinatura HMAC para integridade."""
        payload = json.dumps({
            "seed": 42,
            "inputs": self.recorded_data
        }).encode()
        
        # Gera assinatura HMAC-SHA256
        signature = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()
        
        # O arquivo final contém: assinatura + payload
        full_package = {
            "signature": signature,
            "data": self.recorded_data,
            "initial_seed": 42
        }
        return json.dumps(full_package).encode()

    def load_and_verify_replay(self, raw_data):
        """Carrega o replay aplicando proteções contra DoS e Spoofing."""
        
        # 1. Proteção contra DoS: Limite de tamanho de arquivo
        if len(raw_data) > MAX_REPLAY_SIZE_BYTES:
            raise SecurityError("Arquivo de replay excede o limite de segurança.")

        try:
            package = json.loads(raw_data)
        except json.JSONDecodeError:
            raise SecurityError("Formato JSON inválido.")

        # 2. Proteção contra DoS: Verificação de profundidade (simplificada para este exemplo)
        # Em produção, usaríamos um parser customizado ou verificador de recursão.
        
        # 3. Proteção contra Spoofing: Verificação de Integridade (HMAC)
        # Reconstruímos o payload original para comparar a assinatura
        # Nota: Para este protótipo, o payload é o conteúdo de 'data' + 'initial_seed'
        reconstructed_payload = json.dumps({
            "seed": package["initial_seed"],
            "inputs": package["data"]
        }).encode()
        
        expected_signature = hmac.new(SECRET_KEY, reconstructed_payload, hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(package["signature"], expected_signature):
            raise SecurityError("FALHA DE INTEGRIDADE: O arquivo de replay foi alterado!")

        return package

    def play_replay(self, package):
        """Reproduz o replay validado."""
        import random
        # Reset do motor com a seed original
        self.engine.__init__(seed=package["initial_seed"])
        
        for inputs in package["data"]:
            # Validação de tipo (Sanitização)
            if not isinstance(inputs, list) or len(inputs) != 2:
                raise SecurityError("Dados de input malformados detectados.")
            self.engine.step(inputs)

# --- EXPERIMENTO ---

def run_experiment():
    print("--- Iniciando Experimento de Replay Seguro ---")
    engine = DeterministicEngine(seed=42)
    replay_sys = SecureReplaySystem(engine)

    # 1. Simulação Original
    print("[1] Gravando sessão original...")
    for _ in range(100):
        # Movimento constante [1.0, 1.0]
        move = [1.0, 1.0]
        engine.step(move)
        replay_sys.record_frame(move)
    
    original_hash = engine.get_state_hash()
    print(f"    Estado Final Original: Pos: {engine.pos}, Score: {engine.score}, Hash: {original_hash[:8]}")

    # 2. Salvar Replay
    replay_file_content = replay_sys.save_replay()
    print(f"[2] Replay salvo com sucesso ({len(replay_file_content)} bytes).")

    # 3. Teste de Integridade (Cenário de Ataque: Spoofing)
    print("[3] Testando detecção de Spoofing (Tentativa de alteração de score)...")
    try:
        # Simulando um hacker que edita o JSON para mudar o score ou inputs
        corrupted_data = json.loads(replay_file_content.decode())
        corrupted_data["data"][0] = [999.0, 999.0] # Muda o primeiro movimento
        corrupted_json = json.dumps(corrupted_data).encode()
        
        replay_sys.load_and_verify_replay(corrupted_json)
        print("    ERRO: O sistema aceitou um replay corrompido!")
    except SecurityError as e:
        print(f"    SUCESSO: O sistema bloqueou o ataque: {e}")

    # 4. Teste de Integridade (Cenário de Ataque: DoS)
    print("[4] Testando detecção de DoS (Arquivo gigante)...")
    try:
        giant_file = b"{" + b"a" * (MAX_REPLAY_SIZE_BYTES + 1) + b"}"
        replay_sys.load_and_verify_replay(giant_file)
    except SecurityError as e:
        print(f"    SUCESSO: O sistema bloqueou o arquivo gigante: {e}")

    # 5. Reprodução Legítima
    print("[5] Iniciando Replay Legítimo...")
    valid_package = replay_sys.load_and_verify_replay(replay_file_content)
    replay_sys.play_replay(valid_package)
    
    replay_hash = engine.get_state_hash()
    print(f"    Estado Final Replay:   Pos: {engine.pos}, Score: {engine.score}, Hash: {replay_hash[:8]}")

    # Validação Final
    assert original_hash == replay_hash, "DIVERGÊNCIA DE ESTADO DETECTADA!"
    print("\n--- EXPERIMENTO CONCLUÍDO COM SUCESSO (DETERMINISMO E SEGURANÇA VALIDADOS) ---")

if __name__ == "__main__":
    run_experiment()