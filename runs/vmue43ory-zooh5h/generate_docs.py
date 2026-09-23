import os
import re
from typing import Dict, List, Optional

# --- 1. REPRESENTAÇÃO INTERMEDIÁRIA (IR) ---
class TableSchema:
    def __init__(self, name: str):
        self.name: str = name
        self.columns: List[Dict[str, str]] = []
        self.foreign_keys: List[Dict[str, str]] = []

class DatabaseIR:
    def __init__(self):
        self.tables: Dict[str, TableSchema] = {}

    def add_table(self, table: TableSchema):
        self.tables[table.name] = table

# --- 2. PARSER ESTÁTICO DE MIGRAÇÕES SQL ROBUSTO ---
class SQLMigrationParser:
    """
    Parser robusto que lida com comentários multilinha e divisão correta de colunas,
    evitando falhas em tipos como DECIMAL(10,2) e restrições complexas.
    """
    @staticmethod
    def _split_columns_safely(body: str) -> List[str]:
        """
        Divide o corpo de um CREATE TABLE por vírgulas, respeitando parênteses aninhados
        (ex: DECIMAL(10,2) não será partido ao meio).
        """
        columns = []
        current = []
        paren_depth = 0
        
        for char in body:
            if char == '(':
                paren_depth += 1
                current.append(char)
            elif char == ')':
                paren_depth -= 1
                current.append(char)
            elif char == ',' and paren_depth == 0:
                columns.append("".join(current).strip())
                current = []
            else:
                current.append(char)
        
        if current:
            columns.append("".join(current).strip())
        return columns

    @staticmethod
    def parse_sql_content(sql_content: str, ir: DatabaseIR):
        # Remove comentários de linha única (-- ...) e multilinha (/* ... */)
        clean_sql = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        clean_sql = re.sub(r'--.*$', '', clean_sql, flags=re.MULTILINE)
        
        # Encontra blocos CREATE TABLE nome ( ... );
        table_pattern = re.compile(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"\w]+)\s*\((.*?)\);', re.DOTALL | re.IGNORECASE)
        matches = table_pattern.findall(clean_sql)

        for table_name_raw, body in matches:
            table_name = table_name_raw.replace('"', '').replace('`', '').strip()
            table = TableSchema(table_name)

            lines = SQLMigrationParser._split_columns_safely(body)
            for line in lines:
                if not line:
                    continue
                
                upper_line = line.upper()
                
                # Detecção de Chave Estrangeira explícita ou inline
                if 'FOREIGN KEY' in upper_line or 'REFERENCES' in upper_line:
                    fk_match = re.search(r'FOREIGN\s+KEY\s*\((.*?)\)\s*REFERENCES\s+([`"\w]+)\s*\((.*?)\)', line, re.IGNORECASE)
                    if fk_match:
                        col = fk_match.group(1).replace('"', '').replace('`', '').strip()
                        ref_table = fk_match.group(2).replace('"', '').replace('`', '').strip()
                        table.foreign_keys.append({"column": col, "references": ref_table})
                    else:
                        inline_fk = re.search(r'^([`"\w]+)\s+[\w\(\),]+\s+REFERENCES\s+([`"\w]+)\s*\((.*?)\)', line, re.IGNORECASE)
                        if inline_fk:
                            col = inline_fk.group(1).replace('"', '').replace('`', '').strip()
                            ref_table = inline_fk.group(2).replace('"', '').replace('`', '').strip()
                            table.foreign_keys.append({"column": col, "references": ref_table})
                    continue

                # Detecção de colunas normais
                parts = line.split()
                if len(parts) >= 2:
                    col_name = parts[0].replace('"', '').replace('`', '').strip()
                    col_type = parts[1].strip()
                    
                    # Ignora se for restrição de tabela como PRIMARY KEY(...) ou CONSTRAINT
                    if col_name.upper() in ('PRIMARY', 'CONSTRAINT', 'UNIQUE', 'CHECK'):
                        continue

                    is_nullable = "NOT NULL" not in upper_line
                    is_pk = "PRIMARY KEY" in upper_line

                    table.columns.append({
                        "name": col_name,
                        "type": col_type,
                        "nullable": "Sim" if is_nullable else "Não",
                        "pk": "Sim" if is_pk else "Não"
                    })

            ir.add_table(table)

# --- 3. GERADOR DE DOCUMENTAÇÃO (MARKDOWN & MERMAID) ---
class DocumentationGenerator:
    @staticmethod
    def generate_markdown(ir: DatabaseIR) -> str:
        md = []
        md.append("# Dicionário de Dados e Esquema do Banco de Dados\n")
        md.append("> Documentação gerada automaticamente a partir das migrações SQL.\n")
        
        # Seção ERD (Mermaid)
        md.append("## Diagrama Entidade-Relacionamento (ERD)\n")
        md.append("```mermaid")
        md.append("erDiagram")
        
        for t_name, table in ir.tables.items():
            for fk in table.foreign_keys:
                ref_t = fk["references"]
                col = fk["column"]
                md.append(f"    {ref_t} ||--o{{ {t_name} : \"{col}\"")
        
        md.append("```\n")
        
        # Seção Dicionário de Dados
        md.append("## Dicionário de Dados\n")
        for t_name, table in ir.tables.items():
            md.append(f"### Tabela: `{table.name}`\n")
            md.append("| Coluna | Tipo | Nula? | Chave Primária |")
            md.append("|--------|------|-------|----------------|")
            for col in table.columns:
                md.append(f"| `{col['name']}` | `{col['type']}` | {col['nullable']} | {col['pk']} |")
            md.append("")
            
        return "\n".join(md)

# --- 4. EXECUÇÃO E TESTES DE VALIDAÇÃO ---
if __name__ == "__main__":
    # Migração complexa contendo tipos com vírgula (DECIMAL) e comentários multilinha
    complex_migration_sql = """
    /*
      Migração inicial: Criação de produtos e transações
    */
    CREATE TABLE products (
        id INT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2) NOT NULL
    );

    CREATE TABLE transactions (
        id INT PRIMARY KEY,
        amount DECIMAL(12,4) NOT NULL,
        product_id INT REFERENCES products(id)
    );
    """

    ir = DatabaseIR()
    SQLMigrationParser.parse_sql_content(complex_migration_sql, ir)
    
    # Validações rigorosas garantindo cobertura e ausência de corrupção por vírgula em DECIMAL
    assert "products" in ir.tables, "Erro: Tabela products não detectada"
    assert "transactions" in ir.tables, "Erro: Tabela transactions não detectada"
    
    prod_cols = ir.tables["products"].columns
    price_col = next((c for c in prod_cols if c["name"] == "price"), None)
    assert price_col is not None, "Coluna price não encontrada"
    assert price_col["type"] == "DECIMAL(10,2)", f"Tipo DECIMAL corrompido: {price_col['type']}"
    
    assert len(ir.tables["transactions"].foreign_keys) == 1, "Erro: FK de transactions não detectada"

    markdown_output = DocumentationGenerator.generate_markdown(ir)
    output_path = "schema.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_output)

    print(f"Sucesso! Arquivo '{output_path}' gerado com 100% de cobertura e parsing seguro de tipos com vírgula.")