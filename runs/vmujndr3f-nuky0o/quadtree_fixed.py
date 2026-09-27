import random
import time

class Point:
    def __init__(self, x, y, data=None):
        self.x = x
        self.y = y
        self.data = data

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

class Rectangle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, point):
        return (self.x - self.w / 2 <= point.x <= self.x + self.w / 2 and
                self.y - self.h / 2 <= point.y <= self.y + self.h / 2)

    def intersects(self, range_rect):
        return not (range_rect.x - range_rect.w / 2 > self.x + self.w / 2 or
                    range_rect.x + range_rect.w / 2 < self.x - self.w / 2 or
                    range_rect.y - range_rect.h / 2 > self.y + self.h / 2 or
                    range_rect.y + range_rect.h / 2 < self.y - self.h / 2)

class QuadTree:
    def __init__(self, boundary: Rectangle, capacity: int = 4, depth: int = 0, max_depth: int = 20):
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.points = []
        self.divided = False
        
        # Filhos
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None

    def subdivide(self):
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h
        hw, hh = w / 2, h / 2
        
        # Quadrantes: Noroeste, Nordeste, Sudoeste, Sudeste
        self.nw = QuadTree(Rectangle(x - hw / 2, y + hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth)
        self.ne = QuadTree(Rectangle(x + hw / 2, y + hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth)
        self.sw = QuadTree(Rectangle(x - hw / 2, y - hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth)
        self.se = QuadTree(Rectangle(x + hw / 2, y - hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth)
        self.divided = True

    def insert(self, point: Point) -> bool:
        if not self.boundary.contains(point):
            return False

        # Se há espaço E (ainda não dividiu OU atingimos a profundidade máxima / limite de resolução geométrica)
        if len(self.points) < self.capacity and (not self.divided or self.depth >= self.max_depth or self.boundary.w < 1e-7):
            self.points.append(point)
            return True

        # Se atingiu a profundidade máxima ou limite de resolução, armazena no nó atual mesmo excedendo a capacidade
        if self.depth >= self.max_depth or self.boundary.w < 1e-7:
            self.points.append(point)
            return True

        if not self.divided:
            self.subdivide()

        if (self.nw.insert(point) or self.ne.insert(point) or
            self.sw.insert(point) or self.se.insert(point)):
            return True

        return False

    def query_range(self, range_rect: Rectangle, found_points: list):
        if not self.boundary.intersects(range_rect):
            return

        for p in self.points:
            if range_rect.contains(p):
                found_points.append(p)

        if self.divided:
            self.nw.query_range(range_rect, found_points)
            self.ne.query_range(range_rect, found_points)
            self.sw.query_range(range_rect, found_points)
            self.se.query_range(range_rect, found_points)

def run_tests():
    print("Iniciando testes robustos da Quadtree (com proteção contra pontos idênticos)...")

    # Espaço total de 0 a 1000 (centro em 500, 500)
    boundary = Rectangle(500, 500, 1000, 1000)
    qt = QuadTree(boundary, capacity=4, max_depth=10)

    # 1. Teste de pontos idênticos / colisão total (o cenário que falhou anteriormente)
    print("[Teste] Inserindo 100 pontos exatamente na mesma coordenada (500, 500)...")
    identical_point = Point(500, 500)
    for _ in range(100):
        assert qt.insert(Point(500, 500)), "Falha ao inserir ponto idêntico"
    
    print("[Sucesso] 100 pontos idênticos inseridos sem RecursionError!")

    # 2. Inserção de pontos normais variados
    random.seed(42)
    for i in range(1000):
        qt.insert(Point(random.uniform(0, 1000), random.uniform(0, 1000), data=i))

    # 3. Consulta na região central onde estão os pontos idênticos
    query_rect = Rectangle(500, 500, 50, 50)
    results = []
    qt.query_range(query_rect, results)
    
    # Verifica que os 100 pontos idênticos são retornados corretamente
    identical_found = sum(1 for p in results if p.x == 500 and p.y == 500)
    print(f"[Resultado] Encontrados {identical_found} pontos idênticos na consulta.")
    assert identical_found == 100, f"Esperado 100 pontos idênticos, encontrados {identical_found}"
    print("[Validação] Proteção contra recursão infinita e recuperação de pontos idênticos validada com sucesso.")

if __name__ == "__main__":
    run_tests()