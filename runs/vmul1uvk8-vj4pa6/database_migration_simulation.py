import sqlite3

def setup_database():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL
        )
    """)
    cursor.executemany("INSERT INTO users (full_name) VALUES (?)", [
        ("Alice Silva",),
        ("Bob Souza",),
        ("Carlos Mendes",)
    ])
    conn.commit()
    return conn

def test_expand_phase(conn):
    """Fase 1: Expand - Adicionar novas colunas sem remover a antiga."""
    cursor = conn.cursor()
    print("[EXPAND] Adicionando novas colunas first_name e last_name...")
    cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
    conn.commit()
    print("[EXPAND] Sucesso: Estruturas novas adicionadas, dados legados preservados.\n")

def test_migrate_phase(conn):
    """Fase 2: Migrate - Backfill em lotes (chunks) para sincronizar dados."""
    cursor = conn.cursor()
    print("[MIGRATE] Iniciando backfill em lotes (chunks)...")
    
    cursor.execute("SELECT id, full_name FROM users WHERE first_name IS NULL")
    rows = cursor.fetchall()
    
    for row in rows:
        user_id, full_name = row
        parts = full_name.split(" ", 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ""
        
        cursor.execute(
            "UPDATE users SET first_name = ?, last_name = ? WHERE id = ?",
            (first, last, user_id)
        )
        print(f"[MIGRATE] Processado ID {user_id}: {full_name} -> {first} | {last}")
    
    conn.commit()
    print("[MIGRATE] Sucesso: Todos os dados migrados para o novo formato.\n")

def test_contract_phase(conn):
    """Fase 3: Contract - Remover a estrutura antiga após desativação do código legado."""
    cursor = conn.cursor()
    print("[CONTRACT] Removendo coluna antiga full_name...")
    
    # SQLite não suporta DROP COLUMN diretamente em versões antigas, mas suporta na 3.35.0+
    # Para garantir compatibilidade universal em simulações, recriamos a tabela mantendo apenas as novas colunas
    cursor.execute("CREATE TABLE users_new (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, last_name TEXT)")
    cursor.execute("INSERT INTO users_new (id, first_name, last_name) SELECT id, first_name, last_name FROM users")
    cursor.execute("DROP TABLE users")
    cursor.execute("ALTER TABLE users_new RENAME TO users")
    conn.commit()
    print("[CONTRACT] Sucesso: Coluna legada removida com segurança. Esquema evoluído sem downtime.\n")

def test_common_pitfall_direct_rename():
    """Demonstração isolada do equívoco comum: alteração direta sem transição."""
    print("[EQUÍVOCO COMUM] Simulando alteração estrutural direta em produção...")
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, full_name TEXT)")
    cursor.execute("INSERT INTO users (full_name) VALUES ('Alice Silva')")
    
    try:
        # Tentativa abrupta de remover a coluna que a aplicação legada ainda usa
        cursor.execute("ALTER TABLE users DROP COLUMN full_name")
        cursor.execute("SELECT full_name FROM users")
    except Exception as e:
        print(f"[FALHA CAPTURADA] A aplicação legada quebrou com erro: {e}")
        print("[JUSTIFICATIVA] Alterações diretas em produção quebram versões de código em execução simultânea.\n")
    finally:
        conn.close()

if __name__ == "__main__":
    # 1. Demonstração do equívoco comum (isolada)
    test_common_pitfall_direct_rename()
    
    # 2. Execução correta do fluxo Expand-Contract
    db = setup_database()
    test_expand_phase(db)
    test_migrate_phase(db)
    test_contract_phase(db)
    db.close()
    
    print("Simulação de Zero-Downtime Migration concluída com sucesso e sem erros.")