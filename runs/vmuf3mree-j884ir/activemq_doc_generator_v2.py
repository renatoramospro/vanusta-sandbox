import http.server
import json
import threading
import urllib.request
import unittest
import time

# -------------------------------------------------------------------------
# Simulação fiel do contrato bruto da API Jolokia/JMX do Apache ActiveMQ
# -------------------------------------------------------------------------
# Diferente da versão anterior (que recebia campos prontos), aqui o Jolokia
# expõe atributos JMX brutos que exigem resolução de defaults, fallbacks para 
# campos ausentes e distinção de TTL por mensagem vs expiração do destino.
ACTIVEMQ_RAW_JMX_DATA = {
    "broker": {
        "globalDefaults": {
            "dlq": "ActiveMQ.DLQ",
            "ttl": "Disabled",
            "retentionPolicy": "FIFO (Default)"
        }
    },
    "destinations": [
        {
            # Fila padrão: herda políticas globais e possui campos ausentes
            "name": "orders.process.q",
            "type": "Queue",
            "enqueueCount": 15420,
            "dequeueCount": 15400,
            # 'dlq' e 'ttl' omitidos propositalmente para testar fallback para defaults
        },
        {
            # Fila com override explícito e TTL por mensagem vs expiração de destino
            "name": "payments.capture.q",
            "type": "Queue",
            "enqueueCount": 0,
            "dequeueCount": 0,
            "inFlightCount": 0,
            "dlq": "Custom.Payments.DLQ",
            "messageTtl": "60000ms (1min)",       # TTL aplicado por mensagem
            "destinationExpiry": "Disabled",     # Expiração do destino em si
            "retentionPolicy": "Discard oldest",
            "isRuntimeCreated": True
        },
        {
            # Fila ativa sem tráfego (Enqueue/Dequeue = 0, mas presente no broker)
            "name": "audit.archive.q",
            "type": "Queue",
            "enqueueCount": 0,
            "dequeueCount": 0,
            "inFlightCount": 0,
            # Sem tráfego mas ativa
            "dlq": "ActiveMQ.DLQ",
            "retentionPolicy": "FIFO (Default)"
        }
    ]
}

class AdvancedActiveMQHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/jolokia/read/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(ACTIVEMQ_RAW_JMX_DATA).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

class ActiveMQDocumenterEngine:
    def __init__(self, jolokia_url):
        self.jolokia_url = jolokia_url

    def fetch_raw_data(self):
        req = urllib.request.urlopen(self.jolokia_url)
        return json.loads(req.read().decode("utf-8"))

    def process_destinations(self, raw_data):
        globals_def = raw_data["broker"]["globalDefaults"]
        processed = []

        for dest in raw_data["destinations"]:
            # 1. Tratamento de campos ausentes e resolução de herança (defaults globais)
            resolved_dlq = dest.get("dlq", globals_def["dlq"])
            resolved_ttl = dest.get("messageTtl", dest.get("destinationExpiry", globals_def["ttl"]))
            resolved_retention = dest.get("retentionPolicy", globals_def["retentionPolicy"])

            # 2. Definição precisa de "Fila Ativa":
            # Consideramos ativa qualquer fila registrada no MBean do broker,
            # independentemente de ter tráfego atual (enqueueCount > 0) ou zero tráfego.
            is_active = True 
            has_traffic = (dest.get("enqueueCount", 0) > 0 or dest.get("dequeueCount", 0) > 0)

            processed.append({
                "name": dest["name"],
                "type": dest["type"],
                "enqueueCount": dest.get("enqueueCount", 0),
                "dequeueCount": dest.get("dequeueCount", 0),
                "dlq": resolved_dlq,
                "ttl": resolved_ttl,
                "retentionPolicy": resolved_retention,
                "hasTraffic": has_traffic,
                "isRuntimeCreated": dest.get("isRuntimeCreated", False)
            })

        return processed

    def generate_markdown(self, destinations):
        md = "# Relatório de Mensageria — Apache ActiveMQ (Staging Avançado)\n\n"
        md += "| Nome da Fila | Criada em Runtime? | Com Tráfego? | Enfileiradas | Desemfileiradas | DLQ Resolvida | TTL / Expiração | Retenção |\n"
        md += "| :--- | :---: | :---: | :---: | :---: | :--- | :--- | :--- |\n"
        
        for d in destinations:
            runtime_str = "Sim" if d["isRuntimeCreated"] else "Não (XML)"
            traffic_str = "Sim" if d["hasTraffic"] else "Não (Ociosa)"
            md += f"| `{d['name']}` | {runtime_str} | {traffic_str} | {d['enqueueCount']} | {d['dequeueCount']} | `{d['dlq']}` | {d['ttl']} | {d['retentionPolicy']} |\n"
        
        return md

class TestActiveMQAdvancedDocumenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), AdvancedActiveMQHandler)
        cls.port = cls.server.server_port
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_correct = True

    def test_robust_extraction_and_inheritance(self):
        url = f"http://127.0.0.1:{self.port}/api/jolokia/read/all"
        engine = ActiveMQDocumenterEngine(url)
        raw = engine.fetch_raw_data()
        processed = engine.process_destinations(raw)

        # Validação 1: Fila 'orders.process.q' deve herdar o default global de DLQ e TTL
        orders_q = next(d for d in processed if d["name"] == "orders.process.q")
        self.assertEqual(orders_q["dlq"], "ActiveMQ.DLQ", "Deveria herdar o DLQ global do broker")
        self.assertEqual(orders_q["ttl"], "Disabled", "Deveria herdar o TTL global do broker")

        # Validação 2: Fila 'payments.capture.q' deve respeitar override de runtime e distinção de TTL
        payments_q = next(d for d in processed if d["name"] == "payments.capture.q")
        self.assertEqual(payments_q["dlq"], "Custom.Payments.DLQ")
        self.assertEqual(payments_q["ttl"], "60000ms (1min)", "Deve distinguir TTL de mensagem da expiração de destino")
        self.assertTrue(payments_q["isRuntimeCreated"])

        # Validação 3: Fila ativa sem tráfego ('audit.archive.q') deve ser documentada (cobertura 100% de filas ativas)
        audit_q = next(d for d in processed if d["name"] == "audit.archive.q")
        self.assertFalse(audit_q["hasTraffic"])
        self.assertTrue(any(d["name"] == "audit.archive.q" for d in processed), "Filas ativas sem tráfego não podem ser ignoradas")

        # Geração do artefato Markdown final
        report = engine.generate_markdown(processed)
        print("\n--- INÍCIO DA SAÍDA GERADA (V2) ---")
        print(report)
        print("--- FIM DA SAÍDA GERADA (V2) ---\n")

        self.assertIn("orders.process.q", report)
        self.assertIn("payments.capture.q", report)
        self.assertIn("audit.archive.q", report)

if __name__ == "__main__":
    unittest.main(argv=['first-arg-is-ignored'], exit=False)