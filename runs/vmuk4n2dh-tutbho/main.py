python path=main.py
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Set, Any

# Simulação de Relógios com Drift (Equívoco do LWW)
class RegionNode:
    def __init__(self, name: str, clock_drift_ms: int):
        self.name = name
        self.clock_drift_ms = clock_drift_ms
        self.storage: Dict[str, Any] = {}
        self.lww_timestamps: Dict[str, float] = {}

    def get_time(self) -> float:
        # Simula relógio local com viés/drift em milissegundos
        return time.time() + (self.clock_drift_ms / 1000.0)

    def write_lww(self, key: str, value: Any):
        ts = self.get_time()
        # LWW: só aceita se o timestamp for maior que o registrado
        if key not in self.lww_timestamps or ts >= self.lww_timestamps[key]:
            self.storage[key] = value
            self.lww_timestamps[key] = ts
            print(f"[{self.name}] LWW WRITE: key='{key}' val='{value}' at ts={ts:.4f}")
        else:
            print(f"[{self.name}] LWW REJECTED: key='{key}' val='{value}' (stale timestamp)")

@dataclass
class ORSetElement:
    value: str
    tag: str

class CRDTORSet:
  """Implementação simplificada de Observed-Remove Set (CRDT) para convergência sem conflito."""
  def __init__(self, name: str):
      self.name = name
      self.add_set: Set[tuple] = set() # guarda (value, unique_tag)
      self.remove_set: Set[str] = set() # guarda unique_tags removidas

  def add(self, value: str) -> str:
      tag = str(uuid.uuid4())
      self.add_set.add((value, tag))
      print(f"[{self.name}] CRDT ADD: '{value}' com tag {tag[:6]}")
      return tag

  def remove(self, value: str):
      # Remove todas as tags associadas a este valor observadas até o momento
      tags_to_remove = [tag for val, tag in self.add_set if val == value]
      for tag in tags_to_remove:
          self.remove_set.add(tag)
      print(f"[{self.name}] CRDT REMOVE: '{value}' (marcou {len(tags_to_remove)} tags)")

  def read(self) -> Set[str]:
      # Elemento está presente se existe pelo menos uma tag de adição não presente no remove_set
      return {val for val, tag in self.add_set if tag not in self.remove_set}

  def merge(self, other: 'CRDTORSet'):
      self.add_set.update(other.add_set)
      self.remove_set.update(other.remove_set)
      print(f"[{self.name}] MERGE realizado com {other.name}")

# --- DEMONSTRAÇÃO DOS CONCEITOS E TESTES ---

def test_lww_failure_due_to_clock_drift():
    print("=== TESTE 1: Falha do Last-Write-Wins por Clock Skew ===")
    # Região A tem relógio atrasado em 500ms
    # Região B tem relógio correto
    regiao_a = RegionNode("Regiao-A-SP", clock_drift_ms=-500)
    regiao_b = RegionNode("Regiao-B-TYO", clock_drift_ms=0)

    # Cliente na Região A escreve "ItemX" com valor "Update-A"
    regiao_a.write_lww("carrinho", "Update-A")
    
    # Poucos milissegundos depois no tempo real, Cliente na Região B escreve "Update-B"
    # Devido ao atraso do relógio da Região A, o timestamp de A pode parecer MAIOR ou MENOR
    # de forma inconsistente dependendo da ordem de chegada, causando perda de escrita legítima.
    regiao_b.write_lww("carrinho", "Update-B")

    # Simula replicação cruzada
    regiao_a.write_lww("carrinho", regiao_b.storage["carrinho"])
    regiao_b.write_lww("carrinho", regiao_a.storage["carrinho"])

    print(f"Estado final Região A: {regiao_a.storage}")
    print(f"Estado final Região B: {regiao_b.storage}")
    print("Conclusão LWW: Dependência de relógio físico gera comportamento não determinístico sob concorrência.\n")

def test_crdt_convergence():
    print("=== TESTE 2: Convergência Determinística com CRDT (OR-Set) ===")
    replica_a = CRDTORSet("Replica-A")
    replica_b = CRDTORSet("Replica-B")

    # Concorrência: A adiciona "Maçã", B adiciona "Banana" ao mesmo carrinho de compras
    replica_a.add("Maca")
    replica_b.add("Banana")

    # Sincronização / Merge bidirecional
    replica_a.merge(replica_b)
    replica_b.merge(replica_a)

    print(f"Itens na Replica A após merge: {replica_a.read()}")
    print(f"Itens na Replica B após merge: {replica_b.read()}")
    
    assert replica_a.read() == {"Maca", "Banana"}
    assert replica_b.read() == {"Maca", "Banana"}
    print("Sucesso: Estados convergiram perfeitamente sem perda de dados concorrentes!\n")

if __name__ == "__main__":
    test_lww_failure_due_to_clock_drift()
    test_crdt_convergence()
    print("Todos os testes executados com sucesso (Código de saída 0).")