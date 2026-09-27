import io

# --- CONSTANTES E CONFIGURAÇÕES DE SEGURANÇA ---
WIRE_VARINT = 0
WIRE_LENGTH_DELIMITED = 2

MAX_RECURSION_DEPTH = 64
MAX_BUFFER_SIZE = 64 * 1024 * 1024  # 64 MB
MAX_FIELD_NUMBER = (1 << 29) - 1

def encode_varint(value: int) -> bytes:
    """Codifica um inteiro sem sinal no formato Varint (LEB128)."""
    if value < 0:
        value &= 0xFFFFFFFFFFFFFFFF
    
    result = bytearray()
    while True:
        to_write = value & 0x7F
        value >>= 7
        if value:
            result.append(to_write | 0x80)
        else:
            result.append(to_write)
            break
    return bytes(result)

def decode_varint(buffer: bytes, pos: int):
    """Decodifica um Varint com proteção contra overflow e over-encoding (máx 10 bytes)."""
    result = 0
    shift = 0
    start_pos = pos
    while True:
        if pos >= len(buffer):
            raise ValueError("Buffer truncado ao ler varint")
        b = buffer[pos]
        pos += 1
        
        # Um varint de 64 bits pode ocupar no máximo 10 bytes
        if (pos - start_pos) > 10:
            raise ValueError("Varint excede o tamanho máximo permitido (overflow/over-encoding)")
            
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
        if shift >= 64:
            raise ValueError("Varint muito longo (deslocamento >= 64)")
    return result, pos

def encode_tag(field_number: int, wire_type: int) -> bytes:
    """Codifica a tag validando o intervalo do número do campo."""
    if not (1 <= field_number <= MAX_FIELD_NUMBER):
        raise ValueError(f"Número de campo inválido: {field_number}")
    return encode_varint((field_number << 3) | wire_type)

class SecureProtoMessage:
    def __init__(self, field_id: int = 0, name: str = "", nested=None):
        self.field_id = field_id
        self.name = name
        self.nested = nested

    def serialize(self) -> bytes:
        """Serializa a mensagem omitindo campos com valores default (regra proto3)."""
        buffer = bytearray()
        
        # Campo 1: field_id (varint) - omitido se for 0 (default do proto3)
        if self.field_id != 0:
            buffer.extend(encode_tag(1, WIRE_VARINT))
            buffer.extend(encode_varint(self.field_id))
            
        # Campo 2: name (string) - omitido se for vazio (default do proto3)
        if self.name and self.name != "":
            encoded_name = self.name.encode('utf-8', errors='strict')
            buffer.extend(encode_tag(2, WIRE_LENGTH_DELIMITED))
            buffer.extend(encode_varint(len(encoded_name)))
            buffer.extend(encoded_name)
            
        # Campo 3: nested (sub-mensagem) - omitido se for None
        if self.nested is not None:
            nested_bytes = self.nested.serialize()
            if nested_bytes:
                buffer.extend(encode_tag(3, WIRE_LENGTH_DELIMITED))
                buffer.extend(encode_varint(len(nested_bytes)))
                buffer.extend(nested_bytes)
                
        return bytes(buffer)

    @classmethod
    def parse(cls, buffer: bytes, depth: int = 0):
        """Desserializa o buffer aplicando estritamente limites de segurança e validações."""
        if depth > MAX_RECURSION_DEPTH:
            raise ValueError(f"Profundidade máxima de aninhamento excedida ({MAX_RECURSION_DEPTH})")
        if len(buffer) > MAX_BUFFER_SIZE:
            raise ValueError(f"Buffer excede o tamanho máximo permitido ({MAX_BUFFER_SIZE} bytes)")

        field_id = 0
        name = ""
        nested = None
        
        pos = 0
        length = len(buffer)
        
        while pos < length:
            tag, pos = decode_varint(buffer, pos)
            field_number = tag >> 3
            wire_type = tag & 0x07
            
            if not (1 <= field_number <= MAX_FIELD_NUMBER):
                raise ValueError(f"Número de campo fora do intervalo válido: {field_number}")
                
            if field_number == 1:
                if wire_type != WIRE_VARINT:
                    raise TypeError(f"Wire type incorreto para field_id (esperado 0, obtido {wire_type})")
                field_id, pos = decode_varint(buffer, pos)
                
            elif field_number == 2:
                if wire_type != WIRE_LENGTH_DELIMITED:
                    raise TypeError(f"Wire type incorreto para name (esperado 2, obtido {wire_type})")
                str_len, pos = decode_varint(buffer, pos)
                if pos + str_len > length:
                    raise ValueError("Buffer truncado ao ler string length-delimited")
                raw_str_bytes = buffer[pos:pos+str_len]
                pos += str_len
                try:
                    name = raw_str_bytes.decode('utf-8', errors='strict')
                except UnicodeDecodeError as e:
                    raise ValueError(f"String UTF-8 inválida: {e}")
                    
            elif field_number == 3:
                if wire_type != WIRE_LENGTH_DELIMITED:
                    raise TypeError(f"Wire type incorreto para nested (esperado 2, obtido {wire_type})")
                msg_len, pos = decode_varint(buffer, pos)
                if pos + msg_len > length:
                    raise ValueError("Buffer truncado ao ler sub-mensagem length-delimited")
                sub_buffer = buffer[pos:pos+msg_len]
                pos += msg_len
                nested = cls.parse(sub_buffer, depth + 1)
                
            else:
                # Campos desconhecidos ignorados (forward compatibility do Protobuf)
                if wire_type == WIRE_VARINT:
                    _, pos = decode_varint(buffer, pos)
                elif wire_type == WIRE_LENGTH_DELIMITED:
                    str_len, pos = decode_varint(buffer, pos)
                    pos += str_len
                else:
                    raise TypeError(f"Wire type desconhecido/não suportado: {wire_type}")
                    
        return cls(field_id=field_id, name=name, nested=nested)

