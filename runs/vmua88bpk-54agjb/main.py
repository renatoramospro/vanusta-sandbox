import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional

# --- 1. EVENTOS E HIERARQUIA CORRIGIDA ---
# Para evitar o TypeError: non-default argument follows default argument,
# garantimos que campos com valores padrão venham sempre por último ou
# que todos os campos na hierarquia sigam uma ordem consistente.

@dataclass(frozen=True)
class Event:
    aggregate_id: str
    version: int
    event_type: str = "" # Valor padrão para evitar conflito na herança

@dataclass(frozen=True)
class ContaCriadaV1(Event):
    titular: str = "" # Campo V1
    event_type: str = "ContaCriada"

@dataclass(frozen=True)
class ContaCriadaV2(Event):
    # Evolução: 'titular' (str) -> 'titular_info' (dict)
    titular_info: Dict[str, str] = field(default_factory=dict)
    event_type: str = "ContaCriada"

@dataclass(frozen=True)
class ValorDepositado(Event):
    valor: float = 0.0
    event_type: str = "ValorDepositado"

# --- 2. UPCASTER ROBUSTO (CORREÇÃO DE SEGURANÇA E ERROS) ---

class UpcastingError(Exception):
    """Exceção específica para falhas de evolução de esquema."""
    pass

class EventUpcaster:
    """
    Transforma eventos de versões antigas para a versão mais atual.
    Implementa validação de esquema para evitar KeyError/DoS.
    """
    @staticmethod
    def upcast(raw_event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = raw_event.get("event_type")
        if not event_type:
            raise UpcastingError("Evento sem 'event_type' detectado.")

        # Lógica de Upcasting para ContaCriada (V1 -> V2)
        if event_type == "ContaCriada":
            # Se já for V2 (tem titular_info), não faz nada
            if "titular_info" in raw_event:
                return raw_event
            
            # Se for V1 (tem titular), transforma
            if "titular" in raw_event:
                try:
                    old_name = raw_event.pop("titular")
                    raw_event["titular_info"] = {"nome": str(old_name), "sobrenome": "N/A"}
                    return raw_event
                except Exception as e:
                    raise UpcastingError(f"Falha ao converter titular: {e}")
            else:
                raise UpcastingError("Evento 'ContaCriada' malformado: falta 'titular' ou 'titular_info'.")

        return raw_event

# --- 3. EVENT STORE (APPEND-ONLY) ---

class EventStore:
    def __init__(self):
        self._storage: List[Dict[str, Any]] = []

    def append(self, event: Event):
        # Simulação de imutabilidade: o evento é convertido para dict e armazenado
        self._storage.append(asdict(event))

    def get_events(self, aggregate_id: str) -> List[Dict[str, Any]]:
        # Recupera e aplica o upcasting de forma segura
        raw_events = [e for e in self._storage if e["aggregate_id"] == aggregate_id]
        upcasted_events = []
        for e in raw_events:
            upcasted_events.append(EventUpcaster.upcast(e.copy()))
        return upcasted_events

# --- 4. AGGREGATE ROOT E PROJEÇÃO ---

class ContaBancaria:
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.titular_nome = ""
        self.saldo = 0.0
        self.version = 0

    def apply(self, event_dict: Dict[str, Any]):
        """Aplica o evento ao estado interno (Replay)."""
        etype = event_dict["event_type"]
        
        if etype == "ContaCriada":
            # Note que o Aggregate agora só conhece a estrutura V2
            info = event_dict["titular_info"]
            self.titular_nome = info["nome"]
        elif etype == "ValorDepositado":
            self.saldo += event_dict["valor"]
        
        self.version = event_dict["version"]

    @classmethod
    def rebuild(cls, aggregate_id: str, store: EventStore) -> 'ContaBancaria':
        conta = cls(aggregate_id)
        events = store.get_events(aggregate_id)
        if not events:
            return conta
        
        for e in events:
            conta.apply(e)
        return conta

class ContaProjecao:
    """Projeção de leitura (CQRS)."""
    def __init__(self):
        self.dados: Dict[str, Dict[str, Any]] = {}

    def handle(self, event_dict: Dict[str, Any]):
        aid = event_dict["aggregate_id"]
        if aid not in self.dados:
            self.dados[aid] = {"titular": "", "saldo": 0.0}
        
        if event_dict["event_type"] == "ContaCriada":
            self.dados[aid]["titular"] = event_dict["titular_info"]["nome"]
        elif event_dict["event_type"] == "ValorDepositado":
            self.dados[aid]["saldo"] += event_dict["valor"]

# --- 5. EXPERIMENTO DE VALIDAÇÃO ---

def run_experiment():
    print("🚀 Iniciando Experimento de CQRS + Event Sourcing + Upcasting\n")
    store = EventStore()
    projecao = ContaProjecao()
    acc_id = str(uuid.uuid4())

    # 1. Simular histórico de eventos legados (V1)
    print("--- Passo 1: Inserindo eventos legados (V1) ---")
    e1 = ContaCriadaV1(aggregate_id=acc_id, version=1, titular="Joao Silva")
    e2 = ValorDepositado(aggregate_id=acc_id, version=2, valor=100.0)
    
    store.append(e1)
    store.append(e2)

    # 2. Testar Reconstrução (Replay) com Upcasting
    print("--- Passo 2: Reconstruindo Aggregate via Replay ---")
    start_time = time.time()
    conta = ContaBancaria.rebuild(acc_id, store)
    end_time = time.time()
    
    print(f"  [Replay] Titular: {conta.titular_nome}, Saldo: {conta.saldo}")
    print(f"  [Performance] Tempo de replay: {(end_time - start_time)*1000:.4f}ms")
    
    assert conta.titular_nome == "Joao Silva"
    assert conta.saldo == 100.0
    assert (end_time - start_time) < 0.2 # < 200ms

    # 3. Testar Projeção (Consistência Eventual)
    print("\n--- Passo 3: Atualizando Projeção ---")
    for e_raw in store.get_events(acc_id):
        projecao.handle(e_raw)
    
    print(f"  [Projeção] Dados: {projecao.dados[acc_id]}")
    assert projecao.dados[acc_id]["titular"] == "Joao Silva"
    assert projecao.dados[acc_id]["saldo"] == 100.0

    # 4. Testar Resiliência (Evento Corrompido/Malformado)
    print("\n--- Passo 4: Testando Resiliência contra Eventos Corrompidos ---")
    corrupt_id = "bad-id"
    # Inserindo um dicionário que simula um evento sem as chaves necessárias
    store._storage.append({"aggregate_id": corrupt_id, "event_type": "ContaCriada"}) # Falta 'titular'
    
    try:
        ContaBancaria.rebuild(corrupt_id, store)
        print("❌ ERRO: O sistema deveria ter falhado ao processar evento corrompido.")
    except UpcastingError as e:
        print(f"✅ SUCESSO: O sistema detectou e barrou o evento corrompido: {e}")

    print("\n✨ EXPERIMENTO FINALIZADO COM SUCESSO!")

if __name__ == "__main__":
    run_experiment()