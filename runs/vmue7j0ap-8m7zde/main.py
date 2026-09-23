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

SENSITIVE_KEYS = {"key", "secret", "password", "token", "authorization"}

def mask_sensitive_config(config_dict):
    """Mascara valores sensíveis nas configurações dos plugins do Kong."""
    masked = {}
    for k, v in config_dict.items():
        if any(sk in k.lower() for sk in SENSITIVE_KEYS):
            masked[k] = "********"
        elif isinstance(v, dict):
            masked[k] = mask_sensitive_config(v)
        else:
            masked[k] = v
    return masked

def generate_markdown(state):
    md = []
    md.append("# 🚪 Documentação Oficial de Rotas e Políticas (Kong API Gateway)")
    md.append("\n## 🌐 Políticas Globais")
    
    global_plugins = state.get("plugins", [])
    if global_plugins:
        for gp in global_plugins:
            cfg = mask_sensitive_config(gp.get("config", {}))
            md.append(- `- **Plugin:** `{gp['name']}` | **Configuração:** `{cfg}`")
    else:
        md.append("- *Nenhum plugin global ativo.*")
        
    md.append("\n## 🚀 Microsserviços e Rotas")
    
    for svc in state.get("services", []):
        svc_name = svc.get("name", "unnamed-service")
        md.append(f"\n### Serviço: `{svc_name}`")
        md.append(f"- **Backend:** `{svc.get('protocol')}://{svc.get('host')}:{svc.get('port')}`")
        
        svc_plugins = svc.get("plugins", [])
        if svc_plugins:
            md.append("- **Plugins no Escopo de Serviço:**")
            for sp in svc_plugins:
                cfg = mask_sensitive_config(sp.get("config", {}))
                md.append(f"  - `{sp['name']}` (Config: `{cfg}`)")
                
        routes = svc.get("routes", [])
        if routes:
            md.append("- **Rotas Associadas:**")
            for r in routes:
                r_name = r.get("name", "unnamed")
                paths = ", ".join(r.get("paths", []))
                methods = ", ".join(r.get("methods", ["ANY"]))
                md.append(f"  - **Rota:** `{r_name}`")
                md.append(f"    - **Caminhos:** `{paths}`")
                md.append(f"    - **Métodos:** `{methods}`")
                
                r_plugins = r.get("plugins", [])
                if r_plugins:
                    md.append(f"    - **Plugins no Escopo de Rota:**")
                    for rp in r_plugins:
                        cfg = mask_sensitive_config(rp.get("config", {}))
                        md.append(f"      - `{rp['name']}` (Config: `{cfg}`)")
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