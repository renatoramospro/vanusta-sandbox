from analyzer import run_analysis
import pipeline_scenarios

# Configuração do Analisador
# Definimos o que é perigoso no nosso ecossistema de agentes
UNSAFE_SINKS = ["web_agent.search", "external_api.send"]
SOURCES = ["get_user_secret"]

def test_suite():
    # Pegamos o código fonte do arquivo de cenários para análise estática
    import inspect
    code = inspect.getsource(pipeline_scenarios)
    
    print("--- Iniciando Análise Estática de Pipeline ---")
    leaks = run_analysis(code, UNSAFE_SINKS, SOURCES)
    
    # Resultados esperados baseados em pipeline_scenarios.py:
    # 1. web_agent.search(secret) -> Linha ~13
    # 2. web_agent.search(processed_data) -> Linha ~17
    # 3. external_api.send(user_context) -> Linha ~23
    
    expected_leaks_count = 3
    
    print(f"Análise concluída. Vazamentos detectados: {len(leaks)}")
    for leak in leaks:
        print(f"  [!] ALERTA: Vazamento na linha {leak['line']}: Variável '{leak['variable']}' atingiu o sink '{leak['sink']}'")

    # Validação do Critério de Sucesso (Simplificado para o experimento)
    if len(leaks) == expected_leaks_count:
        print("\n[RESULTADO] SUCESSO: Todos os vazamentos conhecidos foram detectados.")
        return True
    else:
        print(f"\n[RESULTADO] FALHA: Detectados {len(leaks)} vazamentos, esperados {expected_leaks_count}.")
        return False

if __name__ == "__main__":
    success = test_suite()
    if not success:
        exit(1)
    exit(0)