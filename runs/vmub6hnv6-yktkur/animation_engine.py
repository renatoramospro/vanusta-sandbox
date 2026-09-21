import math

class Pose:
    """Representa a posição de um osso no espaço."""
    def __init__(self, position: float):
        self.position = position

    def __add__(self, other):
        return Pose(self.position + other.position)

    def __sub__(self, other):
        return Pose(self.position - other.position)

    def __mul__(self, scalar: float):
        return Pose(self.position * scalar)

    def __repr__(self):
        return f"Pos({self.position:.2f})"

def lerp(a: Pose, b: Pose, t: float) -> Pose:
    """Interpolação linear entre duas poses."""
    return (a * (1.0 - t)) + (b * t)

class AnimationState:
    def __init__(self, name: str, pose: Pose):
        self.name = name
        self.pose = pose

class AnimationController:
    def __init__(self):
        self.current_state = None
        self.previous_state = None
        self.transition_time = 0.0
        self.transition_duration = 0.0
        self.additive_layer = None
        self.additive_delta = Pose(0.0)

    def set_state(self, new_state: AnimationState, duration: float = 0.0):
        """Inicia uma transição (crossfade) para um novo estado."""
        if self.current_state is None:
            self.current_state = new_state
            self.previous_state = new_state
            return

        if duration > 0.0:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.transition_time = 0.0
            self.transition_duration = duration
        else:
            self.current_state = new_state
            self.previous_state = new_state
            self.transition_time = 0.0
            self.transition_duration = 0.0

    def update(self, dt: float):
        """Atualiza o tempo de transição da FSM."""
        if self.transition_time < self.transition_duration:
            self.transition_time += dt
            if self.transition_time > self.transition_duration:
                self.transition_time = self.transition_duration

    def set_additive_layer(self, layer_state: AnimationState, reference_pose: Pose):
        """Define uma camada aditiva calculando o delta em relação à pose de referência."""
        self.additive_layer = layer_state
        self.additive_delta = layer_state.pose - reference_pose

    def get_final_pose(self) -> Pose:
        """Calcula a pose final considerando o Crossfade da FSM e a Camada Aditiva."""
        # 1. Cálculo do Crossfade entre estado anterior e atual
        if self.transition_duration > 0.0 and self.transition_time < self.transition_duration:
            t = self.transition_time / self.transition_duration
            base_pose = lerp(self.previous_state.pose, self.current_state.pose, t)
        else:
            base_pose = self.current_state.pose if self.current_state else Pose(0.0)

        # 2. Aplicação da camada aditiva (Soma do Delta)
        if self.additive_layer is not None:
            final_pose = base_pose + self.additive_delta
        else:
            final_pose = base_pose

        return final_pose


def run_experiment():
    print("--- INICIANDO TESTE DE ARQUITETURA DE ANIMAÇÃO ---")

    # Definindo estados básicos
    idle = AnimationState("IDLE", Pose(0.0))
    walk = AnimationState("WALK", Pose(10.0))
    run = AnimationState("RUN", Pose(20.0))

    controller = AnimationController()
    controller.set_state(idle)

    print(f"Estado Inicial: {controller.get_final_pose()}")

    # [1] Testando Crossfade de IDLE (0.0) para WALK (10.0) com duração de 1.0s
    print("\n[1] Testando Crossfade: IDLE -> WALK (duração 1.0s)")
    controller.set_state(walk, duration=1.0)

    dt = 0.2
    # Simula 5 frames (1.0s total)
    for i in range(1, 6):
        controller.update(dt)
        pose = controller.get_final_pose()
        print(f"Tempo: {i * dt:.1f}s | Pose Base: {pose}")
        
        # Validação ajustada para cobrir a progressão exata do lerp (0.0 a 10.0)
        expected_min = (i * dt) * 10.0 - 0.001
        expected_max = (i * dt) * 10.0 + 0.001
        assert expected_min <= pose.position <= expected_max, f"Falha na interpolação no tempo {i*dt}s!"

    # [2] Testando Blending Aditivo (Ex: Caminhar + Acenar)
    print("\n[2] Testando Blending Aditivo (Camada de Aceno sobre WALK)")
    wave_anim = AnimationState("WAVE", Pose(15.0)) # Pose absoluta do aceno
    # A pose de referência para o aceno é o IDLE (0.0) ou a pose neutra
    controller.set_additive_layer(wave_anim, reference_pose=Pose(0.0))
    
    final_pose_additive = controller.get_final_pose()
    print(f"Pose Final com Aditivo: {final_pose_additive}")
    
    # O resultado esperado é a pose base atual (WALK = 10.0) + delta aditivo (15.0 - 0.0 = 15.0) = 25.0
    assert abs(final_pose_additive.position - 25.0) < 1e-5, "Blending aditivo incorreto!"

    # [3] Comparação com Override incorreto (Demonstração do equívoco comum)
    print("\n[3] Contraste com Override (Comportamento incorreto conceitualmente)")
    # No override puro, a camada de aceno substituiria o movimento, perdendo a base.
    # O sistema aditivo preserva porque soma o delta.
    print(f"Delta aditivo isolado somado à base: {controller.additive_delta}")

    print("\n[SUCESSO] Todos os testes passaram com sucesso!")

if __name__ == "__main__":
    run_experiment()