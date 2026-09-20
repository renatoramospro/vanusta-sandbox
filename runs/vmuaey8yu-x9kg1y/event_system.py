import weakref
import time

class EventBus:
    """Interface base para o Event Bus."""
    def subscribe(self, event_type, callback): raise NotImplementedError
    def unsubscribe(self, event_type, callback): raise NotImplementedError
    def publish(self, event_type, *args, **kwargs): raise NotImplementedError

class RobustEventBus(EventBus):
    def __init__(self):
        # Dicionário: { event_type: [lista_de_referencias_fracas] }
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # CORREÇÃO: Diferenciar entre métodos de instância e funções/lambdas
        if hasattr(callback, "__self__") and callback.__self__ is not None:
            # É um método de instância (ex: self.on_event)
            ref = weakref.WeakMethod(callback)
        else:
            # É uma função global ou lambda (não pode ser WeakMethod puro)
            # Usamos um wrapper para manter a referência de forma segura ou direta
            ref = callback 
            
        self._subscribers[event_type].append(ref)

    def unsubscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            return
        
        # Filtra a lista removendo o callback correspondente
        # Precisamos comparar o callback original com o que está guardado
        new_list = []
        for ref in self._subscribers[event_type]:
            actual_callback = ref() if isinstance(ref, weakref.WeakMethod) else ref
            if actual_callback != callback:
                new_list.append(ref)
        self._subscribers[event_type] = new_list

    def publish(self, event_type, *args, **kwargs):
        if event_type not in self._subscribers:
            return

        still_alive = []
        for ref in self._subscribers[event_type]:
            # Se for WeakMethod, tenta recuperar o método. Se for função, usa direto.
            callback = ref() if isinstance(ref, weakref.WeakMethod) else ref
            
            if callback is not None:
                callback(*args, **kwargs)
                still_alive.append(ref)
            # Se callback for None, o objeto morreu; não adicionamos em still_alive (limpeza automática)
        
        self._subscribers[event_type] = still_alive

class BadEventBus(EventBus):
    """Exemplo de implementação errada que causa Memory Leaks."""
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback) # Referência FORTE

    def unsubscribe(self, event_type, callback):
        self._subscribers[event_type].remove(callback)

    def publish(self, event_type, *args, **kwargs):
        for callback in self._subscribers.get(event_type, []):
            callback(*args, **kwargs)