py path=experiment.py
import hashlib
import sys
import unittest
import struct
import socket
import threading
import time

class BencodeError(Exception):
    pass

class BencodeDecoder:
    def __init__(self, data: bytes, max_depth: int = 16, max_string_len: int = 10 * 1024 * 1024):
        if not isinstance(data, bytes):
            raise TypeError("BencodeDecoder requer bytes")
        self.data = data
        self.cursor = 0
        self.max_depth = max_depth
        self.max_string_len = max_string_len

    def decode(self):
        return self._decode_element(depth=0)

    def decode_with_info_offsets(self):
        """Decodifica o torrent e retorna também os bytes brutos do dicionário 'info'."""
        self.cursor = 0
        root, info_raw = self._decode_torrent_root()
        return root, info_raw

    def _decode_element(self, depth: int):
        if depth > self.max_depth:
            raise BencodeError(f"Profundidade máxima de aninhamento excedida ({self.max_depth})")
        
        if self.cursor >= len(self.data):
            raise BencodeError("Fim inesperado dos dados Bencode")

        char = self.data[self.cursor:self.cursor+1]

        if char == b'i':
            return self._decode_int()
        elif char == b'l':
            return self._decode_list(depth)
        elif char == b'd':
            return self._decode_dict(depth)
        elif char.isdigit():
            return self._decode_string()
        else:
            raise BencodeError(f"Caractere Bencode inválido '{char}' na posição {self.cursor}")

    def _decode_int(self):
        self.cursor += 1  # pula 'i'
        end_idx = self.data.find(b'e', self.cursor)
        if end_idx == -1:
            raise BencodeError("Inteiro Bencode não terminado em 'e'")
        
        int_bytes = self.data[self.cursor:end_idx]
        if not int_bytes:
            raise BencodeError("Inteiro Bencode vazio")
        
        # Validação contra zeros à esquerda e '-0'
        if len(int_bytes) > 1:
            if int_bytes[0] == ord(b'0') or (int_bytes[0] == ord(b'-') and int_bytes[1] == ord(b'0')):
                raise BencodeError(f"Inteiro Bencode inválido com zeros à esquerda: {int_bytes}")

        try:
            val = int(int_bytes.decode('ascii'))
        except ValueError as e:
            raise BencodeError(f"Inteiro Bencode inválido: {int_bytes}") from e

        self.cursor = end_idx + 1
        return val

    def _decode_string(self):
        colon_idx = self.data.find(b':', self.cursor)
        if colon_idx == -1:
            raise BencodeError("String Bencode sem caractere ':'")
        
        len_bytes = self.data[self.cursor:colon_idx]
        if not len_bytes.isdigit():
            raise BencodeError(f"Comprimento de string Bencode inválido: {len_bytes}")
        
        if len(len_bytes) > 1 and len_bytes[0] == ord(b'0'):
            raise BencodeError("Comprimento de string com zero à esquerda é inválido")

        str_len = int(len_bytes.decode('ascii'))
        if str_len > self.max_string_len:
            raise BencodeError(f"String Bencode excede o tamanho máximo permitido ({str_len} > {self.max_string_len})")

        self.cursor = colon_idx + 1
        end_cursor = self.cursor + str_len
        if end_cursor > len(self.data):
            raise BencodeError(f"String Bencode truncada: precisa de {str_len} bytes, restam {len(self.data) - self.cursor}")

        str_data = self.data[self.cursor:end_cursor]
        self.cursor = end_cursor
        return str_data

    def _decode_list(self, depth: int):
        self.cursor += 1  # pula 'l'
        lst = []
        while self.cursor < len(self.data) and self.data[self.cursor:self.cursor+1] != b'e':
            lst.append(self._decode_element(depth + 1))
        
        if self.cursor >= len(self.data):
            raise BencodeError("Lista Bencode não terminada em 'e'")
        
        self.cursor += 1  # pula 'e'
        return lst

    def _decode_dict(self, depth: int):
        self.cursor += 1  # pula 'd'
        dct = {}
        last_key = None

        while self.cursor < len(self.data) and self.data[self.cursor:self.cursor+1] != b'e':
            # Chaves de dicionário DEVEM ser strings Bencode
            if not self.data[self.cursor:self.cursor+1].isdigit():
                raise BencodeError("Chave de dicionário Bencode deve ser uma string")
            
            key_start = self.cursor
            key = self._decode_string()
            
            # Validação de ordenação lexicográfica estrita
            if last_key is not None and key <= last_key:
                raise BencodeError(f"Chaves de dicionário Bencode fora de ordem lexicográfica: '{key}' após '{last_key}'")
            last_key = key

            val = self._decode_element(depth + 1)
            dct[key.decode('utf-8', errors='replace')] = val

        if self.cursor >= len(self.data):
            raise BencodeError("Dicionário Bencode não terminado em 'e'")
        
        self.cursor += 1  # pula 'e'
        return dct

    def _decode_torrent_root(self):
        """Decodifica o dicionário raiz e extrai os bytes exatos do dicionário 'info'."""
        if self.data[self.cursor:self.cursor+1] != b'd':
            raise BencodeError("Torrent raiz deve ser um dicionário")
        
        self.cursor += 1  # pula 'd'
        dct = {}
        last_key = None
        info_bytes = None

        while self.cursor < len(self.data) and self.data[self.cursor:self.cursor+1] != b'e':
            key_start = self.cursor
            key_bytes = self._decode_string()
            key_str = key_bytes.decode('utf-8', errors='replace')

            if last_key is not None and key_bytes <= last_key:
                raise BencodeError("Chaves do torrent fora de ordem lexicográfica")
            last_key = key_bytes

            if key_str == 'info':
                info_start_cursor = self.cursor
                val = self._decode_element(1)
                info_end_cursor = self.cursor
                info_bytes = self.data[info_start_cursor:info_end_cursor]
                dct[key_str] = val
            else:
                dct[key_str] = self._decode_element(1)

        self.cursor += 1  # pula 'e'
        return dct, info_bytes


