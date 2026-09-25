import unittest
from main import Coordenador, Participante

class TesteProtocolo2PC(unittest.TestCase):
    def test_comit(self):
        coordenador = Coordenador([Participante("Participante 1"), Participante("Participante 2")])
        coordenador.preparar()
        coordenador.comitar()
        self.assertTrue(all(participante.preparado for participante in coordenador.participantes))

    def test_abort(self):
        coordenador = Coordenador([Participante("Participante 1"), Participante("Participante 2")])
        coordenador.preparar()
        coordenador.abortar()
        self.assertFalse(all(participante.preparado for participante in coordenador.participantes))

if __name__ == "__main__":
    unittest.main()