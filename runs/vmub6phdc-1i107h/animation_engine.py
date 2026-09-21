import math

class Transform:
    """Representa a transformação de um osso (Rotação em radianos e Translação)."""
    def __init__(self, rotation: float, translation: float):
        self.rotation = rotation         # Rotação (onde o aditivo é matematicamente seguro)
        self.translation = translation   # Translação (onde aditivo direto causa deslocamento indesejado)

    def __add__(self, other):
        # NOTA ARQUITETURAL: Rotações usam soma aditiva de deltas. 
        # Translações em aditivo exigem cuidado extremo para evitar "drift" espacial.
        return Transform(
            self.rotation + other.rotation,
            self.translation + other.translation
        )

    def __sub__(self, other):
        return Transform(
            self.rotation - other.rotation,
            self.translation - other.translation
        )

    def __mul__(self, scalar: float):
        return Transform(
            self.rotation * scalar,
            self.translation * scalar
        )

    def __repr__(self):
        return f"Rot({self.rotation:.2f}rad), Trans({self.translation:.2f})"

def lerp_transform(a: Transform, b: Transform, t: float) -> Transform:
    """Interpolação linear segura para pesos normalizados de crossfade."""
    return (a * (1.0 - t)) + (b * t)

class AnimationState:
    def __init__(self, name: str, transform: Transform):
        self.name = name
        self.transform = transform

class RobustAnimationController:
    """
    Controlador de Animação com suporte a FSM, Crossfade interrompível 
    e Blending Aditivo seguro (separando rotação de translação).
    """
    def __init__(self):
        self.current_state = None
        self.previous_state = None
        
        # Controle de tempo do Crossfade
        self.transition_time = 0.0
        self.transition_duration = 0.0
        
        # Camada Aditiva
        self.additive_layer = None
        self.additive_reference = Transform(0.0, 0.0)

    def set_state(self, new_state: AnimationState, duration: float =.0):
        """
        Define um novo estado, suportando a interrupção de transições em curso
        (Crossfade de um Crossfade) sem saltos visuais.
        """
        current_pose = self.get_base_pose()

        if self.current_state is None:
            self.current_state = new_state
            self.previous_state = new_state
            return

        if duration > 0.0:
            # CORREÇÃO ARQUITETURAL: Captura a pose exata no momento da interrupção
            # para evitar o salto visual que ocorreria se resetássemos a base.
            self.previous_state = AnimationState("InterruptedPose", current_pose)
            self.current_state = new_state
            self.transition_time = 0.0
            self.transition_duration = duration
        else:
            self.current_state = new_state
            self.previous_state = new_state
            self.transition_time = 0.0
            self.transition_duration = 0.0

    def update(self, dt: float):
        """Avança o tempo da transição da FSM."""
        if self.transition_time < self.transition_duration:
            self.transition_time += dt
            if self.transition_time > self.transition_duration:
                self.transition_time = self.transition_duration

    def get_base_pose(self) -> Transform:
        """Calcula a pose base interpolada entre o estado anterior e o atual (Crossfade)."""
        if self.previous_state is None or self.current_state is None:
            return Transform(0.0, 0.0)

        if self.transition_duration <= 0.0 or self.transition_time >= self.transition_duration:
            return self.current_state.transform

        t = self.transition_time / self.transition_duration
        # Garante pesos normalizados (t entre 0 e 1)
        t = max(0.0, min(1.0, t))
        return lerp_transform(self.previous_state.transform, self.current_state.transform, t)

    def set_additive_layer(self, state: AnimationState, reference_pose: Transform):
        """Define a camada aditiva e sua pose de referência (restrita a rotações)."""
        self.additive_layer = state
        self.additive_reference = reference_pose

    def get_final_pose(self) -> Transform:
        """
        Combina a camada base (FSM/Crossfade) com a camada aditiva.
        NOTA DE SEGURANÇA: O delta aditivo é aplicado principalmente nas ROTAÇÕES.
        Em translações, somar aditivamente o espaço absoluto causa 'drift' espacial.
        """
        base_pose = self.get_base_pose()

        if self.additive_layer is not None:
            # Calcula o delta apenas do que é seguro (ex: rotações)
            # Evita o erro conceitual de somar translações absolutas aditivamente
            delta_rotation = self.additive_layer.transform.rotation - self.additive_reference.rotation
            
            # A translação base é mantida, aplicando o delta aditivo na rotação
            safe_rotation = base_pose.rotation + delta_rotation
            return Transform(safe_rotation, base_pose.translation)

        return base_pose

