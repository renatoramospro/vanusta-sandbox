import struct
import zlib

# Definindo o formato de cabeçalho:
# Magic (4s), Version (B), Length (I), Checksum (H)
# Nota: O struct.pack/unpack deve refletir a ordem de montagem: Magic(4s), Version(B), Length(I), Checksum(H)
# O formato de empacotamento do cabeçalho fixo (sem o payload) é: !4sBH H
HEADER_FORMAT_FIXED = '!4sBH' # Magic (4s), Version (B), Length (I)
HEADER_SIZE_FIXED = struct.calcsize(HEADER_FORMAT_FIXED) # 9 bytes
CHECKSUM_SIZE = 2
MIN_HEADER_SIZE = HEADER_SIZE_FIXED + CHECKSUM_SIZE # 11 bytes

MAGIC_NUMBER = b'VNST'
PROTOCOL_VERSION = 1

def calculate_checksum(data: bytes) -> int:
    """Simula um CRC-16 simples para o payload."""
    return (sum(data) % 65536) & 0xFFFF

def serialize_message(payload: bytes, version: int = PROTOCOL_VERSION) -> bytes:
    """Serializa um payload binário de acordo com o protocolo VNST."""
    payload_len = len(payload)
    checksum = calculate_checksum(payload)
    
    # Estrutura de serialização: Magic (4s) | Version (B) | Length (I) | Checksum (H) | Payload (N)
    # Montamos o cabeçalho fixo primeiro
    header_fixed = struct.pack(HEADER_FORMAT_FIXED, MAGIC_NUMBER, version, payload_len)
    # Em seguida, o checksum
    checksum_bytes = struct.pack('!H', checksum)
    
    return header_fixed + checksum_bytes + payload

def deserialize_message(data: bytes) -> tuple[bytes, bool]:
    """Desserializa um buffer binário e verifica a integridade."""
    
    if len(data) < MIN_HEADER_SIZE:
        return b'', False # Buffer incompleto
    
    try:
        # 1. Extrair cabeçalho fixo (Magic, Version, Length)
        header_data = data[:HEADER_SIZE_FIXED]
        magic, version, payload_len = struct.unpack(HEADER_FORMAT_FIXED, header_data)
        
        if magic != MAGIC_NUMBER:
            return b'', False # Magic Number incorreto
        
        # 2. Verificar se o buffer tem o tamanho total esperado
        expected_total_size = MIN_HEADER_SIZE + payload_len
        if len(data) < expected_total_size:
            return b'', False # Buffer truncado (não contém o payload completo)
        
        # 3. Extrair Checksum (2 bytes)
        checksum_bytes = data[HEADER_SIZE_FIXED:MIN_HEADER_SIZE]
        received_checksum = struct.unpack('!H', checksum_bytes)[0]
        
        # 4. Extrair Payload
        payload = data[MIN_HEADER_SIZE:expected_total_size]
        
        # 5. Verificação de Checksum
        calculated_checksum = calculate_checksum(payload)
        
        if received_checksum != calculated_checksum:
            return b'', False # Checksum inválido
            
        return payload, True
        
    except struct.error:
        return b'', False # Erro de parsing estrutural

# --- Teste de Carga ---
NUM_MESSAGES = 100
test_results = []

print("Iniciando teste de serialização/desserialização de 100 mensagens...")

for i in range(NUM_MESSAGES):
    # Gerar payloads de tamanhos variados (1 a 1024 bytes)
    payload_size = (i % 1024) + 1
    original_payload = bytes([i % 256] * payload_size)
    
    # Serializar
    serialized_data = serialize_message(original_payload)
    
    # Desserializar
    reconstructed_payload, success = deserialize_message(serialized_data)
    
    # Verificar
    if success and reconstructed_payload == original_payload:
        test_results.append(True)
    else:
        test_results.append(False)

success_count = sum(test_results)

print(f"\n--- Resultado do Teste ---")
print(f"Total de mensagens testadas: {NUM_MESSAGES}")
print(f"Mensagens reconstruídas com sucesso: {success_count}")
print(f"Taxa de sucesso: {success_count / NUM_MESSAGES * 100:.2f}%")

# Verificação final do critério de sucesso
assert success_count == NUM_MESSAGES, "Falha no critério de sucesso: Não atingiu 100% de sucesso."
print("Critério de sucesso (100% de sucesso) ATINGIDO.")