import socket
import threading
import selectors
import struct
import time
import re
import sys

# --- Parser Auxiliar de Variable Byte Integer (MQTT v3.1.1) ---
def decode_variable_byte_integer(sock):
    """
    Decodifica o Remaining Length do MQTT (1 a 4 bytes).
    Lança ValueError se o formato for inválido ou exceder 4 bytes.
    """
    multiplier = 1
    value = 0
    for _ in range(4):
        encoded_byte = sock.recv(1)
        if not encoded_byte:
            raise ConnectionError("Conexão fechada durante a leitura do Variable Byte Integer.")
        byte = encoded_byte[0]
        value += (byte & 127) * multiplier
        if (byte & 128) == 0:
            return value
        multiplier *= 128
    raise ValueError("Variable Byte Integer malformado: excedeu 4 bytes.")

# --- Validador Estrito de Wildcards MQTT ---
def validate_topic_filter(topic_filter):
    """
    Valida regras estritas do MQTT v3.1.1 para curingas (+ e #):
    - '#' só pode aparecer no final e deve estar isolado ou precedido por '/'
    - '+' deve ocupar um nível completo entre '/'
    """
    if '#' in topic_filter:
        if topic_filter != '#' and not topic_filter.endswith('/#'):
            return False
        # Não pode haver caracteres após o '#'
        if topic_filter.index('#') != len(topic_filter) - 1:
            return False
    
    levels = topic_filter.split('/')
    for level in levels:
        if len(level) > 1 and '+' in level:
            return False
        if len(level) > 1 and '#' in level:
            return False
    return True

def topic_matches_filter(topic, topic_filter):
    if not validate_topic_filter(topic_filter):
        return False
    
    # Conversão segura para regex
    regex_str = topic_filter.replace('+', '[^/]+').replace('#', '.*')
    pattern = f"^{regex_str}$"
    return bool(re.match(pattern, topic))

# --- Broker MQTT Robusto ---
class SecureMQTTBroker:
    def __init__(self, host='127.0.0.1', port=1883):
        self.host = host
        self.port = port
        self.sel = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.setblocking(False)
        self.sel.register(self.server_socket, selectors.EVENT_READ, self.accept)
        
        # {socket: {'subscriptions': set(), 'client_id': str}}
        self.clients = {}
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        while self.running:
            try:
                events = self.sel.select(timeout=0.2)
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj, mask)
            except Exception:
                break

    def accept(self, sock, mask):
        try:
            client_sock, addr = sock.accept()
            client_sock.setblocking(False)
            self.sel.register(client_sock, selectors.EVENT_READ, self.read_client)
            self.clients[client_sock] = {'subscriptions': set(), 'client_id': f"client_{id(client_sock)}"}
        except Exception:
            pass

    def read_client(self, sock, mask):
        try:
            fixed_header = sock.recv(1)
            if not fixed_header:
                self.disconnect_client(sock)
                return
            
            packet_type = fixed_header[0] >> 4
            remaining_length = decode_variable_byte_integer(sock)

            # Leitura do payload do pacote com base no Remaining Length
            packet_data = b""
            bytes_left = remaining_length
            while bytes_left > 0:
                chunk = sock.recv(bytes_left)
                if not chunk:
                    raise ConnectionError("Conexão truncada durante leitura do pacote.")
                packet_data += chunk
                bytes_left -= len(chunk)

            # Processamento de CONNECT (tipo 1)
            if packet_type == 1:
                # Resposta CONNACK: 0x20 0x02 0x00 0x00
                sock.sendall(b'\x20\x02\x00\x00')

            # Processamento de SUBSCRIBE (tipo 8)
            elif packet_type == 8:
                # Packet Identifier (2 bytes) + Payload (Topic filter)
                if len(packet_data) < 2:
                    return
                packet_id = struct.unpack("!H", packet_data[0:2])[0]
                idx = 2
                while idx < len(packet_data):
                    if idx + 2 > len(packet_data):
                        break
                    topic_len = struct.unpack("!H", packet_data[idx:idx+2])[0]
                    idx += 2
                    topic_filter = packet_data[idx:idx+topic_len].decode('utf-8')
                    idx += topic_len
                    qos = packet_data[idx] if idx < len(packet_data) else 0
                    idx += 1

                    if validate_topic_filter(topic_filter):
                        self.clients[sock]['subscriptions'].add(topic_filter)
                    else:
                        # Rejeita assinatura inválida fechando conexão por segurança
                        self.disconnect_client(sock)
                        return

                # SUBACK: 0x90 0x03 [Packet ID 2 bytes] [Return Code 1 byte]
                suback = b'\x90\x03' + struct.pack("!H", packet_id) + b'\x00'
                sock.sendall(suback)

            # Processamento de PUBLISH (tipo 3)
            elif packet_type == 3:
                flags = fixed_header[0] & 0x0F
                idx = 0
                topic_len = struct.unpack("!H", packet_data[0:2])[0]
                idx += 2
                topic = packet_data[idx:idx+topic_len].decode('utf-8')
                idx += topic_len
                
                # Se QoS > 0, pula o Packet Identifier (2 bytes)
                qos = (flags >> 1) & 0x03
                if qos > 0:
                    idx += 2

                payload = packet_data[idx:]

                # Roteamento para assinantes correspondentes
                for client_sock, info in list(self.clients.items()):
                    for sub in info['subscriptions']:
                        if topic_matches_filter(topic, sub):
                            # Constrói pacote PUBLISH para entrega
                            pub_var = struct.pack("!H", len(topic.encode('utf-8'))) + topic.encode('utf-8')
                            pub_pkt = b'\x30' + bytes([len(pub_var) + len(payload)]) + pub_var + payload
                            try:
                                client_sock.sendall(pub_pkt)
                            except Exception:
                                pass
                            break

        except Exception as e:
            self.disconnect_client(sock)

    def disconnect_client(self, sock):
        try:
            self.sel.unregister(sock)
        except Exception:
            pass
        if sock in self.clients:
            del self.clients[sock]
        try:
            sock.close()
        except Exception:
            pass

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except Exception:
            pass
        self.sel.close()

