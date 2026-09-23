import ast
import os
import json

# Código-fonte simulado da aplicação para análise estática
SAMPLE_APP_CODE = """
from flask import Flask
from opentelemetry import trace, metrics, logs

app = Flask(__name__)
tracer = trace.get_tracer("my-service")
meter = metrics.get_meter("my-service")
logger = logs.get_logger("my-service")

request_counter = meter.create_counter("http_requests_total", description="Total requests")

@app.route("/api/v1/users", methods=["GET"])
def get_users():
    with tracer.start_as_current_span("fetch_users_from_db"):
        request_counter.add(1, {"route": "/api/v1/users"})
        logger.info("Fetched users successfully", extra={"user_count": 10})
    return {"users": []}

@app.route("/api/v1/orders", methods=["POST"])
def create_order():
    with tracer.start_as_current_span("process_payment_gateway"):
        request_counter.add(1, {"route": "/api/v1/orders"})
    return {"status": "created"}

def internal_helper_function():
    # Esta função não é endpoint, deve ser ignorada no catálogo de rotas
    pass
"""

class TelemetryAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.endpoints = []
        self.current_endpoint = None

    def visit_FunctionDef(self, node):
        # Verifica se a função é um endpoint web (possui decoradores)
        route_info = None
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr == "route" or decorator.func.attr in ["get", "post", "put", "delete"]:
                    # Tenta extrair o path da rota (primeiro argumento)
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        route_info = decorator.args[0].value
            elif isinstance(decorator, ast.Name):
                # Caso simplificado de decorador
                pass

        if route_info:
            self.current_endpoint = {
                "name": node.name,
                "route": route_info,
                "spans": [],
                "metrics": [],
                "logs": []
            }
            self.endpoints.append(self.current_endpoint)
            # Visita os nós internos da função
            self.generic_visit(node)
            self.current_endpoint = None
        else:
            # Função comum, apenas visita sem registrar como endpoint primário
            self.generic_visit(node)

    def visit_Call(self, node):
        if self.current_endpoint is not None:
            # Detecção de Spans (ex: tracer.start_as_current_span)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "start_as_current_span":
                if node.args and isinstance(node.args[0], ast.Constant):
                    self.current_endpoint["spans"].append(node.args[0].value)

            # Detecção de Métricas (ex: counter.add)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in ["add", "record"]:
                # Tenta associar o nome do objeto métrica se possível
                metric_name = getattr(node.func.value, "id", "unknown_metric")
                self.current_endpoint["metrics"].append(metric_name)

            # Detecção de Logs (ex: logger.info)
            elif isinstance(node.func, ast.Attribute) and node.func.attr in ["info", "error", "warn", "debug"]:
                if node.args and isinstance(node.args[0], ast.Constant):
                    self.current_endpoint["logs"].append(node.args[0].value)

        self.generic_visit(node)

def generate_markdown_catalog(endpoints):
    md = "# Catálogo de Observabilidade (OpenTelemetry)\n\n"
    md += "Este documento foi gerado automaticamente por análise estática de AST.\n\n"
    
    for ep in endpoints:
        md += f"## Rota: `{ep['route']}` (Função: `{ep['name']}`)\n\n"
        
        md += "### Traces (Spans)\n"
        if ep["spans"]:
            for span in ep["spans"]:
                md += f"- Span: `{span}`\n"
        else:
            md += "- *Nenhum span registrado explicitamente.*\n"
        
        md += "\n### Métricas\n"
        if ep["metrics"]:
            for m in ep["metrics"]:
                md += f"- Métrica incrementada/registrada via objeto: `{m}`\n"
        else:
            md += "- *Nenhuma métrica registrada.*\n"

        md += "\n### Logs\n"
        if ep["logs"]:
            for l in ep["logs"]:
                md += f"- Log emitido: \"{l}\"\n"
        else:
            md += "- *Nenhum log registrado.*\n"

        md += "\n---\n\n"
    
    return md

if __name__ == "__main__":
    # Salva o código de exemplo num arquivo temporário
    with open("app_sample.py", "w") as f:
        f.write(SAMPLE_APP_CODE)

    # Executa a análise AST
    with open("app_sample.py", "r") as f:
        tree = ast.parse(f.read())

    analyzer = TelemetryAnalyzer()
    analyzer.visit(tree)

    print(f"Endpoints encontrados e analisados: {len(analyzer.endpoints)}")
    for ep in analyzer.endpoints:
        print(f" -> {ep['route']} | Spans: {ep['spans']} | Métricas: {ep['metrics']} | Logs: {len(ep['logs'])}")

    # Gera o catálogo Markdown
    markdown_output = generate_markdown_catalog(analyzer.endpoints)
    
    with open("observability_catalog.md", "w") as f:
        f.write(markdown_output)

    print("\nCatálogo Markdown gerado com sucesso em 'observability_catalog.md'.")
    
    # Validação de Cobertura (Critério de Sucesso)
    assert len(analyzer.endpoints) == 2, "Deveria ter encontrado exatamente 2 endpoints."
    assert all(len(ep["spans"]) > 0 for ep in analyzer.endpoints), "Todos os endpoints devem possuir telemetria de trace associada."
    print("Validação de cobertura de 100% concluída com êxito!")

    # Limpeza de arquivos gerados no teste
    for cleanup_file in ["app_sample.py", "observability_catalog.md"]:
        if os.path.exists(cleanup_file):
            os.remove(cleanup_file)