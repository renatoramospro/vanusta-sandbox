import re
import ast

class CacheDocExtractor:
    """
    Extrator estático avançado de políticas de cache, TTLs e estratégias de invalidação
    a partir de código-fonte Python e arquivos de configuração Redis.
    """
    def __init__(self):
        self.cache_patterns = set()
        self.ttls = {}
        self.invalidation_rules = []
        self._constants = {}

    def parse_source_code(self, source_code: str):
        # Utiliza AST (Abstract Syntax Tree) para análise estática robusta de código Python
        try:
            tree = ast.parse(source_code)
            self._extract_from_ast(tree)
        except SyntaxError:
            pass

        # Fallback / complementação via Regex avançada para casos específicos e literais
        self._extract_via_regex(source_code)

    def _extract_from_ast(self, tree: ast.AST):
        for node in ast.walk(tree):
            # Captura atribuições de constantes (ex: CACHE_TTL = 3600)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                            self._constants[target.id] = node.value.value
                        elif isinstance(node.value, ast.BinOp):
                            # Tenta resolver expressões simples como 15 * 60
                            try:
                                val = eval(ast.unparse(node.value))
                                self._constants[target.id] = int(val)
                            except Exception:
                                pass

            # Captura chamadas de métodos (ex: redis.setex, r.expire, etc.)
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr.lower()
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id.lower()

                # Extração de TTL e chaves em chamadas como setex(key, ttl, val)
                if func_name in ("setex", "psetex"):
                    if len(node.args) >= 2:
                        key_val = self._extract_ast_string(node.args[0])
                        ttl_val = self._extract_ast_ttl(node.args[1])
                        if key_val:
                            self.cache_patterns.add(key_val)
                        if key_val and ttl_val is not None:
                            self.ttls[key_val] = ttl_val

                # Extração em expire(key, ttl)
                elif func_name in ("expire", "pexpire"):
                    if len(node.args) >= 2:
                        key_val = self._extract_ast_string(node.args[0])
                        ttl_val = self._extract_ast_ttl(node.args[1])
                        if key_val:
                            self.cache_patterns.add(key_val)
                        if key_val and ttl_val is not None:
                            self.ttls[key_val] = ttl_val

                # Extração de argumentos nomeados (ex: set(..., ex=CACHE_TTL))
                for keyword in node.keywords:
                    if keyword.arg in ("ex", "px", "exat", "pxat"):
                        ttl_val = self._extract_ast_ttl(keyword.value)
                        # Tenta associar à primeira chave encontrada na mesma chamada
                        if node.args and ttl_val is not None:
                            key_val = self._extract_ast_string(node.args[0])
                            if key_val:
                                self.cache_patterns.add(key_val)
                                self.ttls[key_val] = ttl_val

    def _extract_ast_string(self, node) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if not node.value.startswith(("http://", "https://", "Error", "Info")):
                return node.value
        elif isinstance(node.value, ast.JoinedStr):
            # F-strings convertidas para padrão de chave legível
            parts = []
            for value in node.value.values:
                if isinstance(value, ast.Constant):
                    parts.append(str(value.value))
                elif isinstance(value, ast.FormattedValue):
                    parts.append("{id}")
            return "".join(parts)
        return ""

    def _extract_ast_ttl(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return int(node.value)
        elif isinstance(node, ast.Name) and node.id in self._constants:
            return self._constants[node.id]
        elif isinstance(node, ast.BinOp):
            try:
                return int(eval(ast.unparse(node)))
            except Exception:
                return None
        return None

    def _extract_via_regex(self, source_code: str):
        # Ignora comentários comuns no código fonte
        clean_code = re.sub(r'#.*$', '', source_code, flags=re.MULTILINE)

        # Captura padrões literais de chaves (com dois-pontos ou identificadores de cache)
        literal_keys = re.findall(r'[\'"]([a-zA-Z0-9_-]+:[a-zA-Z0-9_:{}-]+)[\'"]', clean_code)
        for lk in literal_keys:
            if not lk.startswith(("http://", "https://")):
                self.cache_patterns.add(lk)

        # Captura comandos de invalidação
        inv_matches = re.findall(r'\b(DEL|UNLINK|FLUSHDB|FLUSHALL)\b[\s\(]+[\'"]?([^\'")\s]*)', clean_code, re.IGNORECASE)
        for cmd, target in inv_matches:
            self.invalidation_rules.append({
                "command": cmd.upper(),
                "target": target if target else "global/pattern"
            })

    def parse_config(self, config_content: str):
        for line in config_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                if parts[0] in ("maxmemory-policy", "save", "appendonly"):
                    self.invalidation_rules.append({
                        "command": "CONFIG",
                        "target": parts[1]
                    })

    def generate_markdown(self) -> str:
        md = "# Relatório Automatizado de Políticas de Cache e Invalidação\n\n"
        
        md.endswith("")
        md += "## 1. Chaves Monitoradas e Padrões\n"
        if self.cache_patterns:
            md += "| Padrão / Chave | TTL Padrão (s) |\n|---|---|\n"
            for pattern in sorted(self.cache_patterns):
                ttl = self.ttls.get(pattern, "Não definido / Dinâmico")
                md += f"| `{pattern}` | {ttl} |\n"
        else:
            md += "_Nenhum padrão estático de chave detectado._\n"

        md += "\n## 2. Estratégias e Regras de Invalidação\n"
        if self.invalidation_rules:
            md += "| Comando / Configuração | Alvo / Escopo |\n|---|---|\n"
            for rule in self.invalidation_rules:
                md += f"| `{rule['command']}` | `{rule['target']}` |\n"
        else:
            md += "_Nenhuma regra de invalidação detectada._\n"

        return md