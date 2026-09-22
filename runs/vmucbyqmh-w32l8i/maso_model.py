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
        Normaliza métricas de recursos para o intervalo [0, 1].
        - eficiencia_energetica: kWh economizados por unidade (maior é melhor, ref: 0-1000)
        - circularidade_material: % de materiais reciclados/renováveis (0 a 100)
        - consumo_hidrico: m3 consumidos por unidade (menor é melhor, ref: inverso 0-50)
        """
        norm_energia = min(max(eficiencia_energetica / 1000.0, 0.0), 1.0)
        norm_circularidade = min(max(circularidade_material / 100.0, 0.0), 1.0)
        norm_hidrico = max(0.0, 1.0 - (consumo_hidrico / 50.0))
        
        return (norm_energia * 0.4) + (norm_circularidade * 0.4) + (norm_hidrico * 0.2)

    def normalize_ambiental(self, emissores_gee, residuos_perigosos, ecotoxicidade):
        """
        Normaliza pegada ambiental (menor impacto = maior score).
        - emissores_gee: toneladas CO2eq por ciclo (inverso, ref: 0-100 t)
        - residuos_perigosos: toneladas geradas (inverso, ref: 0-20 t)
        - ecotoxicidade: índice de impacto (0 a 10, inverso)
        """
        score_gee = max(0.0, 1.0 - (emissores_gee / 100.0))
        score_residuos = max(0.0, 1.0 - (residuos_perigosos / 20.0))
        score_tox = max(0.0, 1.0 - (ecotoxicidade / 10.0))
        
        return (score_gee * 0.5) + (score_residuos * 0.3) + (score_tox * 0.2)

    def normalize_social(self, empregos_locais, seguranca_trabalho, engajamento_comunitario):
        """
        Normaliza impacto social (maior é melhor).
        - empregos_locais: % da força de trabalho contratada localmente (0 a 100)
        - seguranca_trabalho: índice de conformidade em segurança (0 a 100)
        - engajamento_comunitario: score de satisfação/parcerias locais (0 a 10)
        """
        norm_empregos = min(max(empregos_locais / 100.0, 0.0), 1.0)
        norm_seguranca = min(max(seguranca_trabalho / 100.0, 0.0), 1.0)
        norm_engajamento = min(max(engajamento_comunitario / 10.0, 0.0), 1.0)
        
        return (norm_empregos * 0.3) + (norm_seguranca * 0.4) + (norm_engajamento * 0.3)

    def avaliar_projeto(self, nome, dados):
        score_rec = self.normalize_recursos(
            dados["eficiencia_energetica"], 
            dados["circularidade_material"], 
            dados["consumo_hidrico"]
        )
        score_amb = self.normalize_ambiental(
            dados["emissores_gee"], 
            dados["residuos_perigosos"], 
            dados["ecotoxicidade"]
        )
        score_soc = self.normalize_social(
            dados["empregos_locais"], 
            dados["seguranca_trabalho"], 
            dados["engajamento_comunitario"]
        )

        iso = (score_rec * self.weights["recursos"] + 
               score_amb * self.weights["ambiental"] + 
               score_soc * self.weights["social"]) * 100.0

        recomendacoes = self.gerar_recomendacoes(score_rec, score_amb, score_soc, dados)

        return {
            "projeto": nome,
            "iso_score": round(iso, 2),
            "subscores": {
                "uso_recursos": round(score_rec * 100, 2),
                "pegada_ambiental": round(score_amb * 100, 2),
                "impacto_social": round(score_soc * 100, 2)
            },
            "recomendacoes": recomendacoes
        }

    def gerar_recomendacoes(self, rec, amb, soc, dados):
        recs = []
        if rec < 0.6:
            recs.append("CRÍTICO (Recursos): Otimizar eficiência energética e aumentar o uso de insumos circulares para mitigar o esgotamento de recursos.")
        if amb < 0.6:
            recs.append("CRÍTICO (Ambiental): Implementar tecnologias de abatimento de emissões de GEE e plano rigoroso de redução de resíduos perigosos.")
        if soc < 0.6:
            recs.append("CRÍTICO (Social): Fortalecer políticas locais de contratação e revisar protocolos de segurança ocupacional.")
        if not recs:
            recs.append("MANUTENÇÃO: Projeto com alta sustentabilidade operacional. Manter monitoramento contínuo via auditorias trimestrais.")
        return recs

def test_maso_execution():
    modelo = MASOModel()

    # Cenário 1: Projeto de Inovação Tradicional (Alta pegada, baixo reuso)
    projeto_tradicional = {
        "eficiencia_energetica": 300.0,
        "circularidade_material": 15.0,
        "consumo_hidrico": 35.0,
        "emissores_gee": 75.0,
        "residuos_perigosos": 12.0,
        "ecotoxicidade": 6.5,
        "empregos_locais": 40.0,
        "seguranca_trabalho": 80.0,
        "engajamento_comunitario": 5.0
    }

    # Cenário 2: Projeto de Inovação Limpa e Circular
    projeto_sustentavel = {
        "eficiencia_energetica": 850.0,
        "circularidade_material": 85.0,
        "consumo_hidrico": 8.0,
        "emissores_gee": 10.0,
        "residuos_perigosos": 1.5,
        "ecotoxicidade": 1.0,
        "empregos_locais": 90.0,
        "seguranca_trabalho": 98.0,
        "engajamento_comunitario": 9.0
    }

    res1 = modelo.avaliar_projeto("Projeto Alfa (Industrial Tradicional)", projeto_tradicional)
    res2 = modelo.avaliar_projeto("Projeto Beta (Inovação Circular Limpa)", projeto_sustentavel)

    print("=== RESULTADOS DA AVALIAÇÃO MASO ===")
    print(json.dumps(res1, indent=2, ensure_ascii=False))
    print("-" * 40)
    print(json.dumps(res2, indent=2, ensure_ascii=False))

    # Validações estruturais e asserções
    assert res2["iso_score"] > res1["iso_score"], "Erro: O projeto sustentável deve possuir ISO superior ao tradicional."
    assert len(res1["recomendacoes"]) > 0, "O projeto tradicional deve gerar recomendações corretivas."
    print("\n[SUCESSO] O modelo executou corretamente, gerou pontuações normalizadas e produziu recomendações operacionais acionáveis.")

if __name__ == "__main__":
    try:
        test_maso_execution()
    except Exception as e:
        print(f"[FALHA DO EXPERIMENTO]: {e}")
        exit(1)