import json
import sys

def calcular_infracost_diff(custo_base: float, custo_atual: float) -> dict:
    """
    Simula a análise de diff do Infracost entre o estado base e o estado proposto.
    """
    delta = custo_atual - custo_base
    percentual = (delta / custo_base * 100) if custo_base > 0 else (100.0 if custo_atual > 0 else 0.0)
    return {
        "custo_base": custo_base,
        "custo_atual": custo_atual,
        "delta": delta,
        "percentual": round(percentual, 2)
    }

def gerar_comentario_markdown(analise: dict) -> str:
    """
    Gera a tabela formatada em Markdown idêntica à produzida por 'infracost comment'.
    Cobre o requisito de documentação dinâmica em PRs.
    """
    sinal = "+" if analise["delta"] >= 0 else ""
    md = f"""### 💰 Infracost Relatório de Impacto Financeiro

| Projeto | Custo Base | Custo Atual | Variação ($) | Variação (%) |
| :--- | :--- | :--- | :--- | :--- |
| **terraform/prod** | ${analise['custo_base']:.2f}/mês | ${analise['custo_atual']:.2f}/mês | {sinal}${analise['delta']:.2f} | {sinal}{analise['percentual']}% |

> **Nota:** Este comentário é atualizado automaticamente a cada commit enviado para este Pull Request.
"""
    return md

def aplicar_guardrail(analise: dict, limite_absoluto: float, limite_percentual: float) -> bool:
    """
    Aplica políticas de controle (Guardrails).
    Retorna True se o orçamento foi violado (deve bloquear o PR), False caso contrário.
    """
    violacao_absoluta = analise["delta"] > limite_absoluto
    violacao_percentual = analise["percentual"] > limite_percentual
    return violacao_absoluta or violacao_percentual

if __name__ == "__main__":
    print("=== EXECUTANDO SIMULAÇÃO DE INFRACOST CI/CD ===")
    
    # Cenário de Teste: Adição de recursos custosos na AWS via Terraform
    custo_base_projeto = 500.00  # Custo atual em produção ($)
    custo_proposto_projeto = 650.00  # Custo após o PR ($)
    
    # Limites definidos pela governança (Guardrails)
    ORCAMENTO_LIMITE_DELTA_USD = 100.00  # Não pode aumentar mais que $100
    ORCAMENTO_LIMITE_PERCENTUAL = 15.00  # Não pode aumentar mais que 15%
    
    analise = calcular_infracost_diff(custo_base_projeto, custo_proposto_projeto)
    print(f"\nResultado da Análise:")
    print(json.dumps(analise, indent=2))
    
    comentario_pr = gerar_comentario_markdown(analise)
    print(f"\n[Mock GitHub API] Comentário gerado para o Pull Request:\n")
    print(comentario_pr)
    
    bloquear_merge = aplicar_guardrail(analise, ORCAMENTO_LIMITE_DELTA_USD, ORCAMENTO_LIMITE_PERCENTUAL)
    print(f"Avaliação de Guardrail (Limite Absoluto: ${ORCAMENTO_LIMITE_DELTA_USD}, Limite %: {ORCAMENTO_LIMITE_PERCENTUAL}%):")
    
    if bloquear_merge:
        print(f"❌ FALHA: A variação de custo (${analise['delta']}) excedeu o limite permitido de orçamento!")
        print("Ação de CI/CD: Bloqueando o merge do Pull Request (Exit Code 1).")
        # Em um pipeline real, usaríamos sys.exit(1) para falhar o job.
    else:
        print("✅ APROVADO: A mudança está dentro do orçamento financeiro.")
        sys.exit(0)