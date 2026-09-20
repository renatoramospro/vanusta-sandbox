import ast

class ContextLeakAnalyzer(ast.NodeVisitor):
    def __init__(self, unsafe_sinks, sources):
        """
        :param unsafe_sinks: Lista de nomes de métodos/objetos que são destinos inseguros.
        :param sources: Lista de nomes de funções que produzem dados sensíveis.
        """
        self.unsafe_sinks = unsafe_sinks
        self.sources = sources
        self.tainted_vars = set()
        self.leaks = []

    def visit_Assign(self, node):
        # Regra de Propagação: y = x
        # Se x é tainted, y torna-se tainted.
        source_is_tainted = False
        
        # Verifica se o lado direito (value) é uma fonte ou uma variável tainted
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id in self.sources:
                source_is_tainted = True
        elif isinstance(node.value, ast.Name):
            if node.value.id in self.tainted_vars:
                source_is_tainted = True

        if source_is_tainted:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tainted_vars.add(target.id)
        
        self.generic_visit(node)

    def visit_Call(self, node):
        # Regra de Detecção: sink(tainted_var)
        # Verifica se a função chamada é um sink inseguro
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Trata chamadas como agent.process()
            func_name = f"{node.func.value.id}.{node.func.attr}" if hasattr(node.func.value, 'id') else node.func.attr

        if func_name in self.unsafe_sinks:
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in self.tainted_vars:
                    self.leaks.append({
                        "line": node.lineno,
                        "sink": func_name,
                        "variable": arg.id
                    })
        
        self.generic_visit(node)

def run_analysis(code, unsafe_sinks, sources):
    tree = ast.parse(code)
    analyzer = ContextLeakAnalyzer(unsafe_sinks, sources)
    analyzer.visit(tree)
    return analyzer.leaks