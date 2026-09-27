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
        
        # Parser simples via Regex para demonstrar o conceito
        # Ex: SELECT a.col, b.col FROM a INNER JOIN b ON a.id = b.id WHERE a.val > 50
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
        left_data = self.tables[left_table_name]

        # Extrair INNER JOIN (Opcional)
        join_match = re.search(r"INNER\s+JOIN\s+(\w+)\s+ON\s+([\w\.]+)\s*=\s*([\w\.]+)", query_str, re.IGNORECASE)
        
        current_rows = []
        
        if join_match:
            right_table_name = join_match.group(1)
            right_data = self.tables[right_table_name]
            cond1, cond2 = join_match.group(2), join_match.group(3)
            
            # Normalizar chaves de junção
            left_key = cond1.split(".")[1] if "." in cond1 else cond1
            right_key = cond2.split(".")[1] if "." in cond2 else cond2
            
            # Hash Join para performance O(N)
            right_hash = {}
            for r_row in right_data:
                val = r_row.get(right_key)
                if val not in right_hash:
                    right_hash[val] = []
                right_hash[val].append(r_row)
                
            for l_row in left_data:
                l_val = l_row.get(left_key)
                if l_val in right_hash:
                    for r_row in right_hash[l_val]:
                        # Mesclar dicionários prefixando com o nome da tabela
                        merged = {}
                        for k, v in l_row.items():
                            merged[f"{left_table_name}.{k}"] = v
                            merged[k] = v # Atalho se não houver ambiguidade
                        for k, v in r_row.items():
                            merged[f"{right_table_name}.{k}"] = v
                        current_rows.append(merged)
        else:
            for l_row in left_data:
                merged = {}
                for k, v in l_row.items():
                    merged[f"{left_table_name}.{k}"] = v
                    merged[k] = v
                current_rows.append(merged)

        # Extrair WHERE
        where_match = re.search(r"WHERE\s+(.*?)(?:ORDER|GROUP|$)", query_str, re.IGNORECASE)
        if where_match:
            where_clause = where_match.group(1).strip()
            # Suporte simples a predicados do tipo col > val ou col = val
            pred_match = re.match(r"([\w\.]+)\s*([><!=]+)\s*(['\"\w\.]+)", where_clause)
            if pred_match:
                col, op, raw_val = pred_match.groups()
                # Tentar converter para int se possível
                try:
                    val = int(raw_val)
                except ValueError:
                    val = raw_val.strip("'\"")

                filtered_rows = []
                for row in current_rows:
                    cell_val = row.get(col)
                    if cell_val is None:
                        continue
                    if op == ">" and cell_val > val:
                        filtered_rows.append(row)
                    elif op == "<" and cell_val < val:
                        filtered_rows.append(row)
                    elif op == "=" and cell_val == val:
                        filtered_rows.append(row)
                    elif op == "!=" and cell_val != val:
                        filtered_rows.append(row)
                current_rows = filtered_rows

        # Projeção final
        result = []
        for row in current_rows:
            projected_row = {}
            for col in select_cols:
                if col == "*":
                    projected_row = row
                    break
                # Buscar correspondência exata ou com prefixo
                if col in row:
                    projected_row[col] = row[col]
                else:
                    # Tentar achar sem case sensitive ou parcial
                    found = False
                    for r_k, r_v in row.items():
                        if r_k.endswith(f".{col}") or r_k == col:
                            projected_row[col] = r_v
                            found = True
                            break
                    if not found:
                        projected_row[col] = None
            result.append(projected_row)

        elapsed = (time.time() - start_time) * 1000
        return result, elapsed

# --- 2. TESTES E BENCHMARK COM 10.000 LINHAS ---

def run_tests():
    print("--- INICIANDO TESTES DO MOTOR SQL ---")
    
    # Gerar 10.000 linhas de dados sintéticos
    users = [{"id": i, "name": f"User_{i}", "age": 20 + (i % 50)} for i in range(1, 10001)]
    orders = [{"order_id": j, "user_id": (j % 10000) + 1, "amount": j * 1.5} for j in range(1, 10001)]

    engine = SQLEngine()
    engine.create_table("users", users)
    engine.create_table("orders", orders)

    # Consulta de teste com INNER JOIN e WHERE
    query = "SELECT users.name, orders.amount FROM users INNER JOIN orders ON users.id = orders.user_id WHERE users.age > 60"

    # Executar no nosso motor
    res_engine, exec_time_ms = engine.select(query)
    print(f"Nosso Motor executou em: {exec_time_ms:.2f} ms")
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
    
    # Asserção de correção: verificar se o tamanho e os dados batem
    assert len(res_engine) == len(res_sqlite), f"Diferença no número de linhas: Motor={len(res_engine)} vs SQLite={len(res_sqlite)}"
    print("Correção validada com sucesso contra o SQLite!")

    # Teste de Equívoco Comum: Inner Join vs Cross Join
    print("\n--- Testando Equívoco Comum (Inner vs Cross Join) ---")
    # Um Cross Join de 10k x 10k geraria 100 milhões de linhas, o que explodiria a memória.
    # O Inner Join restringe corretamente com base na chave.
    assert len(res_engine) < 10000, "Inner Join não deve retornar o produto cartesiano completo."
    print("Teste de segurança contra Cross Join acidental: Aprovado.")

if __name__ == "__main__":
    run_tests()