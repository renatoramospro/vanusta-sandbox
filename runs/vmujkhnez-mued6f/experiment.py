import hashlib
import unittest

class BencodeDecodeError(Exception):
    """Exceção lançada para dados Bencode mal-formados."""
    pass

class BencodeDecoder:
    def __init__(self, data: bytes):
        self.data = data
        self.index = 0

    def decode(self):
        if self.index >= len(self.data):
            raise BencodeDecodeError("Dados insuficientes para decodificação.")
        
        char = self.data[self.index:self.index+1]
        if char == b'i':
            return self._decode_int()
        elif char == b'l':
            return self._decode_list()
        elif char == b'd':
            return self._decode_dict()
        elif char.isdigit():
            return self._decode_string()
        else:
            raise BencodeDecodeError(f"Caractere desconhecido ou inválido no índice {self.index}: {char}")

    def _decode_int(self):
        self.index += 1  # pula 'i'
        try:
            e_idx = self.data.index(b'e', self.index)
        except ValueError:
            raise BencodeDecodeError("Inteiro Bencode não terminando em 'e'.")
        
        int_bytes = self.data[self.index:e_idx]
        
        # Validação contra zeros à esquerda (ex: i03e) e -0 (i-0e)
        if len(int_bytes) > 1 and int_bytes[0] == ord(b'0'):
            raise BencodeDecodeError("Inteiro Bencode com zero à esquerda inválido.")
        if len(int_bytes) > 2 and int_bytes[0:2] == b'-0':
            raise BencodeDecodeError("Inteiro Bencode -0 inválido.")
        if int_bytes == b'-':
            raise BencodeDecodeError("Inteiro Bencode inválido '-' isolado.")

        try:
            val = int(int_bytes.decode('ascii'))
        except UnicodeDecodeError:
            raise BencodeDecodeError("Inteiro Bencode contém bytes não-ASCII.")
        except ValueError:
            raise BencodeDecodeError(f"Inteiro Bencode inválido: {int_bytes}")

        self.index = e_idx + 1
        return val

    def _decode_string(self):
        colon_idx = self.data.find(b':', self.index)
        if colon_idx == -1:
            raise BencodeDecodeError("String Bencode sem delimitador ':' encontrado.")
        
        len_str_bytes = self.data[self.index:colon_idx]
        if len(len_str_bytes) > 1 and len_str_bytes[0] == ord(b'0'):
            raise BencodeDecodeError("Comprimento de string Bencode com zero à esquerda inválido.")
        
        try:
            str_len = int(len_str_bytes.decode('ascii'))
        except ValueError:
            raise BencodeDecodeError(f"Comprimento de string inválido: {len_str_bytes}")

        self.index = colon_idx + 1
        end_idx = self.index + str_len
        
        if end_idx > len(self.data):
            raise BencodeDecodeError("String Bencode excede o tamanho dos dados fornecidos.")

        val = self.data[self.index:end_idx]
        self.index = end_idx
        return val

    def _decode_list(self):
        self.index += 1  # pula 'l'
        lst = []
        while self.index < len(self.data):
            if self.data[self.index:self.index+1] == b'e':
                self.index += 1
                return lst
            lst.append(self.decode())
        raise BencodeDecodeError("Lista Bencode não terminada em 'e'.")

    def _decode_dict(self):
        self.index += 1  # pula 'd'
        d = {}
        last_key = None
        while self.index < len(self.data):
            if self.data[self.index:self.index+1] == b'e':
                self.index += 1
                return d
            
            key = self.decode()
            if not isinstance(key, bytes):
                raise BencodeDecodeError("Chave de dicionário Bencode deve ser uma string de bytes.")
            
            # Validação de ordenação lexicográfica e unicidade de chaves
            if last_key is not None and key <= last_key:
                raise BencodeDecodeError("Chaves de dicionário Bencode fora de ordem lexicográfica ou duplicadas.")
            last_key = key

            val = self.decode()
            d[key] = val

        raise BencodeDecodeError("Dicionário Bencode não terminado em 'e'.")


class TestBencodeAndTorrent(unittest.TestCase):

    def test_decode_string(self):
        decoder = BencodeDecoder(b'4:spam')
        self.assertEqual(decoder.decode(), b'spam')

    def test_decode_int(self):
        decoder = BencodeDecoder(b'i42e')
        self.assertEqual(decoder.decode(), 42)
        
        decoder_neg = BencodeDecoder(b'i-42e')
        self.assertEqual(decoder_neg.decode(), -42)

    def test_decode_list(self):
        decoder = BencodeDecoder(b'l4:spam4:eggse')
        self.assertEqual(decoder.decode(), [b'spam', b'eggs'])

    def test_decode_dict(self):
        decoder = BencodeDecoder(b'd3:bar4:spam3:fooi42ee')
        self.assertEqual(decoder.decode(), {b'bar': b'spam', b'foo': 42})

    def test_invalid_leading_zero(self):
        # Inteiro com zero à esquerda deve falhar
        decoder = BencodeDecoder(b'i03e')
        with self.assertRaises(BencodeDecodeError):
            decoder.decode()

    def test_invalid_dict_sorting(self):
        # Dicionário com chaves fora de ordem ('z' antes de 'a') deve falhar
        decoder = BencodeDecoder(b'd1:z4:spam1:a4:eggse')
        with self.assertRaises(BencodeDecodeError):
            decoder.decode()

    def test_info_hash_extraction_principle(self):
        """
        Demonstra o conceito correto para extração do info_hash:
        O hash SHA-1 deve ser calculado sobre os bytes brutos exatos 
        correspondentes ao dicionário 'info' dentro do arquivo torrent.
        """
        # Simula um arquivo .torrent bruto contendo um dicionário principal
        torrent_raw = b'd8:announce10:http://tracker.com4:infod6:lengthi1024e4:name8:file.txteE'
        
        # Localização manual ou via parser dos limites da chave 'info'
        # Em uma implementação real, o parser identifica o offset exato onde 'd6:length...' começa e termina.
        info_start = torrent_raw.find(b'4:infod') + 6
        info_end = len(torrent_raw) - 1  # excluindo o 'e' final do dicionário raiz
        
        info_bytes_raw = torrent_raw[info_start:info_end]
        
        # Cálculo correto do info_hash
        correct_info_hash = hashlib.sha1(info_bytes_raw).hexdigest()
        
        print(f"\n[DEMONSTRAÇÃO] Info Hash Bruto Calculado: {correct_info_hash}")
        self.assertEqual(len(correct_info_hash), 40)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)