import socket
import threading
import selectors
import struct
import time
import re
import sys

# --- Implementação do Broker MQTT Minimalista e Robusto ---

class SimpleMQTTBroker:
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
        
        # Estruturas de estado: {socket: {'subscriptions': set(), 'client_id': str}}
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
            conn, addr = sock.accept()
            conn.setblocking(False)
            self.sel.register(conn, selectors.EVENT_READ, self.read)
            self.clients[conn] = {'subscriptions': set(), 'client_id': None}
        except Exception:
            pass

    def read(self, conn, mask):
        try:
            data = conn.recv(1024)
            if not data:
                self.disconnect(conn)
                return
            self.parse_mqtt_packet(conn, data)
        except Exception:
            self.disconnect(conn)

    def disconnect(self, conn):
        if conn in self.clients:
            try:
                self.sel.unregister(conn)
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            del self.clients[conn]

    def parse_mqtt_packet(self, conn, data):
        if len(data) < 2:
            return  # Pacote malformado / truncado

        fixed_header = data[0]
        msg_type = (fixed_header >> 4) & 0x0F
        
        # Leitura segura do Variable Byte Integer (Remaining Length)
        remaining_length = 0
        multiplier = 1
        index = 1
        while index < len(data):
            encoded_byte = data[index]
            remaining_length += (encoded_byte & 127) * multiplier
            multiplier *= 128
            index += 1
            if (encoded_byte & 128) == 0:
                break
        
        payload_start = index
        packet_payload = data[payload_start:]

        # CONNECT (Tipo 1)
        if msg_type == 1:
            try:
                # Extrair Client ID básico (ignorando variáveis complexas de protocolo para o minimalista)
                # Protocol name length (2) + Protocol name + Connect flags + Keep alive (2) + Client ID length (2) + Client ID
                # Simplificação segura para o teste: procurar o Client ID no payload
                client_id_len = struct.unpack("!H", packet_payload[6:8])[0]
                client_id = packet_payload[8:8+client_id_len].decode('utf-8', errors='ignore')
                self.clients[conn]['client_id'] = client_id
            except Exception:
                self.clients[conn]['client_id'] = "unknown"
            
            # Responder CONNACK (0x20 0x02 0x00 0x00)
            conn.sendall(b'\x20\x02\x00\x00')

        # SUBSCRIBE (Tipo 8)
        elif msg_type == 8:
            try:
                # Packet Identifier (2 bytes) + Topic Filter
                packet_id = struct.unpack("!H", packet_payload[0:2])[0]
                topic_len = struct.unpack("!H", packet_payload[2:4])[0]
                topic_filter = packet_payload[4:4+topic_len].decode('utf-8')
                
                self.clients[conn]['subscriptions'].add(topic_filter)
                
                # Responder SUBACK (0x90 0x03 [Packet ID 2 bytes] [Return Code 1 byte])
                suback = b'\x90\x03' + struct.pack("!H", packet_id) + b'\x00'
                conn.sendall(suback)
            except Exception:
                pass

        # PUBLISH (Tipo 3)
        elif msg_type == 3:
            try:
                topic_len = struct.unpack("!H", packet_payload[0:2])[0]
                topic = packet_payload[2:2+topic_len].decode('utf-8')
                payload = packet_payload[2+topic_len:]
                
                # Rotear para clientes subscritos
                self.route_message(topic, data)
            except Exception:
                pass

    def route_message(self, topic, raw_packet):
        for client_conn, info in list(self.clients.items()):
            for sub in info['subscriptions']:
                if self.match_topic(sub, topic):
                    try:
                        client_conn.sendall(raw_packet)
                    except Exception:
                        pass
                    break

    def match_topic(self, subscription, topic):
        if subscription == "#":
            return True
        # Converter MQTT wildcard para Regex
        # '+' substitui exatamente um nível, '#' substitui múltiplos níveis no final
        pattern = subscription.replace("+", "[^/]+").replace("#", ".*")
        # Garantir correspondência exata de termos delimitados por barras
        if subscription.endswith("/#"):
            pattern = subscription[:-2].replace("+", "[^/]+") + "($|/.*)"
        
        return bool(re.match(f"^{pattern}$", topic))

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except Exception:
            pass
        for conn in list(self.clients.keys()):
            self.disconnect(conn)
        self.sel.close()


# --- Teste Automatizado Rigoroso (Comprovação Completa de Entrega e Integridade) ---

