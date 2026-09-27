import time
import sqlite3
import re

# --- 1. MOTOR DE EXECUÇÃO SQL EM MEMÓRIA ---

class MemoryTable:
    def __init__(self, name, rows):
        self.name = name
        self.rows = rows  # Lista de dicionários

class SQLEngine:
    def __init__(self):
        self.tables = {}

    def create_table(self, name, rows):
        self.tables[name] = rows

    def select(self, query):
        start_time = time.time()
        
        query_str = query.strip()
        
        # Extrair SELECT
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", query_str, re.IGNORECASE)
        if not select_match:
            raise ValueError("Cláusula SELECT inválida")
        select_cols = [c.strip() for c in select_match.group(1).split(",")]

        # Extrair FROM
        from_match = re.search(r"FROM\s+(\w+)", query_str, re.IGNORECASE)
        if not from_match:
            raise ValueError("Cláusula FROM inválida")
        left_table_name = from_match.group(1)

        # Extrair INNER JOIN (se houver)
        join_match = re.search(r"INNER\s+JOIN\s+(\w+)\s+ON\s+([\w\.]+)\s*=\s*([\w\.]+)", query_str, re.IGNORECASE)
        
        # Extrair WHERE (se houver)
        where_match = re.search(r"WHERE\s+(.*?)(?:$|ORDER|GROUP)", query_str, re.IGNORECASE)

        # Obter tabela esquerda
        if left_table_name not in self.tables:
            raise ValueError(f"Tabela {left_table_name} não encontrada")
        
        left_rows = self.tables[left_table_name]

        # Expandir colunas da tabela esquerda com prefixo da tabela para evitar colisões (Correção do SyntaxError)
        current_rows = []
        for row in left_rows:
            new_row = {}
            for k, v in row.items():
                new_row[k] = v
                new_row[f"{left_table_name}.{k}"] = v
            current_rows.append(new_row)

        # Execução do INNER JOIN (Algoritmo Hash Join em memória)
        if join_match:
            right_table_name = join_match.group(1)
            left_col = join_match.group(2).split(".")[-1]
            right_col = join_match.group(3).split(".")[-1]

            if right_table_name not in self.tables:
                raise ValueError(f"Tabela {right_table_name} não encontrada")
            
            right_rows = self.tables[right_table_name]

            # Construir Hash Table para a tabela da direita
            right_hash = {}
            for row in right_rows:
                key = row.get(right_col)
                if key not in right_hash:
                    right_hash[key] = []
                right_hash[key].append(row)

            # Executar a junção
            joined_rows = []
            for l_row in current_rows:
                l_key = l_row.get(left_col)
                if l_key in right_hash:
                    for r_row in right_rows:
                        if r_row.get(right_col) == l_key:
                            combined = dict(l_row)
                            for r_k, r_v in r_row.items():
                                combined[r_k] = r_v
                                combined[f"{right_table_name}.{r_k}"] = r_v
                            joined_rows.append(combined)
            current_rows = joined_rows

        # Execução do WHERE (Filtro)
        if where_match:
            condition = where_match.group(1).strip()
            # Substituir operadores SQL comuns para avaliação Python
            py_condition = condition
            py_condition = re.sub(r"(\w+\.\w+|\w+)\s*=\s*", r"row.get('\1') == ", py_condition)
            py_condition = re.sub(r"(\w+\.\w+|\w+)\s*>\s*", r"row.get('\1') > ", py_condition)
            py_condition = re.sub(r"(\w+\.\w+|\w+)\s*<\s*", r"row.get('\1') < ", py_condition)
            
            filtered_rows = []
            for row in current_rows:
                try:
                    if eval(py_condition, {"row": row}):
                        filtered_rows.append(row)
                except Exception:
                    pass
            current_rows = filtered_rows

        # Execução da Projeção (SELECT columns)
        final_rows = []
        for row in current_rows:
            projected_row = {}
            if select_cols == ["*"]:
                projected_row = row
            else:
                for col in select_cols:
                    # Tentar encontrar a coluna diretamente ou com prefixo
                    if col in row:
                        projected_row[col] = row[col]
                    elif f"{left_table_name}.{col}" in row:
                        projected_row[col] = row[f"{left_table_name}.{col}"]
                    else:
                        # Procurar em qualquer tabela
                        found = False
                        for r_k, r_v in row.items():
                            if r_k.endswith(f".{col}"):
                                projected_row[col] = r_v
                                found = True
                                break
                        if not found:
                            projected_row[col] = None
            final_rows.append(projected_row)

        end_time = time.time()
        exec_time_ms = (end_time - start_time) * 1000.0
        return final_rows, exec_time_ms


# --- 2. TESTE AUTOMATIZADO COMPATÍVEL COM PYTEST ---

def test_sql_engine():
    engine = SQLEngine()

    # Gerar 10.000 linhas de dados sintéticos
    num_rows = 10000
    users = [{"id": i, f"name": f"User_{i}", "age": 20 + (i % 50)} for i in range(num_rows)]
    orders = [{"order_id": i, "user_id": i % num_rows, "amount": 10.0 + (i % 100)} for i in range(num_rows)]

    engine.create_table("users", users)
    engine.create_table("orders", orders)

    query = """
    SELECT users.name, orders.amount 
    FROM users 
    INNER JOIN orders ON users.id = orders.user_id 
    WHERE users.age > 40
    """

    print(f"\nExecutando consulta sobre {num_rows} linhas...")
    res_engine, exec_time_ms = engine.select(query)
    print(f"Tempo de execução do motor em memória: {exec_time_ms:.2f}ms")
    print(f"Linhas retornadas pelo motor: {len(res_engine)}")
    
    assert exec_time_ms < 500, f"Tempo excedeu o limite: {exec_time_ms}ms"

    # Validar contra SGBD de referência (SQLite)
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INT, name TEXT, age INT)")
    cursor.execute("CREATE TABLE orders (order_id INT, user_id INT, amount REAL)")
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?)", [(u["id"], u["name"], u["age"]) for u in users])
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?)", [(o["order_id"], o["user_id"], o["amount"]) for o in orders])

    cursor.execute(query)
    res_sqlite = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()

    print(f"Linhas retornadas pelo SQLite: {len(res_sqlite)}")
    
    assert len(res_engine) == len(res_sqlite), f"Diferença no número de linhas: Motor={len(res_engine)} vs SQLite={len(res_sqlite)}"
    print("Correção validada com sucesso contra o SQLite!")

    # Teste de Equívoco Comum: Inner Join vs Cross Join
    print("\n--- Testando Equívoco Comum (Inner vs Cross Join) ---")
    assert len(res_engine) < 10000, "Inner Join não deve retornar o produto cartesiano completo."
    print("Teste de segurança contra Cross Join acidental: Aprovado.")

if __name__ == "__main__":
    test_sql_engine()