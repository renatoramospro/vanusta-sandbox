import hashlib
import bisect

class ConsistentHashing:
    def __init__(self, num_servers):
        self.num_servers = num_servers
        self.circle = [None] * num_servers

    def hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def map_key(self, key):
        index = self.hash(key) % self.num_servers
        return index

    def distribute_key(self, key):
        index = self.map_key(key)
        self.circle[index] = key
        return index

    def get_server(self, key):
        index = self.map_key(key)
        return self.circle[index]

# Testes
ch = ConsistentHashing(5)
keys = [f"key{i}" for i in range(10000)]
for key in keys:
    ch.distribute_key(key)

# Adicionar um servidor
ch.num_servers += 1
ch.circle = [None] * ch.num_servers
for key in keys:
    ch.distribute_key(key)

# Remover um servidor
ch.num_servers -= 1
ch.circle = [None] * ch.num_servers
for key in keys:
    ch.distribute_key(key)