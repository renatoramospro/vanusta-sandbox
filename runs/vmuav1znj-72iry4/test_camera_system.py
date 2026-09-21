import math

class Vector3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, scalar: float):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

class CameraFramingCalculator:
    # Constantes de segurança para robustez
    MIN_DISTANCE = 0.5
    MIN_FOV = 10.0
    MAX_FOV = 170.0

    @staticmethod
    def calculate_bounding_sphere(targets: list) -> tuple:
        """
        Calcula o centro (C) e o raio (R) usando uma aproximação de Ritter.
        Resolve o problema de assimetria do centroide.
        """
        if not targets:
            return Vector3(0, 0, 0), 0.0
        if len(targets) == 1:
            return targets[0], 0.0
        
        # Passo 1: Inicializa com o primeiro alvo
        center = targets[0]
        radius = 0.0
        
        # Passo 2: Expansão iterativa (Ritter simplificado)
        for t in targets:
            dist = (t - center).magnitude()
            if dist > radius:
                # O novo raio é a média entre o raio atual e a nova distância
                new_radius = (radius + dist) / 2.0
                # O novo centro se desloca para o ponto médio entre o centro antigo e o novo alvo
                # para manter a esfera cobrindo ambos
                weight = (dist - radius) / (2.0 * dist)
                center = center + (t - center) * weight
                radius = new_radius
                
        return center, radius

    @staticmethod
    def required_fov(radius: float, distance: float) -> float:
        """
        Calcula o FOV com clamping de distância e ângulo para evitar saltos de 180°.
        """
        # Robustez 1: Clamping de distância para evitar divisão por zero ou FOV infinito
        safe_distance = max(distance, CameraFramingCalculator.MIN_DISTANCE)
        
        # Cálculo trigonométrico
        rad = 2.0 * math.atan(radius / safe_distance)
        fov_deg = math.degrees(rad)
        
        # Robustez 2: Clamping de FOV para evitar efeitos de olho de peixe extremos
        return max(CameraFramingCalculator.MIN_FOV, 
                   min(CameraFramingCalculator.MAX_FOV, fov_deg))

class SmoothstepTransition:
    @staticmethod
    def evaluate(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

# --- TESTES AUTOMATIZADOS (Convenção Pytest) ---

def test_asymmetric_targets_framing():
    """
    Testa se o algoritmo de Ritter lida melhor com assimetria que o centroide.
    Cenário: Alvos em (0,0,0), (10,0,0) e (5, 10, 0) - Um triângulo alto.
    O centroide seria (5, 3.33, 0).
    """
    targets = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(10.0, 0.0, 0.0),
        Vector3(5.0, 10.0, 0.0)
    ]
    
    center, radius = CameraFramingCalculator.calculate_bounding_sphere(targets)
    
    # Com o centroide (5, 3.33), a distância ao alvo (5, 10) seria 6.67.
    # Com Ritter, o centro deve ser mais equilibrado verticalmente.
    # Verificamos se o centro está em uma posição razoável para enquadramento.
    assert center.x > 0 and center.x < 10
    assert center.y > 3.33  # O centro deve subir para compensar o alvo no topo
    assert radius >= 5.0    # O raio deve cobrir pelo menos a metade da base

def test_fov_robustness_near_zero():
    """
    Testa se o FOV é protegido contra distâncias próximas de zero (evita salto de 180°).
    """
    radius = 5.0
    # Distância quase zero
    fov_extreme = CameraFramingCalculator.required_fov(radius, 0.00001)
    
    # O FOV não deve ser 180°, deve ser limitado pelo MAX_FOV (170°)
    assert fov_extreme <= 170.0
    assert fov_extreme > 0

def test_fov_robustness_clamping():
    """
    Testa se o FOV respeita os limites mínimos e máximos.
    """
    # Caso de distância muito grande (FOV deve ser mínimo)
    fov_far = CameraFramingCalculator.required_fov(1.0, 1000.0)
    assert fov_far >= 10.0
    
    # Caso de distância muito pequena (FOV deve ser máximo)
    fov_near = CameraFramingCalculator.required_fov(100.0, 0.1)
    assert fov_near <= 170.0

def test_smoothstep_interpolation():
    assert SmoothstepTransition.evaluate(0.0) == 0.0
    assert SmoothstepTransition.evaluate(1.0) == 1.0
    assert math.isclose(SmoothstepTransition.evaluate(0.5), 0.5, rel_tol=1e-5)