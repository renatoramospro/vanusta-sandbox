class TrieNode:
    def __init__(self):
        self.children = {}         # Mapeia string de segmento estático -> TrieNode
        self.handlers = {}         # Mapeia método HTTP -> handler function
        self.param_child = None    # Ponteiro para filho dinâmico (ex: :id)
        self.param_name = None     # Nome do parâmetro (ex: 'id')
        self.wildcard_child = None # Ponteiro para wildcard (ex: *filepath)
        self.wildcard_name = None

class TrieRouter:
    def __init__(self):
        self.root = TrieNode()

    def _split_path(self, path: str):
        return [seg for seg in path.strip("/").split("/") if seg]

    def add_route(self, method: str, path: str, handler):
        segments = self._split_path(path)
        current = self.root
        
        for seg in segments:
            if seg.startswith(":"):
                param_name = seg[1:]
                if current.param_child is None:
                    current.param_child = TrieNode()
                    current.param_name = param_name
                elif current.param_name != param_name:
                    raise ValueError(f"Conflito de parâmetro no mesmo nível: '{current.param_name}' vs '{param_name}'")
                current = current.param_child
            elif seg.startswith("*"):
                wildcard_name = seg[1:]
                if current.wildcard_child is None:
                    current.wildcard_child = TrieNode()
                    current.wildcard_name = wildcard_name
                elif current.wildcard_name != wildcard_name:
                    raise ValueError(f"Conflito de wildcard no mesmo nível: '{current.wildcard_name}' vs '{wildcard_name}'")
                current = current.wildcard_child
            else:
                if seg not in current.children:
                    current.children[seg] = TrieNode()
                current = current.children[seg]
                
        current.handlers[method] = handler

    def lookup(self, method: str, path: str):
        segments = self._split_path(path)
        params = {}
        handler = self._lookup_rec(self.root, segments, 0, method, params)
        return handler, params

    def _lookup_rec(self, node: TrieNode, segments: list, idx: int, method: str, params: dict):
        # Caso base: consumimos todos os segmentos da URL
        if idx == len(segments):
            return node.handlers.get(method)

        seg = segments[idx]

        # 1. Tentar correspondência exata estática primeiro (maior precedência)
        if seg in node.children:
            handler = self._lookup_rec(node.children[seg], segments, idx + 1, method, params)
            if handler is not None:
                return handler

        # 2. Tentar correspondência dinâmica (:param) com isolamento de estado (backtracking seguro)
        if node.param_child is not None:
            param_name = node.param_name
            # Verificar se já existia para restaurar corretamente em caso de falha do ramo
            had_key = param_name in params
            old_val = params.get(param_name)
            
            params[param_name] = seg
            handler = self._lookup_rec(node.param_child, segments, idx + 1, method, params)
            if handler is not None:
                return handler
            
            # Backtracking: restaurar estado anterior do dicionário de parâmetros
            if had_key:
                params[param_name] = old_val
            else:
                del params[param_name]

        # 3. Tentar correspondência wildcard (*filepath)
        if node.wildcard_child is not None:
            wildcard_name = node.wildcard_name
            remaining_path = "/".join(segments[idx:])
            had_key = wildcard_name in params
            old_val = params.get(wildcard_name)
            
            params[wildcard_name] = remaining_path
            handler = node.wildcard_child.handlers.get(method)
            if handler is not None:
                return handler
            
            if had_key:
                params[wildcard_name] = old_val
            else:
                del params[wildcard_name]

        return None

def run_experiment():
    print("=== Iniciando Experimento do Roteador Trie (Com Correção de Backtracking) ===")
    router = TrieRouter()

    # Registrar rotas para o teste
    router.add_route("GET", "/api/v1/users/admin", lambda p: "Admin Especial")
    router.add_route("GET", "/api/v1/users/:id", lambda p: f"Usuário dinâmico: {p.get('id')}")
    router.add_route("GET", "/api/v1/items/:item_id/details", lambda p: f"Item {p.get('item_id')}")

    print("\n--- 1. Testando Precedência Estática vs Dinâmica ---")
    handler, params = router.lookup("GET", "/api/v1/users/admin")
    print(f"Match: {handler(params)} | Params: {params}")
    assert handler(params) == "Admin Especial", "Rota estática admin falhou"
    assert params == {}, "Parâmetros não devem vazar na rota estática"

    print("\n--- 2. Testando Rota Dinâmica Padrão ---")
    handler, params = router.lookup("GET", "/api/v1/users/42")
    print(f"Match: {handler(params)} | Params: {params}")
    assert params.get("id") == "42", "Parâmetro dinâmico incorreto"

    print("\n--- 3. Testando Cenário Adversarial de Backtracking com Limpeza de Estado ---")
    # Tenta um caminho que falha no ramo estático/dinâmico interno e força backtracking limpo
    handler, params = router.lookup("GET", "/api/v1/items/99/details")
    print(f"Match: {handler(params)} | Params: {params}")
    assert params.get("item_id") == "99", "Falha na extração do parâmetro item_id"

    print("\n[SUCESSO] Experimento executado com sucesso e isolamento de estado validado.")

if __name__ == "__main__":
    run_experiment()