import re
import os

class CacheDocExtractor:
    """
    Extrator estático de políticas de cache, TTLs e estratégias de invalidação
    a partir de arquivos de código-fonte e configuração do Redis.
    """
    def __init__(self):
        self.cache_patterns = set()
        self.ttls = {}
        self.invalidation_rules = []

    def parse_source_code(self, source_code: str):
        # 1. Extração de padrões de chaves e namespaces (ex: f"user:{id}:profile" ou 'session:*')
        key_matches = re.findall(r'(?:cache|redis)[._\w]*\b.*?[\'"]([^\'"]*[:*][^\'"]*)[\'"]', source_code, re.IGNORECASE)
        for k in key_matches:
            self.cache_patterns.add(k)

        # Captura genérica de strings parecidas com chaves Redis em atribuições ou literais (incluindo placeholders como {id})
        literal_keys = re.findall(r'[\'"]([a-zA-Z0-9_-]+:[a-zA-Z0-9_:{}-]+)[\'"]', source_code)
        for lk in literal_keys:
            self.cache_patterns.add(lk)

        # 2. Extração de TTLs configurados no código (ex: EXPIRE, SETEX, setex(..., 3600))
        ttl_matches = re.findall(r'(?:EXPIRE|setex|PEXPIRE)\s*\(\s*[\'"][^\'"]+[\'"]\s*,\s*(\d+)', source_code, re.IGNORECASE)
        for m in ttl_matches:
            self.ttls["dynamic_ttl_seconds"] = int(m)

        # Captura de chamadas diretas ao comando EXPIRE via cliente redis-py
        redis_expire = re.findall(r'\.expire\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(\d+)\s*\)', source_code, re.IGNORECASE)
        for key, t in redis_expire:
            self.ttls[key] = int(t)

        # 3. Extração de gatilhos de invalidação (DEL, UNLINK, flushall, etc.)
        inv_matches = re.findall(r'\b(DEL|UNLINK|FLUSHDB|FLUSHALL)\b[\s\(]+[\'"]?([^\'")\s]*)', source_code, re.IGNORECASE)
        for cmd, target in inv_matches:
            self.invalidation_rules.append({"command": cmd.upper(), "target": target if target else "Global/Dynamic"})

    def parse_config(self, config_content: str):
        # Extração de diretivas do redis.conf (ex: maxmemory-policy)
        policy_match = re.search(r'^\s*maxmemory-policy\s+([a-zA-Z0-9_-]+)', config_content, re.MULTILINE)
        if policy_match:
            self.invalidation_rules.append({"command": "CONFIG", "target": policy_match.group(1)})

    def generate_markdown(self) -> str:
        md = "# Relatório Automatizado de Políticas de Cache e Invalidação\n\n"
        
        md += "## 1. Padrões de Chaves Monitoradas\n"
        if self.cache_patterns:
            for pattern in sorted(self.cache_patterns):
                md += f"- `{pattern}`\n"
        else:
            md += "_Nenhum padrão estático de chave detectado._\n"
        
        md += "\n## 2. TTLs Configurados\n"
        if self.ttls:
            md += "| Chave / Escopo | TTL (Segundos) |\n|---|---|\n"
            for k, v in self.ttls.items():
                md += f"| `{k}` | {v} |\n"
        else:
            md += "_Nenhum TTL explícito detectado._\n"

        md += "\n## 3. Regras de Invalidação e Políticas\n"
        if self.invalidation_rules:
            md += "| Comando / Diretiva | Alvo / Escopo |\n|---|---|\n"
            for rule in self.invalidation_rules:
                md += f"| `{rule['command']}` | `{rule['target']}` |\n"
        else:
            md += "_Nenhuma regra de invalidação detectada._\n"

        return md