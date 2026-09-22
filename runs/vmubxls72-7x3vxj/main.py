path=validador_evm.py
import pandas as pd
import numpy as np

def simular_projeto_evm(nome_cenario, dados_brutos):
    """
    Simula o cálculo de Earned Value Management (EVM) para validar
    a integridade dos índices CPI, SPI e detecção de desvios.
    """
    df = pd.DataFrame(dados_brutos)
    
    # Agregações globais para o projeto no período
    pv = df['ValorPlanejado'].sum()
    ev = df['ValorAgregado'].sum()
    ac = df['CustoReal'].sum()
    
    # Tratamento de divisão por zero (mitigação do equívoco de dados zerados)
    cpi = ev / ac if ac > 0 else 1.0
    spi = ev / pv if pv > 0 else 1.0
    
    # Regra de Alerta de Desvio
    if cpi < 0.90 or spi < 0.90:
        status = "CRÍTICO (Vermelho)"
    elif cpi < 1.00 or spi < 1.00:
        status = "ATENÇÃO (Amarelo)"
    else:
        status = "SAUDÁVEL (Verde)"
        
    print(f"--- Cenário: {nome_cenario} ---")
    print(f"  PV (Valor Planejado): R$ {pv:,.2f}")
    print(f"  EV (Valor Agregado):  R$ {ev:,.2f}")
    print(f"  AC (Custo Real):      R$ {ac:,.2f}")
    print(f"  CPI (Custo):          {cpi:.2f}")
    print(f"  SPI (Prazo):          {spi:.2f}")
    print(f"  Status do Dashboard:  {status}\n")
    
    return {'cpi': cpi, 'spi': spi, 'status': status}

# 1. Cenário Ideal / Saudável
cenario_saudavel = [
    {'ValorPlanejado': 10000, 'ValorAgregado': 10000, 'CustoReal': 9500},
    {'ValorPlanejado': 15000, 'ValorAgregado': 15000, 'CustoReal': 14800}
]

# 2. Cenário com Estouro de Custo (AC > EV)
cenario_estouro_custo = [
    {'ValorPlanejado': 10000, 'ValorAgregado': 8000, 'CustoReal': 12000},
    {'ValorPlanejado': 15000, 'ValorAgregado': 12000, 'CustoReal': 18000}
]

# 3. Cenário com Atraso Crítico e Dados Ausentes (Teste de Robustez)
cenario_atraso_extremo = [
    {'ValorPlanejado': 20000, 'ValorAgregado': 10000, 'CustoReal': 10000},
    {'ValorPlanejado': 0,     'ValorAgregado': 0,     'CustoReal': 0} # Projeto sem custo alocado / zero
]

# Execução das simulações
res1 = simular_projeto_evm("Projeto Saudável", cenario_saudavel)
res2 = simular_projeto_evm("Projeto com Estouro de Custo", cenario_estouro_custo)
res3 = simular_projeto_extremo = simular_projeto_evm("Projeto com Atraso e Dados Nulos", cenario_atraso_extremo)

# Asserções para garantir o comportamento correto do modelo
assert res1['status'] == "SAUDÁVEL (Verde)", "Erro na lógica do cenário saudável"
assert res2['cpi'] < 1.0, "CPI deveria indicar estouro de custo"
assert res3['spi'] < 1.0, "SPI deveria indicar atraso"

print("Validação lógica dos indicadores EVM concluída com sucesso absoluto!")