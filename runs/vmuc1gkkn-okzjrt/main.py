def calcular_indice_sucesso_gmo(taxa_adocao: float, indice_proficiencia: float, satisfacao_stakeholders: float) -> dict:
    """
    Calcula o Índice de Sucesso de GMO com base em três pilares fundamentais:
    1. Taxa de Adoção (Meta mínima: 80% ou +20% sobre o legado)
    2. Índice de Proficiência (Meta mínima: 80%)
    3. Satisfação de Stakeholders pós-implementação (Meta mínima: 80%)
    """
    score_geral = (taxa_adocao * 0.4 + indice_proficiencia * 0.3 + satisfacao_stakeholders * 0.3) * 100
    
    # Critérios de sucesso da missão: Satisfação > 80% e adoção alinhada
    aprovado = (taxa_adocao >= 0.80) and (indice_proficiencia >= 0.80) and (satisfacao_stakeholders >= 0.80)
    
    return {
        "score_geral": round(score_geral, 2),
        "status_aprovado": aprovado,
        "detalhes": {
            "adocao": taxa_adocao,
            "proficiencia": indice_proficiencia,
            "satisfacao": satisfacao_stakeholders
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