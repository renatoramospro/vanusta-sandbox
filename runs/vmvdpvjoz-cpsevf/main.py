class LRUCache:

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.keys = []

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.keys.remove(key)
        self.keys.append(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.keys.remove(key)
        elif len(self.cache) >= self.capacity:
            del self.cache[self.keys.pop(0)]
        self.keys.append(key)
        self.cache[key] = value

# --- testes do benchmark (não fazem parte da resposta) ---
c = LRUCache(2)
c.put(1, 1); c.put(2, 2)
assert c.get(1) == 1
c.put(3, 3)
assert c.get(2) == -1
c.put(4, 4)
assert c.get(1) == -1
assert c.get(3) == 3 and c.get(4) == 4
d = LRUCache(1)
d.put(1, 10); d.put(1, 11)
assert d.get(1) == 11
d.put(2, 20)
assert d.get(1) == -1 and d.get(2) == 20
print("BENCHMARK_OK")