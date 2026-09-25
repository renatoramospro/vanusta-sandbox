import hashlib
import bisect

class ConsistentHashing:
    def __init__(self, num_servers):
        self.num_servers = num_servers
        self.table = [None] * num_servers

    def hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def map_key(self, key):
        index = self.hash(key) % self.num_servers
        return index

    def distribute_key(self, key):
        index = self.map_key(key)
        self.table[index] = key
        return index

    def get_server(self, key):
        index = self.map_key(key)
        return self.table[index]

# Testes
ch = ConsistentHashing(5)
keys = [f"key{i}" for i in range(10000)]

for key in keys:
    ch.distribute_key(key)

print("Chaves distribuídas:")
for i, key in enumerate(keys):
    print(f"{i}: {ch.get_server(key)}")

# Adicionar um servidor
ch.num_servers += 1
ch.table = [None] * ch.num_servers

for key in keys:
    ch.distribute_key(key)

print("\nChaves distribuídas após adicionar servidor:")
for i, key in enumerate(keys):
    print(f"{i}: {ch.get_server(key)}")

# Remover um servidor
ch.num_servers -= 1
ch.table = [None] * ch.num_servers

for key in keys:
    ch.distribute_key(key)

print("\nChaves distribuídas após remover servidor:")
for i, key in enumerate(keys):
    print(f"{i}: {ch.get_server(key)}")