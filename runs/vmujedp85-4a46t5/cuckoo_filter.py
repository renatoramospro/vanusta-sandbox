import hashlib

class CuckooFilter:
    """
    Implementação de um Filtro de Cuckoo em memória para testar a pertinência 
    de elementos de forma probabilística. Suporta inserção, consulta e deleção.
    """
    def __init__(self, capacity=16384, bucket_size=4, fingerprint_size=2, max_kicks=500):
        # A capacidade deve ser uma potência de 2 para o cálculo eficiente do índice via XOR/bitwise mask
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
        """Calcula o primeiro índice de bucket candidato."""
        return item_hash % self.capacity

    def _index2(self, current_index: int, fingerprint: int) -> int:
        """
        Calcula o segundo índice alternativo usando partial-key cuckoo hashing:
        index2 = index1 ^ hash(fingerprint)
        Usamos uma função de hash robusta para o fingerprint e aplicamos XOR com o índice atual,
        garantindo dispersão uniforme e evitando colisões estruturais que elevavam os falsos positivos.
        """
        # Hash do fingerprint para garantir independência estatística
        fp_bytes = fingerprint.to_bytes(self.fingerprint_size, byteorder='big')
        h2_val = int.from_bytes(hashlib.blake2b(fp_bytes, digest_size=8).digest(), byteorder='big')
        return (current_index ^ h2_val) % self.capacity

    def insert(self, item: str) -> bool:
        """
        Insere uma chave no filtro. Retorna True se bem-sucedido, False se o filtro estiver cheio
        ou atingir o limite de 'kicks'.
        """
        h = self._hash(item)
        fp = self._fingerprint(h)
        i1 = self._index1(h)
        i2 = self._index2(i1, fp)

        # Verifica se já existe para evitar duplicatas desnecessárias (opcional, mas boa prática)
        if self.search(item):
            return True

        # Tenta inserir em um slot livre no bucket 1 ou bucket 2
        for idx in range(self.bucket_size):
            if self.buckets[i1][idx] == 0:
                self.buckets[i1][idx] = fp
                self.num_items += 1
                return True

        for idx in range(self.bucket_size):
            if self.buckets[i2][idx] == 0:
                self.buckets[i2][idx] = fp
                self.num_items += 1
                return True

        # Se ambos os buckets estiverem cheios, fazemos o "cuckoo eviction" (kicks)
        current_index = i1 if (hashlib.blake2b(str(h).encode()).digest()[0] % 2 == 0) else i2
        current_fp = fp

        for _ in range(self.max_kicks):
            # Escolhe um slot aleatório no bucket atual para desalojar
            slot_idx = hashlib.blake2b(str(current_fp).encode()).digest()[0] % self.bucket_size
            
            # Troca o fingerprint
            old_fp = self.buckets[current_index][slot_idx]
            self.buckets[current_index][slot_idx] = current_fp
            current_fp = old_fp

            # Calcula o próximo índice alternativo para o fingerprint desalojado
            current_index = self._index2(current_index, current_fp)

            for idx in range(self.bucket_size):
                if self.buckets[current_index][idx] == 0:
                    self.buckets[current_index][idx] = current_fp
                    self.num_items += 1
                    return True

        return False  # Filtro cheio / falha nos kicks

    def search(self, item: str) -> bool:
        """
        Verifica se um item está presente no filtro.
        Retorna True se o fingerprint for encontrado em i1 ou i2.
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
        Remove um item do filtro, se presente.
        Retorna True se removido com sucesso, False caso contrário.
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