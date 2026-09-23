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
            # Parse usando o dialeto padrão (compatível com ANSI/Postgres/Snowflake genérico)
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
            print(f"Erro ao processar query SQL: {e}")

    def generate_mermaid_diagram(self) -> str:
        """Gera a representação visual do grafo em sintaxe Mermaid.js."""
        mermaid_lines = ["graph TD;"]
        for src, tgt in sorted(self.edges):
            # Normaliza nomes para IDs válidos no Mermaid
            src_id = src.replace(".", "_")
            tgt_id = tgt.replace(".", "_")
            mermaid_lines.append(f"    {src_id}[{src}] --> {tgt_id}[{tgt}]")
            
        return "\n".join(mermaid_lines)

# --- SETUP DO EXPERIMENTO ---

def setup_mock_repository():
    """Cria um ambiente temporário com arquivos SQL simulando um pipeline de ETL."""
    os.makedirs("models", exist_ok=True)
    
    # Modelo 1: Camada Staging a partir de fonte bruta
    with open("models/stg_users.sql", "w") as f:
        f.write("CREATE TABLE stg_users AS SELECT id, name, signup_date FROM raw_users;")
        
    # Modelo 2: Camada Staging de transações
    with open("models/stg_transactions.sql", "w") as f:
        f.write("CREATE TABLE stg_transactions AS SELECT tx_id, user_id, amount, created_at FROM raw_transactions;")
        
    # Modelo 3: Camada Mart unindo as duas stgs (Join)
    with open("models/mart_user_summary.sql", "w") as f:
        f.write("""
            CREATE TABLE mart_user_summary AS 
            SELECT 
                u.id AS user_id,
                u.name,
                COUNT(t.tx_id) AS total_transactions,
                SUM(t.amount) AS lifetime_value
            FROM stg_users u
            LEFT JOIN stg_transactions t ON u.id = t.user_id
            GROUP BY 1, 2;
        """)

if __name__ == "__main__":
    print("--- INICIANDO EXPERIMENTO DE LINHAGEM DE DADOS ---")
    
    # 1. Cria o ambiente simulado de código SQL
    setup_mock_repository()
    
    # 2. Instancia o extrator apontando para o diretório de modelos
    extractor = LineageExtractor(sql_dir="models")
    extractor.parse_sql_files()
    
    # 3. Valida se capturou as tabelas esperadas
    print(f"Tabelas identificadas: {sorted(list(extractor.tables))}")
    print(f"Arestas de linhagem (Origem -> Destino): {extractor.edges}")
    
    # 4. Gera o artefato visual (Mermaid.js)
    mermaid_diagram = extractor.generate_mermaid_diagram()
    print("\n--- DIAGRAMA MERMAID GERADO ---")
    print(mermaid_diagram)
    
    # Assrições para garantir o sucesso do experimento
    assert "raw_users" in extractor.tables, "Erro: raw_users deveria estar mapeado."
    assert "mart_user_summary" in extractor.tables, "Erro: mart_user_summary deveria estar mapeado."
    assert ("stg_users", "mart_user_summary") in extractor.edges, "Erro: Dependência entre stg_users e mart_user_summary não encontrada."
    
    print("\n[SUCESSO] Grafo de linhagem extraído e validado com sucesso!")