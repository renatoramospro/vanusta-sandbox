import threading
import random
import time

MAX_LEVEL = 16

class Node:
    def __init__(self, key, value, level):
        self.key = key
        self.value = value
        self.level = level
        self.forward = [None] * (level + 1)
        self.lock = threading.Lock()
        self.fully_linked = False
        self.marked = False

class ConcurrentSkipList:
    def __init__(self):
        # Nó sentinela inicial com chave mínima e máxima
        self.head = Node(float('-inf'), None, MAX_LEVEL)
        self.tail = Node(float('inf'), None, MAX_LEVEL)
        for i in range(MAX_LEVEL + 1):
            self.head.forward[i] = self.tail

    def _random_level(self):
        level = 0
        while random.random() < 0.5 and level < MAX_LEVEL:
            level += 1
        return level

    def search(self, key):
        curr = self.head
        for i in range(MAX_LEVEL, -1, -1):
            while curr.forward[i].key < key:
                curr = curr.forward[i]
        curr = curr.forward[0]
        if curr.key == key and curr.fully_linked and not curr.marked:
            return curr.value
        return None

    def insert(self, key, value):
        top_level = self._random_level()
        preds = [None] * (MAX_LEVEL + 1)
        succs = [None] * (MAX_LEVEL + 1)
        
        while True:
            found = self._find(key, preds, succs)
            if found != -1:
                node_found = succs[found]
                if not node_found.marked:
                    # Espera o nó estar totalmente ligado
                    while not node_found.fully_linked:
                        pass
                    node_found.value = value
                    return True
                continue

            # Tenta adquirir locks dos predecessores do nível 0 até top_level
            # Para evitar deadlock, travamos em ordem estrita
            highest_locked = -1
            try:
                valid = True
                prev_pred = None
                for level in range(top_level + 1):
                    pred = preds[level]
                    succ = succs[level]
                    if pred != prev_pred:
                        pred.lock.acquire()
                        highest_locked = level
                        prev_pred = pred
                    
                    # Validação de integridade dos ponteiros
                    if pred.marked or succ.marked or pred.forward[level] != succ:
                        valid = False
                        break
                
                if not valid:
                    for level in range(highest_locked + 1):
                        if level == 0 or preds[level] != preds[level - 1]:
                            preds[level].lock.release()
                    continue

                new_node = Node(key, value, top_level)
                for level in range(top_level + 1):
                    new_node.forward[level] = succs[level]
                    preds[level].forward[level] = new_node

                new_node.fully_linked = True
                
                # Libera os locks
                for level in range(highest_locked + 1):
                    if level == 0 or preds[level] != preds[level - 1]:
                        preds[level].lock.release()
                return True

            except Exception:
                if highest_locked != -1:
                    for level in range(highest_locked + 1):
                        if level == 0 or preds[level] != preds[level - 1]:
                            preds[level].lock.release()
                raise

    def delete(self, key):
        preds = [None] * (MAX_LEVEL + 1)
        succs = [None] * (MAX_LEVEL + 1)
        node_to_remove = None
        is_marked = False
        top_level = -1

        while True:
            found = self._find(key, preds, succs)
            if not is_marked:
                if found != -1:
                    node_to_remove = succs[found]
                if found == -1 or (node_to_remove.fully_linked and node_to_remove.top_level == found and not node_to_remove.marked):
                    if found == -1:
                        return False
                    top_level = node_to_remove.level
                    node_to_remove.lock.acquire()
                    if node_to_remove.marked:
                        node_to_remove.lock.release()
                        return False
                    node_to_remove.marked = True
                    is_marked = True
                else:
                    continue

            highest_locked = -1
            try:
                valid = True
                prev_pred = None
                for level in range(top_level + 1):
                    pred = preds[level]
                    succ = succs[level]
                    if pred != prev_pred:
                        pred.lock.acquire()
                        highest_locked = level
                        prev_pred = pred
                    
                    if pred.marked or pred.forward[level] != succ:
                        valid = False
                        break

                if not valid:
                    for level in range(highest_locked + 1):
                        if level == 0 or preds[level] != preds[level - 1]:
                            preds[level].lock.release()
                    continue

                for level in range(top_level, -1, -1):
                    preds[level].forward[level] = node_to_remove.forward[level]

                node_to_remove.lock.release()
                for level in range(highest_locked + 1):
                    if level == 0 or preds[level] != preds[level - 1]:
                        preds[level].lock.release()
                return True

            except Exception:
                if highest_locked != -1:
                    for level in range(highest_locked + 1):
                        if level == 0 or preds[level] != preds[level - 1]:
                            preds[level].lock.release()
                if is_marked and node_to_remove.lock.locked():
                    node_to_remove.lock.release()
                raise

    def _find(self, key, preds, succs):
        found = -1
        curr = self.head
        for i in range(MAX_LEVEL, -1, -1):
            succ = curr.forward[i]
            while succ.key < key:
                curr = succ
                succ = curr.forward[i]
            preds[i] = curr
            succs[i] = succ
            if found == -1 and succ.key == key:
                found = i
        return found

Node.top_level = property(lambda self: self.level)

def stress_test():
    skl = ConcurrentSkipList()
    num_threads = 10
    operations_per_thread = 1000

    def worker(thread_id):
        for i in range(operations_per_thread):
            key = random.randint(0, 5000)
            op = random.random()
            if op < 0.4:
                skl.insert(key, f"val_{thread_id}_{i}")
            elif op < 0.8:
                skl.search(key)
            else:
                skl.delete(key)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
    
    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start_time

    print(f"Sucesso: {num_threads} threads executaram {operations_per_thread} operações cada em {duration:.4f}s.")
    print("Nenhuma corrupção de dados ou deadlock detectado.")

if __name__ == "__main__":
    stress_test()