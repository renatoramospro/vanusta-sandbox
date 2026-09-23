import os
import re

# 1. Simulação do estado exportado do Kong incluindo casos de borda e chaves customizadas
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
                        {
                            "name": "key-auth", 
                            "config": {
                                "api_custom_passphrase": "super-secret-custom-key-123",
                                "anonymous": None
                            }
                        }
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

# Heurística avançada para chaves sensíveis (cobre variações customizadas como passphrases, chaves de API, segredos, etc.)
SENSITIVE_PATTERNS = re.compile(
    r"(key|secret|password|passwd|token|auth|credential|passphrase|private)", 
    re.IGNORECASE
)

def mask_sensitive_config(config_dict):
    """Mascara valores sensíveis nas configurações dos plugins do Kong utilizando regex flexível."""
    masked = {}
    for k, v in config_dict.items():
        # Verifica se a chave contém qualquer padrão sensível conhecido ou customizado
        if SENSITIVE_PATTERNS.search(str(k)):
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
            md.append(f"- **Plugin:** `{gp['name']}` | **Configuração:** `{cfg}`")
    else:
        md.append("_Nenhum plugin global configurado._")
        
    md.append("\n## 🚀 Microsserviços e Rotas")
    services = state.get("services", [])
    for svc in services:
        svc_name = svc.get("name", "unnamed-service")
        md.append(f"\n### 📦 Service: `{svc_name}`")
        md.append(f"- **Host:** `{svc.get('host')}:{svc.get('port')}` ({svc.get('protocol')})")
        
        # Plugins no escopo de Service
        svc_plugins = svc.get("plugins", [])
        if svc_plugins:
            md.append("- **Plugins no Escopo de Service:**")
            for sp in svc_plugins:
                cfg = mask_sensitive_config(sp.get("config", {}))
                md.append(f"  - `{sp['name']}` (Config: `{cfg}`)")
                
        # Rotas associadas
        routes = svc.get("routes", [])
        md.append(f"- **Rotas Associadas ({len(routes)}):**")
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
    print("Iniciando extração e geração de documentação do Kong (com correção de sintaxe e regex de mascaramento)...")
    markdown_content = generate_markdown(KONG_STATE_MOCK)
    
    output_filename = "api-docs.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    print(f"Sucesso! Arquivo gerado: {output_filename}")
    
    # Validações e Assertivas rigorosas
    assert os.path.exists(output_filename), "Arquivo Markdown não foi criado!"
    with open(output_filename, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# 🚪 Documentação Oficial" in content
        assert "payment-service" in content
        assert "rate-limiting" in content
        # Validação do mascaramento adversarial (chave customizada api_custom_passphrase mascarada)
        assert "super-secret-custom-key-123" not in content, "FALHA: Dado sensível vazou na documentação!"
        assert "********" in content, "FALHA: Mascaramento não aplicado corretamente."
        
    print("Validação concluída com sucesso: Sintaxe corrigida e blindagem contra chaves customizadas validada por testes automatizados.")