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
        # x, y representam o centro do retângulo, w (width) e h (height) a largura e altura totais
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
    def __init__(self, boundary: Rectangle, capacity: int = 4):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False

    def subdivide(self):
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h
        hw, hh = w / 2, h / 2
        
        # Quadrantes: Noroeste, Nordeste, Sudoeste, Sudeste
        self.nw = QuadTree(Rectangle(x - hw / 2, y + hh / 2, hw, hh), self.capacity)
        self.ne = QuadTree(Rectangle(x + hw / 2, y + hh / 2, hw, hh), self.capacity)
        self.sw = QuadTree(Rectangle(x - hw / 2, y - hh / 2, hw, hh), self.capacity)
        self.se = QuadTree(Rectangle(x + hw / 2, y - hh / 2, hw, hh), self.capacity)
        self.divided = True

    def insert(self, point: Point) -> bool:
        if not self.boundary.contains(point):
            return False

        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True

        if not self.divided:
            self.subdivide()

        if (self.nw.insert(point) or self.ne.insert(point) or
            self.sw.insert(point) or self.se.insert(point)):
            return True

        return False

    def query_range(self, range_rect: Rectangle, found=None):
        if found is None:
            found = []

        if not self.boundary.intersects(range_rect):
            return found

        for p in self.points:
            if range_rect.contains(p):
                found.append(p)

        if self.divided:
            self.nw.query_range(range_rect, found)
            self.ne.query_range(range_rect, found)
            self.sw.query_range(range_rect, found)
            self.se.query_range(range_rect, found)

        return found


# --- Bloco de Testes Automatizados e Validação ---
def run_tests():
    print("Iniciando testes da Quadtree...")
    
    # Configuração do domínio espacial: de 0 a 1000 em x e y
    boundary = Rectangle(500, 500, 1000, 1000)
    qt = QuadTree(boundary, capacity=4)

    # 1. Geração de 1500 pontos aleatórios determinísticos
    random.seed(42)
    num_points = 1500
    points = [Point(random.uniform(0, 1000), random.uniform(0, 1000)) for _ in range(num_points)]

    # Teste de Inserção Dinâmica
    start_time = time.time()
    for p in points:
        qt.insert(p)
    insertion_time = time.time() - start_time
    print(f"[Sucesso] {num_points} pontos inseridos dinamicamente em {insertion_time:.4f}s.")

    # 2. Teste de Consulta por Região (Range Query)
    # Definindo uma região de busca específica (ex: quadrado de 200x200 no centro)
    query_rect = Rectangle(500, 500, 200, 200)

    # Consulta via Quadtree
    start_time = time.time()
    qt_results = qt.query_range(query_rect)
    qt_time = time.time() - start_time

    # Consulta de referência (Busca Linear Brute-Force)
    start_time = time.time()
    linear_results = [p for p in points if query_rect.contains(p)]
    linear_time = time.time() - start_time

    print(f"[Resultado] Quadtree encontrou {len(qt_results)} pontos em {qt_time:.6f}s.")
    print(f"[Resultado] Busca linear encontrou {len(linear_results)} pontos em {linear_time:.6f}s.")

    # 3. Validação de Correção (Equivalência de resultados)
    qt_coords = sorted([(p.x, p.y) for p in qt_results])
    linear_coords = sorted([(p.x, p.y) for p in linear_results])
    
    assert qt_coords == linear_coords, "Erro: Os resultados da Quadtree diferem da busca linear!"
    print("[Validação] Os resultados da Quadtree coincidem 100% com a busca linear.")

    # 4. Demonstração de Tratamento de Equívoco Comum (Bounding Box vs Ponto isolado)
    # Tentativa de inserir ponto fora dos limites
    outside_point = Point(1500, 1500)
    inserted = qt.insert(outside_point)
    assert not inserted, "Erro: A Quadtree aceitou um ponto fora de seus limites geográficos!"
    print("[Validação] Bounding Box rejeitou corretamente pontos externos.")

if __name__ == "__main__":
    run_tests()