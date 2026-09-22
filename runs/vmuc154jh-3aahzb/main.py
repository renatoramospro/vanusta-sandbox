path=governance_test.py
def calcular_indice_sucesso_gmo(taxa_adocao: float, indice_proficiencia: float, satisfacao_stakeholder: float) -> dict:
    """
    Calcula se o projeto atinge os critérios de sucesso ajustados para a missão de aprendizagem:
    - Taxa de adoção >= 85%
    - Índice de proficiência >= 80%
    - Satisfação de stakeholders >= 80%
    """
    sucesso_adocao = taxa_adocao >= 0.85
    sucesso_proficiencia = indice_proficiencia >= 0.80
    sucesso_satisfacao = satisfacao_stakeholder >= 0.80
    
    score_geral = (taxa_adocao + indice_proficiencia + satisfacao_stakeholder) / 3.0
    aprovado = sucesso_adocao and sucesso_proficiencia and sucesso_satisfacao
    
    return {
        "score_geral": round(score_geral * 100, 2),
        "status_aprovado": aprovado,
        "detalhes": {
            "adocao": sucesso_adocao,
            "proficiencia": sucesso_proficiencia,
            "satisfacao": sucesso_satisfacao
        }
    }

def testar_modelo_governanca():
    print("Iniciando simulação do Modelo de Governança de Mudança Organizacional...")
    
    # Cenário 1: Projeto com falha no Middle Management (resistência e baixa adoção)
    cenario_falha = calcular_indice_sucesso_gmo(0.70, 0.75, 0.65)
    print(f"Cenário 1 (Piloto com resistência não mitigada): Score={cenario_falha['score_geral']}%, Aprovado={cenario_falha['status_aprovado']}")
    assert cenario_falha['status_aprovado'] is False, "O cenário de falha deveria ser reprovado."

    # Cenário 2: Projeto com aplicação correta do framework de GMO (Piloto bem-sucedido)
    cenario_sucesso = calcular_indice_sucesso_gmo(0.90, 0.85, 0.88)
    print(f"Cenário 2 (Piloto com governança e GMO ativas): Score={cenario_sucesso['score_geral']}%, Aprovado={cenario_sucesso['status_aprovado']}")
    assert cenario_sucesso['status_aprovado'] is True, "O cenário de sucesso deveria ser aprovado."

    print("Todos os testes de validação do modelo de governança passaram com sucesso!")

if __name__ == "__main__":
    testar_modelo_governanca()