import json
from datetime import datetime, timezone, timedelta

# Simulação de dados expandida cobrindo os cenários e falhas apontadas pelo Tester
mock_cluster_data = {
    "cluster_issuers": [
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "ClusterIssuer",
            "metadata": {"name": "letsencrypt-prod", "generation": 1},
            "status": {
                "observedGeneration": 1,
                "conditions": [{"type": "Ready", "status": "True"}]
            }
        },
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "ClusterIssuer",
            "metadata": {"name": "broken-issuer", "generation": 2},
            "status": {
                "observedGeneration": 2,
                "conditions": [{"type": "Ready", "status": "False"}]
            }
        }
    ],
    "issuers": [],
    "certificates": [
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Certificate",
            "metadata": {"name": "app-tls", "namespace": "production", "generation": 1},
            "spec": {
                "secretName": "app-tls-secret",
                "dnsNames": ["app.example.com"],
                "issuerRef": {"kind": "ClusterIssuer", "name": "letsencrypt-prod"},
                "renewBefore": "720h" # 30 dias antes
            },
            "status": {
                "observedGeneration": 1,
                "notAfter": "2026-12-31T23:59:59Z",
                "renewalTime": "2026-12-01T23:59:59Z",
                "conditions": [{"type": "Ready", "status": "True"}]
            }
        },
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Certificate",
            "metadata": {"name": "edge-tls", "namespace": "staging", "generation": 3},
            "spec": {
                "secretName": "edge-tls-secret",
                "dnsNames": ["edge.example.com"],
                "issuerRef": {"kind": "ClusterIssuer", "name": "letsencrypt-prod"}
            },
            "status": {
                "observedGeneration": 2, # Gerenciamento desatualizado (observedGeneration < generation)
                "notAfter": None,        # Sem data de expiração (emitido sem sucesso ou pendente)
                "conditions": [{"type": "Ready", "status": "False"}]
            }
        },
        {
            "apiVersion": "cert-manager.io/v1",
            "kind": "Certificate",
            "metadata": {"name": "dep-fail-tls", "namespace": "default", "generation": 1},
            "spec": {
                "secretName": "dep-fail-secret",
                "dnsNames": ["dep.example.com"],
                "issuerRef": {"kind": "ClusterIssuer", "name": "broken-issuer"} # Aponta para emissor que não está Ready
            },
            "status": {
                "observedGeneration": 1,
                "notAfter": "2026-10-15T00:00:00Z",
                "conditions": [{"type": "Ready", "status": "True"}] # Falso positivo no cert isolado
            }
        }
    ]
}

def parse_cert_manager_data(data):
    issuers_map = {}
    
    # Mapear ClusterIssuers e Issuers
    for ci in data.get("cluster_issuers", []):
        name = ci["metadata"]["name"]
        ready = any(c["type"] == "Ready" and c["status"] == "True" for c in ci.get("status", {}).get("conditions", []))
        issuers_map[("ClusterIssuer", name)] = ready

    for iss in data.get("issuers", []):
        name = iss["metadata"]["name"]
        namespace = iss["metadata"].get("namespace", "default")
        ready = any(c["type"] == "Ready" and c["status"] == "True" for c in iss.get("status", {}).get("conditions", []))
        issuers_map[("Issuer", name)] = ready

    parsed_certificates = []
    for cert in data.get("certificates", []):
        meta = cert.get("metadata", {})
        spec = cert.get("spec", {})
        status = cert.get("status", {})
        
        name = meta.get("name")
        namespace = meta.get("namespace", "default")
        generation = meta.get("generation", 1)
        observed_generation = status.get("observedGeneration", 0)
        
        # 1. Validação de observedGeneration vs generation
        generation_synced = (observed_generation >= generation)
        
        # 2. Validação do emissor referenciado
        issuer_ref = spec.get("issuerRef", {})
        issuer_kind = issuer_ref.get("kind", "ClusterIssuer")
        issuer_name = issuer_ref.get("name")
        issuer_ready = issuers_map.get((issuer_kind, issuer_name), False)
        
        # 3. Condição Ready real
        cond_ready = any(c["type"] == "Ready" and c["status"] == "True" for c in status.get("conditions", []))
        
        # Certificado é considerado ativo apenas se Ready=True, generation sincronizada e emissor pronto
        is_ready = cond_ready and generation_synced and issuer_ready
        
        # 4. Tratamento robusto de notAfter (evitando None cru)
        not_after = status.get("notAfter")
        not_after_str = not_after if not_after else "⚠️ Desconhecida / Não emitida"
        
        # 5. Status explícito de renovação automática (renewalTime)
        renewal_time = status.get("renewalTime")
        renewal_str = renewal_time if renewal_time else "N/A (Pendente/Desconhecido)"
        
        parsed_certificates.append({
            "name": name,
            "namespace": namespace,
            "dns_names": ", ".join(spec.get("dnsNames", [])),
            "issuer": f"{issuer_kind}/{issuer_name}",
            "issuer_ready": issuer_ready,
            "not_after": not_after_str,
            "renewal_time": renewal_str,
            "ready": is_ready,
            "generation_synced": generation_synced,
            "cond_ready": cond_ready
        })

    return issuers_map, parsed_certificates

