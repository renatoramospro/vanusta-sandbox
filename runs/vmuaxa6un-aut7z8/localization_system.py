import time
from typing import Dict, Callable, List, Any, Optional

class LocalizationManager:
    def __init__(self, default_lang: str = "en"):
        self._current_lang: str = default_lang
        self._default_lang: str = default_lang
        # Estrutura: { 'en': {'key': 'val'}, 'pt-BR': {'key': 'val'} }
        self._dictionaries: Dict[str, Dict[str, str]] = {}
        # Lista de observadores (callbacks)
        self._observers: List[Callable[[], None]] = []

    def subscribe(self, callback: Callable[[], None]):
        """Registra um componente para ser notificado em mudanças de idioma."""
        if callback not in self._observers:
            self._observers.append(callback)

    def unsubscribe(self, callback: Callable[[], None]):
        """Remove um componente para evitar vazamento de memória (Memory Leak)."""
        try:
            self._observers.remove(callback)
        except ValueError:
            pass

    def load_language(self, lang_code: str, data: Any):
        """
        Carrega um dicionário de idioma com validação estrutural.
        Se o dado for inválido, o carregamento é abortado para proteger o estado atual.
        """
        if not isinstance(data, dict):
            print(f"[Error] Falha no Hot-Reload: Dados para '{lang_code}' são inválidos (deve ser dict).")
            return False
        
        self._dictionaries[lang_code] = data
        return True

    def set_language(self, lang_code: str):
        """Troca o idioma atual e notifica observadores."""
        if lang_code in self._dictionaries:
            self._current_lang = lang_code
            self._notify_observers()
            return True
        print(f"[Error] Idioma '{lang_code}' não encontrado.")
        return False

    def _notify_observers(self):
        """Dispara o evento de atualização para todos os componentes ativos."""
        for callback in self._observers:
            callback()

    def get_text(self, key: str) -> str:
        """
        Busca o texto com suporte a fallback hierárquico:
        1. Idioma atual (ex: pt-BR)
        2. Idioma genérico (ex: pt)
        3. Idioma padrão (ex: en)
        4. Retorna a própria chave como último recurso.
        """
        # 1. Tenta o idioma atual
        current_dict = self._dictionaries.get(self._current_lang, {})
        if key in current_dict:
            return current_dict[key]

        # 2. Tenta o fallback regional (ex: de pt-BR para pt)
        if "-" in self._current_lang:
            generic_lang = self._current_lang.split("-")[0]
            generic_dict = self._dictionaries.get(generic_lang, {})
            if key in generic_dict:
                return generic_dict[key]

        # 3. Tenta o idioma padrão (default)
        default_dict = self._dictionaries.get(self._default_lang, {})
        if key in default_dict:
            return default_dict[key]

        # 4. Fallback final: retorna a chave para evitar quebra de UI
        return key

class TextLabel:
    """Componente de UI que reage a mudanças de idioma."""
    def __init__(self, manager: LocalizationManager, key: str):
        self.manager = manager
        self.key = key
        self.current_text: str = ""
        # Assina o manager para atualizações automáticas
        self.manager.subscribe(self.update_text)
        self.update_text()

    def update_text(self):
        """Atualiza o conteúdo visual com a nova tradução."""
        self.current_text = self.manager.get_text(self.key)

    def destroy(self):
        """Limpa referências para evitar vazamento de memória."""
        self.manager.unsubscribe(self.update_text)
        self.current_text = "[DESTROYED]"

def run_experiment():
    print("--- Iniciando Experimento de Localization Robusto ---")
    
    # Setup inicial
    manager = LocalizationManager(default_lang="en")
    
    # Dados de teste
    en_data = {"welcome": "Welcome", "play": "Play", "exit": "Exit"}
    pt_data = {"welcome": "Bem-vindo", "play": "Jogar"} # 'exit' está faltando
    pt_br_data = {"welcome": "Bem-vindo (BR)"}        # 'play' e 'exit' faltando
    
    manager.load_language("en", en_data)
    manager.load_language("pt", pt_data)
    manager.load_language("pt-BR", pt_br_data)
    
    # 1. Teste de Fallback Hierárquico
    manager.set_language("pt-BR")
    label_welcome = TextLabel(manager, "welcome")
    label_play = TextLabel(manager, "play")
    label_exit = TextLabel(manager, "exit")
    
    print(f"Teste Fallback (pt-BR -> pt -> en):")
    print(f"  welcome (direto pt-BR): {label_welcome.current_text}")
    print(f"  play (via pt): {label_play.current_text}")
    print(f"  exit (via en): {label_exit.current_text}")
    
    assert label_welcome.current_text == "Bem-vindo (BR)"
    assert label_play.current_text == "Jogar"
    assert label_exit.current_text == "Exit"

    # 2. Teste de Hot-Reload com Validação de Integridade
    print("\n--- Testando Hot-Reload de 'pt-BR' ---")
    new_pt_br = {"welcome": "NOVO Texto PT-BR"}
    manager.load_language("pt-BR", new_pt_br)
    manager.set_language("pt-BR")
    print(f"  Após Reload (pt-BR): {label_welcome.current_text}")
    assert label_welcome.current_text == "NOVO Texto PT-BR"

    # Teste de carga corrompida (não deve alterar o estado atual)
    print("--- Testando Hot-Reload de dado corrompido (deve falhar silenciosamente) ---")
    manager.load_language("pt-BR", "ESTE_NAO_E_UM_DICT") 
    manager.set_language("pt-BR")
    print(f"  Após tentativa de carga inválida: {label_welcome.current_text}")
    assert label_welcome.current_text == "NOVO Texto PT-BR"

    # 3. Teste de Vazamento de Memória (Unsubscribe)
    print("\n--- Testando Unsubscribe (Ciclo de Vida) ---")
    label_temp = TextLabel(manager, "welcome")
    print(f"  Label temporário criado: {label_temp.current_text}")
    
    label_temp.destroy() # Remove o observador
    
    # Muda o idioma; se o unsubscribe falhou, o label_temp tentaria atualizar (mas está destruído)
    manager.set_language("en")
    print(f"  Label temporário após destruir e mudar idioma: {label_temp.current_text}")
    assert label_temp.current_text == "[DESTROYED]"

    # 4. Teste de Performance (10k chaves)
    print("\n--- Testando Performance (10.000 chaves) ---")
    large_data = {f"key_{i}": f"value_{i}" for i in range(10000)}
    manager.load_language("large", large_data)
    
    start_time = time.perf_counter()
    manager.set_language("large")
    end_time = time.perf_counter()
    
    duration_ms = (end_time - start_time) * 1000
    print(f"  Tempo para trocar 10k chaves: {duration_ms:.4f}ms")
    assert duration_ms < 50

    print("\n[SUCESSO] Todos os critérios de robustez e performance foram atendidos.")

if __name__ == "__main__":
    run_experiment()