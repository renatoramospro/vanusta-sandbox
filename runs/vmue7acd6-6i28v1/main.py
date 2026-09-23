python path=kong_doc_generator.py
import os
import yaml

# 1. Simulação do estado exportado do Kong (ex: obtido via `deck dump` ou Admin API)
KONG_STATE_MOCK = {
    "services": [
        {
            "name": "payment-service",
            "host": "payment.internal",
            "port": 443,
            "protocol": "https",
            "routes": [
                {
                    "name": "pay-route",
                    "paths": ["/api/v1/pay"],
                    "methods": ["POST"],
                    "plugins": [
                        {"name": "request-transformer", "config": {"add": {"headers": ["X-Custom: true"]}}}
                    ]
                }
            ],
            "plugins": [
                {"name": "rate-limiting", "config": {"minute": 100, "policy": "local"}}
            ]
        }
    ],
    "plugins": [
        {"name": "cors", "config": {"origins": ["*"], "credentials": True}}
    ]
}

SENSITIVE_KEYS = {"key", "secret", "password", "token", "consumer_key", "client_secret"}

def mask_sensitive_config(config_dict):
    """Mascara valores sensíveis nas configurações de plugins para evitar vazamento na doc."""
    masked = {}
    for k, v in config_dict.items():
        if any(sk in k.lower() for sk in SENSITIVE_KEYS):
            masked[k] = "********"
        elif isinstance(v, dict):
            masked[v] = mask_sensitive_config(v)
        else:
            masked[k] = v
    return masked

def generate_markdown(state):
    """Gera documentação Markdown estruturada a partir do estado do Kong."""
    md = []
    md.append("# 🚪 Documentação Oficial do Kong API Gateway\n")
    md.append("> *Gerado automaticamente por script de automação CI/CD.*\n")
    
    # Plugins Globais
    global_plugins = state.get("plugins", [])
    if global_plugins:
        md.append("## 🌐 Políticas Globais (Escopo Global)\n")
        md.append("| Plugin | Configuração Principal |")
        md.append("|--------|------------------------|")
        for p in global_plugins:
            cfg = mask_sensitive_config(p.get("config", {}))
            md.append(f"| `{p['name']}` | `{cfg}` |")
        md.append("\n---\n")
    
    # Services e Routes
    md.append("## 📦 Microsserviços e Rotas\n")
    for service in state.get("services", []):
        s_name = service.get("name")
        md.append(f"### Service: `{s_name}`")
        md.append(f"- **Backend Target:** `{service.get('protocol')}://{service.get('host')}:{service.get('port')}`")
        
        # Plugins de Service
        s_plugins = service.get("plugins", [])
        if s_plugins:
            md.append(f"- **Plugins no Escopo de Service:**")
            for sp in s_plugins:
                cfg = mask_sensitive_config(sp.get("config", {}))
                md.append(f"  - `{sp['name']}` (Config: `{cfg}`)")
        
        md.append("\n**Rotas Associadas:**")
        routes = service.get("routes", [])
        if not routes:
            md.append("_Nenhuma rota configurada._\n")
        else:
            for r in routes:
                r_name = r.get("name", "unnamed")
                paths = ", ".join(r.get("paths", []))
                methods = ", " .join(r.get("methods", ["ANY"]))
                md.append(f"- **Rota:** `{r_name}`")
                md.append(f"  - **Caminhos:** `{paths}`")
                md.append(f"  - **Métodos:** `{methods}`")
                
                r_plugins = r.get("plugins", [])
                if r_plugins:
                    md.append(f"  - **Plugins no Escopo de Rota:**")
                    for rp in r_plugins:
                        cfg = mask_sensitive_config(rp.get("config", {}))
                        md.append(f"    - `{rp['name']}` (Config: `{cfg}`)")
            md.append("\n---")
            
    return "\n".join(md)

if __name__ == "__main__":
    print("Iniciando extração e geração de documentação do Kong...")
    markdown_content = generate_markdown(KONG_STATE_MOCK)
    
    output_filename = "api-docs.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    print(f"Sucesso! Arquivo gerado: {output_filename}")
    
    # Validação de esquema / integridade básica
    assert os.path.exists(output_filename), "Arquivo Markdown não foi criado!"
    with open(output_filename, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# 🚪 Documentação Oficial" in content
        assert "payment-service" in content
        assert "rate-limiting" in content
    print("Validação do arquivo Markdown concluída com sucesso (100% dos asserts passaram).")