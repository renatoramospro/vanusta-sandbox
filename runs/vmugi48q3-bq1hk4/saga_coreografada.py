import uuid
import time
from kafka import KafkaProducer

# Configuração do Kafka
bootstrap_servers = ['localhost:9092']
topic = 'saga_coreografada'

# Criar um produtor Kafka
producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

# Definir a classe SagaCoreografada
class SagaCoreografada:
    def __init__(self):
        self.id_transacao = uuid.uuid4()
        self.eventos = []

    def iniciar_transacao(self):
        # Enviar evento de início da transação para o Kafka
        evento = {'id_transacao': self.id_transacao, 'tipo': 'iniciar_transacao'}
        producer.send(topic, value=evento)
        self.eventos.append(evento)

    def realizar_servico_a(self):
        # Realizar o serviço A
        print('Realizando serviço A...')
        # Simular tempo de execução
        time.sleep(2)
        # Enviar evento de conclusão do serviço A para o Kafka
        evento = {'id_transacao': self.id_transacao, 'tipo': 'concluir_servico_a'}
        producer.send(topic, value=evento)
        self.eventos.append(evento)

    def realizar_servico_b(self):
        # Realizar o serviço B
        print('Realizando serviço B...')
        # Simular tempo de execução
        time.sleep(2)
        # Enviar evento de conclusão do serviço B para o Kafka
        evento = {'id_transacao': self.id_transacao, 'tipo': 'concluir_servico_b'}
        producer.send(topic, value=evento)
        self.eventos.append(evento)

    def realizar_servico_c(self):
        # Realizar o serviço C
        print('Realizando serviço C...')
        # Simular tempo de execução
        time.sleep(2)
        # Enviar evento de conclusão do serviço C para o Kafka
        evento = {'id_transacao': self.id_transacao, 'tipo': 'concluir_servico_c'}
        producer.send(topic, value=evento)
        self.eventos.append(evento)

    def compensar_transacao(self):
        # Compensar a transação
        print('Compensando transação...')
        # Simular tempo de execução
        time.sleep(2)
        # Enviar evento de compensação para o Kafka
        evento = {'id_transacao': self.id_transacao, 'tipo': 'compensar_transacao'}
        producer.send(topic, value=evento)
        self.eventos.append(evento)

# Criar uma instância da classe SagaCoreografada
saga = SagaCoreografada()

# Iniciar a transação
saga.iniciar_transacao()

# Realizar os serviços
saga.realizar_servico_a()
saga.realizar_servico_b()
saga.realizar_servico_c()

# Compensar a transação
saga.compensar_transacao()