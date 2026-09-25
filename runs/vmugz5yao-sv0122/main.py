import os
import time
import random

class LSMTree:
    def __init__(self):
        self.memtable = []
        self.sstable = []

    def insert(self, key, value):
        self.memtable.append((key, value))

    def flush(self):
        self.sstable.append(self.memtable)
        self.memtable = []

    def search(self, key):
        for sstable in self.sstable:
            for item in sstable:
                if item[0] == key:
                    return item[1]
        return None

def main():
    lsm_tree = LSMTree()

    # Inserir dados na MemTable
    for i in range(100):
        lsm_tree.insert(i, f"Valor {i}")

    # Flushing da MemTable para SSTable
    lsm_tree.flush()

    # Buscar dados na LSM-Tree
    print(lsm_tree.search(50))

if __name__ == "__main__":
    main()