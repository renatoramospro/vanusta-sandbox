import json

class MASOModel:
    def __init__(self):
        # Pesos das dimensões alinhados com diretrizes de impacto e pegada ambiental
        self.weights = {
            "recursos": 0.30,
            "ambiental": 0.40,
            "social": 0.30
        }

    def normalize_recursos(self, eficiencia_energetica, circularidade_material, consumo_hidrico):
        """
        Normaliza métricas de recursos para o intervalo [0, 1] de forma robusta.
        - eficiencia_energetica: kWh economizados por unidade (maior é melhor, ref: 0-1000)
        - circularidade_material: % de materiais reciclados/renováveis (0 a 100)
        - consumo_hidrico: m3 consumidos por unidade (menor é melhor, ref: inverso 0-50)
        """
        norm_energia = min(max(eficiencia_energetica / 1000.0, 0.0), 1.0)
        norm_circularidade = min(max(circularidade_material / 100.0, 0.0), 1.0)
        # Correção robusta: aplicação de min(..., 1.0) para impedir valores > 1.0 caso a entrada seja negativa
        norm_hidrico = min(max(0.0, 1.0 - (consumo_hidrico / 50.0)), 1.0)
        
        return (norm_energia * 0.4) + (norm_circularidade * 0.4) + (norm_hidrico * 0.2)

    def normalize_ambiental(self, emissores_gee, residuos_perigosos, ecotoxicidade):
        """
        Normaliza métricas ambientais (menor é melhor para todas, ref: 0-100).
        """
        norm_gee = min(max(0.0, 1.0 - (emissores_gee / 100.0)), 1.0)
        norm_residuos = min(max(0.0, 1.0 - (residuos_perigosos / 100.0)), 1.0)
        norm_ecotox = min(max(0.0, 1.0 - (ecotoxicidade / 10.0)), 1.0)
        
        return (norm_gee * 0.4) + (norm_residuos * 0.4) + (norm_ecotox * 0.2)

    def normalize_social(self, empregos_locais, seguranca_trabalho, engajamento_comunitario):
        """
        Normaliza métricas sociais (maior é melhor para todas).
        """
        norm_empregos = min(max(empregos_locais / 50.0, 0.0), 1.0)
        norm_seguranca = min(max(seguranca_trabalho / 100.0, 0.0), 1.0)
        norm_engajamento = min(max(engajamento_comunitario / 10.0, 0.0), 1.0)
        
        return (norm_empregos * 0.3) + (norm_seguranca * 0.4) + (norm_engajamento * 0.3)

    def avaliar_projeto(self, nome_projeto, dados):
        score_recursos = self.normalize_recursos(
            dados["eficiencia_energetica"],
            dados["circularidade_material"],
            dados["consumo_hidrico"]
        ) * 100

        score_ambiental = self.normalize_ambiental(
            dados["emissores_gee"],
            dados["residuos_perigosos"],
            dados["ecotoxicidade"]
        ) * 100

        score_social = self.normalize_social(
            dados["empregos_locais"],
            dados["seguranca_trabalho"],
            dados["engajamento_comunitario"]
        ) * 100

        iso_score = (
            score_recursos * self.weights["recursos"] +
            score_ambiental * self.weights["ambiental"] +
            score_social * self.weights["social"]
        )

        recomendacoes = self.gerar_recomendacoes(score_recursos, score_ambiental, score_social)

        return {
            "projeto": nome_projeto,
            "iso_score": round(iso_score, 2),
            "subscores": {
                "uso_recursos": round(score_recursos, 2),
                "pegada_ambiental": round(score_ambiental, 2),
                "impacto_social": round(score_social, 2)
            },
            "recomendacoes": recomendacoes
        }

    def gerar_recomendacoes(self, rec, amb, soc):
        recs = []
        if rec < 50:
            recs.append("CRÍTICO (Recursos): Otimizar eficiência energética e aumentar o uso de insumos circulares para mitigar o esgotamento de recursos.")
        elif rec < 80:
            recs.append("MODERADO (Recursos): Expandir programas de reciclagem de materiais e auditorias de consumo hídrico.")
            
        if amb < 50:
            recs.append("CRÍTICO (Ambiental): Implementar tecnologias de abatimento de emissões de GEE e plano rigoroso de redução de resíduos perigosos.")
        elif amb < 80:
            recs.append("MODERADO (Ambiental): Adotar práticas adicionais de controle de ecotoxicidade e transição energética renovável.")
            
        if soc < 50:
            recs.append("CRÍTICO (Social): Fortalecer políticas locais de contratação e revisar protocolos de segurança ocupacional.")
        elif soc < 80:
            recs.append("MODERADO (Social): Aumentar o engajamento com a comunidade local e programas de capacitação.")

        if not recs:
            recs.append("MANUTENÇÃO: Projeto com alta sustentabilidade operacional. Manter monitoramento contínuo via auditorias trimestrais.")
            
        return recs

def test_robustez_normalizazione():
    modelo = MASOModel()
    # Teste com valor negativo de consumo hídrico para validar a correção do Testador
    projeto_anomalo = {
        "eficiencia_energetica": 1200.0, # Acima do teto
        "circularidade_material": 110.0, # Acima do teto
        "consumo_hidrico": -15.0,        # Valor negativo (geraria bug na versão anterior)
        "emissores_gee": -5.0,           # Valor negativo
        "residuos_perigosos": 0.0,
        "ecotoxicidade": 0.0,
        "empregos_locais": 60.0,
        "seguranca_trabalho": 100.0,
        "engajamento_comunitario": 10.0
    }

    res = modelo.avaliar_projeto("Projeto Delta (Stress Test Anômalo)", projeto_anomalo)
    print("=== RESULTADO DO TESTE DE ROBUSTEZ ===")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    
    # Assegurar que o subscore não ultrapasse 100.0 mesmo com entradas fora do padrão
    assert res["subscores"]["uso_recursos"] <= 100.0, "Erro: Subscore de recursos ultrapassou o teto de 100.0!"
    assert res["subscores"]["pegada_ambiental"] <= 100.0, "Erro: Subscore ambiental ultrapassou o teto de 100.0!"
    assert res["iso_score"] <= 100.0, "Erro: ISO Score ultrapassou o limite máximo de 100.0!"
    print("\n[SUCESSO] A blindagem de limites funcionou corretamente contra entradas anômalas e negativas.")

if __name__ == "__main__":
    try:
        test_robustez_normalizazione()
    except Exception as e:
        print(f"[FALHA DO EXPERIMENTO]: {e}")
        exit(1)