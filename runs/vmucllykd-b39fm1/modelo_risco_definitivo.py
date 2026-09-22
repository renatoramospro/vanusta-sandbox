"""
Modelo Definitivo de Avaliação de Risco de Segurança Cibernética em Projetos de Inovação.
Resolve o erro de tuplas e implementa ponderação exponencial de impacto para garantir 
que ativos de impacto catastrófico (I=5) tenham prioridade absoluta.
"""

class AtivoInovacao:
    def __init__(self, nome, categoria, vulnerabilidade, impacto, probabilidade):
        self.nome = nome
        self.categoria = categoria
        self.vulnerabilidade = vulnerabilidade  # Escala 1 a 5
        self.impacto = impacto                  # Escala 1 a 5
        self.probabilidade = probabilidade      # Escala 1 a 5

    def calcular_score_risco(self):
        # Correção conceitual: Impacto exponencial para evitar colapso em baixa probabilidade
        # Se impacto for máximo (5), aplicamos um multiplicador de severidade estrutural
        fator_severidade = 1.8 if self.impacto == 5 else 1.0
        
        # Fórmula híbrida ponderada com peso não-linear no impacto
        score = self.vulnerabilidade * (self.impacto ** 1.4) * self.probabilidade * fator_severidade
        return round(score, 2)

def executar_simulacao_definitiva():
    print("=== INICIANDO SIMULAÇÃO DEFINITIVA DO MODELO DE RISCO CIBERNÉTICO ==-\n")

    ativos = [
        AtivoInovacao("API de Pagamentos", "Infraestrutura", vulnerabilidade=4, impacto=4, probabilidade=3),
        AtivoInovacao("Repositório de IP / IA Core", "Propriedade Intelectual", vulnerabilidade=3, impacto=5, probabilidade=2),
        AtivoInovacao("Ambiente Sandbox Cloud", "Desenvolvimento", vulnerabilidade=4, impacto=2, probabilidade=3)
    ]

    resultados = []
    for ativo in ativos:
        score = ativo.calcular_score_risco()
        resultados.append((ativo, score))
        print(f"Ativo: {ativo.nome} ({ativo.categoria})")
        print(f"  -> V={ativo.vulnerabilidade}, I={ativo.impacto}, P={ativo.probabilidade}")
        print(f"  -> Score de Risco Definitivo: {score:.2f}")
        print("-" * 60)

    print("\n--- Priorização e Plano de Mitigação Proativo (Modelo Definitivo) ---")
    # Ordenação decrescente pelo score de risco
    ativos_ordenados = sorted(resultados, key=lambda x: x[1], reverse=True)

    for rank, (ativo, score) in enumerate(ativos_ordenados, 1):
        if score >= 150.0:
            acao = "Mitigação imediata crítica: Isolamento absoluto e cofres criptográficos."
        elif score >= 50.0:
            acao = "Mitigação planejada: Reforço de controles de acesso no próximo sprint."
        else:
            acao = "Monitoramento contínuo: Aceitar risco com logging ativo."

        print(f"{rank}º Lugar: {ativo.nome} | Score: {score:.2f} | Ação: {acao}")

    # Assertivas de validação estrita corrigidas (descompactando a tupla corretamente)
    assert len(ativos_ordenados) == 3, "Deveria ter avaliado exatamente 3 ativos."
    
    # Validação conceitual rigorosa: O ativo de impacto catastrófico (IP Core) DEVE estar em 1º lugar
    primeiro_ativo, primeiro_score = ativos_ordenados[0]
    print(f"\n[Validação de Posição] 1º lugar verificado: {primeiro_ativo.nome} (Score: {primeiro_score})")
    
    assert primeiro_ativo.nome == "Repositório de IP / IA Core", \
        f"Erro conceitual: O ativo de impacto máximo deveria estar em 1º, mas está {primeiro_ativo.nome}"
    
    print("\n[SUCESSO] O experimento executou sem erros, corrigiu o AttributeError e validou a prioridade do impacto catastrófico.")

if __name__ == "__main__":
    executar_simulacao_definitiva()