import ast
import os

# Código-fonte avançado com múltiplos decoradores, aliases de variáveis e funções auxiliares
ADVANCED_APP_CODE = """
from flask import Flask
from opentelemetry import trace as ot_trace, metrics as ot_metrics, logs as ot_logs

app = Flask(__name__)
custom_tracer = ot_trace.get_tracer("payment-service")
custom_meter = ot_metrics.get_meter("payment-service")
custom_logger = ot_logs.get_logger("payment-service")

pay_counter = custom_meter.create_counter("payments_total")

def helper_record_telemetry(amount):
    # Função auxiliar indireta encapsulando telemetria
    with custom_tracer.start_as_current_span("helper_db_commit"):
        pay_counter.add(amount, {"status": "success"})
        custom_logger.info("Payment committed via helper", extra={"amount": amount})

@app.route("/api/v1/payments", methods=["POST"])
@login_required_decorator
@cache_decorator(timeout=30)
def process_payment():
    # Chamada indireta através de função auxiliar
    helper_record_telemetry(100.0)
    return {"status": "processed"}
"""

class AdvancedTelemetryAnalyzer(ast.NodeVisitor):
    def __init__(self, tree):
        self.tree = tree
        self.tracer_aliases = set()
        self.meter_aliases = set()
        self.logger_aliases = set()
        self.endpoints = []
        self.helper_functions = {} # Nome -> FunctionDef node
        
        # 1. Pré-passagem para identificar aliases e funções auxiliares
        self._resolve_bindings_and_helpers(tree)

    def _resolve_bindings_and_helpers(self, node):
        for subnode in ast.walk(node):
            # Identifica atribuições de tracer, meter, logger
            if isinstance(subnode, ast.Assign):
                for target in subnode.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(subnode.value, ast.Call):
                            func = subnode.value.func
                            func_str = ""
                            if isinstance(func, ast.Attribute):
                                func_str = f"{getattr(func.value, 'id', '')}.{func.attr}"
                            elif isinstance(func, ast.Name):
                                func_str = func.id
                            
                            if "get_tracer" in func_str:
                                self.tracer_aliases.add(target.id)
                            elif "get_meter" in func_str:
                                self.meter_aliases.add(target.id)
                            elif "get_logger" in func_str:
                                self.logger_aliases.add(target.id)
            
            # Armazena funções auxiliares para inspeção indireta
            if isinstance(subnode, ast.FunctionDef):
                self.helper_functions[subnode.name] = subnode

    def visit_FunctionDef(self, node):
        # Verifica múltiplos decoradores por rota
        is_route = False
        for decorator in node.decorator_list:
            dec_str = self._get_decorator_string(decorator)
            if "route" in dec_str or "get" in dec_str or "post" in dec_str:
                is_route = True
                break
        
        if is_route:
            endpoint_data = {
                "route_func": node.name,
                "spans": set(),
                "metrics": set(),
                "logs": []
            }
            
            # Analisa o corpo da função da rota e também funções auxiliares chamadas
            self._analyze_scope(node, endpoint_data)
            
            # Converte sets para listas para serialização
            endpoint_data["spans"] = list(endpoint_data["spans"])
            endpoint_data["metrics"] = list(endpoint_data["metrics"])
            self.endpoints.append(endpoint_data)
        
        self.generic_visit(node)

    def _get_decorator_string(self, decorator):
        if isinstance(decorator, ast.Call):
            return self._get_decorator_string(decorator.func)
        if isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_string(decorator.value)}.{decorator.attr}"
        if isinstance(decorator, ast.Name):
            return decorator.id
        return ""

    def _analyze_scope(self, node, endpoint_data, visited_helpers=None):
        if visited_helpers is None:
            visited_helpers = set()

        for child in ast.walk(node):
            # Detecta chamadas de Span (ex: tracer.start_as_current_span)
            if isinstance(child, ast.With):
                for item in child.items:
                    if isinstance(item.context_expr, ast.Call):
                        func = item.context_expr.func
                        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                            if func.value.id in self.tracer_aliases or "tracer" in func.value.id:
                                if child.items[0].optional_vars: # se houver span var
                                    pass
                                # Tenta extrair o nome literal do span
                                for arg in item.context_expr.args:
                                    if isinstance(arg, ast.Constant):
                                        endpoint_data["spans"].add(arg.value)

            # Detecta incremento de métricas ou logs
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Attribute):
                    attr_name = func.attr
                    # Verifica se é chamada em meter/logger ou aliases
                    if attr_name in ["add", "record", "increment"]:
                        if isinstance(func.value, ast.Name):
                            endpoint_data["metrics"].add(func.value.id)
                    elif attr_name in ["info", "error", "warn", "debug", "exception"]:
                        if isinstance(func.value, ast.Name):
                            endpoint_data["logs"].append(f"Log via {func.value.id}")

                # Suporte a chamadas indiretas a funções auxiliares
                if isinstance(func, ast.Name):
                    helper_name = func.id
                    if helper_name in self.helper_functions and helper_name not in visited_helpers:
                        visited_helpers.add(helper_name)
                        self._analyze_scope(self.helper_functions[helper_name], endpoint_data, visited_helpers)

def generate_markdown(endpoints):
    md = "# Catálogo de Observabilidade Avançado\n\n"
    for ep in endpoints:
        md += f"## Rota: `{ep['route_func']}`\n"
        md += f"- **Spans:** {ep['spans']}\n"
        md += f"- **Métricas:** {ep['metrics']}\n"
        md += f"- **Logs:** {len(ep['logs'])} eventos\n\n"
    return md

if __name__ == "__main__":
    with open("advanced_app.py", "w") as f:
        f.write(ADVANCED_APP_CODE)

    tree = ast.parse(ADVANCED_APP_CODE)
    analyzer = AdvancedTelemetryAnalyzer(tree)
    analyzer.visit(tree)

    print(f"Endpoints avançados encontrados: {len(analyzer.endpoints)}")
    for ep in analyzer.endpoints:
        print(f" -> Função: {ep['route_func']} | Spans: {ep['spans']} | Métricas: {ep['metrics']} | Logs: {len(ep['logs'])}")

    # Asserts rigorosos validando que a análise resistiu aos cenários adversariais
    assert len(analyzer.endpoints) == 1, "Deveria encontrar a rota decorada apesar de múltiplos decoradores."
    assert "helper_db_commit" in analyzer.endpoints[0]["spans"], "Deve capturar spans encapsulados em funções auxiliares."
    assert len(analyzer.endpoints[0]["logs"]) > 0, "Deve capturar logs emitidos indiretamente."
    print("Validação robusta com sucesso: múltiplos decoradores, aliases e funções auxiliares mapeados!")

    # Limpeza
    for file in ["advanced_app.py"]:
        if os.path.exists(file):
            os.remove(file)