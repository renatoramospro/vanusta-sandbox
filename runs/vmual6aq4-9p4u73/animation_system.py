import math

class Transform:
    def __init__(self, x=0.0, y=0.0, rotation=0.0):
        self.x = x
        self.y = y
        self.rotation = rotation

    def interpolate(self, other, t):
        # Interpolação linear para posição e rotação
        nx = self.x + (other.x - self.x) * t
        ny = self.y + (other.y - self.y) * t
        nrot = self.rotation + (other.rotation - self.rotation) * t
        return Transform(nx, ny, nrot)

    def add_additive(self, other, weight=1.0):
        return Transform(
            self.x + other.x * weight,
            self.y + other.y * weight,
            self.rotation + other.rotation * weight
        )

    def __repr__(self):
        return f"Pos({self.x:.1f}, {self.y:.1f}, Rot({self.rotation:.1f}°))"

class Pose:
    def __init__(self, bones=None):
        self.bones = bones if bones else {}

    def blend(self, other, weight, mask=None):
        new_bones = {}
        # Se não houver máscara, aplica em todos os ossos (Override)
        # Se houver máscara, aplica apenas nos ossos presentes na máscara
        target_bones = mask if mask is not None else self.bones.keys()
        
        # Começamos com a pose base
        for bone_name, transform in self.bones.items():
            if bone_name in target_bones and bone_name in other.bones:
                # Blend entre base e outro
                new_bones[bone_name] = transform.interpolate(other.bones[bone_name], weight)
            else:
                # Mantém a base
                new_bones[bone_name] = transform
        return Pose(new_bones)

    def add_additive(self, additive_pose, weight):
        new_bones = {}
        for bone_name, transform in self.bones.items():
            if bone_name in additive_pose.bones:
                new_bones[bone_name] = transform.add_additive(additive_pose.bones[bone_name], weight)
            else:
                new_bones[bone_name] = transform
        return Pose(new_bones)

class State:
    def __init__(self, name, pose):
        self.name = name
        self.pose = pose

class FSM:
    def __init__(self, initial_state):
        self.current_state = initial_state
        self.previous_state = None
        self.transition_time = 0.0
        self.transition_duration = 0.0
        self.is_transitioning = False

    def transition_to(self, next_state, duration):
        # CORREÇÃO: Se já estiver em transição, o "current_state" (que é uma pose interpolada)
        # deve ser tratado como o novo ponto de partida para evitar o POP.
        # No nosso modelo simplificado, para capturar a pose exata do frame,
        # o 'previous_state' passa a ser uma pose estática que representa o estado atual.
        
        if self.is_transitioning:
            # Captura a pose exata de onde estamos agora para iniciar a nova transição
            # Isso evita o salto visual (popping)
            current_pose_snapshot = self.get_current_pose()
            self.previous_state = State("Snapshot", current_pose_snapshot)
        else:
            self.previous_state = self.current_state

        self.current_state = next_state
        self.transition_duration = duration
        self.transition_time = 0.0
        self.is_transitioning = True if duration > 0 else False

    def get_current_pose(self):
        if not self.is_transitioning:
            return self.current_state.pose
        
        t = self.transition_time / self.transition_duration
        return self.previous_state.pose.blend(self.current_state.pose, t)

    def update(self, dt):
        if self.is_transitioning:
            self.transition_time += dt
            if self.transition_time >= self.transition_duration:
                self.transition_time = self.transition_duration
                self.is_transitioning = False

class AnimationManager:
    def __init__(self, base_fsm):
        self.base_fsm = base_fsm
        self.upper_layer = {"active": False, "pose": None, "weight": 0.0, "mask": None}
        self.additive_layer = {"active": False, "pose": None, "weight": 0.0}

    def set_upper_body(self, pose, weight, mask):
        self.upper_layer = {"active": True, "pose": pose, "weight": weight, "mask": mask}

    def set_additive(self, pose, weight):
        self.additive_layer = {"active": True, "pose": pose, "weight": weight}

    def evaluate(self, dt):
        self.base_fsm.update(dt)
        pose = self.base_fsm.get_current_pose()

        # 1. Camada de Upper Body (Masked Blend)
        if self.upper_layer["active"]:
            pose = pose.blend(self.upper_layer["pose"], self.upper_layer["weight"], self.upper_layer["mask"])

        # 2. Camada Aditiva (Additive Blend)
        if self.additive_layer["active"]:
            pose = pose.add_additive(self.additive_layer["pose"], self.additive_layer["weight"])
        
        return pose

