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
        try:
            tree = ast.parse(source_code)
            self._extract_from_ast(tree)
        except SyntaxError:
            pass

        self._extract_via_regex(source_code)

    def _extract_from_ast(self, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, (int, float)):
                            self._constants[target.id] = node.value.value
                        elif isinstance(node.value, ast.BinOp):
                            try:
                                code = compile(ast.Expression(node.value), '<string>', 'eval')
                                val = eval(code, {"__builtins__": {}}, self._constants)
                                if isinstance(val, (int, float)):
                                    self._constants[target.id] = int(val)
                            except Exception:
                                pass

            elif isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr.lower()
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id.lower()

                if func_name in ('set', 'setex', 'setnx', 'expire', 'pexpire'):
                    key_arg = None
                    ttl_arg = None
                    
                    if node.args:
                        if isinstance(node.args[0], (ast.Constant, ast.Str)):
                            key_arg = node.args[0].value if hasattr(node.args[0], 'value') else node.args[0].s
                        elif isinstance(node.args[0], ast.JoinedStr):
                            parts = []
                            for value in node.args[0].values:
                                if isinstance(value, ast.Constant):
                                    parts.append(str(value.value))
                                elif isinstance(value, ast.FormattedValue):
                                    if isinstance(value.value, ast.Name):
                                        parts.append(f"{{{value.value.id}}}")
                                    else:
                                        parts.append("{id}")
                            key_arg = "".join(parts)

                    for keyword in node.keywords:
                        if keyword.arg in ('ex', 'px', 'expire'):
                            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, (int, float)):
                                ttl_arg = keyword.value.value
                            elif isinstance(keyword.value, ast.Name) and keyword.value.id in self._constants:
                                ttl_arg = self._constants[keyword.value.id]

                    if len(node.args) > 1:
                        if isinstance(node.args[1], (ast.Constant, ast.Num, ast.Constant)):
                            val = node.args[1].value if hasattr(node.args[1], 'value') else getattr(node.args[1], 'n', None)
                            if isinstance(val, int):
                                ttl_arg = val
                        elif isinstance(node.args[1], ast.Name) and node.args[1].id in self._constants:
                            ttl_arg = self._constants[node.args[1].id]

                    if key_arg and self._is_valid_cache_key(key_arg):
                        self.cache_patterns.add(key_arg)
                        if ttl_arg is not None:
                            self.ttls[key_arg] = ttl_arg

                elif func_name in ('delete', 'del', 'unlink', 'exists'):
                    for arg in node.args:
                        if isinstance(arg, (ast.Constant, ast.Str)):
                            k = arg.value if hasattr(arg, 'value') else arg.s
                            if self._is_valid_cache_key(k):
                                self.invalidation_rules.append({"trigger": func_name, "target": k})

    def _extract_via_regex(self, source_code: str):
        # Regex melhorada para capturar chaves literais ou f-strings em comandos Redis
        pattern_str = r'(?:set|setex|setnx|expire|delete|del|unlink)\s*\(\s*(?:f["\']([^"\']+)["\']|["\']([^"\']+)["\'])'
        for match in re.finditer(pattern_str, source_code, re.IGNORECASE):
            key = match.group(1) or match.group(2)
            if key and self._is_valid_cache_key(key):
                self.cache_patterns.add(key)

    def _is_valid_cache_key(self, key: str) -> bool:
        if not key or len(key) < 2:
            return False
        if key.startswith("http://") or key.startswith("https://"):
            return False
        if "Error" in key or "error" in key or "failed" in key:
            return False
        return True

    def parse_config(self, config_content: str):
        for line in config_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                self.invalidation_rules.append({"directive": parts[0], "target": parts[1]})

    def generate_markdown(self) -> str:
        lines = ["# Relatório Automatizado de Políticas de Cache e Invalidação\n"]
        
        lines.append("## Chaves Monitoradas e TTLs\n")
        if self.cache_patterns:
            lines.append("| Padrão de Chave | TTL Configurado (s) |")
            lines.append("|-----------------|---------------------|")
            for key in sorted(self.cache_patterns):
                ttl = self.ttls.get(key, "Não definido / Dinâmico")
                lines.append(f"| `{key}` | {ttl} |")
        else:
            lines.append("_Nenhum padrão estático de chave detectado._")

        lines.append("\n## Regras de Invalidação\n")
        if self.invalidation_rules:
            lines.append("| Gatilho / Diretiva | Alvo / Parâmetro |")
            lines.append("|---------------------|------------------|")
            for rule in self.invalidation_rules:
                trigger = rule.get("trigger", rule.get("directive", "Configuração"))
                target = rule.get("target", "")
                lines.append(f"| `{trigger}` | `{target}` |")
        else:
            lines.append("_Nenhuma regra de invalidação detectada._")

        return "\n".join(lines)