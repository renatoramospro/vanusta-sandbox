import asyncio
import uuid

# Configuração do banco de escrita (Write DB)
write_db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "write_db",
    "user": "postgres",
    "password": "password"
}

# Configuração do banco de leitura (Read DB)
read_db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "read_db",
    "user": "postgres",
    "password": "password"
}

# Event Bus/Message Broker assíncrono
event_bus_config = {
    "host": "localhost",
    "port": 5672,
    "exchange": "events",
    "queue": "reservas"
}

# Modelo de dados para a reserva
class Reserva:
    def __init__(self, id, cliente, data_reserva):
        self.id = id
        self.cliente = cliente
        self.data_reserva = data_reserva

# Comando para cadastrar uma reserva
class CadastrarReserva:
    def __init__(self, cliente, data_reserva):
        self.cliente = cliente
        self.data_reserva = data_reserva

# Handler para o comando de cadastrar uma reserva
async def cadastrar_reserva_handler(command):
    # Gravação no banco de escrita
    async with asyncpg.connect(**write_db_config) as conn:
        await conn.execute("INSERT INTO reservas (id, cliente, data_reserva) VALUES ($1, $2, $3)", command.id, command.cliente, command.data_reserva)

    # Publicação do evento
    async with aio_pika.connect_robust(**event_bus_config) as conn:
        channel = await conn.channel()
        await channel.default_exchange.publish(aio_pika.Message(body=command.id), routing_key=event_bus_config["queue"])

# Consumidor de eventos para atualizar o banco de leitura
async def consumidor_eventos():
    async with aio_pika.connect_robust(**event_bus_config) as conn:
        channel = await conn.channel()
        queue = await channel.queue_declare(queue=event_bus_config["queue"])

        async with queue.consume() as consumer:
            async for message in consumer:
                # Atualização do banco de leitura
                async with asyncpg.connect(**read_db_config) as conn:
                    await conn.execute("INSERT INTO reservas (id, cliente, data_reserva) VALUES ($1, $2, $3)", message.body, "Cliente X", "2023-03-15")

# Teste de integração com consistência eventual
async def test_integracao():
    # Cadastrar uma reserva
    command = CadastrarReserva(uuid.uuid4(), "Cliente X", "2023-03-15")
    await cadastrar_reserva_handler(command)

    # Esperar por 500ms para simular atraso no broker
    await asyncio.sleep(0.5)

    # Verificar se a reserva foi cadastrada no banco de leitura
    async with asyncpg.connect(**read_db_config) as conn:
        result = await conn.fetch("SELECT * FROM reservas WHERE id = $1", command.id)
        assert result

# Execução do experimento
async def main():
    await test_integracao()

# Execução do experimento
asyncio.run(main())