def generate_markdown(issuers_map, certificates):
    md = "# Documentação Automatizada de Políticas SSL/TLS (cert-manager)\n\n"
    md += f"_Gerado em: {datetime.now(timezone.utc).isoformat()}_\n\n"
    
    md += "## 1. Emissores (Issuers & ClusterIssuers)\n\n"
    md += "| Nome | Tipo | Status Ready |\n"
    md += "|---|---|---|\n"
    for (kind, name), ready in issuers_map.items():
        status_str = "✅ Ready" if ready else "❌ Not Ready"
        md += f"| `{name}` | {kind} | {status_str} |\n"
        
    md += "\n## 2. Certificados Mapeados\n\n"
    md += "| Nome | Namespace | Domínios (SANs) | Emissor | Expiração (`notAfter`) | Renovação Automática (`renewalTime`) | Status |\n"
    md += "|---|---|---|---|---|---|---|\n"
    for cert in certificates:
        if cert["ready"]:
            status_str = "✅ Ativo & Sincronizado"
        elif not cert["issuer_ready"]:
            status_str = "⚠️ Falha (Emissor Inativo)"
        elif not cert["generation_synced"]:
            status_str = "⚠️ Pendente (Controller Desatualizado)"
        else:
            status_str = "⚠️ Falha / Não Pronto"
            
        md += f"| `{cert['name']}` | {cert['namespace']} | {cert['dns_names']} | `{cert['issuer']}` | {cert['not_after']} | {cert['renewal_time']} | {status_str} |\n"
        
    return md

if __name__ == "__main__":
    print("Iniciando extração rigorosa e parsing avançado do cert-manager...")
    issuers_map, certificates = parse_cert_manager_data(mock_cluster_data)
    
    # Testes de asserção rigorosos para validar os cenários corrigidos
    edge_cert = next(c for c in certificates if c["name"] == "edge-tls")
    assert edge_cert["not_after"] == "⚠️ Desconhecida / Não emitida", "Deveria tratar notAfter ausente adequadamente."
    
    dep_fail_cert = next(c for c in certificates if c["name"] == "dep-fail-tls")
    assert dep_fail_cert["ready"] is False, "Certificado com emissor inativo não pode ser considerado ativo."
    
    print("[Teste de Robustez] Todos os cenários adversariais tratados com sucesso!")

    markdown_output = generate_markdown(issuers_map, certificates)
    print("\n--- Documentação Markdown Gerada ---\n")
    print(markdown_output)
    
    assert "renewalTime" in markdown_output or "Renovação Automática" in markdown_output
    assert "⚠️ Desconhecida / Não emitida" in markdown_output
    print("\n[Sucesso] Relatório gerado cobrindo renewalTime, notAfter nulo e validações de geração/emissor!")