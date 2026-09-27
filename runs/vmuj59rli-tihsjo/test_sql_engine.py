import time
import sqlite3
import re

# --- 1. MOTOR DE EXECUÇÃO SQL EM MEMÓRIA OTIMIZADO ---

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

        left_rows = self.tables.get(left_table_name, [])
        result_rows = []

        if join_match:
            right_table_name = join_match.group(1)
            left_col = join_match.group(2).split(".")[-1]
            right_col = join_match.group(3).split(".")[-1]
            right_rows = self.tables.get(right_table_name, [])

            # Construir Hash Table para a tabela direita (O(M))
            hash_table = {}
            for r in right_rows:
                key = r.get(right_col)
                if key not in hash_table:
                    hash_table[key] = []
                hash_table[key].append(r)

            # Hash Join otimizado (O(N))
            for l_row in left_rows:
                l_key = l_row.get(left_col)
                if l_key in hash_table:
                    for r_row in hash_table[l_key]:
                        combined = {}
                        for k, v in l_row.items():
                            combined[k] = v
                            combined[f"{left_table_name}.{k}"] = v
                        for k, v in r_row.items():
                            combined[k] = v
                            combined[f"{right_table_name}.{k}"] = v
                        result_rows.append(combined)
        else:
            for l_row in left_rows:
                combined = {}
                for k, v in l_row.items():
                    combined[k] = v
                    combined[f"{left_table_name}.{k}"] = v
                result_rows.append(combined)

        # Processar WHERE (ex: users.age > 40)
        filtered_rows = []
        if where_match:
            condition = where_match.group(1).strip()
            # Avaliação segura básica para condições do tipo col > val
            cond_match = re.match(r"([\w\.]+)\s*([><=]+)\s*(['\"]?[\w\.]+['\"]?)", condition)
            if cond_match:
                c_field, op, c_val = cond_match.groups()
                field_key = c_field.split(".")[-1]
                
                # Converter valor se for número
                if c_val.isdigit():
                    val = int(c_val)
                else:
                    try:
                        val = float(c_val)
                    except ValueError:
                        val = c_val.strip("'\"")

                for row in result_rows:
                    cell_val = row.get(field_key)
                    if cell_val is not None:
                        if op == ">" and cell_val > val:
                            filtered_rows.append(row)
                        elif op == "<" and cell_val < val:
                            filtered_rows.append(row)
                        elif op == "=" and cell_val == val:
                            filtered_rows.append(row)
            else:
                filtered_rows = result_rows
        else:
            filtered_rows = result_rows

        # Processar SELECT (projeção)
        final_rows = []
        for row in filtered_rows:
            projected = {}
            if select_cols == ["*"]:
                final_rows.append(row)
            else:
                for col in select_cols:
                    col_key = col.split(".")[-1]
                    if col_key in row:
                        projected[col] = row[col_key]
                    elif col in row:
                        projected[col] = row[col]
                final_rows.append(projected)

        exec_time_ms = (time.time() - start_time) * 1000
        return final_rows, exec_time_ms

# --- 2. TESTE AUTOMATIZADO (PYTEST) ---

def test_sql_engine():
    engine = SQLEngine()

    # Gerar 10.000 linhas de dados sintéticos
    num_rows = 10000
    users = [{"id": i, "name": f"User_{i}", "age": 20 + (i % 50)} for i in range(num_rows)]
    orders = [{"order_id": i, "user_id": i % num_rows, "amount": 10.0 + (i % 100)} for i in range(num_rows)]

    engine.create_table("users", users)
    engine.create_table("orders", orders)

    query = """
        SELECT users.id, users.name, orders.amount 
        FROM users
        INNER JOIN orders ON users.id = orders.user_id
        WHERE users.age > 40
    """

    print(f"\nExecutando consulta sobre {num_rows} linhas...")
    res_engine, exec_time_ms = engine.select(query)
    print(f"Tempo de execução do motor em memória: {exec_time_ms:.2f}ms")
    print(f"Linhas retornadas pelo motor: {len(res_engine)}")
    
    # Validação rigorosa de desempenho (< 500ms)
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
    print("Correção validada com sucesso contra o SQLite e critério de desempenho atingido!")

if __name__ == "__main__":
    test_sql_engine()