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

class BankAccount:
    def __init__(self):
        self.id: Optional[str] = None
        self.owner: Optional[str] = None
        self.balance: float = 0.0
        self.version: int = 0

    def apply(self, event: Event) -> None:
        """Aplica um evento ao estado atual de forma determinística e pura. Não gera efeitos colaterais (como envio de notificações ou chamadas de rede)."""
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

class EventStore:
    def __init__(self):
        # Armazenamento interno privado para garantir encapsulamento
        self._streams: Dict[str, List[Event]] = {}

    def append_events(self, stream_id: str, expected_version: int, events: List[Event]) -> None:
        """Adiciona novos eventos ao stream garantindo imutabilidade e consistência de versão."""
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
                    f"Concorrência detectada ou evento fora de ordem! "
                    f"Esperado versão {current_version + 1}, recebido {event.version}"
                )
            current_stream.append(event)
            current_version += 1

# Testes
event_store = EventStore()
account_id = "12345"

# Criação da conta
account_created_event = AccountCreated(stream_id=account_id, version=1, timestamp=1600000000.0, owner="João")
event_store.append_events(account_id, 0, [account_created_event])

# Depósito
money_deposited_event = MoneyDeposited(stream_id=account_id, version=2, timestamp=1600000001.0, amount=100.0)
event_store.append_events(account_id, 1, [money_deposited_event])

# Saque
money_withdrawn_event = MoneyWithdrawn(stream_id=account_id, version=3, timestamp=1600000002.0, amount=50.0)
event_store.append_events(account_id, 2, [money_withdrawn_event])

# Replay
events_list = event_store.get_stream(account_id)
for event in events_list:
    bank_account = BankAccount()
    bank_account.apply(event)
    print(f"Versão: {bank_account.version}, Saldo: {bank_account.balance}")