import unittest
from main import Coordenador, Participante

class TesteCoordenador(unittest.TestCase):
    def test_falha_participante(self):
        coordenador = Coordenador([Participante("Participante 1"), Participante("Participante 2")])
        coordenador.preparar()
        coordenador.falhar_participante()
        for participante in coordenador.participantes:
            self.assertFalse(participante.preparado)
            self.assertFalse(participante.comitado)

if __name__ == "__main__":
    unittest.main()