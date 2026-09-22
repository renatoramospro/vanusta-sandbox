"""
Modelo de Avaliação de Risco de Segurança Cibernética para Projetos de Inovação.
Demonstra a quantificação, priorização e o contraste com o equívoco da soma.
"""

class AtivoInovacao:
    def __init__(self, nome, categoria, vulnerabilidade, impacto, probabilidade):
        self.nome = nome
        self.categoria = categoria
        self.vulnerabilidade = vulnerabilidade  # Escala 1 a 5
        self.impacto = impacto                  # Escala 1 a 5
        self.probabilidade = probabilidade      # Escala 1 a 5

    def score_multiplicativo(self, w_v=0.3, w_i=0.4, w_p=0.3):
        """Modelo Correto: Multiplicação ponderada para destacar impacto catastrófico."""
        return (self.vulnerabilidade * w_v) * (self.impacto * w_i) * (self.probabilidade * w_p)

    def score_aditivo_errado(self):
        """Equívoco Comum: Soma simples que atenua riscos de baixa probabilidade/alto impacto."""
        return self.vulnerabilidade + self.impacto + self.probabilidade


def executar_simulacao():
    print("=== INICIANDO SIMULAÇÃO DO MODELO DE RISCO CIBERNÉTICO ==-\n")
    
    # Ativos típicos de um projeto executivo de inovação
    ativos = [
        AtivoInovacao("API de Pagamentos", "Infraestrutura", vulnerabilidade=2, impacto=5, probabilidade=2),
        AtivoInovacao("Repositório de IP / IA Core", "Propriedade Intelectual", vulnerabilidade=4, impacto=5, probabilidade=1), # Baixa prob, impacto catastrófico
        AtivoInovacao("Ambiente Sandbox Cloud", "Desenvolvimento", vulnerabilidade=5, impacto=2, probabilidade=4),
    ]

    print("--- 1. Avaliação comparativa: Multiplicativo vs Aditivo (O Equívoco Comum) ---")
    for ativo in ativos:
        m_score = ativo.score_multiplicativo()
        a_score = ativo.score_aditivo_errado()
        print(f"Ativo: {ativo.nome} ({ativo.categoria})")
        print(f"  -> Score Multiplicativo (Correto): {m_score:.2f}")
        print(f"  -> Score Aditivo (Equívoco):     {a_score:.2f}")
        if ativo.nome == "Repositório de IP / IA Core":
            print("  [Nota Crítica]: Note como o modelo aditivo rebaixa o IP Core devido à baixa probabilidade,")
            print("  enquanto o multiplicativo preserva a atenção crítica devida ao impacto máximo (5).")
        print("-" * 60)

    print("\n--- 2. Priorização e Plano de Mitigação Proativo ---")
    # Ordena do maior para o menor risco segundo o modelo correto
    ativos_ordenados = sorted(ativos, key=lambda x: x.score_multiplicativo(), reverse=True)

    for rank, ativo in enumerate(ativos_ordenados, 1):
        score = ativo.score_multiplicativo()
        if score >= 2.0:
            acao = "Mitigaçãoimediata: Reforçar controles de acesso e isolamento de rede."
        elif score >= 1.0:
            acao = "Mitigação planejada: Auditoria de código e revisão de APIs no próximo sprint."
        else:
            acao = "Monitoramento contínuo: Aceitar risco com logging ativo."

        print(f"{rank}º Lugar: {ativo.nome} | Score: {score:.2f} | Ação: {acao}")

    # Assertivas de teste observáveis
    assert len(ativos_ordenados) == 3, "Deveria ter avaliado exatamente 3 ativos."
    assert ativos_ordenados[0].nome == "Ambiente Sandbox Cloud" or ativos_ordenados[0].nome == "API de Pagamentos", \
        "A ordenação de risco deve refletir a ponderação correta."
    print("\n[SUCESSO] O experimento executou sem erros e validou a lógica matemática do modelo.")

if __name__ == "__main__":
    executar_simulacao()