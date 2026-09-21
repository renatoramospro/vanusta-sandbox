import math

class Vector3:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

class CameraFramingCalculator:
    @staticmethod
    def calculate_bounding_sphere(targets: list) -> tuple:
        """Calcula o centro (C) e o raio (R) da Bounding Sphere para N alvos."""
        if not targets:
            return Vector3(0, 0, 0), 0.0
        
        sum_x = sum(t.x for t in targets)
        sum_y = sum(t.y for t in targets)
        sum_z = sum(t.z for t in targets)
        n = len(targets)
        
        center = Vector3(sum_x / n, sum_y / n, sum_z / n)
        
        max_dist = 0.0
        for t in targets:
            dist = (t - center).magnitude()
            if dist > max_dist:
                max_dist = dist
                
        return center, max_dist

    @staticmethod
    def required_fov(radius: float, distance: float) -> float:
        """Calcula o FOV vertical necessário em graus para enquadrar o raio a uma distância D."""
        if distance <= 0:
            return 0.0
        rad = 2.0 * math.atan(radius / distance)
        return math.degrees(rad)

class SmoothstepTransition:
    @staticmethod
    def evaluate(t: float) -> float:
        """Função Smoothstep: 3t^2 - 2t^3 para t em [0, 1]."""
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

# --- TESTES AUTOMATIZADOS (Convenção Pytest) ---

def test_bounding_sphere_framing():
    # Cenário com múltiplos alvos no espaço 3D
    targets = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(10.0, 0.0, 0.0),
        Vector3(5.0, 0.0, 0.0)
    ]
    center, radius = CameraFramingCalculator.calculate_bounding_sphere(targets)
    
    # O centro deve ser (5.0, 0.0, 0.0) e o raio deve ser 5.0
    assert math.isclose(center.x, 5.0, rel_tol=1e-5)
    assert math.isclose(center.y, 0.0, rel_tol=1e-5)
    assert math.isclose(radius, 5.0, rel_tol=1e-5)
    
    # Validação do FOV necessário para distância 10.0
    fov = CameraFramingCalculator.required_fov(radius, 10.0)
    expected_fov = 2.0 * math.degrees(math.atan(5.0 / 10.0))
    assert math.isclose(fov, expected_fov, rel_tol=1e-5)

def test_smoothstep_interpolation():
    # Verifica os limites da curva
    assert SmoothstepTransition.evaluate(0.0) == 0.0
    assert SmoothstepTransition.evaluate(1.0) == 1.0
    
    # Verifica o comportamento de aceleração/desaceleração no meio (t = 0.5)
    # 0.5 * 0.5 * (3 - 2 * 0.5) = 0.25 * 2.0 = 0.5 (simetria exata)
    assert math.isclose(SmoothstepTransition.evaluate(0.5), 0.5, rel_tol=1e-5)

    # Garante que a transição é mais suave que a linear nos extremos
    linear_mid = 0.2
    smooth_mid = SmoothstepTransition.evaluate(0.2)
    # O smoothstep inova por ter derivada zero nas pontas (início e fim mais suaves)
    assert smooth_mid < linear_mid