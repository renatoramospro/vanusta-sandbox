import random

# Configuração fixa para reprodutibilidade dos dados sintéticos
random.seed(42)

def calcular_ivf(criticidade, exclusividade, lead_time, saude_financeira):
    """
    Calcula o Índice de Vulnerabilidade de Fornecedores (IVF) de 0 a 100.
    Pesos calibrados: 
    - Criticidade (w1 = 0.30)
    - Exclusividade (w2 = 0.30)
    - Lead Time (w3 = 0.20)
    - Saúde Financeira (w4 = 0.20)
    """
    w1, w2, w3, w4 = 0.30, 0.30, 0.20, 0.20
    
    ivf = 100 * (
        (w1 * criticidade) + 
        (w2 * exclusividade) + 
        (w3 * lead_time) + 
        (w4 * saude_financeira)
    )
    return round(ivf, 2)

def gerar_recomendacao_mitigacao(ivf, exclusividade, saude_financeira):
    """
    Evita o equívoco de recomendações genéricas, vinculando a mitigação 
    diretamente à causa raiz da vulnerabilidade.
    """
    if ivf >= 70:
        acoes = []
        if exclusividade > 0.7:
            acoes.append("Implementar programa de P&D interno ou coinovação para reduzir dependência de IP exclusiva.")
            acoes.append("Desenvolver fornecedor alternativo (Dual Sourcing) mesmo com custo inicial de transição.")
        if saude_financeira > 0.6:
            acoes.append("Exigir garantias financeiras contratuais ou monitoramento trimestral de balanço do fornecedor.")
        if not acoes:
            acoes.append("Estabelecer estoque de segurança crítico para componentes de alto lead time.")
        return "CRÍTICO: " + " | ".join(acoes)
    elif ivf >= 40:
        return "MÉDIO: Monitorar prazos de entrega e manter contato regular com fornecedores secundários."
    else:
        return "BAIXO: Manter processos padrão de gestão de suprimentos."

def executar_simulacao_projetos():
    print("=== INICIANDO SIMULAÇÃO DE VALIDAÇÃO DO MODELO (30 PROJETOS PILOTO) ===\n")
    
    projetos = []
    acertos_criticos = corretos_historico = 0
    total_projetos_criticos_reais = 0
    
    # Gerando 30 projetos piloto sintéticos com histórico conhecido de falha de suprimento
    for i in range(1, 31):
        # Simula variáveis de entrada entre 0.0 e 1.0
        cc = round(random.uniform(0.1, 1.0), 2)
        et = round(random.uniform(0.1, 1.0), 2)
        lt = round(random.uniform(0.1, 1.0), 2)
        fs = round(random.uniform(0.1, 1.0), 2)
        
        ivf = calcular_ivf(cc, et, lt, fs)
        
        # Critério real histórico: projetos com alta exclusividade e criticidade falharam por suprimento (True/False)
        falha_historica_real = True if (cc * et) > 0.45 else False
        
        if falha_historica_real:
            total_projetos_criticos_reais += 1
            # O modelo classifica como crítico se IVF >= 70.0
            if ivf >= 70.0:
                acertos_criticos += 1

        recomendacao = gerar_recomendacao_mitigacao(ivf, et, fs)
        
        projetos.append({
            "id": f"PRJ-{i:02d}",
            "ivf": ivf,
            "falha_real": falha_historica_real,
            "recomendacao": recomendacao
        })

    # Cálculo da taxa de identificação de risco crítico
    taxa_deteccao = (acertos_criticos / total_projetos_criticos_reais) * 100 if total_projetos_criticos_reais > 0 else 0

    print(f"Total de projetos analisados: 30")
    print(f"Projetos com risco crítico real no histórico: {total_projetos_criticos_reais}")
    print(f"Projetos críticos identificados corretamente pelo modelo (IVF >= 70): {acertos_criticos}")
    print(f"Taxa de Identificação de Risco Crítico: {taxa_deteccao:.1f}%\n")

    # Demonstração de relatório de mitigação para os 3 primeiros projetos
    print("=== AMOSTRA DE RELATÓRIOS DE MITIGAÇÃO GERADOS ===")
    for p in projetos[:3]:
        print(f"[{p['id']}] IVF: {p['ivf']} | Recomendação: {p['recomendacao']}")

    # Validação do Critério de Sucesso (> 80%)
    assert taxa_deteccao >= 80.0, f"Falha no critério de sucesso: Taxa de detecção de {taxa_deteccao:.1f}% é inferior à meta de 80%."
    print("\n[SUCESSO] O modelo atingiu o critério de validação exigido (>= 80% de identificação de risco crítico).")

if __name__ == "__main__":
    executar_simulacao_projetos()