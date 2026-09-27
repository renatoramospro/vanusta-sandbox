import io

# --- IMPLEMENTAÇÃO DO PROTOBUF DO ZERO ---

# Wire Types
WIRE_VARINT = 0
WIRE_LENGTH_DELIMITED = 2

def encode_varint(value: int) -> bytes:
    """Codifica um inteiro sem sinal no formato Varint (LEB128)."""
    if value < 0:
        # No proto3, int32/int64 negativos são tratados como 64-bits e usam 10 bytes no varint padrão
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
    """Decodifica um Varint a partir de um buffer de bytes na posição dada."""
    result = 0
    shift = 0
    while True:
        if pos >= len(buffer):
            raise ValueError("Buffer truncado ao ler varint")
        b = buffer[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
        if shift >= 64:
            raise ValueError("Varint muito longo (overflow)")
    return result, pos

def encode_tag(field_number: int, wire_type: int) -> bytes:
    """Codifica a tag combinando o número do campo e o wire type."""
    return encode_varint((field_number << 3) | wire_type)

class SimpleProtoMessage:
    def __init__(self, field_id: int = 0, name: str = "", nested = None):
        self.field_id = field_id
        self.name = name
        self.nested = nested # Outra instância de SimpleProtoMessage ou None

    def serialize(self) -> bytes:
        buf = bytearray()
        
        # Campo 1: field_id (int32 -> wire type 0)
        if self.field_id != 0:
            buf.extend(encode_tag(1, WIRE_VARINT))
            buf.extend(encode_varint(self.field_id))
            
        # Campo 2: name (string -> wire type 2)
        if self.name:
            encoded_name = self.name.encode('utf-8')
            buf.extend(encode_tag(2, WIRE_LENGTH_DELIMITED))
            buf.extend(encode_varint(len(encoded_name)))
            buf.extend(encoded_name)
            
        # Campo 3: nested (sub-mensagem -> wire type 2)
        if self.nested is not None:
            nested_bytes = self.nested.serialize()
            buf.extend(encode_tag(3, WIRE_LENGTH_DELIMITED))
            buf.extend(encode_varint(len(nested_bytes)))
            buf.extend(nested_bytes)
            
        return bytes(buf)

    @classmethod
    def parse(cls, data: bytes):
        msg = cls()
        pos = 0
        while pos < len(data):
            tag, pos = decode_varint(data, pos)
            wire_type = tag & 0x07
            field_number = tag >> 3
            
            if field_number == 1:
                if wire_type != WIRE_VARINT:
                    raise TypeError("Wire type incorreto para field_id")
                msg.field_id, pos = decode_varint(data, pos)
            elif field_number == 2:
                if wire_type != WIRE_LENGTH_DELIMITED:
                    raise TypeError("Wire type incorreto para name")
                length, pos = decode_varint(data, pos)
                msg.name = data[pos:pos+length].decode('utf-8')
                pos += length
            elif field_number == 3:
                if wire_type != WIRE_LENGTH_DELIMITED:
                    raise TypeError("Wire type incorreto para sub-mensagem")
                length, pos = decode_varint(data, pos)
                sub_data = data[pos:pos+length]
                msg.nested = cls.parse(sub_data)
                pos += length
            else:
                # Pular campos desconhecidos (avanço básico por wire type)
                if wire_type == WIRE_VARINT:
                    _, pos = decode_varint(data, pos)
                elif wire_type == WIRE_LENGTH_DELIMITED:
                    length, pos = decode_varint(data, pos)
                    pos += length
                else:
                    raise ValueError(f"Wire type desconhecido: {wire_type}")
        return msg


# --- TESTES DE VALIDAÇÃO E ROUND-TRIP ---

def test_round_trip():
    # Criando mensagem aninhada complexa
    inner = SimpleProtoMessage(field_id=42, name="inner_proto")
    original = SimpleProtoMessage(field_id=100, name="root_proto", nested=inner)
    
    # Serialização
    binary_data = original.serialize()
    print(f"Bytes serializados com sucesso ({len(binary_data)} bytes): {binary_data.hex()}")
    
    # Desserialização (Round-Trip)
    decoded = SimpleProtoMessage.parse(binary_data)
    
    # Validação de fidelidade
    assert decoded.field_id == original.field_id, f"Esperado {original.field_id}, obtido {decoded.field_id}"
    assert decoded.name == original.name, f"Esperado {original.name}, obtido {decoded.name}"
    assert decoded.nested is not None, "Sub-mensagem não deveria ser nula"
    assert decoded.nested.field_id == inner.field_id, "Fidelidade binária falhou no campo aninhado (id)"
    assert decoded.nested.name == inner.name, "Fidelidade binária falhou no campo aninhado (name)"
    
    print("Teste de Round-Trip com sub-mensagens passou 100%!")

def test_equivoco_comum_wire_type():
    """Demonstra que desserializar com wire type incorreto levanta exceção (contraexemplo)."""
    # Enviar um varint forçando wire type de length-delimited (2)
    bad_data = encode_tag(1, WIRE_LENGTH_DELIMITED) + encode_varint(15)
    try:
        SimpleProtoMessage.parse(bad_data)
        assert False, "Deveria ter falhado ao encontrar wire type incompatível"
    except TypeError as e:
        print(f"Contraexemplo capturado com sucesso: {e}")

if __name__ == "__main__":
    test_round_trip()
    test_equivoco_comum_wire_type()