import hashlib
import random

class CuckooFilter:
    """
    Implementação de um Filtro de Cuckoo em memória para testar a pertinência 
    de elementos de forma probabilística. Suporta inserção, consulta e deleção.
    """
    def __init__(self, capacity=1024, bucket_size=4, fingerprint_size=1, max_kicks=500):
        # A capacidade deve ser uma potência de 2 para o cálculo eficiente do índice via XOR/bitwise mask
        self.capacity = capacity
        self.bucket_size = bucket_size
        self.fingerprint_size = fingerprint_size  # em bytes (1 byte = 8 bits)
        self.max_kicks = max_kicks
        
        # Cada bucket é uma lista de fingerprints (valores inteiros ou bytes)
        # Inicialmente, vazios são representados por 0 (assumindo que fingerprint 0 não é válido)
        self.buckets = [[0] * bucket_size for _ in range(capacity)]
        self.num_items = 0

    def _hash(self, item: str) -> int:
        """Gera um hash inteiro de 64 bits para o item."""
        h = hashlib.blake2b(item.encode('utf-8'), digest_size=8).digest()
        return int.from_bytes(h, byteorder='big')

    def _fingerprint(self, item_hash: int) -> int:
        """
        Gera um fingerprint de tamanho fixo a partir do hash do item.
        Evita o equívoco comum de usar o hash completo (mantém ganho de espaço).
        Garante que o fingerprint nunca seja 0 (0 indica bucket vazio).
        """
        mask = (1 << (self.fingerprint_size * 8)) - 1
        fp = item_hash & mask
        if fp == 0:
            fp = 1
        return fp

    def _index1(self, item_hash: int) -> int:
        """Calcula o primeiro índice de bucket candidato."""
        return item_hash % self.capacity

    def _index2(self, current_index: int, fingerprint: int) -> int:
        """
        Calcula o segundo índice alternativo usando a técnica de partial-key cuckoo hashing:
        index2 = index1 ^ hash(fingerprint)
        Isso garante que index1(index2(i)) == i.
        """
        fp_hash = hashlib.blake2b(str(fingerprint).encode('utf-8'), digest_size=8).digest()
        h2 = int.from_bytes(fp_hash, byteorder='big')
        return (current_index ^ h2) % self.capacity

    def insert(self, item: str) -> bool:
        """
        Insere uma chave no filtro. Retorna True se bem-sucedido, False se o filtro estiver cheio
        ou atingir o limite de 'kicks'.
        """
        if self.search(item):
            # Opcional: permitir duplicatas ou ignorar. Aqui permitimos se couber, mas vamos tratar chaves únicas.
            pass

        h = self._hash(item)
        fp = self._fingerprint(h)
        i1 = self._index1(h)
        i2 = self._index2(i1, fp)

        # Tenta inserir em um slot livre no bucket 1
        for idx in range(self.bucket_size):
            if self.buckets[i1][idx] == 0:
                self.buckets[i1][idx] = fp
                self.num_items += 1
                return True

        # Tenta inserir em um slot livre no bucket 2
        for idx in range(self.bucket_size):
            if self.buckets[i2][idx] == 0:
                self.buckets[i2][idx] = fp
                self.num_items += 1
                return True

        # Se ambos os buckets estiverem cheios, fazemos o "cuckoo displacement" (evicts random entry)
        current_index = random.choice([i1, i2])
        current_fp = fp

        for _ in range(self.max_kicks):
            # Escolhe aleatoriamente um slot no bucket atual para desalojar
            slot = random.randrange(self.bucket_size)
            # Troca o fingerprint existente pelo novo
            self.buckets[current_index][slot], current_fp = current_fp, self.buckets[current_index][slot]
            
            # Calcula o próximo índice alternativo para o fingerprint desalojado
            current_index = self._index2(current_index, current_fp)

            # Tenta inserir o fingerprint desalojado em um slot livre do novo bucket
            for idx in range(self.bucket_size):
                if self.buckets[current_index][idx] == 0:
                    self.buckets[current_index][idx] = current_fp
                    self.num_items += 1
                    return True

        # Se esgotar os kicks, a inserção falha (requer resize ou o filtro está saturado)
        return False

    def search(self, item: str) -> bool:
        """
        Verifica a pertinência do item em tempo O(1) médio (checa apenas dois buckets).
        """
        h = self._hash(item)
        fp = self._fingerprint(h)
        i1 = self._index1(h)
        i2 = self._index2(i1, fp)

        if fp in self.buckets[i1] or fp in self.buckets[i2]:
            return True
        return False

    def delete(self, item: str) -> bool:
        """
        Remove um item do filtro, zerando o slot correspondente do fingerprint.
        Corrige o equívoco comum de achar que a deleção exige rehash de toda a estrutura.
        """
        h = self._hash(item)
        fp = self._fingerprint(h)
        i1 = self._index1(h)
        i2 = self._index2(i1, fp)

        for idx in range(self.bucket_size):
            if self.buckets[i1][idx] == fp:
                self.buckets[i1][idx] = 0
                self.num_items -= 1
                return True

        for idx in range(self.bucket_size):
            if self.buckets[i2][idx] == fp:
                self.buckets[i2][idx] = 0
                self.num_items -= 1
                return True

        return False