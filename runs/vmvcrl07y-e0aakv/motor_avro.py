import json
import struct

# Simulação da Codificação Varint (utilizada pelo Avro)
def encode_varint(n: int) -> bytes:
    # Codificação ZigZag para suportar números negativos
    # Fórmula: (n << 1) ^ (n >> 31) para 32-bit
    zigzag = (n << 1) ^ (n >> 31)
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
    # Decodificação ZigZag reversa
    unzigzag = (value >> 1) ^ -(value & 1)
    return unzigzag, index

class MotorAvroSimulado:
    """
    Motor que serializa um dicionário Python baseado em um schema simplificado
    para formato binário compacto (simulando Apache Avro) e vice-versa.
    """
    def __init__(self, schema: dict):
        self.schema = schema

    def serializar(self, record: dict) -> bytes:
        buffer = bytearray()
        for field in self.schema["fields"]:
            fname = field["name"]
            ftype = field["type"]
            val = record.get(fname)
            
            if ftype == "int":
                buffer.extend(encode_varint(int(val)))
            elif ftype == "string":
                encoded_str = val.encode("utf-8")
                buffer.extend(encode_varint(len(encoded_str)))
                buffer.extend(encoded_str)
            else:
                raise ValueError(f"Tipo não suportado neste protótipo: {ftype}")
        return bytes(buffer)

    def desserializar(self, data: bytes) -> dict:
        record = {}
        index = 0
        for field in self.schema["fields"]:
            fname = field["name"]
            ftype = field["type"]
            
            if ftype == "int":
                val, index = decode_varint(data, index)
                record[fname] = val
            elif ftype == "string":
                length, index = decode_varint(data, index)
                val_bytes = data[index:index+length]
                index += length
                record[fname] = val_bytes.decode("utf-8")
        return record

# --- Execução do Experimento e Validação ---
if __name__ == "__main__":
    schema_usuario = {
        "type": "record",
        "name": "Usuario",
        "fields": [
            {"name": "id", "type": "int"},
            {"name": "nome", "type": "string"},
            {"name": "idade", "type": "int"}
        ]
    }

    motor = MotorAvroSimulado(schema_usuario)

    dado_original = {"id": 15049, "nome": "Vanusta Arquiteta", "idade": 30}
    
    # Serialização Binária
    binario = motor.serializar(dado_original)
    
    # Serialização JSON (para comparação de tamanho)
    json_bytes = json.dumps(dado_original).encode("utf-8")

    print(f"Payload JSON ({len(json_bytes)} bytes): {json_bytes}")
    print(f"Payload Avro Binário ({len(binario)} bytes): {binario}")

    # Desserialização de volta para Objeto/JSON
    dado_reconstruido = motor.desserializar(binario)
    print(f"Dado Desserializado: {dado_reconstruido}")

    # Asserções de Sucesso Rigorosas
    assert dado_reconstruido == dado_original, "Erro: O dado desserializado difere do original!"
    print("Sucesso: A serialização e desserialização binária ocorreram com 100% de fidelidade.")