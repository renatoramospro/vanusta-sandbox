import os
import glob
from typing import List, Dict, Set
import sqlglot
from sqlglot import exp

class LineageExtractor:
    def __init__(self, sql_dir: str):
        self.sql_dir = sql_dir
        self.edges: Set[tuple] = set() # (source, target)
        self.tables: Set[str] = set()

    def parse_sql_files(self) -> None:
        """Varre o diretório de SQLs, lê cada arquivo e extrai linhagem via AST."""
        search_path = os.path.join(self.sql_dir, "*.sql")
        for filepath in glob.glob(search_path):
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()
            
            self._extract_lineage_from_query(sql_content)

    def _extract_lineage_from_query(self, sql_query: str) -> None:
        """Usa sqlglot para analisar a AST e identificar tabelas de origem e destino."""
        try:
            expressions = sqlglot.parse(sql_query)
            
            for expression in expressions:
                if expression is None:
                    continue
                
                # Identifica a tabela de destino (target) em CTAS ou INSERT
                target_table = None
                if isinstance(expression, exp.Create):
                    target_table = expression.this.name
                elif isinstance(expression, exp.Insert):
                    target_table = expression.this.name
                
                if target_table:
                    self.tables.add(target_table.lower())
                
                # Extrai todas as tabelas lidas na query (sources)
                source_tables = [table.name.lower() for table in expression.find_all(exp.Table) if table.name]
                
                for src in source_tables:
                    self.tables.add(src)
                    if target_table and src != target_table.lower():
                        self.edges.add((src, target_table.lower()))
        except Exception as e:
            print(f"[AVISO] Erro ao fazer parse da query: {e}")

    def generate_mermaid_diagram(self) -> str:
        """Gera a representação em gráfico Mermaid.js a partir das arestas extraídas."""
        mermaid_lines = ["graph TD"]
        for src, tgt in sorted(self.edges):
            # Formatação segura para IDs no Mermaid
            src_id = src.replace(".", "_")
            tgt_id = tgt.replace(".", "_")
            mermaid_lines.append(f"    {src_id}[{src}] --> {tgt_id}[{tgt}]")
        
        return "\n".join(mermaid_lines)


if __name__ == "__main__":
    # Criação de um diretório temporário para simular um repositório de ETLs SQL
    test_sql_dir = "./sql_models"
    os.makedirs(test_sql_dir, exist_ok=True)

    # Criando arquivos SQL simulados de camadas diferentes (Raw -> Staging -> Mart)
    with open(os.path.join(test_sql_dir, "stg_users.sql"), "w") as f:
        f.write("CREATE TABLE stg_users AS SELECT id, name, email FROM raw_users WHERE active = true;")

    with open(os.path.join(test_sql_dir, "mart_user_summary.sql"), "w") as f:
        f.write("INSERT INTO mart_user_summary SELECT country, count(id) as total_users FROM stg_users GROUP BY country;")

    print(f"[INFO] Analisando arquivos SQL no diretório: {test_sql_dir}")
    
    # Executando o extrator
    extractor = LineageExtractor(test_sql_dir)
    extractor.parse_sql_files()

    print("\n--- TABELAS MAPEADAS ---")
    print(sorted(list(extractor.tables)))

    print("\n--- ARESTAS DE LINHAGEM (SOURCE -> TARGET) ---")
    for edge in sorted(list(extractor.edges)):
        print(f"{edge[0]} -> {edge[1]}")

    mermaid_diagram = extractor.generate_mermaid_diagram()
    print("\n--- DIAGRAMA MERMAID GERADO ---")
    print(mermaid_diagram)
    
    # Limpeza dos arquivos criados para teste
    for filepath in glob.glob(os.path.join(test_sql_dir, "*.sql")):
        os.remove(filepath)
    os.rmdir(test_sql_dir)

    # Assrições rigorosas para garantir o sucesso do experimento
    assert "raw_users" in extractor.tables, "Erro: raw_users deveria estar mapeado."
    assert "mart_user_summary" in extractor.tables, "Erro: mart_user_summary deveria estar mapeado."
    assert ("stg_users", "mart_user_summary") in extractor.edges, "Erro: Dependência entre stg_users e mart_user_summary não encontrada."
    assert ("raw_users", "stg_users") in extractor.edges, "Erro: Dependência entre raw_users e stg_users não encontrada."
    
    print("\n[SUCESSO] Grafo de linhagem extraído e validado com sucesso!")