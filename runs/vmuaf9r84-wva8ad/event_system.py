import weakref
import gc

class RobustEventBus:
    """
    Um sistema de mensageria centralizado que utiliza referências fracas para 
    evitar vazamentos de memória e permite mutação segura durante o publish.
    """
    def __init__(self):
        # { event_type: [lista_de_referencias] }
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # Se for um método de instância (ex: self.on_event), usamos WeakMethod
        if hasattr(callback, "__self__") and callback.__self__ is not None:
            ref = weakref.WeakMethod(callback)
        else:
            # Se for função global ou lambda, usamos a referência direta
            ref = callback
            
        self._subscribers[event_type].append(ref)

    def unsubscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            return
        
        # Filtra a lista removendo o callback correspondente
        new_list = []
        for ref in self._subscribers[event_type]:
            actual_callback = ref() if isinstance(ref, weakref.WeakMethod) else ref
            if actual_callback != callback:
                new_list.append(ref)
        self._subscribers[event_type] = new_list

    def publish(self, event_type, *args, **kwargs):
        if event_type not in self._subscribers:
            return

        # CORREÇÃO: Copy-on-Publish para evitar erro de mutação durante iteração
        # Criamos uma cópia da lista para que desinscrições durante o loop não quebrem o iterador
        current_subscribers = list(self._subscribers[event_type])
        
        # Lista para armazenar assinantes que devem ser removidos (mortos)
        to_remove = []

        for ref in current_subscribers:
            # Resolve a referência fraca se necessário
            callback = ref() if isinstance(ref, weakref.WeakMethod) else ref
            
            if callback is None:
                to_remove.append(ref)
                continue
            
            try:
                # CORREÇÃO: Passagem correta de argumentos (*args, **kwargs)
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[EventBus] Erro ao disparar evento '{event_type}': {e}")

        # Limpeza automática de referências mortas (Garbage Collection manual do Bus)
        if to_remove:
            self._subscribers[event_type] = [
                r for r in self._subscribers[event_type] 
                if (r() if isinstance(r, weakref.WeakMethod) else r) is not None
            ]