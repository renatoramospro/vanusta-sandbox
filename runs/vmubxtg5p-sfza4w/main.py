def calcular_evm(pv, ev, ac):
    """
    Calcula os indicadores de Earned Value Management (EVM)
    evitando divisão por zero em cenários de dados nulos.
    """
    cpi = (ev / ac) if ac > 0 else 1.0
    spi = (ev / pv) if pv > 0 else 1.0
    
    if cpi < 0.95 and spi < 0.95:
        status = "CRÍTICO (Vermelho)"
    elif cpi < 0.95 or spi < 0.95:
        status = "ATENÇÃO (Amarelo)"
    else:
        status = "SAUDÁVEL (Verde)"
        
    return {
        'pv': pv,
        'ev': ev,
        'ac': ac,
        'cpi': round(cpi, 2),
        'spi': round(spi, 2),
        'status': status
    }

def testar_cenarios():
    # Cenário 1: Projeto Saudável
    res1 = calcular_evm(pv=10000, ev=10000, ac=10000)
    assert res1['status'] == "SAUDÁVEL (Verde)", f"Falha no cenário saudável: {res1}"
    assert res1['cpi'] == 1.0
    assert res1['spi'] == 1.0

    # Cenário 2: Estouro de Custo (AC maior que EV)
    res2 = calcular_evm(pv=10000, ev=8000, ac=12000)
    assert res2['cpi'] < 1.0, f"CPI deveria ser < 1.0, foi {res2['cpi']}"
    assert res2['status'] == "CRÍTICO (Vermelho)", f"Status incorreto: {res2['status']}"

    # Cenário 3: Dados Nulos / Sem Orçamento Alocado (Tratamento de divisão por zero)
    res3 = calcular_evm(pv=0, ev=0, ac=0)
    assert res3['cpi'] == 1.0, "Deveria tratar AC=0 sem quebrar a aplicação"
    assert res3['spi'] == 1.0, "Deveria tratar PV=0 sem quebrar a aplicação"

    print("=== TODOS OS TESTES EXECUTADOS COM SUCESSO ===")
    print(f"Cenário 1 (Saudável): {res1}")
    print(f"Cenário 2 (Crítico/Estouro): {res2}")
    print(f"Cenário 3 (Dados Nulos): {res3}")

if __name__ == "__main__":
    testar_cenarios()