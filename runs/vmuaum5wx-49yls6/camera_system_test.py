import math

class Vector3:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

class Interpolator:
    @staticmethod
    def linear(t): return t
    @staticmethod
    def smoothstep(t): return 3 * t**2 - 2 * t**3

class CameraSystem:
    def __init__(self):
        self.position = Vector3(0, 0, -10)
        self.fov = 60.0
        self.targets = []

    def add_targets(self, targets):
        self.targets = targets

    def calculate_framing(self, camera_dist):
        if not self.targets: return
        
        # 1. Calcular Centro (C)
        avg_x = sum(t.x for t in self.targets) / len(self.targets)
        avg_y = sum(t.y for t in self.targets) / len(self.targets)
        avg_z = sum(t.z for t in self.targets) / len(self.targets)
        center = Vector3(avg_x, avg_y, avg_z)

        # 2. Calcular Raio (R)
        max_dist = 0
        for t in self.targets:
            dist = (t - center).magnitude()
            if dist > max_dist: max_dist = dist
        
        # 3. Calcular FOV necessário para a distância D
        # FOV = 2 * atan(R / D)
        required_fov = 2 * math.degrees(math.atan2(max_dist, camera_dist))
        return center, max_dist, required_fov

def run_experiment():
    print("--- INICIANDO EXPERIMENTO DE CÂMERA ---")
    
    # Cenário: Dois alvos distantes
    target1 = Vector3(0, 0, 0)
    target2 = Vector3(10, 0, 0)
    targets = [target1, target2]
    
    cam = CameraSystem()
    cam.add_targets(targets)
    
    # Teste 1: Enquadramento Matemático
    dist_camera = 10.0
    center, radius, fov = cam.calculate_framing(dist_camera)
    
    print(f"[TESTE 1] Alvos: {targets}")
    print(f"          Centro Calculado: {center}")
    print(f"          Raio da Bounding Sphere: {radius:.2f}")
    print(f"          FOV Necessário para Dist {dist_camera}: {fov:.2f}°")
    
    assert math.isclose(radius, 5.0), "Raio incorreto!"
    assert math.isclose(fov, 2 * math.degrees(math.atan2(5, 10)), rel_tol=1e-5), "FOV incorreto!"
    print("          RESULTADO: Enquadramento OK.\n")

    # Teste 2: Transição (Snap vs Smoothstep)
    # Simulando transição de posição de 0.0 para 10.0
    start_pos = 0.0
    end_pos = 10.0
    steps = 5
    
    print("[TESTE 2] Comparação de Transição (0.0 -> 10.0):")
    print(f"{'Passo':<6} | {'Snap (Errado)':<15} | {'Smoothstep (Correto)':<20}")
    print("-" * 50)
    
    for i in range(steps + 1):
        t = i / steps
        snap_val = start_pos + (end_pos - start_pos) * t # Simulação de erro de lógica ou linear simples
        # No snap real, o valor pularia, aqui simulamos a progressão linear para comparar a curva
        
        smooth_val = start_pos + (end_pos - start_pos) * Interpolator.smoothstep(t)
        
        print(f"{i:<6} | {snap_val:<15.2f} | {smooth_val:<20.2f}")

    print("\n[CONCLUSÃO] O Smoothstep apresenta aceleração e desaceleração suaves,")
    print("evitando o impacto visual de mudanças bruscas de velocidade.")

if __name__ == "__main__":
    run_experiment()