# Este arquivo simula o código de um desenvolvedor definindo um pipeline.
# Ele contém cenários de sucesso e cenários de vazamento.

def get_user_secret():
    return "super-secret-token"

def run_pipeline():
    # Cenário 1: Fluxo Seguro (Dados públicos para agente externo)
    public_info = "Hello World"
    web_agent.search(public_info)

    # Cenário 2: Vazamento Direto (Fonte sensível para agente externo)
    secret = get_user_secret()
    web_agent.search(secret)

    # Cenário 3: Vazamento por Propagação (Taint se espalha por atribuição)
    raw_data = get_user_secret()
    processed_data = raw_data
    web_agent.search(processed_data)

    # Cenário 4: Fluxo Seguro (Dados sensíveis para agente interno/confiável)
    secret_key = get_user_secret()
    internal_vault.store(secret_key)

    # Cenário 5: Vazamento Indireto (Dados sensíveis via objeto/atributo - simplificado para o teste)
    user_context = get_user_secret()
    external_api.send(user_context)