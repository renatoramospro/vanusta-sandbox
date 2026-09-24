import time
from dataclasses import dataclass
from typing import List, Dict, Optional

# ==========================================
# 1. Definição dos Eventos (Imutáveis)
# ==========================================
@dataclass(frozen=True)
class Event:
    stream_id: str
    version: int
    timestamp: float
    
@dataclass(frozen=True)
class AccountCreated(Event):
    owner: str

@dataclass(frozen=True)
class MoneyDeposited(Event):
    amount: float

@dataclass(frozen=True)
class MoneyWithdrawn(Event):
    amount: float


# ==========================================
# 2. Entidade de Domínio (BankAccount)
# ==========================================
class BankAccount:
    def __init__(self):
        self.id: Optional[str] = None
        self.owner: Optional[str] = None
        self.balance: float = 0.0
        self.version: int = 0

    def apply(self, event: Event) -> None:
        """
        Aplica um evento ao estado atual de forma determinística e pura.
        Não gera efeitos colaterais (como envio de notificações ou chamadas de rede).
        """
        if self.version == 0 and not isinstance(event, AccountCreated):
            raise ValueError("A conta deve ser criada primeiro com AccountCreated.")
            
        if event.version != self.version + 1:
            raise ValueError(
                f"Concorrência detectada ou evento fora de ordem! "
                f"Esperado versão {self.version + 1}, recebido {event.version}"
            )

        if isinstance(event, AccountCreated):
            self.id = event.stream_id
            self.owner = event.owner
            self.balance = 0.0
        elif isinstance(event, MoneyDeposited):
            self.balance += event.amount
        elif isinstance(event, MoneyWithdrawn):
            self.balance -= event.amount
        
        self.version = event.version


# ==========================================
# 3. Event Store (Append-Only e Imutável)
# ==========================================
class EventStore:
    def __init__(self):
        # Armazenamento interno privado para garantir encapsulamento
        self._streams: Dict[str, List[Event]] = {}

    def append_events(self, stream_id: str, expected_version: int, events: List[Event]) -> None:
        """
        Adiciona novos eventos ao stream garantindo imutabilidade e consistência de versão.
        """
        if stream_id not in self._streams:
            self._streams[stream_id] = []
            
        current_stream = self._streams[stream_id]
        current_version = len(current_stream)
        
        if current_version != expected_version:
            raise ValueError(
                f"Erro de concorrência: versão esperada {expected_version}, "
                f"versão atual do stream {current_version}"
            )
            
        for event in events:
            if event.version != current_version + 1:
                raise ValueError(
                    f"Versão do evento inválida: {event.version}. "
                    f"Esperada: {current_version + 1}"
                )
            current_stream.append(event)
            current_version += 1

    def get_stream(self, stream_id: str, up_to_timestamp: Optional[float] = None) -> List[Event]:
        """
        Retorna uma cópia da lista de eventos para evitar mutações externas.
        Permite filtragem opcional por timestamp para replay parcial.
        """
        if stream_id not in self._streams:
            return []
        
        events = self._streams[stream_id]
        if up_to_timestamp is not None:
            events = [e for e in events if e.timestamp <= up_to_timestamp]
            
        # Retorna uma nova lista contendo os mesmos eventos imutáveis
        return list(events)


# ==========================================
# 4. Serviços e Isolamento de Efeitos Colaterais
# ==========================================
class NotificationService:
    """Serviço simulado que representa um efeito colateral externo."""
    def __init__(self):
        self.notifications_sent = 0

    def send_notification(self, message: str):
        self.notifications_sent += 1


class AccountService:
    """
    Serviço de aplicação que gerencia a execução de comandos,
    persistência de eventos e disparo de efeitos colaterais.
    """
    def __init__(self, event_store: EventStore, notification_service: NotificationService):
        self.event_store = event_store
        self.notification_service = notification_service

    def create_account(self, account_id: str, owner: str, timestamp: float) -> BankAccount:
        # 1. Executa a lógica de negócio e gera o evento
        event = AccountCreated(stream_id=account_id, version=1, timestamp=timestamp, owner=owner)
        
        # 2. Persiste no Event Store
        self.event_store.append_events(account_id, 0, [event])
        
        # 3. Reconstrói o estado local
        account = BankAccount()
        account.apply(event)
        
        # 4. Dispara efeitos colaterais (Apenas no fluxo de comando!)
        self.notification_service.send_notification(f"Conta criada para {owner}!")
        return account

    def deposit(self, account_id: str, amount: float, timestamp: float) -> BankAccount:
        # Reconstrói o estado atual para validação
        account = self.reconstruct(account_id)
        
        # Gera o evento
        event = MoneyDeposited(stream_id=account_id, version=account.version + 1, timestamp=timestamp, amount=amount)
        
        # Persiste
        self.event_store.append_events(account_id, account.version, [event])
        
        # Aplica localmente
        account.apply(event)
        
        # Dispara efeito colateral
        self.notification_service.send_notification(f"Depósito de R$ {amount} realizado.")
        return account

    def withdraw(self, account_id: str, amount: float, timestamp: float) -> BankAccount:
        account = self.reconstruct(account_id)
        if account.balance < amount:
            raise ValueError("Saldo insuficiente!")
            
        event = MoneyWithdrawn(stream_id=account_id, version=account.version + 1, timestamp=timestamp, amount=amount)
        self.event_store.append_events(account_id, account.version, [event])
        account.apply(event)
        
        self.notification_service.send_notification(f"Saque de R$ {amount} realizado.")
        return account

    def reconstruct(self, account_id: str, up_to_timestamp: Optional[float] = None) -> BankAccount:
        """
        Reconstrói o estado da entidade a partir do histórico de eventos (Replay).
        Este processo é puro e NÃO dispara notificações (efeitos colaterais).
        """
        events = self.event_store.get_stream(account_id, up_to_timestamp)
        account = BankAccount()
        for event in events:
            account.apply(event)
        return account


