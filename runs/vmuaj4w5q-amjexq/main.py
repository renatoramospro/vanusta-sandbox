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

class QuadtreeNode:
    def __init__(self):
        self.boundary = (0, 0, 0, 0)
        self.capacity = 0
        self.entities = []
        self.divided = False
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None

    def reset(self, boundary, capacity):
        self.boundary = boundary
        self.capacity = capacity
        self.entities = []
        self.divided = False
        self.nw = self.ne = self.sw = self.se = None

class Quadtree:
    def __init__(self, boundary, capacity, max_depth=5):
        self.boundary = boundary
        self.capacity = capacity
        self.max_depth = max_depth
        self.pool = []  # Object Pool para mitigar GC Spikes
        self.root = self._get_new_node(boundary, capacity, 0)

    def _get_new_node(self, boundary, capacity, depth):
        # Tenta pegar um nó do pool, se não, cria um novo
        if self.pool:
            node = self.pool.pop()
            node.reset(boundary, capacity)
        else:
            node = QuadtreeNode()
            node.reset(boundary, capacity)
        
        node.depth = depth
        return node

    def _intersects(self, b1, b2):
        return not (b1[2] < b2[0] or b1[0] > b2[2] or b1[3] < b2[1] or b1[1] > b2[3])

    def insert(self, node, entity):
        e_aabb = entity.get_aabb()
        if not self._intersects(node.boundary, e_aabb):
            return False

        if len(node.entities) < node.capacity or node.depth >= self.max_depth:
            node.entities.append(entity)
            return True
        
        if not node.divided:
            self._subdivide(node)

        # Tenta inserir nos filhos
        if self.insert(node.nw, entity): return True
        if self.insert(node.ne, entity): return True
        if self.insert(node.sw, entity): return True
        if self.insert(node.se, entity): return True
        
        # Se não couber em nenhum filho de forma limpa (overlap), mantém no pai
        node.entities.append(entity)
        return True

    def _subdivide(self, node):
        x_min, y_min, x_max, y_max = node.boundary
        mid_x = (x_min + x_max) / 2
        mid_y = (y_min + y_max) / 2
        new_depth = node.depth + 1

        node.nw = self._get_new_node((x_min, y_min, mid_x, mid_y), node.capacity, new_depth)
        node.ne = self._get_new_node((mid_x, y_min, x_max, mid_y), node.capacity, new_depth)
        node.sw = self._get_new_node((x_min, mid_y, mid_x, y_max), node.capacity, new_depth)
        node.se = self._get_new_node((mid_x, mid_y, x_max, y_max), node.capacity, new_depth)
        node.divided = True

    def query(self, node, range_aabb, found):
        if not self._intersects(node.boundary, range_aabb):
            return

        for e in node.entities:
            if self._intersects(e.get_aabb(), range_aabb):
                found.append(e)

        if node.divided:
            self.query(node.nw, range_aabb, found)
            self.query(node.ne, range_aabb, found)
            self.query(node.sw, range_aabb, found)
            self.query(node.se, range_aabb, found)

    def clear(self, node):
        """Retorna os nós para o pool para evitar alocação/GC."""
        if node.divided:
            self.clear(node.nw)
            self.clear(node.ne)
            self.clear(node.sw)
            self.clear(node.se)
        
        # Adiciona o nó ao pool para reuso
        self.pool.append(node)
        node.divided = False
        node.entities = []

    def rebuild(self, boundary, capacity, max_depth, entities):
        # Limpa a árvore atual e devolve nós ao pool
        self.clear(self.root)
        self.pool = [] # Reset do pool para o novo ciclo
        self.max_depth = max_depth
        self.capacity = capacity
        self.root = self._get_new_node(boundary, capacity, 0)
        
        for e in entities:
            self.insert(self.root, e)

def run_test():
    # Cenário de Teste: Colapso de Densidade (Muitos objetos no mesmo ponto)
    # Isso testaria o RecursionError se não houvesse max_depth
    boundary = (0, 0, 100, 100)
    entities = []
    for i in range(500):
        # 50% das entidades estão quase no mesmo lugar para forçar profundidade
        if i < 250:
            entities.append(Entity(50, 50, 1, i))
        else:
            entities.append(Entity(random.uniform(0, 100), random.uniform(0, 100), 1, i))

    qt = Quadtree(boundary, capacity=4, max_depth=8)
    
    print("--- Teste de Estabilidade (Colapso de Densidade) ---")
    start = time.time()
    qt.rebuild(boundary, 4, 8, entities)
    end = time.time()
    print(f"Rebuild com 500 entidades (250 colapsadas) em: {end-start:.4f}s")

    # Teste de Query
    found = []
    query_range = (45, 45, 55, 55)
    qt.query(qt.root, query_range, found)
    print(f"Entidades encontradas no centro: {len(found)}")
    
    # Verificação de segurança: Se o código chegou aqui sem RecursionError, o max_depth funcionou
    print("Status: SUCESSO (Sem RecursionError)")

if __name__ == "__main__":
    run_test()