import yaml
import json

# ==========================================
# 1. Simulação dos Recursos do Service Mesh (Istio CRDs)
# ==========================================
# Em um ambiente real, estes dados seriam obtidos via kubernetes client 
# consultando VirtualServices e DestinationRules do cluster.
ISTIO_MANIFESTS = [
    """
    apiVersion: networking.istio.io/v1alpha3
    kind: VirtualService
    metadata:
      name: frontend-route
      namespace: production
    spec:
      hosts:
      - frontend.production.svc.cluster.local
      http:
      - route:
        - destination:
            host: auth-service.production.svc.cluster.local
            port:
              number: 8080
    """,
    """
    apiVersion: networking.istio.io/v1alpha3
    kind: VirtualService
    metadata:
      name: auth-route
      namespace: production
    spec:
      hosts:
      - auth-service.production.svc.cluster.local
      http:
      - route:
        - destination:
            host: user-db-service.production.svc.cluster.local
            port:
              number: 5432
    """
]

# ==========================================
# 2. Pipeline de Extração e Modelo Intermediário (IR)
# ==========================================
class ServiceMeshTopologyParser:
    def __init__(self):
        self.nodes = set()
        self.edges = []

    def parse_manifests(self, yaml_docs):
        for doc_str in yaml_docs:
            doc = yaml.safe_load(doc_str)
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
                        port = route.get("destination", {}).get("port", {}).get("number", "default")
                        
                        self.nodes.add(target)
                        self.edges.append({
                            "source": source,
                            "target": target,
                            "protocol": f"TCP:{port}"
                        })

    def generate_mermaid(self):
        """Traduz o Modelo Intermediário (IR) para sintaxe Mermaid válida."""
        mermaid_lines = ["graph TD;"]
        # Adiciona nós explicitamente para evitar falhas de renderização
        for node in sorted(self.nodes):
            safe_node_id = node.replace("-", "_")
            mermaid_lines.append(H_INDENT := f"    {safe_node_id}[\"{node}\"]")
        
        # Adiciona arestas direcionadas com rótulos de protocolo
        for edge in self.edges:
            src = edge["source"].replace("-", "_")
            tgt = edge["target"].replace("-", "_")
            proto = edge["protocol"]
            mermaid_lines.append(f"    {src} -->|{proto}| {tgt}")
            
        return "\n".join(mermaid_lines)

    def validate_consistency(self):
        """Garante que todas as arestas apontam para nós conhecidos (Validação de Consistência)."""
        for edge in self.edges:
            assert edge["source"] in self.nodes, f"Erro: Nó de origem {edge['source']} ausente no conjunto de nós."
            assert edge["target"] in self.nodes, f"Erro: Nó de destino {edge['target']} ausente no conjunto de nós."
        return True

# ==========================================
# 3. Execução e Validação do Experimento
# ==========================================
if __name__ == "__main__":
    print("Iniciando extração de topologia do Service Mesh...")
    parser = ServiceMeshTopologyParser()
    parser.parse_manifests(ISTIO_MANIFESTS)

    # Validação de consistência do grafo gerado
    is_consistent = parser.validate_consistency()
    print(f"Validação de consistência estrutural: {'SUCESSO' if is_consistent else 'FALHA'}")

    # Geração do artefato visual (Mermaid)
    mermaid_diagram = parser.generate_mermaid()
    print("\n--- Diagrama Mermaid Gerado ---")
    print(mermaid_diagram)
    print("--------------------------------")

    # Asserções para garantir comportamento observável correto
    assert "frontend" in parser.nodes, "O nó frontend deveria estar presente."
    assert "auth_service" in parser.nodes, "O nó auth_service deveria estar presente."
    assert "user_db_service" in parser.nodes, "O nó user_db_service deveria estar presente."
    print("\n[OK] Experimento concluído com sucesso e 100% de consistência validada.")