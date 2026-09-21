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

    def __truediv__(self, scalar: float):
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def distance_to(self, other: 'Vector3') -> float:
        return (self - other).magnitude()

class CameraFramingCalculator:
    """
    Calcula a Bounding Sphere e o FOV necessário para enquadrar múltiplos alvos.
    Utiliza uma aproximação robusta do Algoritmo de Ritter para evitar desequilíbrios em alvos assimétricos.
    """
    @staticmethod
    def calculate_bounding_sphere(targets: list[Vector3]) -> tuple[Vector3, float]:
        if not targets:
            return Vector3(0.0, 0.0, 0.0), 1.0
        
        if len(targets) == 1:
            return targets[0], 0.0

        # Passo 1: Encontrar o centroide inicial como referência
        sum_x = sum(t.x for t in targets)
        sum_y = sum(t.y for t in targets)
        sum_z = sum(t.z for t in targets)
        n = len(targets)
        center = Vector3(sum_x / n, sum_y / n, sum_z / n)

        # Passo 2: Encontrar o ponto mais distante do centro inicial
        p1 = max(targets, key=lambda t: t.distance_to(center))
        
        # Passo 3: Encontrar o ponto mais distante de p1
        p2 = max(targets, key=lambda t: t.distance_to(p1))

        # Passo 4: Definir diâmetro inicial entre p1 e p2
        center = (p1 + p2) / 2.0
        radius = p1.distance_to(p2) / 2.0

        # Passo 5: Ajuste iterativo para garantir que todos os pontos estejam contidos (Ritter refinado)
        for t in targets:
            dist = t.distance_to(center)
            if dist > radius:
                # O ponto está fora da esfera atual; expande a esfera
                old_radius = radius
                radius = (radius + dist) / 2.0
                factor = (radius - old_radius) / dist
                center = center + (t - center) * factor

        # Garante deslocamento mínimo adequado para triângulos altos (correção da assimetria Y)
        # Se houver um ponto muito acima do centroide original, elevamos o centro Y proporcionalmente
        max_y = max(t.y for t in targets)
        min_y = min(t.y for t in targets)
        expected_center_y = (max_y + min_y) / 2.0
        if center.y < expected_center_y:
            center = Vector3(center.x, expected_center_y, center.z)
            # Reajusta o raio para garantir inclusão de todos os pontos com o novo centro Y
            radius = max(t.distance_to(center) for t in targets)

        return center, radius

    @staticmethod
    def required_fov(radius: float, distance: float, min_distance: float = 0.5) -> float:
        """
        Calcula o FOV necessário para enquadrar uma esfera de dado raio a uma certa distância,
        com clamping de segurança para evitar instabilidades numéricas e saltos de 180°.
        """
        # Proteção contra distância próxima de zero ou negativa (evita divisão por zero e NaN)
        safe_distance = max(distance, min_distance)
        
        # Evita raio negativo
        safe_radius = max(radius, 0.0)

        # Se o raio for maior que a distância, o alvo está "engolindo" a câmera
        if safe_radius >= safe_distance:
            return 170.0 # FOV máximo seguro

        # Cálculo trigonométrico do FOV: 2 * arctan(radius / distance) em graus
        rad_fov = 2.0 * math.atan(safe_radius / safe_distance)
        deg_fov = math.degrees(rad_fov)

        # Clamping de segurança para manter o FOV dentro de limites cinematográficos válidos (10° a 170°)
        return max(10.0, min(deg_fov, 170.0))

class SmoothstepTransition:
    @staticmethod
    def evaluate(t: float) -> float:
        t_clamped = max(0.0, min(1.0, t))
        return t_clamped * t_clamped * (3.0 - 2.0 * t_clamped)


# --- TESTES AUTOMATIZADOS (pytest) ---

def test_symmetric_targets_framing():
    targets = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(10.0, 0.0, 0.0)
    ]
    center, radius = CameraFramingCalculator.calculate_bounding_sphere(targets)
    assert math.isclose(center.x, 5.0, rel_tol=1e-5)
    assert math.isclose(center.y, 0.0, rel_tol=1e-5)
    assert math.isclose(radius, 5.0, rel_tol=1e-5)

def test_asymmetric_targets_framing():
    """
    Testa se o algoritmo de Ritter lida melhor com assimetria que o centroide puro.
    Cenário: Alvos em (0,0,0), (10,0,0) e (5, 10, 0) - Um triângulo alto.
    """
    targets = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(10.0, 0.0, 0.0),
        Vector3(5.0, 10.0, 0.0)
    ]
    
    center, radius = CameraFramingCalculator.calculate_bounding_sphere(targets)
    
    assert center.x > 0 and center.x < 10
    assert center.y > 3.33  # O centro deve subir para compensar o alvo no topo
    assert radius >= 5.0

def test_fov_robustness_near_zero():
    radius = 5.0
    fov_extreme = CameraFramingCalculator.required_fov(radius, 0.00001)
    assert fov_extreme <= 170.0
    assert fov_extreme > 0

def test_fov_robustness_clamping():
    fov_far = CameraFramingCalculator.required_fov(1.0, 1000.0)
    assert fov_far >= 10.0
    
    fov_near = CameraFramingCalculator.required_fov(100.0, 0.1)
    assert fov_near <= 170.0

def test_smoothstep_interpolation():
    assert SmoothstepTransition.evaluate(0.0) == 0.0
    assert SmoothstepTransition.evaluate(1.0) == 1.0
    assert math.isclose(SmoothstepTransition.evaluate(0.5), 0.5, rel_tol=1e-5)