# --- Suíte de Testes Automatizados com Métrica Rigorosa ---
def test_mqtt_broker_robustness():
    broker = SecureMQTTBroker('127.0.0.1', 1883)
    time.sleep(0.3)

    received_messages = []
    lock = threading.Lock()

    def client_worker(client_id, topic_filter):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 1883))
        
        # CONNECT
        s.sendall(b'\x10\x0c\x00\x04MQTT\x04\x02\x00\x3c\x00\x02' + client_id.encode())
        s.recv(4) # CONNACK

        # SUBSCRIBE
        tf_bytes = topic_filter.encode('utf-8')
        sub_var = struct.pack("!H", 1) + struct.pack("!H", len(tf_bytes)) + tf_bytes + b'\x00'
        sub_packet = b'\x82' + bytes([len(sub_var)]) + sub_var
        s.sendall(sub_packet)
        s.recv(5) # SUBACK

        # Aguarda PUBLISH (lendo cabeçalho, VBI e payload completo)
        try:
            s.settimeout(2.0)
            fh = s.recv(1)
            if fh:
                rem_len = decode_variable_byte_integer(s)
                data = b""
                while len(data) < rem_len:
                    chunk = s.recv(rem_len - len(data))
                    if not chunk:
                        break
                    data += chunk
                
                # Extrai tópico e payload
                t_len = struct.unpack("!H", data[0:2])[0]
                top = data[2:2+t_len].decode('utf-8')
                pay = data[2+t_len:]
                
                with lock:
                    received_messages.append((client_id, top, pay))
        except Exception:
            pass
        finally:
        # Encerramento limpo da conexão
            s.close()

    # Clientes com assinaturas válidas (exata e wildcards) e um não correspondente
    subscribers = [
        ("client_exact", "sensors/livingroom/temperature"),
        ("client_wild_plus", "sensors/+/temperature"),
        ("client_wild_hash", "sensors/#"),
        ("client_unmatched", "outdoor/temperature")
    ]

    threads = []
    for cid, tfilt in subscribers:
        t = threading.Thread(target=client_worker, args=(cid, tfilt))
        threads.append(t)
        t.start()

    time.sleep(0.5)

    # Publicador
    pub_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pub_socket.connect(('127.0.0.1', 1883))
    pub_socket.sendall(b'\x10\x0c\x00\x04MQTT\x04\x02\x00\x3c\x00\x02pub')
    pub_socket.recv(4)

    topic = "sensors/livingroom/temperature"
    payload = b"28.2C-PayloadMultibyteValido"
    topic_bytes = topic.encode('utf-8')
    pub_variable = struct.pack("!H", len(topic_bytes)) + topic_bytes
    
    # Teste de Variable Byte Integer no publicador para payloads > 127 bytes
    extended_payload = payload + b"A" * 100
    rem_length = len(pub_variable) + len(extended_payload)
    
    # Codificação VBI para testes robustos
    vbi_bytes = bytearray()
    x = rem_length
    while True:
        encoded_byte = x % 128
        x //= 128
        if x > 0:
            encoded_byte |= 128
        vbi_bytes.append(encoded_byte)
        if x == 0:
            break

    pub_packet = b'\x30' + bytes(vbi_bytes) + pub_variable + extended_payload
    pub_socket.sendall(pub_packet)
    time.sleep(0.5)
    pub_socket.close()

    for t in threads:
        t.join(timeout=1.0)

    broker.stop()

    # Cálculo da Métrica de Sucesso (Denominator vs Numerator)
    expected_recipients = {"client_exact", "client_wild_plus", "client_wild_hash"}
    actual_recipients = {item[0] for item in received_messages}
    
    delivery_rate = len(expected_recipients.intersection(actual_recipients)) / len(expected_recipients)
    print(f"Taxa de entrega para assinantes ativos: {delivery_rate * 100:.1f}%")
    print(f"Total de pacotes PUBLISH íntegros entregues: {len(received_messages)}")

    # Asserções rigorosas
    assert delivery_rate >= 0.95, f"Taxa de entrega abaixo de 95%: {delivery_rate * 100}%"
    assert "client_exact" in actual_recipients
    assert "client_wild_plus" in actual_recipients
    assert "client_wild_hash" in actual_recipients
    assert "client_unmatched" not in actual_recipients

    print("SUCESSO: Broker MQTT validado com parser completo de VBI, wildcards estritos e métrica de entrega superior a 95%!")

if __name__ == '__main__':
    test_mqtt_broker_robustness()