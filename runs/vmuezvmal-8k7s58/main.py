import json
from datetime import datetime, timezone

# Simulação de dados retornados do cluster Kubernetes (API do cert-manager)
mock_cluster_data = {
    "cluster_issuers": [
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "ClusterIssuer",
            "metadata": {"name": "letsencrypt-prod"},
            "spec": {"acme": {"server": "https://acme-v02.api.letsencrypt.org/directory"}},
            "status": {"conditions": [{"type": "Ready", "status": "True"}]}
        }
    ],
    "issuers": [
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Issuer",
            "metadata": {"name": "internal-ca", "namespace": "kube-system"},
            "spec": {"ca": {"secretName": "internal-ca-secret"}},
            "status": {"conditions": [{"type": "Ready", "status": "False"}]} # Exemplo inativo/com erro
        }
    ],
    "certificates": [
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Certificate",
            "metadata": {"name": "app-tls", "namespace": "production"},
            "spec": {
                "secretName": "app-tls-secret",
                "dnsNames": ["app.example.com", "api.example.com"],
                "issuerRef": {"kind": "ClusterIssuer", "name": "letsencrypt-prod"}
            },
            "status": {
                "notAfter": "2026-12-31T23:59:59Z",
                "renewalTime": "2026-12-01T23:59:59Z",
                "conditions": [{"type": "Ready", "status": "True"}]
            }
        },
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Certificate",
            "metadata": {"name": "broken-tls", "namespace": "staging"},
            "spec": {
                "secretName": "broken-tls-secret",
                "dnsNames": ["staging.example.com"],
                "issuerRef": {"kind": "Issuer", "name": "internal-ca"}
            },
            "status": {
                "notAfter": None,
                "conditions": [{"type": "Ready", "status": "False"}] # Equívoco comum: certificado criado mas não pronto
            }
        }
    ]
}

def parse_cert_manager_data(data):
    issuers_mapped = []
    certificates_mapped = []

    # Processar ClusterIssuers e Issuers
    for ci in data.get("cluster_issuers", []):
        ready = any(c["type"] == "Ready" and c["status"] == "True" for c in ci.get("status", {}).get("conditions", []))
        issuers_mapped.append({
            "name": ci["metadata"]["name"],
            "kind": "ClusterIssuer",
            "namespace": "Global",
            "ready": ready
        })

    for iss in data.get("issuers", []):
        ready = any(c["type"] == "Ready" and c["status"] == "True" for c in iss.get("status", {}).get("conditions", []))
        issuers_mapped.append({
            "name": iss["metadata"]["name"],
            "kind": "Issuer",
            "namespace": iss["metadata"].get("namespace", "default"),
            "ready": ready
        })

    # Processar Certificates
    for cert in data.get("certificates", []):
        status = cert.get("status", {})
        conditions = status.get("conditions", [])
        ready = any(c["type"] == "Ready" and c["status"] == "True" for c in conditions)
        
        not_after = status.get("notAfter", "N/A")
        dns_names = ", ".join(cert.get("spec", {}).get("dnsNames", []))
        issuer_ref = cert.get("spec", {}).get("issuerRef", {}).get("name", "N/A")
        namespace = cert.get("metadata", {}).get("namespace", "default")
        name = cert.get("metadata", {}).get("name", "N/A")

        certificates_mapped.append({
            "name": name,
            "namespace": namespace,
            "dns_names": dns_names,
            "issuer": issuer_ref,
            "not_after": not_after,
            "ready": ready
        })

    return issuers_mapped, certificates_mapped

def generate_markdown(issuers, certificates):
    md = "# Documentação Automatizada de Políticas SSL/TLS (cert-manager)\n\n"
    md += f"_Gerado em: {datetime.now(timezone.utc).isoformat()}_\n\n"
    
    md += "## 1. Emissores (Issuers & ClusterIssuers)\n\n"
    md += "| Nome | Tipo | Namespace | Status Ready |\n"
    md += "|---|---|---|---|\n"
    for iss in issuers:
        status_str = "✅ Ready" if iss["ready"] else "❌ Not Ready"
        md += f"| `{iss['name']}` | {iss['kind']} | {iss['namespace']} | {status_str} |\n"
    
    md += "\n## 2. Certificados Mapeados\n\n"
    md += "| Nome | Namespace | Domínios (SANs) | Emissor | Expiração (`notAfter`) | Status |\n"
    md += "|---|---|---|---|---|---|\n"
    for cert in certificates:
        status_str = "✅ Ativo" if cert["ready"] else "⚠️ Falha / Pendente"
        md += f"| `{cert['name']}` | {cert['namespace']} | {cert['dns_names']} | `{cert['issuer']}` | {cert['not_after']} | {status_str} |\n"
        
    return md

if __name__ == "__main__":
    print("Iniciando extração e parsing de dados do cert-manager...")
    issuers, certificates = parse_cert_manager_data(mock_cluster_data)
    
    # Demonstração de ataque ao equívoco comum:
    # Verificação de que certificados com Ready=False não são mascarados como ativos válidos
    broken_certs = [c for c in certificates if not c["ready"]]
    assert len(broken_certs) == 1, "Deveria identificar exatamente 1 certificado com falha."
    print(f"[Teste de Robustez] Certificado inválido detectado corretamente: {broken_certs[0]['name']} (Ready=False)")

    markdown_output = generate_markdown(issuers, certificates)
    print("\n--- Documentação Markdown Gerada ---\n")
    print(markdown_output)
    
    # Validação do critério de sucesso
    assert "letsencrypt-prod" in markdown_output
    assert "app.example.com" in markdown_output
    print("\n[Sucesso] Documentação gerada sem erros de parsing e 100% aderente aos critérios!")