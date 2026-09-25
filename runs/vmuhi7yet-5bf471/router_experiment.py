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
                break # Wildcard consome o restante da URL
            else:
                if seg not in current.children:
                    current.children[seg] = TrieNode()
                current = current.children[seg]
                
        current.handlers[method] = handler

    def lookup(self, method: str, path: str):
        segments = self._split_path(path)
        
        # DFS / Backtracking para exploração de caminhos na Trie com suporte a dinâmicos e wildcards.
        # Nota: Como o algoritmo pode explorar caminhos alternativos (estáticos vs dinâmicos),
        # a busca não possui complexidade estritamente O(K) universal em caso de múltiplos ramos rejeitados.
        def _search(node: TrieNode, seg_index: int, params: dict):
            if seg_index == len(segments):
                if method in node.handlers:
                    return node.handlers[method], params
                return None, None

            current_seg = segments[seg_index]

            # 1. Tenta correspondência estática exata primeiro (prioridade)
            if current_seg in node.children:
                handler, res_params = _search(node.children[current_seg], seg_index + 1, params)
                if handler is not None:
                    return handler, res_params

            # 2. Tenta correspondência de parâmetro dinâmico se houver
            if node.param_child is not None:
                new_params = params.copy()
                new_params[node.param_name] = current_seg
                handler, res_params = _search(node.param_child, seg_index + 1, new_params)
                if handler is not None:
                    return handler, res_params

            # 3. Tenta correspondência de wildcard se houver
            if node.wildcard_child is not None:
                new_params = params.copy()
                remaining_path = "/".join(segments[seg_index:])
                new_params[node.wildcard_name] = remaining_path
                if method in node.wildcard_child.handlers:
                    return node.wildcard_child.handlers[method], new_params

            return None, None

        return _search(self.root, 0, {})

def run_experiment():
    print("=== Iniciando Experimento do Roteador Trie (Corrigido) ===")
    router = TrieRouter()

    # Registro de rotas
    router.add_route("GET", "/api/v1/users", lambda p: "Lista de Usuários")
    router.add_route("GET", "/api/v1/users/:id", lambda p: f"Perfil do Usuário: {p.get('id')}")
    router.add_route("GET", "/api/v1/users/:id/posts/:post_id", lambda p: f"Usuário {p.get('id')} Post {p.get('post_id')}")
    router.add_route("GET", "/static/*filepath", lambda p: f"Arquivo estático: {p.get('filepath')}")

    print("\n--- 1. Testando Rota Estática ---")
    handler, params = router.lookup("GET", "/api/v1/users")
    print(f"Match: {handler(params)} | Params: {params}")
    assert handler is not None, "Falha ao resolver rota estática"

    print("\n--- 2. Testando Rota Dinâmica Simples ---")
    handler, params = router.lookup("GET", "/api/v1/users/42")
    print(f"Match: {handler(params)} | Params: {params}")
    assert params.get("id") == "42", "Parâmetro dinâmico incorreto"

    print("\n--- 3. Testando Rota Dinâmica Aninhada ---")
    handler, params = router.lookup("GET", "/api/v1/users/99/posts/555")
    print(f"Match: {handler(params)} | Params: {params}")
    assert params.get("id") == "99" and params.get("post_id") == "555", "Parâmetros múltiplos incorretos"

    print("\n--- 4. Testando Rota Wildcard ---")
    handler, params = router.lookup("GET", "/static/images/avatar.png")
    print(f"Match: {handler(params)} | Params: {params}")
    assert params.get("filepath") == "images/avatar.png", "Wildcard incorreto"

    print("\n--- 5. Testando Tratamento de Conflito de Parâmetros ---")
    try:
        router.add_route("GET", "/api/v1/items/:item_id", lambda p: "item")
        router.add_route("GET", "/api/v1/items/:other_id", lambda p: "conflito")
    except ValueError as e:
        print(f"Exceção capturada com sucesso: {e}")

    print("\n[SUCESSO] Experimento executado e validado conforme restrições arquiteturais.")

if __name__ == "__main__":
    run_experiment()