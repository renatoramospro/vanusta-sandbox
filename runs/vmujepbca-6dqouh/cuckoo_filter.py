import hashlib

class CuckooFilter:
    """
    Implementação de um Filtro de Cuckoo em memória para testar a pertinência 
    de elementos de forma probabilística. Suporta inserção, consulta e deleção.
    """
    def __init__(self, capacity=16384, bucket_size=4, fingerprint_size=2, max_kicks=500):
        # A capacidade deve ser uma potência de 2 para o cálculo eficiente do índice via XOR
        self.capacity = capacity
        self.bucket_size = bucket_size
        self.fingerprint_size = fingerprint_size  # em bytes (2 bytes = 16 bits)
        self.max_kicks = max_kicks
        
        # Cada bucket é uma lista de fingerprints
        # Vazios são representados por 0 (fingerprint 0 é reservado para indicar slot vazio)
        self.buckets = [[0] * bucket_size for _ in range(capacity)]
        self.num_items = 0

    def _hash(self, item: str) -> int:
        """Gera um hash inteiro de 64 bits para o item."""
        h = hashlib.blake2b(item.encode('utf-8'), digest_size=8).digest()
        return int.from_bytes(h, byteorder='big')

    def _fingerprint(self, item_hash: int) -> int:
        """
        Gera um fingerprint de tamanho fixo a partir do hash do item.
        Garante que o fingerprint nunca seja 0 (0 indica bucket vazio).
        """
        mask = (1 << (self.fingerprint_size * 8)) - 1
        fp = item_hash & mask
        if fp == 0:
            fp = 1
        return fp

    def _index1(self, item_hash: int) -> int:
        """Calcula o primeiro índice de bucket para o item."""
        # Usa os bits superiores ou uma divisão/máscara limpa
        return (item_hash >> 32) % self.capacity

    def _index2(self, index1: int, fingerprint: int) -> int:
        """
        Calcula o segundo índice alternativo usando partial-key cuckoo hashing:
        index2 = index1 ^ hash(fingerprint)
        Garante independência estatística usando os bytes brutos do fingerprint.
        """
        fp_bytes = fingerprint.to_bytes(self.fingerprint_size, byteorder='big')
        h = hashlib.blake2b(fp_bytes, digest_size=8).digest()
        fp_hash = int.from_bytes(h, byteorder='big')
        return (index1 ^ fp_hash) % self.capacity

    def insert(self, item: str) -> bool:
        """
        Insere uma chave no filtro. Retorna True se bem-sucedido, 
        ou False se o filtro estiver cheio (excedeu max_kicks).
        """
        item_hash = self._hash(item)
        fp = self._fingerprint(item_hash)
        i1 = self._index1(item_hash)
        i2 = self._index2(i1, fp)

        # 1. Tenta inserir em i1
        for slot in range(self.bucket_size):
            if self.buckets[i1][slot] == 0:
                self.buckets[i1][slot] = fp
                self.num_items += 1
                return True

        # 2. Tenta inserir em i2
        for slot in range(self.bucket_size):
            if self.buckets[i2][slot] == 0:
                self.buckets[i2][slot] = fp
                self.num_items += 1
                return True

        # 3. Nenhum slot livre: realiza o processo de "kick" (deslocamento aleatório)
        current_index = i1 if (hashlib.blake2b(item.encode()).digest()[0] % 2 == 0) else i2
        current_fp = fp

        for _ in range(self.max_kicks):
            # Sorteia um slot aleatório no balde atual para desalojar
            slot = hashlib.blake2b(current_fp.to_bytes(self.fingerprint_size, 'big')).digest()[0] % self.bucket_size
            
            # Troca o fingerprint atual com o do slot
            old_fp = self.buckets[current_index][slot]
            self.buckets[current_index][slot] = current_fp
            current_fp = old_fp

            # Calcula o índice alternativo do fingerprint desalojado
            current_index = self._index2(current_index, current_fp)

            # Tenta inserir o fingerprint desalojado em um slot vazio no novo índice
            for s in range(self.bucket_size):
                if self.buckets[current_index][s] == 0:
                    self.buckets[current_index][s] = current_fp
                    self.num_items += 1
                    return True

        # Se esgotou os kicks, o filtro está cheio
        return False

    def search(self, item: str) -> bool:
        """
        Verifica se a chave possivelmente pertence ao conjunto (O(1)).
        """
        item_hash = self._hash(item)
        fp = self._fingerprint(item_hash)
        i1 = self._index1(item_hash)
        i2 = self._index2(i1, fp)

        # Verifica no balde 1
        if fp in self.buckets[i1]:
            return True

        # Verifica no balde 2
        if fp in self.buckets[i2]:
            return True

        return False

    def delete(self, item: str) -> bool:
        """
        Remove uma chave do filtro, se presente. Retorna True se removido, False caso contrário.
        """
        item_hash = self._hash(item)
        fp = self._fingerprint(item_hash)
        i1 = self._index1(item_hash)
        i2 = self._index2(i1, fp)

        # Procura e remove no balde 1
        for slot in range(self.bucket_size):
            if self.buckets[i1][slot] == fp:
                self.buckets[i1][slot] = 0
                self.num_items -= 1
                return True

        # Procura e remove no balde 2
        for slot in range(self.bucket_size):
            if self.buckets[i2][slot] == fp:
                self.buckets[i2][slot] = 0
                self.num_items -= 1
                return True

        return False