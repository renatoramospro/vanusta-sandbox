import json

class RabbitMQExtractor:
    def __init__(self, raw_data):
        """
        Inicializa o extrator com os dados brutos obtidos da RabbitMQ Management API.
        Espera um dicionário contendo as chaves: 'exchanges', 'queues', 'bindings'.
        """
        self.exchanges = raw_data.get("exchanges", [])
        self.queues = raw_data.get("queues", [])
        self.bindings = raw_data.get("bindings", [])

    def process_topology(self):
        """
        Cruza os dados de exchanges, filas e bindings para montar o catálogo estruturado.
        """
        # Mapeia bindings por destination (fila) ou source (exchange)
        # No RabbitMQ Management API, bindings conectam source -> destination
        topology = {}

        # Filtrar exchanges internas padrão se desejado, mas vamos listar todas do vhost
        for ex in self.exchanges:
            if ex.get("name") == "":
                continue  # Ignora a exchange padrão sem nome se necessário, ou documenta
            
            ex_name = ex["name"]
            topology[ex_name] = {
                "vhost": ex.get("vhost", "/"),
                "type": ex.get("type", "direct"),
                "durable": ex.get("durable", True),
                "auto_delete": ex.get("auto_delete", False),
                "arguments": ex.get("arguments", {}),
                "bindings": []
            }

        # Adiciona bindings associados às exchanges
        for b in self.bindings:
            if b.get("source") in topology:
                source = b["source"]
                destination = b["destination"]
                dest_type = b["destination_type"] # 'queue' ou 'exchange'
                routing_key = b["routing_key"]
                args = b.get("arguments", {})

                topology[source]["bindings"].append({
                    "destination": destination,
                    "destination_type": dest_type,
                    "routing_key": routing_key,
                    "arguments": args
                })

        return topology

    def generate_markdown(self):
        """
        Gera o documento Markdown estruturado contendo o catálogo de mensageria.
        """
        topology = self.process_topology()
        
        md = []
        md.append("# Catálogo de Mensageria - RabbitMQ")
        md.append("\n*Documentação gerada automaticamente pelo extrator de topologia AMQP.*\n")

        if not topology:
            md.append("> *Nenhuma exchange encontrada na topologia.*")
            return "\n".join(md)

        for ex_name, details in sorted(topology.items()):
            display_name = ex_name if ex_name else "(Exchange Padrão / Default)"
            md.append(f"## Exchange: `{display_name}`")
            md.append(f"- **Virtual Host:** `{details['vhost']}`")
            md.append(f"- **Tipo:** `{details['type']}`")
            md.append(f"- **Durable:** `{details['durable']}`")
            md.append(f"- **Auto Delete:** `{details['auto_delete']}`")
            
            if details["arguments"]:
                md.append(f"- **Argumentos:** `{json.dumps(details['arguments'])}`")
            else:
                md.append("- **Argumentos:** `Nenhum`")

            md.append("\n### Bindings & Rotas")
            
            if details["bindings"]:
                md.append("| Destino (Fila/Exchange) | Tipo | Chave de Roteamento (`Routing Key`) | Argumentos do Binding |")
                md.append("| :--- | :--- | :--- | :--- |")
                for b in details["bindings"]:
                    args_str = json.dumps(b["arguments"]) if b["arguments"] else "-"
                    md.append(f"| `{b['destination']}` | {b['destination_type']} | `{b['routing_key']}` | `{args_str}` |")
            else:
                md.append("> *Nenhum binding registrado para esta exchange.*")
            
            md.append("\n---\n")

        return "\n".join(md)

if __name__ == "__main__":
    # Exemplo de execução local demonstrativa
    sample_data = {
        "exchanges": [
            {"name": "order.events", "vhost": "/", "type": "topic", "durable": True, "auto_delete": False, "arguments": {}},
            {"name": "notification.direct", "vhost": "/", "type": "direct", "durable": True, "auto_delete": False, "arguments": {"x-max-length": 1000}}
        ],
        "queues": [
            {"name": "order.created.q", "vhost": "/", "durable": True},
            {"name": "email.send.q", "vhost": "/", "durable": True}
        ],
        "bindings": [
            {"source": "order.events", "destination": "order.created.q", "destination_type": "queue", "routing_key": "order.created.*", "arguments": {}},
            {"source": "notification.direct", "destination": "email.send.q", "destination_type": "queue", "routing_key": "email.send", "arguments": {}}
        ]
    }

    extractor = RabbitMQExtractor(sample_data)
    markdown_output = extractor.generate_markdown()
    print("=== Markdown Gerado com Sucesso ===")
    print(markdown_output)