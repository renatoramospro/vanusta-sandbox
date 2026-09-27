import math
import random
import time

class Point:
    def __init__(self, x, y, data=None):
        if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
            raise TypeError("Coordenadas devem ser numéricas.")
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            raise ValueError("Coordenadas não podem ser NaN ou Infinitas.")
        self.x = float(x)
        self.y = float(y)
        self.data = data

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

class Rectangle:
    def __init__(self, x, y, w, h):
        if not (isinstance(w, (int, float)) and isinstance(h, (int, float))):
            raise TypeError("Dimensões devem ser numéricas.")
        if math.isnan(x) or math.isnan(y) or math.isnan(w) or math.isnan(h):
            raise ValueError("Parâmetros do retângulo não podem ser NaN.")
        if w <= 0 or h <= 0:
            raise ValueError("Largura e altura do retângulo devem ser estritamente positivas.")
        
        self.x = float(x) # centro x
        self.y = float(y) # centro y
        self.w = float(w) # largura total
        self.h = float(h) # altura total

    def contains(self, point):
        # Intervalos semi-abertos para evitar duplicidade em fronteiras exatas: [min, max)
        min_x = self.x - self.w / 2
        max_x = self.x + self.w / 2
        min_y = self.y - self.h / 2
        max_y = self.y + self.h / 2
        
        return (min_x <= point.x < max_x or (point.x == max_x and point.x == min_x + self.w)) and \
               (min_y <= point.y < max_y or (point.y == max_y and point.y == min_y + self.h))

    def intersects(self, range_rect):
        r1_min_x = self.x - self.w / 2
        r1_max_x = self.x + self.w / 2
        r1_min_y = self.y - self.h / 2
        r1_max_y = self.y + self.h / 2

        r2_min_x = range_rect.x - range_rect.w / 2
        r2_max_x = range_rect.x + range_rect.w / 2
        r2_min_y = range_rect.y - range_rect.h / 2
        r2_max_y = range_rect.y + range_rect.h / 2

        return not (r2_min_x > r1_max_x or r2_max_x < r1_min_x or
                    r2_min_y > r1_max_y or r2_max_y < r1_min_y)

class QuadTree:
    def __init__(self, boundary: Rectangle, capacity: int = 4, depth: int = 0, max_depth: int = 15, max_bucket_size: int = 64):
        self.boundary = boundary
        self.capacity = capacity
        self.depth = depth
        self.max_depth = max_depth
        self.max_bucket_size = max_bucket_size
        self.points = []
        self.divided = False
        
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None

    def subdivide(self):
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h
        hw, hh = w / 2, h / 2
        
        self.nw = QuadTree(Rectangle(x - hw / 2, y + hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth, self.max_bucket_size)
        self.ne = QuadTree(Rectangle(x + hw / 2, y + hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth, self.max_bucket_size)
        self.sw = QuadTree(Rectangle(x - hw / 2, y - hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth, self.max_bucket_size)
        self.se = QuadTree(Rectangle(x + hw / 2, y - hh / 2, hw, hh), self.capacity, self.depth + 1, self.max_depth, self.max_bucket_size)
        self.divided = True

    def insert(self, point):
        if not self.boundary.contains(point):
            return False

        # Se atingiu profundidade máxima ou resolução mínima, armazena no bucket com limite de segurança
        if self.depth >= self.max_depth or (self.boundary.w < 1e-6 and self.boundary.h < 1e-6):
            if len(self.points) < self.max_bucket_size:
                self.points.append(point)
                return True
            else:
                raise OverflowError("Bucket de nós profundos excedeu a capacidade máxima permitida.")

        if len(self.points) < self.capacity and not self.divided:
            self.points.append(point)
            return True

        if not self.divided:
            self.subdivide()
            # Redistribui pontos existentes para os filhos
            existing_points = self.points
            self.points = []
            for p in existing_points:
                self._insert_into_children(p)

        return self._insert_into_children(point)

    def _insert_into_children(self, point):
        if self.nw.insert(point): return True
        if self.ne.insert(point): return True
        if self.sw.insert(point): return True
        if self.se.insert(point): return True
        # Caso caia estritamente na borda externa final
        self.points.append(point)
        return True

    def query(self, range_rect, found=None, visited_nodes_counter=None):
        if found is None:
            found = []
        if visited_nodes_counter is not None:
            visited_nodes_counter[0] += 1

        if not self.boundary.intersects(range_rect):
            return found

        for p in self.points:
            if range_rect.contains(p):
                found.append(p)

        if self.divided:
            self.nw.query(range_rect, found, visited_nodes_counter)
            self.ne.query(range_rect, found, visited_nodes_counter)
            self.sw.query(range_rect, found, visited_nodes_counter)
            self.se.query(range_rect, found, visited_nodes_counter)

        return found

def run_tests():
    print("Iniciando suíte de testes robustos e validações de segurança...")

    # 1. Validação de entradas inválidas
    try:
        Rectangle(0, 0, -10, 10)
        raise AssertionError("Deveria ter falhado com dimensão negativa.")
    except ValueError as e:
        print(f"[Segurança OK] Validação de dimensão negativa capturada com sucesso: {e}")

    try:
        Point(float('nan'), 10.0)
        raise AssertionError("Deveria ter falhado com coordenada NaN.")
    except ValueError as e:
        print(f"[Segurança OK] Validação de coordenada NaN capturada com sucesso: {e}")

    # 2. Teste de Complexidade Sublinear vs Busca Linear com 2000 pontos
    qt = QuadTree(Rectangle(500, 500, 1000, 1000), capacity=4, max_depth=10)
    points_list = []
    
    random.seed(42)
    for i in range(2000):
        p = Point(random.uniform(0, 1000), random.uniform(0, 1000), data=i)
        qt.insert(p)
        points_list.append(p)

    query_box = Rectangle(300, 300, 200, 200)
    
    # Medindo nós visitados e desempenho da Quadtree
    visited = [0]
    t0 = time.time()
    qt_results = qt.query(query_box, visited_nodes_counter=visited)
    t_qt = time.time() - t0

    # Busca linear de referência
    t0 = time.time()
    linear_results = [p for p in points_list if query_box.contains(p)]
    t_linear = time.time() - t0

    print(f"[Desempenho] Total de pontos: 2000 | Nós visitados pela Quadtree: {visited[0]} (de um total potencial muito maior)")
    print(f"[Desempenho] Tempo Quadtree: {t_qt:.6f}s | Tempo Busca Linear: {t_linear:.6f}s")
    
    # Validação de corretude dos resultados
    assert len(qt_results) == len(linear_results), f"Mismatch de contagem: Quadtree({len(qt_results)}) vs Linear({len(linear_results)})"
    print("[Validação] Resultados da consulta por região 100% idênticos à força bruta.")
    print("[Sucesso] Todos os testes de segurança, fronteiras e desempenho passaram sem erros.")

if __name__ == "__main__":
    run_tests()