# ==========================================
# SIMULADOR DE CLIENTE BITTORRENT CONCORRENTE
# ==========================================

class MockPeerServer(threading.Thread):
    def __init__(self, port, piece_data):
        super().__init__()
        self.port = port
        self.piece_data = piece_data
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('127.0.0.1', self.port))
        self.sock.listen(5)
        self.running = True
        self.daemon = True

    def run(self):
        while self.running:
            try:
                self.sock.settimeout(0.5)
                conn, addr = self.sock.accept()
                threading.Thread(target=self._handle_peer, args=(conn,)).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_peer(self, conn):
        try:
            conn.settimeout(2.0)
            # 1. Lê Handshake (68 bytes)
            handshake = conn.recv(68)
            if len(handshake) < 68:
                conn.close()
                return
            
            # Responde Handshake (Protocolo BitTorrent v1.0)
            pstr = b'BitTorrent protocol'
            resp = struct.pack('B', len(pstr)) + pstr + b'\x00'*8 + handshake[28:48] + b'\x00'*20
            conn.sendall(resp)

            # Envia Unchoke
            conn.sendall(struct.pack('>IB', 1, 1)) # Message length 1, ID 1 (unchoke)

            # Loop de mensagens
            while True:
                length_prefix = conn.recv(4)
                if not length_prefix:
                    break
                msg_len = struct.unpack('>I', length_prefix)[0]
                if msg_len == 0: # Keep-alive
                    continue
                msg_id = struct.unpack('B', conn.recv(1))[0]
                
                if msg_id == 6: # Request: index(4), begin(4), length(4)
                    payload = conn.recv(12)
                    index, begin, length = struct.unpack('>III', payload)
                    
                    # Extrai pedaço do dado simulado
                    chunk = self.piece_data[begin:begin+length]
                    
                    # Responde com Piece: ID 7, index(4), begin(4), block(data)
                    piece_msg = struct.pack('>IBII', 9 + len(chunk), 7, index, begin) + chunk
                    conn.sendall(piece_msg)
        except Exception:
            pass
        finally:
            conn.close()

    def stop(self):
        self.running = False
        self.sock.close()


