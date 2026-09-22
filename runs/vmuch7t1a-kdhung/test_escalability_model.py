import unittest

def calcular_iet(infra: float, arch: float, integram: float) -> float:
    """
    Calcula o Índice de Escalabilidade Tecnológica (IET) com base nos pesos definidos:
    Infraestrutura: 35%, Arquitetura: 40%, Integração: 25%.
    """
    w_infra = 0.35
    w_arch = 0.40
    w_integ = 0.25
    
    # Validação de limites (Equívoco comum: aceitar valores fora do intervalo 0-10)
    for val, nome in zip([infra, arch, integram], ['Infra', 'Arch', 'Integ']):
        if not (0.0 <= val <= 10.0):
            raise ValueError(f"O valor de {nome} ({val}) deve estar entre 0.0 e 10.0.")
            
    iet = (w_infra * infra) + (w_arch * arch) + (w_integ * integram)
    return round(iet, 2)

def determinar_status(iet: float) -> str:
    if iet >= 8.0:
        return "APROVADO"
    elif iet >= 6.0:
        return "APROVADO COM RESSALVAS"
    else:
        return "REPROVADO"

class TestModeloSucesoEscalabilidade(unittest.TestCase):
    
    def setUp(self):
        # 5 Cenários Piloto definidos para teste rigoroso do framework
        self.projetos_piloto = [
            {"id": "Projeto A (Monolito Legado)", "infra": 3.0, "arch": 2.5, "integ": 4.0},
            {"id": "Projeto B (Híbrido Parcialmente em Nuvem)", "infra": 6.5, "arch": 6.0, "integ": 7.0},
            {"id": "Projeto C (Microsserviços Modulares)", "infra": 8.5, "arch": 9.0, "integ": 8.0},
            {"id": "Projeto D (Serverless Orientado a Eventos)", "infra": 9.5, "arch": 9.5, "integ": 9.0},
            {"id": "Projeto E (Protótipo Rápido Monolítico)", "infra": 4.0, "arch": 5.0, "integ": 4.5}
        ]

    def test_calculo_projetos_piloto(self):
        resultados_esperados = {
            "Projeto A (Monolito Legado)": (3.0 * 0.35) + (2.5 * 0.40) + (4.0 * 0.25), # 3.05 -> REPROVADO
            "Projeto B (Híbrido Parcialmente em Nuvem)": (6.5 * 0.35) + (6.0 * 0.40) + (7.0 * 0.25), # 6.425 -> APROVADO COM RESSALVAS
            "Projeto C (Microsserviços Modulares)": (8.5 * 0.35) + (9.0 * 0.40) + (8.0 * 0.25), # 8.575 -> APROVADO
            "Projeto D (Serverless Orientado a Eventos)": (9.5 * 0.35) + (9.5 * 0.40) + (9.0 * 0.25), # 9.375 -> APROVADO
            "Projeto E (Protótipo Rápido Monolítico)": (4.0 * 0.35) + (5.0 * 0.40) + (4.5 * 0.25)  # 4.425 -> REPROVADO
        }

        print("\n--- EXECUTANDO VALIDAÇÃO DOS 5 PROJETOS PILOTO ---")
        for p in self.projetos_piloto:
            iet = calcular_iet(p["infra"], p["arch"], p["integ"])
            status = determinar_status(iet)
            esperado = round(resultados_esperados[p["id"]], 2)
            
            print(f"[{p['id']}] -> IET Calculado: {iet} | Status: {status}")
            self.assertEqual(iet, esperado)

    def test_contraexemplo_valores_invalidos(self):
        """Demonstra o tratamento de erro contra equívocos de entrada de dados fora do escopo."""
        print("\n--- TESTANDO CONTRAEXEMPLO DE ENTRADA INVÁLIDA ---")
        try:
            calcular_iet(11.0, 5.0, 5.0)
        except ValueError as e:
            print(f"Erro capturado com sucesso (comportamento esperado): {e}")
            self.assertTrue(True)
            return
        self.fail("Deveria ter lançado ValueError para entrada acima de 10.0")

if __name__ == '__main__':
    unittest.main()