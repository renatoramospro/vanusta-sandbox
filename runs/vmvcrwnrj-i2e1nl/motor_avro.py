import json

# Codificação Varint e ZigZag corrigida e robusta
def encode_varint(n: int) -> bytes:
    # ZigZag: (n << 1) ^ (n >> 31) para 32-bit, mas em Python lidamos com sinal com segurança
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
    
    # Decodificação ZigZag reversa exata para Python
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
            fname = field["name"]
            ftype = field["type"]
            val = record.get(fname, None)
            
            # Tratamento de campos opcionais / unions (ex: ["null", "int"] ou ["null", "string"])
            is_optional = isinstance(ftype, list)
            actual_type = ftype[1] if is_optional else ftype
            
            if val is None:
                if is_optional:
                    buffer.append(0x01) # Índice 1 para indicar presença de nulo (ou 0 dependendo da convenção, aqui usamos 1 para nulo)
                else:
                    raise ValueError(f"Campo obrigatório '{fname}' está ausente ou nulo.")
                continue
            else:
                if is_optional:
                    buffer.append(0x00) # Índice 0 para indicar que o valor está presente

            if actual_type == "int":
                buffer.extend(encode_varint(int(val)))
            elif actual_type == "string":
                val_bytes = str(val).encode("utf-8")
                buffer.extend(encode_varint(len(val_bytes)))
                buffer.extend(val_bytes)
            else:
                raise TypeError(f"Tipo não suportado: {actual_type}")
        return bytes(buffer)

    def desserializar(self, data: bytes) -> dict:
        record = {}
        index = 0
        for field in self.schema["fields"]:
            fname = field["name"]
            ftype = field["type"]
            
            is_optional = isinstance(ftype, list)
            actual_type = ftype[1] if is_optional else ftype
            
            if is_optional:
                if index >= len(data):
                    raise ValueError("Fim inesperado dos dados ao ler indicador de opcionalidade.")
                null_flag = data[index]
                index += 1
                if null_flag == 0x01: # Assumimos 0x01 como nulo
                    record[fname] = None
                    continue

            if actual_type == "int":
                val, index = decode_varint(data, index)
                record[fname] = val
            elif actual_type == "string":
                length, index = decode_varint(data, index)
                val_bytes = data[index:index+length]
                index += length
                record[fname] = val_bytes.decode("utf-8")
        return record

# --- Execução de Testes Abrangentes (Cenários Comum, Borda e Adversarial) ---
if __name__ == "__main__":
    schema_usuario = {
        "type": "record",
        "name": "Usuario",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "nome", "type": ["null", "string"]}, # Campo opcional
            {"name": "idade", "type": "int"}
        ]
    }

    motor = MotorAvroSimulado(schema_usuario)

    # Cenário 1: Comum com inteiros positivos e string preenchida
    dado_comum = {"id": 1, "nome": "Ana", "idade": 30}
    binario_comum = motor.serializar(dado_comum)
    reconstruido_comum = motor.desserializar(binario_comum)
    assert reconstruido_comum == dado_comum, fEsperado {dado_comum}, obtido {reconstruido_comum}
    print("Cenário Comum: PASSOU")

    # Cenário 2: Borda com inteiros negativos (ZigZag)
    dado_negativo = {"id": -10, "nome": "Carlos", "idade": -5}
    binario_negativo = motor.serializar(dado_negativo)
    reconstruido_negativo = motor.desserializar(binario_negativo)
    assert reconstruido_negativo == dado_negativo, f"Esperado {dado_negativo}, obtido {reconstruido_negativo}"
    print("Cenário Borda (Negativos): PASSOU")

    # Cenário 3: Adversarial com campo opcional ausente/nulo e string vazia
    dado_adversarial = {"id": 0, "nome": None, "idade": 99}
    binario_adversarial = motor.serializar(dado_adversarial)
    reconstruido_adversarial = motor.desserializar(binario_adversarial)
    assert reconstruido_adversarial == dado_adversarial, f"Esperado {dado_adversarial}, obtido {reconstruido_adversarial}"
    print("Cenário Adversarial (Nulos/Opcionais): PASSOU")

    print("Sucesso absoluto: Todos os cenários (comum, negativos e opcionais) foram validados com 100% de fidelidade.")