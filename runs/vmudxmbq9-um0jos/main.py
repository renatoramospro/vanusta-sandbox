import json

# ==========================================
# 1. Simulação dos Recursos do Service Mesh (Istio CRDs em formato Python/JSON nativo)
# ==========================================
# Evitamos dependências externas (como PyYAML) estruturando os manifests 
# diretamente como dicionários Python nativos, simulando o resultado de um parser YAML.
ISTIO_MANIFESTS = [
    {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": "frontend-route",
            "namespace": "production"
        },
        "spec": {
            "hosts": ["frontend.production.svc.cluster.local"],
            "http": [
                {
                    "route": [
                        {
                            "destination": {
                                "host": "auth-service.production.svc.cluster.local",
                                "port": {"number": 8080}
                            }
                        }
                    ]
                }
            ]
        }
    },
    {
        "apiVersion": "networking.istio.io/v1alpha3",
        "kind": "VirtualService",
        "metadata": {
            "name": "auth-route",
            "namespace": "production"
        },
        "spec": {
            "hosts": ["auth-service.production.svc.cluster.local"],
            "http": [
                {
                    "route": [
                        {
                            "destination": {
                                "host": "user-db-service.production.svc.cluster.local",
                                "port": {"number": 5432}
                            }
                        }
                    ]
                }
            ]
        }
    }
]

# ==========================================
# 2. Pipeline de Extração e Modelo Intermediário (IR)
# ==========================================
class ServiceMeshTopologyParser:
    def __init__(self):
        self.nodes = set()
        self.edges = []

    def parse_manifests(self, manifests):
        for doc in manifests:
            if not doc or doc.get("kind") != "VirtualService":
                continue
            
            # Extrai o host de origem (quem expõe a rota)
            hosts = doc.get("spec", {}).get("hosts", [])
            source = hosts[0].split(".")[0] if hosts else "unknown"
            self.nodes.add(source)

            # Extrai as rotas de destino
            http_routes = doc.get("spec", {}).get("http", [])
            for http in http_routes:
                for route in http.get("route", []):
                    dest_host = route.get("destination", {}).get("host", "")
                    if dest_host:
                        target = dest_host.split(".")[0]
                        port = route.get("destination", {}).get("port", {}).get("number", "unknown")
                        
                        self.nodes.add(target)
                        self.edges.append({
                            "source": source,
                            "target": target,
                            "protocol": f"tcp/{port}"
                        })

    def generate_mermaid(self):
        """
        Gera o diagrama em formato Mermaid a partir do Modelo Intermediário (IR).
        Mitiga o equívoco comum de nomes com hifens normalizando-os para underscores.
        """
        lines = ["graph TD"]
        for edge in self.edges:
            src = edge["source"].replace("-", "_")
            tgt = edge["target"].replace("-", "_")
            proto = edge["protocol"]
            lines.append(f"    {src} -->|{proto}| {tgt}")
        return "\n".join(lines)


# ==========================================
# 3. Execução e Validação do Experimento
# ==========================================
if __name__ == "__main__":
    print("Iniciando pipeline de extração de topologia do Service Mesh...")
    
    parser = ServiceMeshTopologyParser()
    parser.parse_manifests(ISTIO_MANIFESTS)

    print(f"\nNós descobertos na malha: {sorted(list(parser.nodes))}")
    print(f"Arestas (comunicações) mapeadas: {len(parser.edges)}")

    mermaid_diagram = parser.generate_mermaid()
    print("\n--- Diagrama Mermaid Gerado ---")
    print(mermaid_diagram)
    print("--------------------------------")

    # Asserções para garantir comportamento observável correto e validação de consistência
    assert "frontend" in parser.nodes, "O nó frontend deveria estar presente."
    assert "auth-service" in parser.nodes, "O nó auth-service deveria estar presente."
    assert "user-db-service" in parser.nodes, "O nó user-db-service deveria estar presente."
    assert len(parser.edges) == 2, f"Esperado 2 arestas, encontrado {len(parser.edges)}"
    
    print("\n[OK] Experimento corrigido, executado com sucesso e 100% de consistência validada.")