class TrieNode:
    def __init__(self):
        self.children = {}      # Mapeia string de segmento -> TrieNode
        self.is_end = False     # Indica se há uma rota completa aqui
        self.handlers = {}      # Mapeia método HTTP -> handler function
        self.param_child = None # Ponteiro para filho dinâmico (ex: :id)
        self.param_name = None  # Nome do parâmetro (ex: 'id')
        self.wildcard_child = None # Ponteiro para wildcard (ex: *filepath)
        self.wildcard_name = None

class TrieRouter:
    def __init__(self):
        self.root = TrieNode()

    def _split_path(self, path: str):
        # Remove barras iniciais/finais e divide por '/'
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
                    raise ValueError(feroz := f"Conflito de parâmetro no mesmo nível: '{current.param_name}' vs '{param_name}'")
                current = current.param_child
            elif seg.startswith("*"):
                wild_name = seg[1:]
                if current.wildcard_child is None:
                    current.wildcard_child = TrieNode()
                    current.wildcard_name = wild_name
                current = current.wildcard_child
                break # Wildcard consome o resto da rota
            else:
                if seg not in current.children:
                    current.children[seg] = TrieNode()
                current = current.children[seg]
                
        current.is_end = True
        current.handlers[method.upper()] = handler

    def lookup(self, method: str, path: str):
        segments = self._split_path(path)
        method = method.upper()
        
        # Fila de busca para backtracking: (node, segment_index, params_dict)
        # Como o roteador HTTP busca o caminho exato ou com precedência determinística,
        # podemos implementar via DFS recursivo ou iterativo.
        
        params = {}
        
        def _search(node: TrieNode, seg_index: int):
            # Caso base: consumimos todos os segmentos
            if seg_index == len(segments):
                if node.is_end and method in node.handlers:
                    return node.handlers[method], params
                # Verifica se há wildcard preenchendo o vazio restante
                if node.wildcard_child and node.wildcard_child.is_end and method in node.wildcard_child.handlers:
                    params[node.wildcard_name] = ""
                    return node.wildcard_child.handlers[method], params
                return None, None

            current_seg = segments[seg_index]

            # 1. Tenta correspondência estática exata (Prioridade máxima)
            if current_seg in node.children:
                handler, found_params = _search(node.children[current_seg], seg_index + 1)
                if handler:
                    return handler, found_params

            # 2. Tenta correspondência com parâmetro dinâmico (:param)
            if node.param_child:
                params[node.param_name] = current_seg
                handler, found_params = _search(node.param_child, seg_index + 1)
                if handler:
                    return handler, found_params
                # Backtrack do parâmetro se falhar em rotas profundas
                del params[node.param_name]

            # 3. Tenta correspondência com Wildcard (*filepath)
            if node.wildcard_child:
                # O wildcard consome todo o resto dos segmentos
                remaining = "/".join(segments[seg_index:])
                params[node.wildcard_name] = remaining
                if method in node.wildcard_child.handlers:
                    return node.wildcard_child.handlers[method], params

            return None, None

        return _search(self.root, 0)

# ==========================================
# EXPERIMENTO DE VALIDAÇÃO E DEMONSTRAÇÃO
# ==========================================
def run_experiment():
    router = TrieRouter()

    # 1. Registro de rotas estáticas e dinâmicas variadas
    router.add_route("GET", "/api/v1/status", lambda p: "Status OK")
    router.add_route("GET", "/api/v1/users/:id", lambda p: f"User Profile: {p.get('id')}")
    router.add_route("GET", "/api/v1/users/:id/posts/:post_id", lambda p: f"User {p.get('id')} Post {p.get('post_id')}")
    router.add_route("GET", "/static/*filepath", lambda p: f"Serving file: {p.get('filepath')}")

    print("--- 1. Testando Rota Estática ---")
    handler, params = router.lookup("GET", "/api/v1/status")
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
    handler, params = router.lookup("GET", "/static/images/avatars/user1.png")
    print(f"Match: {handler(params)} | Params: {params}")
    assert params.get("filepath") == "images/avatars/user1.png", "Wildcard incorreto"

    print("\n--- 5. Contraexemplo / Tratamento de Equívoco Comum ---")
    # Tentativa de invalidar o mito de que Trie não lida com parâmetros dinâmicos ou conflita
    try:
        router.add_route("GET", "/api/v1/items/:item_id", lambda p: "item")
        # Tentativa deliberada de conflito no mesmo nível com nome de parâmetro diferente
        router.add_route("GET", "/api/v1/items/:other_id", lambda p: "conflict")
    except ValueError as e:
        print(f"Exceção capturada com sucesso (Comportamento esperado de segurança da Trie): {e}")

    print("\n[SUCESSO] Todos os testes do roteador Trie passaram com 100% de precisão!")

if __name__ == "__main__":
    run_experiment()