def run_experiment():
    print("--- INICIANDO TESTE AVANÇADO DE ARQUITETURA DE ANIMAÇÃO ---")
    
    controller = RobustAnimationController()
    
    idle = AnimationState("IDLE", Transform(0.0, 0.0))
    walk = AnimationState("WALK", Transform(1.57, 10.0)) # 1.57 rad (~90 graus), 10m de translação
    run = AnimationState("RUN", Transform(3.14, 20.0))   # 3.14 rad (~180 graus), 20m de translação

    # 1. Estado inicial
    controller.set_state(idle)
    print(f"Estado Inicial: {controller.get_final_pose()}")

    # 2. Testando Crossfade normal: IDLE -> WALK (duração 1.0s)
    print("\n[1] Iniciando Crossfade: IDLE -> WALK (1.0s)")
    controller.set_state(walk, duration=1.0)
    
    dt = 0.5
    controller.update(dt)
    pose_mid = controller.get_final_pose()
    print(f"Tempo: {dt}s | Pose Base Intermediária: {pose_mid}")
    # No tempo 0.5 (metade de 1.0), a rotação esperada é 1.57 / 2 = 0.785
    assert abs(pose_mid.rotation - 0.785) < 1e-3, "Crossfade de rotação incorreto!"

    # 3. Testando Interrupção de Transição (Crossfade de um Crossfade) no meio do caminho
    print("\n[2] Interrompendo transição em curso para RUN (duração 1.0s) no t=0.5s")
    # O jogador decide correr antes de terminar de andar. O sistema deve capturar 
    # a pose atual (0.785) como nova origem, evitando saltos visuais.
    controller.set_state(run, duration=1.0)
    
    # Atualiza mais 0.5s da nova transição (InterruptedPose -> RUN)
    controller.update(0.5)
    pose_interrupted = controller.get_final_pose()
    print(f"Tempo após interrupção: 0.5s | Pose: {pose_interrupted}")
    # A nova transição parte de ~0.785 rumo a 3.14. No tempo 0.5, deve estar na média entre ambos.
    expected_val = (0.785 + 3.14) / 2.0
    assert abs(pose_interrupted.rotation - expected_val) < 1e-3, "Falha na interrupção sem saltos visuais!"

    # 4. Testando Blending Aditivo Seguro (Restrito a Rotações)
    print("\n[3] Testando Blending Aditivo Seguro (Camada de Aceno sobre Rotação)")
    aim_state = AnimationState("AIM", Transform(0.5, 0.0)) # Apenas rotação de mira
    # Referência de repouso para a mira é 0.0
    controller.set_additive_layer(aim_state, reference_pose=Transform(0.0, 0.0))
    
    final_pose = controller.get_final_pose()
    print(f"Pose Final com Aditivo de Rotação: {final_pose}")
    
    # O teste valida que o delta aditivo (0.5 - 0.0 = 0.5) foi somado à rotação atual 
    # sem corromper a translação ou causar drift espacial.
    expected_rotation_with_additive = pose_interrupted.rotation + 0.5
    assert abs(final_pose.rotation - expected_rotation_with_additive) < 1e-3, "Blending aditivo de rotação incorreto!"
    assert final_pose.translation == pose_interrupted.translation, "Translação não deve sofrer blending aditivo direto!"

    print("\n[SUCESSO] Todos os testes avançados de arquitetura passaram!")

if __name__ == "__main__":
    run_experiment()