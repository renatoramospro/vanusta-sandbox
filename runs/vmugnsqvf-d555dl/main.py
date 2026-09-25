import queue
import threading
import time
import random

class MessageBroker:
    def __init__(self):
        self.queues = {}

    def create_queue(self, topic):
        if topic not in self.queues:
            self.queues[topic] = queue.Queue()

    def publish(self, topic, message):
        if topic in self.queues:
            self.queues[topic].put(message)
        else:
            print(f"Topic {topic} não encontrado")

    def subscribe(self, topic, callback):
        if topic in self.queues:
            self.queues[topic].get(block=True, timeout=1)
            threading.Thread(target=callback, args=(self.queues[topic].get(),)).start()
        else:
            print(f"Topic {topic} não encontrado")

    def run(self):
        for topic, queue in self.queues.items():
            while not queue.empty():
                message = queue.get(block=False)
                print(f"Recebido mensagem em {topic}: {message}")

if __name__ == "__main__":
    broker = MessageBroker()
    broker.create_queue("topic1")
    broker.create_queue("topic2")

    threading.Thread(target=broker.run).start()

    for i in range(10000):
        topic = "topic1" if i % 2 == 0 else "topic2"
        message = f"Mensagem {i}"
        broker.publish(topic, message)

    time.sleep(1)