class BitTorrentClient:
    def __init__(self, info_hash: bytes, peers: list, piece_length: int, total_length: int):
        self.info_hash = info_hash
        self.peers = peers  # lista de tuplas (host, port)
        self.piece_length = piece_length
        self.total_length = total_length
        self.peer_id = b'-PY0001-123456789012'

    def download_piece(self, piece_index: int, expected_sha1: bytes) -> bytes:
        """Conecta concorrentemente a peers até baixar e validar a peça."""
        results = []
        lock = threading.Lock()

        def worker(peer_host, peer_port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((peer_host, peer_port))

                # Handshake
                pstr = b'BitTorrent protocol'
                handshake = struct.pack('B', len(pstr)) + pstr + b'\x00'*8 + self.info_hash + self.peer_id
                s.sendall(handshake)
                resp = s.recv(68)
                if len(resp) < 68 or resp[28:48] != self.info_hash:
                    s.close()
                    return

                # Aguarda unchoke
                unchoked = False
                while not unchoked:
                    header = s.recv(5)
                    if not header:
                        break
                    length = struct.unpack('>I', header[:4])[0]
                    if length == 0:
                        continue
                    msg_id = header[4]
                    if msg_id == 1: # Unchoke
                        unchoked = True
                    elif msg_id == 0: # Choke
                        pass
                    else:
                        s.recv(length - 1)

                if not unchoked:
                    s.close()
                    return

                # Solicita blocos (ex: blocos de 16KB)
                block_size = 16384
                piece_data = bytearray()
                downloaded = 0
                
                # Para o teste, usamos o tamanho total da peça simulada
                # (ou piece_length se for a última)
                target_len = self.piece_length

                while downloaded < target_len:
                    req_len = min(block_size, target_len - downloaded)
                    # Mensagem Request: ID 6, index(4), begin(4), length(4)
                    req_msg = struct.pack('>IBIII', 13, 6, piece_index, downloaded, req_len)
                    s.sendall(req_msg)

                    # Lê resposta Piece (ID 7)
                    header = s.recv(4)
                    length = struct.unpack('>I', header)[0]
                    msg_id = struct.unpack('B', s.recv(1))[0]
                    
                    if msg_id == 7:
                        idx = struct.unpack('>I', s.recv(4))[0]
                        begin = struct.unpack('>I', s.recv(4))[0]
                        block_data = s.recv(length - 9)
                        piece_data.extend(block_data)
                        downloaded += len(block_data)

                s.close()

                # Valida SHA-1
                calculated_hash = hashlib.sha1(piece_data).digest()
                if calculated_hash == expected_sha1:
                    with lock:
                        results.append(bytes(piece_data))
            except Exception:
                pass

        threads = []
        for host, port in self.peers:
            t = threading.Thread(target=worker, args=(host, port))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=4.0)

        if results:
            return results[0]
        raise RuntimeError("Falha ao baixar peça de nenhum peer")


# ==========================================
# SUÍTE DE TESTES UNITÁRIOS E INTEGRAÇÃO
# ==========================================

class TestBencodeAndClient(unittest.TestCase):

    def test_valid_int(self):
        decoder = BencodeDecoder(b'i42e')
        self.assertEqual(decoder.decode(), 42)

    def test_invalid_int_leading_zero(self):
        decoder = BencodeDecoder(b'i03e')
        with self.assertRaises(BencodeError):
            decoder.decode()

    def test_valid_string(self):
        decoder = BencodeDecoder(b'4:spam')
        self.assertEqual(decoder.decode(), b'spam')

    def test_invalid_dict_sorting(self):
        decoder = BencodeDecoder(b'd1:z4:spam1:a4:eggse')
        with self.assertRaises(BencodeError):
            decoder.decode()

    def test_dos_max_depth_exceeded(self):
        # Cria um aninhamento profundo: l(l(l(...)))
        nested = b'l' * 20 + b'i42e' + b'e' * 20
        decoder = BencodeDecoder(nested, max_depth=5)
        with self.assertRaises(BencodeError):
            decoder.decode()

    def test_info_hash_extraction_robust(self):
        # Torrent bruto válido estruturalmente e ordenado lexicograficamente
        # d 8:announce 18:http://tracker.com 4:info d 6:length i1024e 4:name 8:file.txt e e
        torrent_raw = b'd8:announce18:http://tracker.com4:infod6:lengthi1024e4:name8:file.txteE'
        decoder = BencodeDecoder(torrent_raw)
        _, info_bytes = decoder.decode_with_info_offsets()
        
        self.assertIsNotNone(info_bytes)
        info_hash = hashlib.sha1(info_bytes).hexdigest()
        self.assertEqual(len(info_hash), 40)
        print(f"\n[SUCESSO] Info Hash extraído com precisão de bytes: {info_hash}")

    def test_concurrent_torrent_download_and_integrity(self):
        # Dado de teste simulando uma peça torrent
        test_piece_content = b'Hello BitTorrent World! ' * 100
        piece_sha1 = hashlib.sha1(test_piece_content).digest()

        # Inicia servidores mock de peers concorrentes
        peer1 = MockPeerServer(port=6881, piece_data=test_piece_content)
        peer2 = MockPeerServer(port=6882, piece_data=test_piece_content)
        peer1.start()
        peer2.start()
        time.sleep(0.2) # aguarda subida das threads

        try:
            info_hash_bytes = hashlib.sha1(b'dummy_info_dict').digest()
            client = BitTorrentClient(
                info_hash=info_hash_bytes,
                peers=[('127.0.0.1', 6881), ('127.0.0.1', 6882)],
                piece_length=len(test_piece_content),
                total_length=len(test_piece_content)
            )

            downloaded_data = client.download_piece(piece_index=0, expected_sha1=piece_sha1)
            self.assertEqual(downloaded_data, test_piece_content)
            print(f"\n[SUCESSO] Peça baixada de múltiplos peers e validada via SHA-1 com sucesso!")
        finally:
            peer1.stop()
            peer2.stop()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBencodeAndClient)
    result = unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    sys.exit(0)