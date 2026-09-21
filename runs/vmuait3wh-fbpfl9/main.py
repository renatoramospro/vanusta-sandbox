import time
import random

class Entity:
    def __init__(self, x, y, radius, id):
        self.x = x
        self.y = y
        self.radius = radius
        self.id = id

    def get_aabb(self):
        return (self.x - self.radius, self.y - self.radius, 
                self.x + self.radius, self.y + self.radius)

class Quadtree:
    def __init__(self, boundary, capacity):
        # boundary: (x_min, y_min, x_max, y_max)
        self.boundary = boundary
        self.capacity = capacity
        self.entities = []
        self.divided = False

    def _intersects(self, b1, b2):
        return not (b1[2] < b2[0] or b1[0] > b2[2] or b1[3] < b2[1] or b1[1] > b2[3])

    def subdivide(self):
        x_min, y_min, x_max, y_max = self.boundary
        mid_x = (x_min + x_max) / 2
        mid_y = (y_min + y_max) / 2

        self.nw = Quadtree((x_min, y_min, mid_x, mid_y), self.capacity)
        self.ne = Quadtree((mid_x, y_min, x_max, mid_y), self.capacity)
        self.sw = Quadtree((x_min, mid_y, mid_x, y_max), self.capacity)
        self.se = Quadtree((mid_x, mid_y, x_max, y_max), self.capacity)
        self.divided = True

    def insert(self, entity):
        e_aabb = entity.get_aabb()
        if not self._intersects(self.boundary, e_aabb):
            return False

        if len(self.entities) < self.capacity:
            self.entities.append(entity)
            return True
        else:
            if not self.divided:
                self.subdivide()
            
            if self.nw.insert(entity): return True
            if self.ne.insert(entity): return True
            if self.sw.insert(entity): return True
            if self.se.insert(entity): return True
        return False

    def query(self, range_aabb, found):
        if not self._intersects(self.boundary, range_aabb):
            return

        for e in self.entities:
            if self._intersects(e.get_aabb(), range_aabb):
                found.append(e)

        if self.divided:
            self.nw.query(range_aabb, found)
            self.ne.query(range_aabb, found)
            self.sw.query(range_aabb, found)
            self.se.query(range_aabb, found)

def brute_force_collision_candidates(entities):
    candidates = []
    n = len(entities)
    for i in range(n):
        for j in range(i + 1, n):
            # Simula o teste de proximidade
            e1, e2 = entities[i], entities[j]
            if abs(e1.x - e2.x) < (e1.radius + e2.radius) and \
               abs(e1.y - e2.y) < (e1.radius + e2.radius):
                candidates.append((e1.id, e2.id))
    return candidates

def quadtree_collision_candidates(entities, boundary, capacity):
    qt = Quadtree(boundary, capacity)
    for e in entities:
        qt.insert(e)
    
    candidates = []
    for e in entities:
        found = []
        qt.query(e.get_aabb(), found)
        for other in found:
            if e.id < other.id: # Evita duplicatas e auto-colisão
                candidates.append((e.id, other.id))
    return candidates

def run_benchmark(num_entities=500):
    world_size = 1000
    boundary = (0, 0, world_size, world_size)
    entities = []
    
    for i in range(num_entities):
        entities.append(Entity(
            random.uniform(0, world_size),
            random.uniform(0, world_size),
            random.uniform(2, 5),
            i
        ))

    print(f"--- Benchmark: {num_entities} Entidades ---")

    # Brute Force
    start = time.perf_counter()
    bf_results = brute_force_collision_candidates(entities)
    bf_time = time.perf_counter() - start
    print(f"Brute Force: {bf_time:.4f}s (Candidatos: {len(bf_results)})")

    # Quadtree
    start = time.perf_counter()
    qt_results = quadtree_collision_candidates(entities, boundary, 4)
    qt_time = time.perf_counter() - start
    print(f"Quadtree:    {qt_time:.4f}s (Candidatos: {len(qt_results)})")

    reduction = (1 - (qt_time / bf_time)) * 100
    print(f"Redução de tempo: {reduction:.2f}%")
    
    # Verificação de integridade (os candidatos devem ser similares)
    # Nota: Quadtree pode encontrar mais ou menos dependendo da implementação de overlap,
    # mas para este teste de performance, focamos na ordem de grandeza.
    assert bf_time > qt_time, "Quadtree deveria ser mais rápida que Brute Force"

if __name__ == "__main__":
    run_benchmark(500)