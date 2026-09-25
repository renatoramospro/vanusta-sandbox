import os

class TrieNode:
    def __init__(self):
        self.children = {}         # Mapeia string de segmento estático -> TrieNode
        self.handlers = {}         # Mapeia método HTTP -> handler function
        self.param_child = None    # Ponteiro para filho dinâmico (ex: :id)
        self.param_name = None     # Nome do parâmetro (ex: 'id')
        self.wildcard_child = None # Ponteiro para wildcard (ex: *filepath)
        self.wildcard_name = None

class TrieRouter:
    def __init__(self, max_length=2048, max_depth=32):
        self.root = TrieNode()
        self.max_length = max_length
        self.max_depth = max_depth

    def _split_path(self, path: str):
        if not path or len(path) > self.max_length:
            raise ValueError("URL vazia ou excede o limite máximo de comprimento.")
        
        segments = [seg for seg in path.strip("/").split("/") if seg]
        if len(segments) > self.max_depth:
            raise ValueError("Profundidade de segmentos excede o limite máximo permitido.")
        return segments

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
                break # Wildcard consome o restante
            else:
                if seg not in current.children:
                    current.children[seg] = TrieNode()
                current = current.children[seg]
                
        current.handlers[method.upper()] = handler

    def lookup(self, method: str, path: str):
        segments = self._split_path(path)
        params = {}
        handler = self._lookup_rec(self.root, segments, 0, method.upper(), params)
        return handler, params

    def _lookup_rec(self, node: TrieNode, segments: list, index: int, method: str, params: dict):
        # Caso base: consumiu todos os segmentos
        if index == len(segments):
            return node.handlers.get(method)

        seg = segments[index]

        # 1. Tentar correspondência exata estática
        if seg in node.children:
            handler = self._lookup_rec(node.children[seg], segments, index + 1, method, params)
            if handler is not None:
                return handler

        # 2. Tentar parâmetro dinâmico (:name) com backtracking seguro
        if node.param_child is not None:
            param_name = node.param_name
            params[param_name] = seg
            handler = self._lookup_rec(node.param_child, segments, index + 1, method, params)
            if handler is not None:
                return handler
            # Backtracking: remove o parâmetro se o ramo falhou
            del params[param_name]

        # 3. Tentar wildcard (*filepath) com confinamento e canonicalização anti-path-traversal
        if node.wildcard_child is not None:
            remaining_segments = segments[index:]
            raw_path = "/".join(remaining_segments)
            
            # Canonicalização defensiva contra path traversal
            normalized = os.path.normpath("/" + raw_path).lstrip("/")
            if normalized.startswith("..") or ".." in normalized.split("/"):
                return None # Rejeita tentativa de path traversal

            wildcard_name = node.wildcard_name
            params[wildcard_name] = normalized
            handler = node.wildcard_child.handlers.get(method)
            if handler is not None:
                return handler
            del params[wildcard_name]

        return None

def run_experiment():
    print("=== Iniciando Experimento de Roteamento Seguro (Com Backtracking Real e Mitigação de Segurança) ===")
    router = TrieRouter()

    router.add_route("GET", "/api/v1/users/admin", lambda p: "Admin Especial")
    router.add_route("GET", "/api/v1/users/:id", lambda p: f"Usuário dinâmico: {p.get('id')}")
    router.add_route("GET", "/static/*filepath", lambda p: f"Arquivo seguro: {p.get('filepath')}")

    print("\n--- 1. Testando Rota Estática vs Dinâmica ---")
    h, p = router.lookup("GET", "/api/v1/users/admin")
    assert h(p) == "Admin Especial"
    print("Passou: Rota estática prioritária.")

    print("\n--- 2. Testando Backtracking Real com Falha em Ramo Dinâmico ---")
    # Vamos registrar uma rota que força backtracking se tentarmos um caminho inválido num nível compartilhado
    router.add_route("GET", "/docs/:version/guide", lambda p: f"Guia {p.get('version')}")
    
    # Tentativa que falha no segmento final após passar pelo parâmetro :version, forçando o mecanismo de limpeza
    h_fail, p_fail = router.lookup("GET", "/docs/v2/missing")
    assert h_fail is None, "Deveria retornar None para rota inexistente"
    assert p_fail == {}, "Backtracking garantiu que parâmetros parciais foram limpos do dicionário!"
    print("Passou: Backtracking real executado e dicionário de parâmetros limpo com sucesso.")

    print("\n--- 3. Testando Defesa contra Path Traversal em Wildcard ---")
    # Tentativa de acessar arquivo fora do diretório via ../
    h_safe, p_safe = router.lookup("GET", "/static/../../etc/passwd")
    assert h_safe is None, "Tentativa de Path Traversal bloqueada com sucesso!"
    print("Passou: Tentativa de Path Traversal rejeitada corretamente pelo roteador.")

    print("\n[SUCESSO] Todos os cenários de segurança e robustez passaram.")

if __name__ == "__main__":
    run_experiment()