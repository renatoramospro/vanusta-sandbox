import json

# Codificação Varint e ZigZag corrigida e robusta
def encode_varint(n: int) -> bytes:
    zigzag = (n << 1) ^ (n >> 63) if n < 0 else (n << 1)
    bytes_list = []
    while True:
        byte = zigzag & 0x7F
        zigzag >>= 7
        if zigzag == 0:
            bytes_list.append(byte)
            break
        else:
            bytes_list.append(byte | 0x80)
    return bytes(bytes_list)

def decode_varint(data: bytes, index: int):
    shift = 0
    value = 0
    while True:
        if index >= len(data):
            raise ValueError("Fim inesperado dos dados ao ler varint.")
        b = data[index]
        index += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    
    unzigzag = (value >> 1) ^ -(value & 1)
    return unzigzag, index

class MotorAvroSimulado:
    """
    Motor que serializa um dicionário Python baseado em um schema simplificado
    para formato binário compacto (simulando Apache Avro) e vice-versa,
    com suporte a inteiros negativos via ZigZag e campos opcionais (nulos/ausentes).
    """
    def __init__(self, schema: dict):
        self.schema = schema

    def serializar(self, record: dict) -> bytes:
        buffer = bytearray()
        for field in self.schema["fields"]:
            name = field["name"]
            ftype = field["type"]
            val = record.get(name, None)

            # Trata tipos union opcionais como ["null", "<tipo>"]
            is_union = isinstance(ftype, list)
            if is_union:
                if "null" in ftype:
                    if val is None:
                        buffer.append(0) # Índice 0 para null
                        continue
                    else:
                        buffer.append(1) # Índice 1 para o tipo real
                        actual_type = [t for t in ftype if t != "null"][0]
                else:
                    actual_type = ftype[0]
            else:
                actual_type = ftype

            # Serialização por tipo
            if actual_type == "int":
                if val is None:
                    val = 0
                buffer.extend(encode_varint(val))
            elif actual_type == "string":
                if val is None:
                    val = ""
                encoded_str = val.encode("utf-8")
                buffer.extend(encode_varint(len(encoded_str)))
                buffer.extend(encoded_str)
            else:
                raise ValueError(f"Tipo não suportado: {actual_type}")
        return bytes(buffer)

    def desserializar(self, data: bytes) -> dict:
        record = {}
        index = 0
        for field in self.schema["fields"]:
            name = field["name"]
            ftype = field["type"]

            is_union = isinstance(ftype, list)
            if is_union:
                if "null" in ftype:
                    if index >= len(data):
                        raise ValueError("Fim inesperado dos dados.")
                    union_index = data[index]
                    index += 1
                    if union_index == 0:
                        record[name] = None
                        continue
                    actual_type = [t for t in ftype if t != "null"][0]
                else:
                    actual_type = ftype[0]
            else:
                actual_type = ftype

            if actual_type == "int":
                val, index = decode_varint(data, index)
                record[name] = val
            elif actual_type == "string":
                str_len, index = decode_varint(data, index)
                if index + str_len > len(data):
                    raise ValueError("Fim inesperado ao ler string.")
                val = data[index:index + str_len].decode("utf-8")
                index += str_len
                record[name] = val
            else:
                raise ValueError(f"Tipo não suportado: {actual_type}")
        return record

if __name__ == "__main__":
    schema_usuario = {
        "type": "record",
        "name": "Usuario",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "nome", "type": ["null", "string"]},
            {"name": "idade", "type": "int"}
        ]
    }

    motor = MotorAvroSimulado(schema_usuario)

    # Cenário 1: Comum
    dado_comum = {"id": 1, "nome": "Ana", "idade": 30}
    binario_comum = motor.serializar(dado_comum)
    reconstruido_comum = motor.desserializar(binario_comum)
    assert reconstruido_comum == dado_comum, f"Esperado {dado_comum}, obtido {reconstruido_comum}"
    print("Cenário Comum: PASSOU")

    # Cenário 2: Borda com inteiros negativos (ZigZag corrigido)
    dado_negativo = {"id": -10, "nome": "Carlos", "idade": -5}
    binario_negativo = motor.serializar(dado_negativo)
    reconstruido_negativo = motor.desserializar(binario_negativo)
    assert reconstruido_negativo == dado_negativo, f"Esperado {dado_negativo}, obtido {reconstruido_negativo}"
    print("Cenário Borda (Negativos): PASSOU")

    # Cenário 3: Adversarial com campos opcionais nulos
    dado_adversarial = {"id": 0, "nome": None, "idade": 99}
    binario_adversarial = motor.serializar(dado_adversarial)
    reconstruido_adversarial = motor.desserializar(binario_adversarial)
    assert reconstruido_adversarial == dado_adversarial, f"Esperado {dado_adversarial}, obtido {reconstruido_adversarial}"
    print("Cenário Adversarial (Nulos/Opcionais): PASSOU")

    print("Sucesso absoluto: Todos os cenários foram validados com sucesso.")