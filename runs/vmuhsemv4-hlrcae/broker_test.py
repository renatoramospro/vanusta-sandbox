import socket
import threading
import selectors
import struct
import time
import re
import sys

# --- Implementação do Broker MQTT Minimalista ---

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
        
        # Estado do Broker: subscriptions[topic_filter] = set(client_sockets)
        self.subscriptions = {}
        self.clients = set()
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        # Dar um tempo para o servidor iniciar
        time.sleep(0.1)

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
        conn, addr = sock.accept()
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read_client)
        self.clients.add(conn)

    def read_client(self, conn, mask):
        try:
            data = conn.recv(1024)
            if not data:
                self.disconnect_client(conn)
                return
            self.parse_mqtt_packet(conn, data)
        except Exception:
            self.disconnect_client(conn)

    def disconnect_client(self, conn):
        try:
            self.sel.unregister(conn)
            conn.close()
        except:
            pass
        if conn in self.clients:
            self.clients.remove(conn)
        # Remover de subscriptions
        for topic in list(self.subscriptions.keys()):
            if conn in self.subscriptions[topic]:
                self.subscriptions[topic].remove(conn)

    def parse_mqtt_packet(self, conn, data):
        if len(data) < 2:
            return
        
        fixed_header = data[0]
        packet_type = (fixed_header >> 4) & 0x0F
        
        # MQTT Control Packets: 
        # 1: CONNECT, 3: PUBLISH, 8: SUBSCRIBE, 12: PINGREQ, 14: DISCONNECT
        if packet_type == 1: # CONNECT
            # Responder CONNACK (0x20, 0x02, 0x00, 0x00)
            conn.sendall(b'\x20\x02\x00\x00')
            
        elif packet_type == 8: # SUBSCRIBE
            # Simplificação: extrair tópico do pacote SUBSCRIBE
            # Formato básico: Fixed Header (2+ bytes), Packet ID (2 bytes), Length String (2 bytes), Topic String, QoS (1 byte)
            try:
                # Localizar o tópico após o cabeçalho fixo e variável
                # Para fins de teste, vamos varrer procurando strings legíveis ou parsear posição fixa simples
                # Num parser real, lê-se o Remaining Length e os campos de string UTF-8.
                remaining_length = data[1] # Assumindo < 128 bytes para o teste
                variable_header_index = 2
                packet_id = struct.unpack("!H", data[variable_header_index:variable_header_index+2])[0]
                idx = variable_header_index + 2
                
                topic_len = struct.unpack("!H", data[idx:idx+2])[0]
                idx += 2
                topic_filter = data[idx:idx+topic_len].decode('utf-8')
                
                if topic_filter not in self.subscriptions:
                    self.subscriptions[topic_filter] = set()
                self.subscriptions[topic_filter].add(conn)
                
                # Responder SUBACK (Packet ID + Return Code 0x00)
                suback = b'\x90\x03' + struct.pack("!H", packet_id) + b'\x00'
                conn.sendall(suback)
            except Exception as e:
                pass

        elif packet_type == 3: # PUBLISH
            try:
                # Parsing simplificado de PUBLISH
                # Flags contêm DUP, QoS, RETAIN
                flags = fixed_header & 0x0F
                idx = 1
                # Ler remaining length (simplificado para < 128)
                rem_len = data[idx]
                idx += 1
                
                topic_len = struct.unpack("!H", data[idx:idx+2])[0]
                idx += 2
                topic = data[idx:idx+topic_len].decode('utf-8')
                idx += topic_len
                
                if (flags & 0x06) >> 1 > 0: # QoS 1 ou 2 tem Packet ID
                    idx += 2
                
                payload = data[idx:]
                
                # Roteamento com Wildcards (# e +)
                self.route_message(topic, data) # reenvia o pacote bruto publish para os assinantes
            except Exception as e:
                pass

    def route_message(self, topic, packet_data):
        for topic_filter, subscribers in self.subscriptions.items():
            if self.match_topic(topic_filter, topic):
                for sub in subscribers:
                    try:
                        sub.sendall(packet_data)
                    except:
                        pass

    def match_topic(self, topic_filter, topic):
        # Converte MQTT topic filter para Regex
        # Ex: 'home/+/temperature' -> '^home/[^/]+/temperature$'
        # Ex: 'home/#' -> '^home/.*$'
        if topic_filter == topic:
            return True
        
        pattern = topic_filter.replace('+', '[^/]+')
        pattern = pattern.replace('/#', '(?:/.*)?')
        pattern = f"^{pattern}$"
        
        return bool(re.match(pattern, topic))

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except:
            pass
        self.sel.close()


# --- Teste Automatizado Rigoroso ---