# --- TESTES AUTOMATIZADOS DE VALIDAÇÃO E SEGURANÇA ---

def test_proto3_default_omission():
    """Valida que campos com valores default (0 e string vazia) são omitidos na serialização."""
    msg = SecureProtoMessage(field_id=0, name="", nested=None)
    binary = msg.serialize()
    assert len(binary) == 0, fEsperado buffer vazio para valores default, obtido {len(binary)} bytes"
    print("Teste de omissão de defaults proto3 passou com sucesso!")

def test_security_adversarial_limits():
    """Testa defesas contra entradas maliciosas (overflow de varint, profundidade excessiva, UTF-8 inválido)."""
    
    # 1. Varint excessivamente longo (over-encoding / overflow)
    malicious_varint = b'\x80' * 15 + b'\x01'
    try:
        decode_varint(malicious_varint, 0)
        assert False, "Deveria ter falhado por varint muito longo"
    except ValueError as e:
        print(f"Defesa contra varint overflow validada: {e}")

    # 2. String UTF-8 inválida
    invalid_utf8_data = encode_tag(2, WIRE_LENGTH_DELIMITED) + encode_varint(2) + b'\xff\xff'
    try:
        SecureProtoMessage.parse(invalid_utf8_data)
        assert False, "Deveria ter falhado por UTF-8 inválido"
    except ValueError as e:
        print(f"Defesa contra UTF-8 corrompido validada: {e}")

    # 3. Profundidade excessiva de sub-mensagens (Stack Overflow protection)
    # Constrói mensagem aninhada recursiva profunda (>64 níveis)
    deep_msg = SecureProtoMessage(field_id=1, name="leaf")
    for _ in range(70):
        deep_msg = SecureProtoMessage(field_id=1, name="parent", nested=deep_msg)
    
    try:
        deep_bytes = deep_msg.serialize()
        SecureProtoMessage.parse(deep_bytes)
        assert False, "Deveria ter falhado por excesso de profundidade"
    except ValueError as e:
        print(f"Defesa contra profundidade excessiva validada: {e}")

def test_round_trip_secure():
    """Valida o round-trip completo com estruturas aninhadas válidas."""
    inner = SecureProtoMessage(field_id=42, name="inner_secure")
    original = SecureProtoMessage(field_id=100, name="root_secure", nested=inner)
    
    binary = original.serialize()
    decoded = SecureProtoMessage.parse(binary)
    
    assert decoded.field_id == original.field_id
    assert decoded.name == original.name
    assert decoded.nested.field_id == inner.field_id
    assert decoded.nested.name == inner.name
    print("Teste de Round-Trip seguro passou 100%!")

if __name__ == "__main__":
    test_proto3_default_omission()
    test_security_adversarial_limits()
    test_round_trip_secure()