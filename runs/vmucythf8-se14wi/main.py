import random

# Taxonomia de Dependência de Dados Externos
taxonomia = {
    "APIs de Terceiros": 0.5,
    "Webhooks": 0.3,
    "Feeds de Mercado": 0.2,
    "Bancos de Dados": 0.1,
    "Parceiros": 0.1
}

# Fórmula de Cálculo de Risco
def calcular_risco(probabilidade, impacto):
    return probabilidade * impacto

# Matriz de Pontuação de Risco
def calcular_pontuacao_risco(risco):
    if risco <= 0.2:
        return "Baixo"
    elif risco <= 0.5:
        return "Moderado"
    elif risco <= 0.8:
        return "Alto"
    else:
        return "Muito Alto"

# Recomendações Preventivas e Arquiteturais
def calcular_recomendacoes(probabilidade, impacto):
    if probabilidade > 0.5 and impacto > 0.5:
        return "Implementar caching e circuit breakers"
    elif probabilidade > 0.3 and impacto > 0.3:
        return "Implementar fallbacks de dados e redundância de fornecedores"
    else:
        return "Não há necessidade de recomendações"

# Simulação de Dependência de Dados Externos
def simular_dependencia():
    probabilidade = random.uniform(0, 1)
    impacto = random.uniform(0, 1)
    risco = calcular_risco(probabilidade, impacto)
    pontuacao_risco = calcular_pontuacao_risco(risco)
    recomendacoes = calcular_recomendacoes(probabilidade, impacto)
    return probabilidade, impacto, risco, pontuacao_risco, recomendacoes

# Execução do Experimento
for _ in range(100):
    probabilidade, impacto, risco, pontuacao_risco, recomendacoes = simular_dependencia()
    print(f"Probabilidade: {probabilidade:.2f}, Impacto: {impacto:.2f}, Risco: {risco:.2f}, Pontuação de Risco: {pontuacao_risco}, Recomendações: {recomendacoes}")