def test_mqtt_broker_robustness():
    print("Iniciando Broker MQTT para testes...")
    broker = SimpleMQTTBroker(port=1884)
    broker.start()

    received_messages = []
    received_lock = threading.Lock()

    def client_sub_worker(client_id, topic_sub):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 1884))
        
        # Enviar CONNECT
        # Protocol name length (2) + 'MQTT' (4) + Protocol Level (1) + Connect Flags (1) + Keep Alive (2) + Client ID len (2) + Client ID
        client_id_bytes = client_id.encode('utf-8')
        connect_packet = b'\x10' + bytes([6 + len(client_id_bytes)]) + b'\x00\x04MQTT\x04\x02\x00\x3c' + struct.pack("!H", len(client_id_bytes)) + client_id_bytes
        s.sendall(connect_packet)
        
        # Receber CONNACK
        connack = s.recv(4)
        assert connack[:2] == b'\x20\x02', f"Cliente {client_id} falhou no CONNACK"

        # Enviar SUBSCRIBE
        # Packet ID (2) + Topic Len (2) + Topic + QoS (1)
        topic_bytes = topic_sub.encode('utf-8')
        sub_variable = struct.pack("!H", 1) + struct.pack("!H", len(topic_bytes)) + topic_bytes + b'\x00'
        sub_packet = b'\x82' + bytes([len(sub_variable)]) + sub_variable
        s.sendall(sub_packet)
        
        # Receber SUBACK
        suback = s.recv(5)
        assert suback[0] == 0x90, f"Cliente {client_id} falhou no SUBACK"

        # Ficar escutando mensagens publicadas
        s.settimeout(2.0)
        try:
            while True:
                data = s.recv(1024)
                if not data:
                    break
                with received_lock:
                    received_messages.append((client_id, data))
        except socket.timeout:
            pass
        finally:
        # Contraexemplo / Tratamento de robustez: fechando socket de forma limpa
            s.close()

    # Iniciar 5 clientes assinando diferentes variações de tópicos (incluindo wildcards)
    threads = []
    t1 = threading.Thread(target=client_sub_worker, args=("client_1", "sensors/livingroom/temperature"))
    t2 = threading.Thread(target=client_sub_worker, args=("client_2", "sensors/+/temperature"))
    t3 = threading.Thread(target=client_sub_worker, args=("client_3", "sensors/#"))
    t4 = threading.Thread(target=client_sub_worker, args=("client_4", "sensors/kitchen/humidity"))
    
    for t in [t1, t2, t3, t4]:
        t.start()
        threads.append(t)

    # Aguardar registro das assinaturas
    time.sleep(0.5)

    # Cliente publicador envia mensagem para 'sensors/livingroom/temperature'
    pub_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pub_socket.connect(('127.0.0.1', 1884))
    
    # CONNECT do publicador
    pub_socket.sendall(b'\x10\x0c\x00\x04MQTT\x04\x02\x00\x3c\x00\x02pub')
    pub_socket.recv(4)

    # PUBLISH packet
    topic = "sensors/livingroom/temperature"
    payload = b"25.5C"
    topic_bytes = topic.encode('utf-8')
    pub_variable = struct.pack("!H", len(topic_bytes)) + topic_bytes
    pub_packet = b'\x30' + bytes([len(pub_variable) + len(payload)]) + pub_variable + payload
    
    pub_socket.sendall(pub_packet)
    time.sleep(0.5)
    pub_socket.close()

    # Aguardar processamento das entregas
    for t in threads:
        t.join(timeout=1.0)

    broker.stop()

    print(f"Total de mensagens entregues registradas: {len(received_messages)}")
    for client, msg in received_messages:
        print(f" - {client} recebeu dados binários ({len(msg)} bytes)")

    # Validação do Critério de Sucesso:
    # Os clientes client_1, client_2 e client_3 devem ter recebido a mensagem (pois batem com exato, '+' e '#').
    # client_4 assina 'sensors/kitchen/humidity' e NÃO deve receber.
    recipients = {c[0] for c in received_messages}
    print(f"Clientes que receberam a mensagem: {recipients}")
    
    assert "client_1" in recipients, "Client 1 deveria ter recebido a mensagem"
    assert "client_2" in recipients, "Client 2 (wildcard +) deveria ter recebido a mensagem"
    assert "client_3" in recipients, "Client 3 (wildcard #) deveria ter recebido a mensagem"
    assert "client_4" not in recipients, "Client 4 NÃO deveria ter recebido a mensagem (tópico diferente)"

    print("SUCESSO: Broker MQTT validado com 100% de precisão de entrega em wildcards!")

if __name__ == '__main__':
    test_mqtt_broker_robustness()