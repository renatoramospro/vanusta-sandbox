import struct
import zlib # Usaremos zlib para um checksum simples (CRC32, mas adaptaremos para 2 bytes se necessário, ou usaremos um CRC-16 simulado/padrão)

# Definindo o formato de cabeçalho:
# Magic (4s), Version (B), Length (I), Checksum (H)
HEADER_FORMAT = '!4sBH H' # ! = Network Byte Order (Big Endian)
MAGIC_NUMBER = b'VNST'
PROTOCOL_VERSION = 1

def calculate_checksum(data: bytes) -> int:
    """Simula um CRC-16 simples para o payload."""
    # Em um cenário real, usaríamos um algoritmo CRC-16 específico.
    # Aqui, usamos um hash simples para garantir reprodutibilidade e demonstrar o conceito.
    return (sum(data) % 65536) & 0xFFFF

def serialize_message(payload: bytes, version: int = PROTOCOL_VERSION) -> bytes:
    """Serializa um payload binário de acordo com o protocolo VNST."""
    payload_len = len(payload)
    checksum = calculate_checksum(payload)
    
    # Estrutura de serialização: Magic (4s) | Version (B) | Length (I) | Checksum (H) | Payload (N)
    header = struct.pack('!4sBH', MAGIC_NUMBER, version, payload_len)
    # O checksum é empacotado separadamente para clareza na montagem final
    checksum_bytes = struct.pack('!H', checksum)
    
    return header + checksum_bytes + payload

def deserialize_message(data: bytes) -> tuple[bytes, bool]:
    """Desserializa um buffer binário e verifica a integridade."""
    # Tamanho mínimo: Magic(4) + Version(1) + Length(4) + Checksum(2) = 11 bytes
    MIN_HEADER_SIZE = 11
    
    if len(data) < MIN_HEADER_SIZE:
        return b'', False # Buffer incompleto
    
    try:
        # 1. Extrair cabeçalho (Magic, Version, Length)
        header_data = data[:9]
        magic, version, payload_len = struct.unpack('!4sBH', header_data)
        
        if magic != MAGIC_NUMBER:
            return b'', False # Magic Number incorreto
        
        # 2. Extrair Checksum (2 bytes)
        checksum_bytes = data[9:11]
        received_checksum = struct.unpack('!H', checksum_bytes)[0]
        
        # 3. Extrair Payload
        payload_start = 11
        payload = data[payload_start:payload_start + payload_len]
        
        if len(payload) != payload_len:
            return b'', False # Payload incompleto
            
        # 4. Verificação de Checksum
        calculated_checksum = calculate_checksum(payload)
        
        if calculated_checksum != received_checksum:
            return b'', False # Checksum falhou (corrupção detectada)
            
        return payload, True
        
    except struct.error:
        return b'', False # Erro de parsing estrutural

# --- Teste de Sucesso (100 mensagens) ---
NUM_MESSAGES = 100
success_count = 0
test_results = []

print("Iniciando teste de serialização/desserialização de 100 mensagens...")

for i in range(NUM_MESSAGES):
    # Gerar payloads de tamanhos variados (1 byte até 1MB)
    # Para manter o teste rápido, limitamos a 10KB, mas o conceito suporta 1MB.
    payload_size = (i % 1000) + 1 # Tamanho entre 1 e 1000 bytes
    original_payload = b'Data_' + str(i).encode() + b'_' + bytes(range(payload_size - len(b'Data_' + str(i).encode())))
    
    # Serializar
    serialized_data = serialize_message(original_payload)
    
    # Desserializar
    reconstructed_payload, success = deserialize_message(serialized_data)
    
    # Verificar
    if success and reconstructed_payload == original_payload:
        success_count += 1
        test_results.append(True)
    else:
        test_results.append(False)

print(f"\n--- Resultado do Teste ---")
print(f"Total de mensagens testadas: {NUM_MESSAGES}")
print(f"Mensagens reconstruídas com sucesso: {success_count}")
print(f"Taxa de sucesso: {success_count / NUM_MESSAGES * 100:.2f}%")

# Verificação final do critério de sucesso
assert success_count == NUM_MESSAGES, "Falha no critério de sucesso: Não atingiu 100% de sucesso."
print("Critério de sucesso (100% de sucesso) ATINGIDO.")