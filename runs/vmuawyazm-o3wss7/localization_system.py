import time
import json
from typing import Dict, Callable, List

class LocalizationManager:
    def __init__(self, fallback_lang: str = "en"):
        self._current_lang: str = fallback_lang
        self._fallback_lang: str = fallback_lang
        self._dictionaries: Dict[str, Dict[str, str]] = {}
        self._observers: List[Callable[[], None]] = []

    def subscribe(self, callback: Callable[[], None]):
        """Registra um componente para ser notificado em mudanças de idioma."""
        self._observers.append(callback)

    def load_language(self, lang_code: str, data: dict):
        """Carrega um dicionário de idioma. Simula o carregamento de arquivo."""
        self._dictionaries[lang_code] = data

    def set_language(self, lang_code: str):
        """Troca o idioma atual e notifica observadores."""
        if lang_code not in self._dictionaries:
            print(f"[Error] Language {lang_code} not loaded. Keeping {self._current_lang}")
            return
        
        self._current_lang = lang_code
        self._notify_observers()

    def _notify_observers(self):
        for callback in self._observers:
            callback()

    def get_text(self, key: str) -> str:
        """Busca o texto com fallback para o idioma reserva."""
        # Tenta no idioma atual
        current_dict = self._dictionaries.get(self._current_lang, {})
        if key in current_dict:
            return current_dict[key]
        
        # Fallback para o idioma de reserva
        fallback_dict = self._dictionaries.get(self._fallback_lang, {})
        if key in fallback_dict:
            return fallback_dict[key]
        
        return f"MISSING_KEY: {key}"

# --- Componentes de UI (Simulados) ---

class TextLabel:
    def __init__(self, manager: LocalizationManager, key: str):
        self.manager = manager
        self.key = key
        self.current_text = ""
        # O componente se inscreve para atualizações automáticas
        self.manager.subscribe(self.refresh)
        self.refresh()

    def refresh(self):
        """Atualiza o texto exibido sem intervenção externa."""
        self.current_text = self.manager.get_text(self.key)

    def __repr__(self):
        return f"[Label({self.key}) -> '{self.current_text}']"

# --- Teste de Performance e Funcionalidade ---

def run_experiment():
    print("--- Iniciando Experimento de Localization ---")
    manager = LocalizationManager(fallback_lang="en")

    # 1. Preparação de Dados (10.000 chaves)
    en_data = {f"key_{i}": f"English Text {i}" for i in range(10000)}
    pt_data = {f"key_{i}": f"Texto em Português {i}" for i in range(10000)}
    # Adicionando uma chave que só existe em EN para testar fallback
    en_data["only_en"] = "I am English only"

    manager.load_language("en", en_data)
    manager.load_language("pt", pt_data)

    # 2. Teste de Performance de Carregamento/Troca
    start_time = time.perf_counter()
    manager.set_language("pt")
    end_time = time.perf_counter()
    
    duration_ms = (end_time - start_time) * 1000
    print(f"Tempo de troca de idioma (10k chaves): {duration_ms:.4f}ms")
    assert duration_ms < 50, "Performance abaixo do esperado!"

    # 3. Teste de Hot-Reload e Observadores
    label_welcome = TextLabel(manager, "key_0")
    label_special = TextLabel(manager, "only_en") # Deve usar fallback

    print(f"Antes do reload (PT): {label_welcome}")
    print(f"Antes do reload (Fallback): {label_special}")

    # Simulando Hot-Reload: Carregando um novo PT com dados diferentes
    print("\n--- Simulando Hot-Reload de arquivo PT ---")
    new_pt_data = {f"key_{i}": f"NOVO Texto PT {i}" for i in range(10000)}
    manager.load_language("pt", new_pt_data)
    manager.set_language("pt") # Dispara o evento

    print(f"Depois do reload (PT): {label_welcome}")
    print(f"Depois do reload (Fallback): {label_special}")

    # Validação de Fallback
    assert label_special.current_text == "I am English only", "Fallback falhou!"
    assert label_welcome.current_text == "NOVO Texto PT 0", "Hot-reload falhou!"

    print("\n[SUCESSO] Todos os critérios de performance e funcionalidade foram atendidos.")

if __name__ == "__main__":
    run_experiment()