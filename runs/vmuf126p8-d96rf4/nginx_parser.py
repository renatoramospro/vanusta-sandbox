import os
import re
import glob

class NginxConfigParser:
    def __init__(self, root_config_path):
        self.root_config_path = root_config_path
        self.upstreams = {}
        self.servers = []

    def parse_file(self, filepath):
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Resolve diretivas include antes do parsing estrutural
        dir_name = os.path.dirname(filepath)
        include_pattern = re.compile(r'include\s+([^;]+);')
        
        def replace_include(match):
            inc_path = match.group(1).strip()
            # Se o caminho for relativo, resolve baseado no diretório atual
            if not os.path.isabs(inc_path):
                full_glob = os.path.join(dir_name, inc_path)
            else:
                full_glob = inc_path
            
            included_content = []
            for matched_file in glob.glob(full_glob):
                if os.path.exists(matched_file):
                    with open(matched_file, 'r', encoding='utf-8') as inf:
                        included_content.append(inf.read())
            return "\n".join(included_content)

        # Expande recursivamente os includes
        while include_pattern.search(content):
            content = include_pattern.sub(replace_include, content)

        return self._tokenize_and_parse(content)

    def _tokenize_and_parse(self, content):
        # Remove comentários
        content = re.sub(r'#.*', '', content)
        
        # Máquina de estados simples baseada em contagem de chaves para escopos
        lines = content.split('\n')
        current_context = []
        current_block_type = None
        current_block_name = None
        current_block_data = {}
        
        stack = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Detecta abertura de bloco (ex: upstream nome { , server { , location /rota { )
            if '{' in line:
                parts = line.split('{')[0].strip().split()
                if parts:
                    b_type = parts[0]
                    b_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                    
                    stack.append({
                        'type': b_type,
                        'name': b_name,
                        'data': {'locations': [], 'servers': [], 'directives': {}}
                    })
                i += 1
                continue

            # Detecta fechamento de bloco
            if '}' in line:
                if stack:
                    finished_block = stack.pop()
                    if finished_block['type'] == 'upstream':
                        self.upstreams[finished_block['name']] = finished_block['data']['servers']
                    elif finished_block['type'] == 'server':
                        self.servers.append(finished_block)
                    elif finished_block['type'] == 'location' and stack:
                        # Adiciona location ao server pai
                        stack[-1]['data']['locations'].append(finished_block)
                i += 1
                continue

            # Diretivas dentro dos blocos atuais
            if stack:
                if ';' in line:
                    directive_line = line.rstrip(';')
                    d_parts = directive_line.split(None, 1)
                    if len(d_parts) == 2:
                        d_key, d_val = d_parts[0], d_parts[1]
                        top = stack[-1]
                        
                        if d_key == 'server' and top['type'] == 'upstream':
                            top['data']['servers'].append(d_val)
                        else:
                            top['data']['directives'][d_key] = d_val
            i += 1

    def generate_markdown(self):
        md = []
        md.append("# Documentação de Infraestrutura Nginx (Proxy Reverso & Balanceamento)\n")
        
        md.append("## 1. Upstream Servers (Balanceamento de Carga)\n")
        if self.upstreams:
            for name, servers in self.upstreams.items():
                md.append(f"### Upstream: `{name}`")
                md.append("| Servidor / Destino |")
                md.append("|-------------------|")
                for s in servers:
                    md.append(f"| `{s}` |")
                md.append("")
        else:
            md.append("_Nenhum upstream configurado._\n")

        md.append("## 2. Servidores Virtuais e Rotas (Proxy Reverso)\n")
        if self.servers:
            for idx, srv in enumerate(self.servers, 1):
                srv_name = srv['data']['directives'].get('server_name', 'default')
                listen = srv['data']['directives'].get('listen', '80')
                
                md.append(f"### Servidor #{idx}: `listen {listen}` (Domínio: `{srv_name}`)")
                
                if srv['data']['locations']:
                    md.append("| Rota (`location`) | Política (`proxy_pass`) | Configurações Adicionais |")
                    md.append("|-------------------|-------------------------|--------------------------|")
                    for loc in srv['data']['locations']:
                        path = loc['name']
                        proxy = loc['data']['directives'].get('proxy_pass', 'N/A')
                        extra = ", ".join([f"{k}={v}" for k, v in loc['data']['directives'].items() if k != 'proxy_pass'])
                        md.append(f"| `{path}` | `{proxy}` | `{extra if extra else '-'}` |")
                    md.append("")
                else:
                    md.append("_Nenhuma rota mapeada para este servidor._\n")
        else:
            md.append("_Nenhum servidor virtual mapeado._\n")

        return "\n".join(md)

if __name__ == '__main__':
    # Criação de ambiente de testes simulado
    os.makedirs('conf.d', exist_ok=True)
    
    with open('nginx.conf', 'w') as f:
        f.write("events {}\nhttp {\n    include conf.d/*.conf;\n}\n")
        
    with open('conf.d/app.conf', 'w') as f:
        f.write("""
        upstream api_cluster {
            server 10.0.0.1:8080 weight=3;
            server 10.0.0.2:8080;
        }

        server {
            listen 80;
            server_name api.exemplo.com;

            location /api/v1 {
                proxy_pass http://api_cluster;
                proxy_set_header Host $host;
                proxy_connect_timeout 60s;
            }

            location /static {
                proxy_pass http://cdn.exemplo.com;
            }
        }
        """)

    parser = NginxConfigParser('nginx.conf')
    parser.parse_file('nginx.conf')
    markdown_output = parser.generate_markdown()
    
    print("--- MARKDOWN GERADO COM SUCESSO ---")
    print(markdown_output)
    
    # Assertivas de validação do critério de sucesso
    assert "api_cluster" in markdown_output, "Erro: Upstream não mapeado!"
    assert "api.exemplo.com" in markdown_output, "Erro: Server name não mapeado!"
    assert "/api/v1" in markdown_output, "Erro: Rota location não mapeada!"
    assert "http://api_cluster" in markdown_output, "Erro: Política proxy_pass não mapeada!"
    print("\n[TESTE EXECUTADO] Todas as asserções passaram com sucesso!")