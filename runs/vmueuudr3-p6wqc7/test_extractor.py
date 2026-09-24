import pytest
from extractor import RabbitMQExtractor

def test_mapper_covers_all_exchanges():
    """Garante que 100% das exchanges declaradas aparecem no catálogo."""
    raw_data = {
        "exchanges": [
            {"name": "ex1", "vhost": "/", "type": "fanout", "durable": True, "auto_delete": False, "arguments": {}},
            {"name": "ex2", "vhost": "/", "type": "topic", "durable": True, "auto_delete": False, "arguments": {}}
        ],
        "queues": [{"name": "q1", "vhost": "/", "durable": True}],
        "bindings": [
            {"source": "ex1", "destination": "q1", "destination_type": "queue", "routing_key": "", "arguments": {}}
        ]
    }
    
    extractor = RabbitMQExtractor(raw_data)
    topology = extractor.process_topology()
    
    assert len(topology) == 2
    assert "ex1" in topology
    assert "ex2" in topology

def test_markdown_contains_routing_keys_and_arguments():
    """Valida se o Markdown gerado inclui corretamente chaves de roteamento e argumentos complexos."""
    raw_data = {
        "exchanges": [
            {"name": "payment.topic", "vhost": "/", "type": "topic", "durable": True, "auto_delete": False, "arguments": {"x-dead-letter-exchange": "dlx.exchange"}}
        ],
        "queues": [
            {"name": "payment.processed.q", "vhost": "/", "durable": True}
        ],
        "bindings": [
            {"source": "payment.topic", "destination": "payment.processed.q", "destination_type": "queue", "routing_key": "payment.success", "arguments": {}}
        ]
    }

    extractor = RabbitMQExtractor(raw_data.copy())
    md = extractor.generate_markdown()

    # Verificações fundamentais exigidas pelo Arquiteto
    assert "payment.topic" in md
    assert "topic" in md
    assert "x-dead-letter-exchange" in md
    assert "payment.success" in md
    assert "payment.processed.q" in md
    assert "| Destino (Fila/Exchange) | Tipo | Chave de Roteamento (`Routing Key`) | Argumentos do Binding |" in md

def test_equívoco_comum_evitado_relacionamento_correto():
    """
    Contraexemplo/Teste defensivo contra o equívoco comum listado pelo Arquiteto:
    Consultar apenas o endpoint /api/exchanges (que omite bindings e rotas) 
    em vez de correlacionar com /api/bindings.
    """
    raw_data = {
        "exchanges": [{"name": "isolated.exchange", "vhost": "/", "type": "direct", "durable": True, "auto_delete": False, "arguments": {}}],
        "queues": [{"name": "target.queue", "vhost": "/", "durable": True}],
        "bindings": [
            # Binding real conectando a exchange isolada à fila alvo
            {"source": "isolated.exchange", "destination": "target.queue", "destination_type": "queue", "routing_key": "alert.critical", "arguments": {}}
        ]
    }

    extractor = RabbitMQExtractor(raw_data)
    topology = extractor.process_topology()

    # Valida que o binding foi corretamente mapeado dentro da exchange
    assert len(topology["isolated.exchange"]["bindings"]) == 1
    binding_info = topology["isolated.exchange"]["bindings"][0]
    assert binding_info["routing_key"] == "alert.critical"
    assert binding_info["destination"] == "target.queue"