# --- TESTES ---

def test_interrupted_crossfade():
    print("--- Iniciando Teste: Interrupted Crossfade (Prevenção de Popping) ---")
    
    idle_pose = Pose({"spine": Transform(0, 0, 0), "arm": Transform(0, 0, 0)})
    walk_pose = Pose({"spine": Transform(0, 5, 0), "arm": Transform(0, 0, 10)})
    run_pose = Pose({"spine": Transform(0, 10, 0), "arm": Transform(0, 0, 30)})

    fsm = FSM(State("Idle", idle_pose))
    manager = AnimationManager(fsm)

    # 1. Inicia transição Idle -> Walk (Duração 1.0s)
    fsm.transition_to(State("Walk", walk_pose), duration=1.0)
    
    # 2. Avança o tempo para o meio da transição (0.5s)
    # A pose deveria estar em 50% entre Idle e Walk
    manager.evaluate(0.5)
    mid_pose = manager.evaluate(0.0)
    print(f"Pose no meio da transição (50%): {mid_pose.bones['spine']}")
    
    # Verificação: Spine Y deve ser ~2.5 (metade de 5)
    assert 2.4 <= mid_pose.bones['spine'].y <= 2.6, f"Erro: Pose esperada ~2.5, obtida {mid_pose.bones['spine'].y}"

    # 3. INTERRUPÇÃO: No meio da transição, iniciamos uma nova transição para Run
    print("Interrompendo transição para 'Run' no meio do caminho...")
    fsm.transition_to(State("Run", run_pose), duration=1.0)

    # 4. Se o sistema for CORRETO, a nova transição começa da pose atual (2.5) e vai para a Run (10)
    # Se o sistema for ERRADO (Popping), a nova transição começaria do Walk (5.0) direto, causando um salto de 2.5 para 5.0.
    
    manager.evaluate(0.1) # Pequeno passo para processar o início
    new_mid_pose = manager.evaluate(0.4) # Mais 0.4s (total 0.5s da nova transição)
    
    # Cálculo esperado:
    # Ponto de partida (Snapshot): 2.5
    # Destino (Run): 10.0
    # Progresso: 0.5 / 1.0 = 50%
    # Valor esperado: 2.5 + (10.0 - 2.5) * 0.5 = 2.5 + 3.75 = 6.25
    
    print(f"Pose após interrupção (50% da nova transição): {new_mid_pose.bones['spine']}")
    
    # Verificação de continuidade
    assert 6.1 <= new_mid_pose.bones['spine'].y <= 6.4, f"ERRO DE POPPING! Pose esperada ~6.25, obtida {new_mid_pose.bones['spine'].y}"
    print("Sucesso: A transição foi suave! O sistema usou a pose atual como ponto de partida.")

def test_three_layers_composition():
    print("\n--- Iniciando Teste: Composição de 3 Camadas ---")
    base = Pose({"spine": Transform(0,0,0), "arm": Transform(0,0,0)})
    upper = Pose({"arm": Transform(0,0,45)}) # Braço levantado
    additive = Pose({"spine": Transform(0,2,0)}) # Coluna inclinada

    fsm = FSM(State("Base", base))
    manager = AnimationManager(fsm)
    
    # Camada 1: Base (Idle)
    # Camada 2: Upper Body (Braço em 45°) com máscara apenas no braço
    manager.set_upper_body(upper, weight=1.0, mask={"arm": Transform(0,0,0)})
    # Camada 3: Additive (Spine +2)
    manager.set_additive(additive, weight=0.5)

    final_pose = manager.evaluate(0.016)
    
    print(f"Pose Final - Spine: {final_pose.bones['spine']}")
    print(f"Pose Final - Arm: {final_pose.bones['arm']}")

    # Verificações
    assert final_pose.bones['arm'].rotation == 45.0, "Camada Upper Body falhou."
    assert final_pose.bones['spine'].y == 1.0, "Camada Additive falhou (0 + 2 * 0.5)."
    assert final_pose.bones['spine'].x == 0.0, "Camada Base deve ser preservada."
    print("Sucesso: 3 camadas compostas corretamente.")

if __name__ == "__main__":
    test_interrupted_crossfade()
    test_three_layers_composition()
    print("\n=== TODOS OS TESTES PASSARAM ===")