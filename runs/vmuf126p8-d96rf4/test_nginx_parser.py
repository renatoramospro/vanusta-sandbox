import os
import pytest
from nginx_parser import NginxConfigParser

def test_parser_upstream_and_routes(tmp_path):
    # Setup de arquivos temporários
    conf_dir = tmp_path / "conf.d"
    conf_dir.mkdir()
    
    main_conf = tmp_path / "nginx.conf"
    main_conf.write_text("http { include conf.d/*.conf; }")
    
    sub_conf = conf_dir / "site.conf"
    sub_conf.write_text("""
        upstream backend_pool {
            server 192.168.1.50:5000;
        }
        server {
            listen 443 ssl;
            server_name secure.empresa.com;
            location /secure-data {
                proxy_pass http://backend_pool;
            }
        }
    """)
    
    parser = NginxConfigParser(str(main_conf))
    parser.parse_file(str(main_conf))
    
    # Validações estruturais internas
    assert "backend_pool" in parser.upstreams
    assert len(parser.servers) == 1
    
    server = parser.servers[0]
    assert server['data']['directives']['server_name'] == "secure.empresa.com"
    assert len(server['data']['locations']) == 1
    
    loc = server['data']['locations'][0]
    assert loc['name'] == "/secure-data"
    assert loc['data']['directives']['proxy_pass'] == "http://backend_pool"
    
    # Validação da geração Markdown
    md = parser.generate_markdown()
    assert "secure.empresa.com" in md
    assert "backend_pool" in md
    assert "/secure-data" in md

def test_equivoco_comum_regex_isolado():
    """
    Demonstração de por que um parser baseado em regex simplista falha:
    Se existirem diretivas idênticas dentro de contextos diferentes (ex: proxy_pass 
    dentro de server vs location, ou múltiplos blocks), regex ingênua perde a hierarquia.
    O parser estruturado garante que o proxy_pass pertence ao location correto.
    """
    parser = NginxConfigParser("dummy.conf")
    # Injetando blocos aninhados para testar isolamento de escopo
    content = """
    server {
        server_name a.com;
        location /a {
            proxy_pass http://upstream_a;
        }
    }
    server {
        server_name b.com;
        location /b {
            proxy_pass http://upstream_b;
        }
    }
    """
    parser._tokenize_and_parse(content)
    
    assert len(parser.servers) == 2
    assert parser.servers[0]['data']['directives']['server_name'] == "a.com"
    assert parser.servers[0]['data']['locations'][0]['data']['directives']['proxy_pass'] == "http://upstream_a"
    
    assert parser.servers[1]['data']['directives']['server_name'] == "b.com"
    assert parser.servers[1]['data']['locations'][0]['data']['directives']['proxy_pass'] == "http://upstream_b"