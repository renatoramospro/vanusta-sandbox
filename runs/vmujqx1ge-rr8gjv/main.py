import os
import glob
import json
import shutil
from collections import OrderedDict

class LSMEngine:
    def __init__(self, data_dir="data", memtable_limit=3):
        self.data_dir = data_dir
        self.memtable_limit = memtable_limit
        self.memtable = OrderedDict()
        self.wal_path = os.path.join(data_dir, "wal.log")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        self._recover_from_wal()

    def _append_wal(self, key, value):
        with open(self.wal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "value": value}) + "\n")

    def _clear_wal(self):
        if os.path.exists(self.wal_path):
            open(self.wal_path, "w").close()

    def _recover_from_wal(self):
        if os.path.exists(self.wal_path):
            with open(self.wal_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line.strip())
                        self.memtable[item["key"]] = item["value"]

    def put(self, key, value):
        self._append_wal(key, value)
        self.memtable[key] = value
        if len(self.memtable) >= self.memtable_limit:
            self.flush()

    def delete(self, key):
        # Tombstone representado por um valor sentinela especial
        self.put(key, "__TOMBSTONE__")

    def flush(self):
        if not self.memtable:
            return
        
        # Ordena a MemTable pelas chaves
        sorted_memtable = OrderedDict(sorted(self.memtable.items()))
        
        # Nome único da SSTable baseado em timestamp
        sstable_id = len(glob.glob(os.path.join(self.data_dir, "sstable_*.json")))
        sstable_path = os.path.join(self.data_dir, f"sstable_{sstable_id:04d}.json")
        
        # Escrita atômica via arquivo temporário
        temp_path = sstable_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(list(sorted_memtable.items()), f)
        os.rename(temp_path, sstable_path)
        
        # Limpa MemTable e WAL após flush bem-sucedido
        self.memtable.clear()
        self._clear_wal()
        print(f"[FLUSH] MemTable persistida em {sstable_path}")

    def get(self, key):
        # 1. Busca na MemTable (mais recente)
        if key in self.memtable:
            val = self.memtable[key]
            return None if val == "__TOMBSTONE__" else val

        # 2. Busca nas SSTables (da mais recente para a mais antiga)
        sstable_files = sorted(glob.glob(os.path.join(self.data_dir, "sstable_*.json")), reverse=True)
        for sstable_file in sstable_files:
            with open(sstable_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Busca binária ou linear ordenada na SSTable
                for k, v in data:
                    if k == key:
                        return None if v == "__TOMBSTONE__" else v

        return None

    def compact(self):
        print("[COMPACT] Iniciando compactação de SSTables...")
        sstable_files = sorted(glob.glob(os.path.join(self.data_dir, "sstable_*.json")))
        if not sstable_files:
            return

        merged_data = OrderedDict()
        
        # Lê todas as SSTables da mais antiga para a mais recente
        for sstable_file in sstable_files:
            with open(sstable_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data:
                    merged_data[k] = v  # Sobrepõe com a versão mais recente

        # Escreve nova SSTable compactada unificada
        new_sstable_path = os.path.join(self.data_dir, "sstable_compacted.json")
        with open(new_sstable_path, "w", encoding="utf-8") as f:
            json.dump(list(merged_data.items()), f)

        # Remove as SSTables antigas e substitui pela compactada
        for sstable_file in sstable_files:
            if sstable_file != new_sstable_path:
                os.remove(sstable_file)
        
        os.rename(new_sstable_path, os.path.join(self.data_dir, "sstable_0000.json"))
        print("[COMPACT] Compactação concluída com sucesso.")

if __name__ == "__main__":
    test_dir = "test_data_lsm"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    lsm = LSMEngine(data_dir=test_dir, memtable_limit=2)

    print("\n=== TESTE 1: Escrita e Leitura (Read-After-Write) ===")
    lsm.put("k1", "v1")
    lsm.put("k2", "v2") # Deve disparar flush (limite 2)
    
    assert lsm.get("k1") == "v1"
    assert lsm.get("k2") == "v2"
    print("Sucesso: Leituras consistentes após flush automático.")

    print("\n=== TESTE 2: Múltiplos Flushes e Tombstones ===")
    lsm.put("k3", "v3")
    lsm.put("k1", "v1_updated") # Atualização
    lsm.delete("k2")            # Exclusão (tombstone)
    
    assert lsm.get("k1") == "v1_updated", f"Esperado v1_updated, obtido {lsm.get('k1')}"
    assert lsm.get("k2") is None, f"Esperado None (deletado), obtido {lsm.get('k2')}"
    assert lsm.get("k3") == "v3"
    print("Sucesso: Atualizações e Tombstones resolvidos corretamente.")

    print("\n=== TESTE 3: Compactação de SSTables ===")
    lsm.compact()
    # Verifica consistência após compactação
    assert lsm.get("k1") == "v1_updated"
    assert lsm.get("k2") is None
    assert lsm.get("k3") == "v3"
    print("Sucesso: 100% de consistência mantida após compactação.")

    # Limpeza final
    shutil.rmtree(test_dir)
    print("\nTodos os testes executados com sucesso!")