# ==========================================
# 5. Execução do Experimento e Validações
# ==========================================
def run_experiment():
    print("Iniciando Experimento de Event Sourcing...")
    
    event_store = EventStore()
    notification_service = NotificationService()
    service = AccountService(event_store, notification_service)
    
    account_id = "acc-123"
    start_time = 1600000000.0  # Timestamp base fixo para determinismo
    
    # ---------------------------------------------------------
    # Teste 1: Processar 1000 eventos sequenciais
    # ---------------------------------------------------------
    # Evento 1: Criação da conta
    service.create_account(account_id, "Alice", start_time)
    
    # Gerar mais 999 eventos alternando depósitos e saques
    # 500 depósitos de R$ 10.0
    # 499 saques de R$ 5.0
    # Saldo esperado: 500 * 10 - 499 * 5 = 5000 - 2495 = 2505.0
    # Versão esperada: 1000
    for i in range(2, 1001):
        timestamp = start_time + i
        if i % 2 == 0:
            service.deposit(account_id, 10.0, timestamp)
        else:
            service.withdraw(account_id, 5.0, timestamp)
            
    print(f"-> 1000 eventos gerados com sucesso.")
    print(f"-> Notificações enviadas durante a execução dos comandos: {notification_service.notifications_sent}")
    assert notification_service.notifications_sent == 1000, "Deveria ter enviado 1000 notificações durante os comandos."

    # ---------------------------------------------------------
    # Teste 2: Reconstrução total (Replay de todos os eventos)
    # ---------------------------------------------------------
    # Resetamos o contador de notificações para provar o isolamento de efeitos colaterais
    notification_service.notifications_sent = 0
    
    reconstructed_account = service.reconstruct(account_id)
    print(f"-> Reconstrução total concluída.")
    print(f"   Saldo final reconstruído: R$ {reconstructed_account.balance}")
    print(f"   Versão final reconstruída: {reconstructed_account.version}")
    print(f"   Notificações enviadas durante o replay: {notification_service.notifications_sent}")
    
    assert reconstructed_account.balance == 2505.0, f"Saldo incorreto: {reconstructed_account.balance}"
    assert reconstructed_account.version == 1000, f"Versão incorreta: {reconstructed_account.version}"
    assert notification_service.notifications_sent == 0, "O replay disparou efeitos colaterais indevidamente!"

    # ---------------------------------------------------------
    # Teste 3: Replay Parcial até um timestamp específico
    # ---------------------------------------------------------
    # Vamos fazer o replay até a metade dos eventos (versão 500)
    # Timestamp do evento 500 é start_time + 500
    target_timestamp = start_time + 500
    partial_account = service.reconstruct(account_id, up_to_timestamp=target_timestamp)
    
    # Na versão 500, temos:
    # 1 criação
    # 250 depósitos de R$ 10.0
    # 249 saques de R$ 5.0
    # Saldo esperado: 250 * 10 - 249 * 5 = 2500 - 1245 = 1255.0
    print(f"-> Replay parcial até timestamp {target_timestamp} (Versão 500) concluído.")
    print(f"   Saldo parcial: R$ {partial_account.balance}")
    print(f"   Versão parcial: {partial_account.version}")
    
    assert partial_account.version == 500, f"Versão parcial incorreta: {partial_account.version}"
    assert partial_account.balance == 1255.0, f"Saldo parcial incorreto: {partial_account.balance}"

    # ---------------------------------------------------------
    # Teste 4: Garantia de Imutabilidade do Event Store
    # ---------------------------------------------------------
    # Tentativa de alterar a lista de eventos retornada pelo Event Store
    events_list = event_store.get_stream(account_id)
    try:
        events_list.clear()  # Limpa a lista retornada
        # Recupera novamente para ver se o log interno foi afetado
        events_after_clear = event_store.get_stream(account_id)
        assert len(events_after_clear) == 1000, "O log interno foi corrompido por mutação externa!"
        print("-> Garantia de Imutabilidade do Event Store validada (cópia defensiva funciona).")
    except Exception as e:
        print(f"Falha na validação de imutabilidade: {e}")
        raise e

    # Tentativa de alterar um atributo de um evento (deve falhar pois dataclass é frozen)
    try:
        events_list[0].version = 999
        raise AssertionError("Deveria ter lançado erro ao tentar alterar atributo de evento congelado.")
    except AttributeError:
        print("-> Garantia de Imutabilidade dos Eventos validada (dataclass frozen funciona).")

    # ---------------------------------------------------------
    # Teste 5: Versionamento e Optimistic Concurrency Control
    # ---------------------------------------------------------
    # Tentativa de injetar um evento com versão incorreta (fora de ordem)
    invalid_event = MoneyDeposited(stream_id=account_id, version=1005, timestamp=start_time + 1005, amount=100.0)
    try:
        event_store.append_events(account_id, 1000, [invalid_event])
        raise AssertionError("Deveria ter rejeitado evento com versão inconsistente.")
    except ValueError as e:
        print(f"-> Versionamento validado com sucesso: {e}")

    print("\nTodos os critérios de sucesso foram atingidos com perfeição!")

if __name__ == "__main__":
    run_experiment()