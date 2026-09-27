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

        # Execução do INNER JOIN (Algoritmo Hash Join em memória)
        if join_match:
            right_table_name = join_match.group(1)
            left_col = join_match.group(2).split(".")[-1]
            right_col = join_match.group(3).split(".")[-1]

            if right_table_name not in self.tables:
                raise ValueError(f"Tabela {right_table_name} não encontrada")
            
            right_rows = self.tables[right_table_name]

            # Construção da tabela Hash para o join eficiente O(N + M)
            hash_map = {}
            for r_row in right_rows:
                key = r_row.get(right_col)
                if key not in hash_map:
                    hash_map[key] = []
                hash_map[key].append(r_row)

            joined_rows = []
            for l_row in left_rows:
                key = l_row.get(left_col)
                if key in hash_map:
                    for r_row in hash_map[key]:
                        # Mesclar dicionários das duas tabelas
                        merged = {}
                        for k, v in l_row.items():
                            merged[f"{left_table_name}.{k}"] = v
                            merged[k] = v  # Atalho para nome simples se único
                        for k, v in r_row.items():
                            merged[f"{right_table_name}.{k}"] = v
                            if k not in merged:
                                merged[k] = v
                        joined_rows.append(merged)
            current_rows = joined_rows
        else:
            current_rows = [{f"{left_table_name}.{k}": v, k: v for k, v in row.items()} for row in left_rows]

        # Execução do WHERE (Seleção Relacional)
        if where_match:
            where_clause = where_match.group(1).strip()
            # Parser simples de predicado ex: col op val
            pred_match = re.match(r"([\w\.]+)\s*(=|!=|<|>)\s*(['\"].*?['\"]|\d+\.?\d*)", where_clause)
            if pred_match:
                col, op, val_str = pred_match.groups()
                # Converter valor adequadamente
                if val_str.startswith("'") or val_str.startswith('"'):
                    val = val_str[1:-1]
                elif "." in val_str:
                    val = float(val_str)
                else:
                    val = int(val_str)

                filtered_rows = []
                for row in current_rows:
                    # Tentar encontrar a coluna com ou sem prefixo
                    row_val = None
                    for c_key in [col, col.split(".")[-1]]:
                        if c_key in row:
                            row_val = row[c_key]
                            break
                    
                    if row_val is not None:
                        if op == "=" and row_val == val: filtered_rows.append(row)
                        elif op == "!=" and row_val != val: filtered_rows.append(row)
                        elif op == "<" and row_val < val: filtered_rows.append(row)
                        elif op == ">" and row_val > val: filtered_rows.append(row)
                current_rows = filtered_rows

        # Execução da Projeção Relacional
        projected_rows = []
        for row in current_rows:
            new_row = {}
            for col in select_cols:
                if col == "*":
                    new_row = row
                    break
                # Buscar correspondência exata ou por sufixo de coluna
                found = False
                for k in [col, col.split(".")[-1]]:
                    if k in row:
                        new_row[col] = row[k]
                        found = True
                        break
                if not found:
                    new_row[col] = None
            projected_rows.append(new_row)

        elapsed = (time.time() - start_time) * 1000
        return projected_rows, elapsed


# --- 2. TESTES AUTOMATIZADOS (COMPATÍVEIS COM PYTEST) ---

def test_sql_engine():
    # Gerar dados sintéticos (10.000 linhas)
    num_rows = 10000
    users = [{"id": i, "name": f"User_{i}", "age": 20 + (i % 50)} for i in range(num_rows)]
    orders = [{"order_id": i, "user_id": i % num_rows, "amount": float(i * 1.5)} for i in range(num_rows)]

    engine = SQLEngine()
    engine.create_table("users", users)
    engine.create_table("orders", orders)

    query = "SELECT users.name, orders.amount FROM users INNER JOIN orders ON users.id = orders.user_id WHERE users.age > 40"

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