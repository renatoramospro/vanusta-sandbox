path=lsm_engine.py
import os
import glob
import json
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
        # Tombstone representado por None
        self.put(key, None)

    def flush(self):
        if not self.memtable:
            return
        
        # Ordena a MemTable por chave
        sorted_items = sorted(self.memtable.items())
        
        # Cria nome único baseado em timestamp
        sstable_id = len(glob.glob(os.path.join(self.data_dir, "sstable_*.json"))) + 1
        sstable_path = os.path.join(self.data_dir, f"sstable_{sstable_id}.json")
        
        # Escrita atômica via arquivo temporário
        tmp_path = sstable_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(sorted_items, f)
        os.rename(tmp_path, sstable_path)
        
        # Limpa MemTable e WAL
        self.memtable.clear()
        self._clear_wal()
        print(f"[FLUSH] MemTable persistida em {sstable_path}")

    def get(self, key):
        # 1. Procura na MemTable (mais recente)
        if key in self.memtable:
            val = self.memtable[key]
            return None if val is None else val

        # 2. Procura nas SSTables (da mais recente para a mais antiga)
        sstable_files = sorted(glob.glob(os.path.join(self.data_dir, "sstable_*.json")), reverse=True)
        for sst_file in sstable_files:
            with open(sst_file, "r", encoding="utf-8") as f:
                items = json.load(f)
                # Busca binária ou linear ordenada
                for k, v in items:
                    if k == key:
                        return None if v is None else v
        return None

    def compact(self):
        sstable_files = sorted(glob.glob(os.path.join(self.data_dir, "sstable_*.json")))
        if len(sstable_files) <= 1:
            print("[COMPACT] Nenhuma compactação necessária (<= 1 SSTable).")
            return

        print(f"[COMPACT] Compactando {len(sstable_files)} SSTables...")
        merged_data = OrderedDict()

        # Lê da mais antiga para a mais nova para sobrescrever com versões recentes
        for sst_file in sstable_files:
            with open(sst_file, "r", encoding="utf-8") as f:
                items = json.load(f)
                for k, v in items:
                    merged_data[k] = v

        # Remove tombstones definitivos se desejado, ou mantém. Aqui removemos chaves com valor None para economia de espaço.
        cleaned_data = {k: v for k, v in merged_data.items() if v is not None}
        sorted_items = sorted(cleaned_data.items())

        # Nova SSTable compactada
        new_id = len(sstable_files) + 100
        new_path = os.path.join(self.data_dir, f"sstable_compacted_{new_id}.json")
        
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(sorted_items, f)

        # Remove SSTables antigas e WAL
        for sst_file in sstable_files:
            os.remove(sst_file)
        print(f"[COMPACT] Concluído. Nova SSTable gerada: {new_path}")

# --- TESTES DE VALIDAÇÃO E DEMONSTRAÇÃO ---
if __name__ == "__main__":
    import shutil
    test_dir = "test_data"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("=== TESTE 1: Escrita, MemTable e Read-After-Write ===")
    lsm = LSMEngine(data_dir=test_dir, memtable_limit=2)
    lsm.put("k1", "v1")
    lsm.put("k2", "v2")
    # Limite atingido (2), deve ter feito flush aqui
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