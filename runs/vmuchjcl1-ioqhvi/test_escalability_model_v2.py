import unittest

def calcular_iet_com_veto(infra: float, arch: float, integram: float) -> tuple[float, str]:
    """
    Calcula o Índice de Escalabilidade Tecnológica (IET) aplicando pesos e regra de veto:
    - Infraestrutura: 35% (W1 = 0.35)
    - Arquitetura: 40% (W2 = 0.40)
    - Integração: 25% (W3 = 0.25)
    
    Regra de Veto: Se qualquer dimensão for inferior a 4.0, o projeto é REPROVADO.
    """
    w_infra = 0.35
    w_arch = 0.40
    w_integ = 0.25
    
    # 1. Validação estrita de limites de entrada (0.0 a 10.0)
    for val, nome in zip([infra, arch, integram], ['Infra', 'Arch', 'Integ']):
        if not (0.0 <= val <= 10.0):
            raise ValueError(f"O valor de {nome} ({val}) deve estar entre 0.0 e 10.0.")
            
    # 2. Aplicação da Regra de Veto (Correção estrutural solicitada pelo Testador)
    limiar_veto = 4.0
    if infra < limiar_veto or arch < limiar_veto or integram < limiar_veto:
        iet_parcial = (w_infra * infra) + (w_arch * arch) + (w_integ * integram)
        return round(iet_parcial, 2), "REPROVADO (Acionado Mecanismo de Veto por Dimensão Crítica)"

    # 3. Cálculo padrão de média ponderada
    iet = (w_infra * infra) + (w_arch * arch) + (w_integ * integram)
    iet_arredondado = round(iet, 2)
    
    # 4. Limiares de Decisão Executiva
    if iet_arredondado >= 8.0:
        status = "APROVADO"
    elif 6.0 <= iet_arredondado < 8.0:
        status = "APROVADO COM RESSALVAS"
    else:
        status = "REPROVADO"
        
    return iet_arredondado, status


class TestModeloScomVeto(unittest.TestCase):
    
    def test_cenario_adversarial_veto_arquitetura(self):
        # Cenário adversarial: Infra e Integração excelentes, mas Arquitetura zerada (0.0)
        # Pela média linear antiga, daria 6.55 (Aprovado com ressalvas). Agora deve ser REPROVADO via Veto.
        infra, arch, integ = 9.0, 0.0, 9.0
        iet, status = calcular_iet_com_veto(infra, arch, integ)
        self.assertIn("REPROVADO", status)
        self.assertIn("Veto", status)

    def test_cenario_limiar_minimo_veto(self):
        # Exatamente no limiar de veto (3.9 em Integração)
        infra, arch, integ = 8.0, 8.0, 3.9
        iet, status = calcular_iet_com_veto(infra, arch, integ)
        self.assertIn("REPROVADO", status)

    def test_cenario_aprovado_sem_veto(self):
        # Todas as notas acima de 4.0, IET alto
        infra, arch, integ = 8.5, 9.0, 8.0
        iet, status = calcular_iet_com_veto(infra, arch, integ)
        self.assertEqual(status, "APROVADO")
        self.assertGreaterEqual(iet, 8.0)

    def test_validacao_limites_entrada(self):
        # Garante que valores inválidos continuam gerando exceção
        with self.assertRaises(ValueError):
            calcular_iet_com_veto(10.5, 5.0, 5.0)


if __name__ == '__main__':
    unittest.main()