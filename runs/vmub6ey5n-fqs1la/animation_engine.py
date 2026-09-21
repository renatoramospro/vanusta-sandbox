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
        """Inicia uma transição para um novo estado."""
        if self.current_state == new_state:
            return
        
        if duration > 0:
            self.previous_state = self.current_state
            self.transition_time = 0.0
            self.transition_duration = duration
        else:
            self.previous_state = None
            
        self.current_state = new_state

    def set_additive_layer(self, anim_pose: Pose, ref_pose: Pose):
        """Calcula o delta para uma camada aditiva."""
        self.additive_layer = anim_pose
        self.additive_delta = anim_pose - ref_pose

    def update(self, dt: float):
        """Atualiza o progresso da transição."""
        if self.previous_state and self.transition_time < self.transition_duration:
            self.transition_time += dt
            if self.transition_time >= self.transition_duration:
                self.transition_time = self.transition_duration
                self.previous_state = None

    def get_base_pose(self) -> Pose:
        """Calcula a pose base considerando o crossfade da FSM."""
        if not self.current_state:
            return Pose(0.0)
        
        if self.previous_state and self.transition_duration > 0:
            t = self.transition_time / self.transition_duration
            return lerp(self.previous_state.pose, self.current_state.pose, t)
        
        return self.current_state.pose

    def get_final_pose(self, mode="additive") -> Pose:
        """Aplica as camadas sobre a pose base."""
        base = self.get_base_pose()
        
        if mode == "additive" and self.additive_layer:
            # A lógica correta: Base + Delta
            return base + self.additive_delta
        elif mode == "override" and self.additive_layer:
            # O erro comum: Misturar poses como se fossem estados da FSM
            # Isso faz a base 'sumir' parcialmente
            return lerp(base, self.additive_layer, 0.5)
        
        return base

def run_experiment():
    print("--- INICIANDO TESTE DE ARQUITETURA DE ANIMAÇÃO ---")
    
    # 1. Setup de Estados
    idle = AnimationState("IDLE", Pose(0.0))
    walk = AnimationState("WALK", Pose(10.0))
    run = AnimationState("RUN", Pose(20.0))
    
    controller = AnimationController()
    controller.set_state(idle)
    
    # 2. Teste de Transição Suave (Crossfade)
    print("\n[1] Testando Crossfade: IDLE -> WALK (duração 1.0s)")
    controller.set_state(walk, duration=1.0)
    
    # Simulando frames
    for i in range(6):
        dt = 0.2
        controller.update(dt)
        pose = controller.get_base_pose()
        print(f"Tempo: {controller.transition_time:.1f}s | Pose Base: {pose}")
        # Verificação de expectativa: no meio da transição (0.5s), a pose deve ser 5.0
        if i == 2: # t = 0.4s aprox
            assert 4.0 <= pose.position <= 6.0, "Transição não está sendo interpolada!"

    # 3. Teste de Camada Aditiva vs Override
    print("\n[2] Testando Camada Aditiva (WAVE)")
    # A animação de acenar (WAVE) tem posição 5, mas sua referência (braço parado) é 0.
    # Logo, o DELTA é +5.
    wave_pose = Pose(5.0)
    wave_ref = Pose(0.0)
    controller.set_additive_layer(wave_pose, wave_ref)
    
    # A base agora é WALK (10.0)
    base_pose = controller.get_base_pose()
    print(f"Pose Base Atual (WALK): {base_pose}")
    
    additive_result = controller.get_final_pose(mode="additive")
    print(f"Resultado com Blending ADITIVO (Base + Delta): {additive_result}")
    print(f"Resultado com Blending OVERRIDE (Erro comum): {controller.get_final_pose(mode='override')}")

    # Validação Matemática
    # Esperado: 10 (base) + 5 (delta) = 15
    assert math.isclose(additive_result.position, 15.0), f"Erro Aditivo! Esperado 15, obtido {additive_result.position}"
    # O override falha porque ele tenta fazer a média entre 10 e 5, resultando em 7.5
    assert not math.isclose(controller.get_final_pose(mode="override").position, 15.0), "Override não deveria resultar em 15"

    print("\n[RESULTADO] Todos os testes passaram com sucesso!")

if __name__ == "__main__":
    run_experiment()