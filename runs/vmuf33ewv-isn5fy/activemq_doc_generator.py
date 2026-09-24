import http.server
import json
import threading
import urllib.request
import unittest
import os

# ---------------------------------------------------------
# 1. Simulação do Broker ActiveMQ (Jolokia API & JMX MBeans)
# ---------------------------------------------------------
# O ActiveMQ expõe métricas e políticas via Jolokia (JMX-sobre-JSON).
# Este mock simula o broker real respondendo a consultas de MBeans de filas.
ACTIVEMQ_MOCK_DATA = {
    "queues": [
        {
            "name": "orders.process.q",
            "type": "Queue",
            "enqueueCount": 15420,
            "dequeueCount": 15400,
            "inFlightCount": 20,
            "dlq": "ActiveMQ.DLQ",
            "ttl": "Disabled",
            "retentionPolicy": "FIFO (Default)"
        },
        {
            "name": "notifications.email.q",
            "type": "Queue",
            "enqueueCount": 3200,
            "dequeueCount": 3195,
            "inFlightCount": 5,
            "dlq": "Custom.DeadLetterQueue",
            "ttl": "86400000ms (24h)",
            "retentionPolicy": "Discard old"
        }
    ],
    "topics": [
        {
            "name": "events.user.signup",
            "type": "Topic",
            "subscribers": 4,
            "dlq": "N/A (Pub/Sub)",
            "ttl": "3600000ms (1h)",
            "retentionPolicy": "Durable Subscriptions"
        }
    ]
}

class MockActiveMQHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/jolokia/read/org.apache.activemq:type=Broker,brokerName=localhost,destinationType=Queue,*":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            # Formato compatível com Jolokia
            response = {"value": ACTIVEMQ_MOCK_DATA["queues"]}
            self.wfile.write(json.dumps(response).encode("utf-8"))
        elif self.path == "/api/jolokia/read/org.apache.activemq:type=Broker,brokerName=localhost,destinationType=Topic,*":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"value": ACTIVEMQ_MOCK_DATA["topics"]}
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silencia logs do servidor HTTP durante o teste
        pass

def run_mock_server(port=8161):
    server = http.server.HTTPServer(("127.0.0.1", port), MockActiveMQHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server

# ---------------------------------------------------------
# 2. O Gerador de Documentação (Domínio `documenter`)
# ---------------------------------------------------------
class ActiveMQDocGenerator:
    def __init__(self, jolokia_url: str):
        self.jolokia_url = jolokia_url

    def fetch_destinations(self, dest_type: str) -> list:
        url = f"{self.jolokia_url}/api/jolokia/read/org.apache.activemq:type=Broker,brokerName=localhost,destinationType={dest_type},*"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("value", [])

    def generate_markdown(self) -> str:
        queues = self.fetch_destinations("Queue")
        topics = self.fetch_destinations("Topic")

        md = []
        md.append("# Relatório de Mensageria — Apache ActiveMQ (Staging)")
        md.append("\n> **Gerado automaticamente** pelo módulo `documenter` via inspeção JMX/Jolokia.\n")
        
        md.append("## 1. Filas Ativas (Queues)")
        md.append("| Nome da Fila | Enfileiradas | Desemfileiradas | DLQ Configurada | TTL | Política de Retenção |")
        md.append("| :--- | :---: | :---: | :--- | :--- | :--- |")
        for q in queues:
            md.append(f"| `{q['name']}` | {q['enqueueCount']} | {q['dequeueCount']} | `{q['dlq']}` | {q['ttl']} | {q['retentionPolicy']} |")

        md.append("\n## 2. Tópicos Ativos (Topics)")
        md.append("| Nome do Tópico | Assinantes | DLQ / Tratamento | TTL | Política de Retenção |")
        md.append("| :--- | :---: | :--- | :--- | :--- |")
        for t in topics:
            md.append(f"| `{t['name']}` | {t['subscribers']} | {t['dlq']} | {t['ttl']} | {t['retentionPolicy']} |")

        return "\n".join(md)

# ---------------------------------------------------------
# 3. Testes Automatizados e Validação do Equívoco Comum
# ---------------------------------------------------------
class TestActiveMQDocGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = run_mock_server(8161)

    def test_generator_produces_structured_markdown(self):
        generator = ActiveMQDocGenerator("http://127.0.0.1:8161")
        markdown_output = generator.generate_markdown()

        print("\n--- INÍCIO DA SAÍDA GERADA ---")
        print(markdown_output)
        print("--- FIM DA SAÍDA GERADA ---\n")

        # Validações estruturais cruciais exigidas pelo critério de sucesso
        self.assertIn("orders.process.q", markdown_output, "Fila ativa principal ausente da documentação!")
        self.assertIn("notifications.email.q", markdown_output, "Segunda fila ativa ausente!")
        self.assertIn("Custom.DeadLetterQueue", markdown_output, "Política de DLQ personalizada não mapeada!")
        self.assertIn("events.user.signup", markdown_output, "Tópico ativo ausente!")
        self.assertIn("| Nome da Fila |", markdown_output, "A documentação deve utilizar tabelas Markdown estruturadas.")

    def test_contraexemplo_estatico_falha_em_runtime(self):
        """
        Demonstra o equívoco comum mapeado pelo Arquiteto:
        Confiar apenas na leitura estática de activemq.xml e ignorar destinos dinâmicos.
        """
        # Arquivo estático simulado que só tem 1 fila antiga declarada
        static_xml_mock = ["orders.process.q"]
        
        # O sistema dinâmico retorna 2 filas (orders + notifications criada em runtime)
        generator = ActiveMQDocGenerator("http://127.0.0.1:8161")
        dynamic_queues = [q['name'] for q in generator.fetch_destinations("Queue")]

        # Prova que o estático falha em abranger 100% das filas ativas reais
        untracked_dynamic_queues = [q for q in dynamic_queues if q not in static_xml_mock]
        
        print(f"[Contraexemplo Validação] Filas estáticas: {static_xml_mock}")
        print(f"[Contraexemplo Validação] Filas ativas reais (JMX): {dynamic_queues}")
        print(f"[Contraexemplo Validação] Filas ignoradas pelo parser estático: {untracked_dynamic_queues}")
        
        self.assertTrue(
            len(untracked_dynamic_queues) > 0, 
            "Deveria haver filas dinâmicas não presentes no XML estático para provar o equívoco."
        )

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)