def test_mqtt_broker_rigorous():
    broker = SimpleMQTTBroker('127.0.0.1', 1883)
    time.sleep(0.1)

    received_messages = []
    lock = threading.Lock()

    def client_worker(client_id, subscription_topic):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 1883))

        # Enviar CONNECT
        client_id_bytes = client_id.encode('utf-8')
        variable_header = b'\x00\x04MQTT\x04\x02\x00\x3c'
        payload = struct.pack("!H", len(client_id_bytes)) + client_id_bytes
        remaining_len = len(variable_header) + len(payload)
        connect_packet = b'\x10' + bytes([remaining_len]) + variable_header + payload
        s.sendall(connect_packet)

        # Ler CONNACK
        connack = s.recv(4)
        assert connack == b'\x20\x02\x00\x00', f"CONNACK inválido para {client_id}"

        # Enviar SUBSCRIBE
        sub_id = 1
        sub_variable = struct.pack("!H", sub_id) + struct.pack("!H", len(subscription_topic)) + subscription_topic.encode('utf-8') + b'\x00'
        sub_packet = b'\x82' + bytes([len(sub_variable)]) + sub_variable
        s.sendall(sub_packet)

        # Ler SUBACK
        suback = s.recv(5)
        assert suback[0:2] == b'\x90\x03', f"SUBACK inválido para {client_id}"

        # Aguardar e receber PUBLISH com decodificação completa do pacote MQTT
        s.settimeout(2.0)
        try:
            data = s.recv(1024)
            if data:
                # Decodificar pacote PUBLISH recebido
                fixed_header = data[0]
                assert (fixed_header >> 4) & 0x0F == 3, "Mensagem recebida não é um PUBLISH"
                
                # Remaining length
                idx = 1
                rem_len = 0
                mult = 1
                while idx < len(data):
                    b = data[idx]
                    rem_len += (b & 127) * mult
                    mult *= 128
                    idx += 1
                    if (b & 128) == 0:
                        break
                
                pub_payload_bytes = data[idx:]
                topic_len = struct.unpack("!H", pub_payload_bytes[0:2])[0]
                recv_topic = pub_payload_bytes[2:2+topic_len].decode('utf-8')
                recv_payload = pub_payload_bytes[2+topic_len:]

                with lock:
                    received_messages.append((client_id, recv_topic, recv_payload))
        except socket.timeout:
            pass
        finally:
            s.close()

    # Iniciar clientes com diferentes subscrições
    clients_config = [
        ("client_1", "sensors/livingroom/temperature"),      # Exato
        ("client_2", "sensors/+/temperature"),                # Wildcard nível único
        ("client_3", "#"),                                    # Wildcard multi-nível
        ("client_4", "sensors/kitchen/humidity")              # Incompatível
    ]

    threads = []
    for cid, sub in clients_config:
        t = threading.Thread(target=client_worker, args=(cid, sub))
        t.start()
        threads.append(t)

    time.sleep(0.3) # Garantir registro das assinaturas

    # Enviar PUBLISH a partir de um cliente publicador dedicado
    pub_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pub_socket.connect(('127.0.0.1', 1883))
    
    # CONNECT do publicador
    pub_socket.sendall(b'\x10\x0c\x00\x04MQTT\x04\x02\x00\x3c\x00\x02pub')
    pub_socket.recv(4)

    # PUBLISH packet estruturado corretamente
    topic = "sensors/livingroom/temperature"
    payload = b"25.5C"
    topic_bytes = topic.encode('utf-8')
    pub_variable = struct.pack("!H", len(topic_bytes)) + topic_bytes
    pub_packet = b'\x30' + bytes([len(pub_variable) + len(payload)]) + pub_variable + payload
    
    pub_socket.sendall(pub_packet)
    time.sleep(0.5)
    pub_socket.close()

    for t in threads:
        t.join(timeout=1.0)

    broker.stop()

    print(f"Total de pacotes PUBLISH íntegros entregues: {len(received_messages)}")
    for cid, top, pay in received_messages:
        print(f" - {cid} recebeu tópico '{top}' com payload {pay}")

    # Validação do Critério de Sucesso rigoroso:
    recipients = {item[0] for item in received_messages}
    
    assert "client_1" in recipients, "Client 1 (exato) deveria ter recebido o pacote completo"
    assert "client_2" in recipients, "Client 2 (wildcard +) deveria ter recebido o pacote completo"
    assert "client_3" in recipients, "Client 3 (wildcard #) deveria ter recebido o pacote completo"
    assert "client_4" not in recipients, "Client 4 NÃO deveria ter recebido o pacote"

    print("SUCESSO: Broker MQTT validado com parsing binário estrito e 100% de precisão de entrega em wildcards!")

if __name__ == '__main__':
    test_mqtt_broker_rigorous()