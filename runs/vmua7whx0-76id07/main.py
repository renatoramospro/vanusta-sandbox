import time
import uuid
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Type, Union

# --- 1. EVENTOS E VERSIONAMENTO (UPCASTING) ---

@dataclass(frozen=True)
class Event:
    aggregate_id: str
    version: int
    event_type: str

# Versão 1: Evento simples
@dataclass(frozen=True)
class ContaCriadaV1(Event):
    titular: str
    event_type: str = "ContaCriada"

# Versão 2: Evento evoluído (agora o titular é um dicionário com nome e sobrenome)
@dataclass(frozen=True)
class ContaCriadaV2(Event):
    titular_info: Dict[str, str] # Mudança de 'str' para 'dict'
    event_type: str = "ContaCriada"

@dataclass(frozen=True)
class ValorDepositado(Event):
    valor: float
    event_type: str = "ValorDepositado"

# --- 2. O UPCASTER (O CORAÇÃO DA CORREÇÃO) ---

class EventUpcaster:
    """
    Transforma eventos de versões antigas para a versão mais atual
    antes que eles cheguem ao Aggregate ou Projeção.
    """
    @staticmethod
    def upcast(raw_event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = raw_event.get("event_type")
        
        # Regra de Upcasting: Se for ContaCriada e não tiver 'titular_info', 
        # transformamos o antigo 'titular' (string) em 'titular_info' (dict)
        if event_type == "ContaCriada" and "titular" in raw_event:
            print(f"  [Upcaster] Transformando {event_type} V1 -> V2")
            old_name = raw_event.pop("titular")
            raw_event["titular_info"] = {"nome": old_name, "sobrenome": "N/A"}
            # Nota: Em um sistema real, o 'version' do evento também seria incrementado aqui
            
        return raw_event

# --- 3. EVENT STORE (Simulando persistência de dados brutos/JSON) ---

class EventStore:
    def __init__(self):
        # Armazenamos como DICT para simular o que seria salvo em um banco (JSON/BSON)
        self._storage: List[Dict[str, Any]] = []

    def append(self, event: Event):
        self._storage.append(asdict(event))

    def get_events(self, aggregate_id: str) -> List[Dict[str, Any]]:
        # Recupera eventos e aplica o UPCASTING em tempo de leitura
        events = [e for e in self._storage if e["aggregate_id"] == aggregate_id]
        return [EventUpcaster.upcast(e) for e in events]

# --- 4. AGGREGATE ROOT (Escrita) ---

class ContaBancaria:
    def __init__(self):
        self.id = None
        self.nome_titular = ""
        self.saldo = 0.0
        self._uncommitted_events = []

    def load_from_history(self, events: List[Dict[str, Any]]):
        """Reconstrói o estado usando os eventos já upcasted"""
        for e in events:
            self._apply(e)

    def _apply(self, event_data: Dict[str, Any]):
        """Aplica o dicionário de dados ao estado (Lógica de Replay)"""
        if event_data["event_type"] == "ContaCriada":
            self.id = event_data["aggregate_id"]
            # O Aggregate agora só conhece a versão V2 (titular_info)
            info = event_data["titular_info"]
            self.nome_titular = f"{info['nome']} {info['sobrenome']}"
        elif event_data["event_type"] == "ValorDepositado":
            self.saldo += event_data["valor"]

    def create(self, aggregate_id: str, titular: str):
        # No mundo real, aqui criaríamos um objeto de evento V2
        # Mas para o teste, vamos simular que o banco tem dados V1
        event = ContaCriadaV1(aggregate_id=aggregate_id, version=1, titular=titular)
        self._uncommitted_events.append(event)

    def depositar(self, aggregate_id: str, valor: float):
        event = ValorDepositado(aggregate_id=aggregate_id, version=1, valor=valor)
        self._uncommitted_events.append(event)

# --- 5. EXPERIMENTO ---

def run_experiment():
    print("=== INICIANDO TESTE DE EVOLUÇÃO DE ESQUEMA (UPCASTING) ===\n")
    store = EventStore()
    acc_id = str(uuid.uuid4())

    # 1. Simulamos o passado: Eventos foram salvos no formato V1 (antigo)
    print("1. Simulando persistência de eventos antigos (V1)...")
    v1_event = ContaCriadaV1(aggregate_id=acc_id, version=1, titular="Joao Silva")
    store.append(asdict(v1_event))
    
    # 2. Simulamos um evento novo (V2) sendo adicionado hoje
    print("2. Adicionando novo evento no formato atual (V2)...")
    v2_event = ValorDepositado(aggregate_id=acc_id, version=2, valor=150.0)
    store.append(asdict(v2_event))

    # 3. Tentativa de Replay
    print("\n3. Iniciando Replay para reconstruir o Aggregate...")
    conta = ContaBancaria()
    
    # O segredo: o store retorna eventos já transformados pelo Upcaster
    historico = store.get_events(acc_id)
    conta.load_from_history(historico)

    # 4. Validação
    print(f"\n--- Resultado Final ---")
    print(f"ID: {conta.id}")
    print(f"Titular (Reconstruído via Upcasting): {conta.nome_titular}")
    print(f"Saldo: {conta.saldo}")

    # Verificação de integridade
    assert conta.nome_titular == "Joao Silva N/A", f"Erro no Upcasting! Esperado 'Joao Silva N/A', obtido '{conta.nome_titular}'"
    assert conta.saldo == 150.0, f"Erro no saldo! Esperado 150.0, obtido {conta.saldo}"
    
    print("\n✅ SUCESSO: O Aggregate conseguiu ler eventos antigos (V1) como se fossem novos (V2) graças ao Upcaster.")

if __name__ == "__main__":
    run_experiment()