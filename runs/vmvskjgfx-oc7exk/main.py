class LRUCache:

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.doubly_linked_list = DoublyLinkedList()

    def get(self, key: int) -> int:
        if key in self.cache:
            node = self.cache[key]
            self.doubly_linked_list.move_to_front(node)
            return node.value
        return -1

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self.doubly_linked_list.move_to_front(node)
        else:
            if len(self.cache) >= self.capacity:
                tail = self.doubly_linked_list.tail.prev
                del self.cache[tail.key]
                self.doubly_linked_list.remove_node(tail)
            new_node = Node(key, value)
            self.cache[key] = new_node
            self.doubly_linked_list.add_to_front(new_node)

class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def add_to_front(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def remove_node(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def move_to_front(self, node):
        self.remove_node(node)
        self.add_to_front(node)

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