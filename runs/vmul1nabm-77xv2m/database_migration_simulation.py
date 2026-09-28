import sqlite3
import time

def setup_database():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL
        )
    """)
    # Inserir dados legados
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

    # Simulação de Código Novo (Dual-write / Fallback)
    # Escrevemos em ambos para garantir compatibilidade com códigos antigos e novos
    cursor.execute("UPDATE users SET first_name = 'Dummy', last_name = 'User' WHERE first_name IS NULL")
    conn.commit()
    print("[EXPAND] Sucesso: Estruturas novas adicionadas, dados legados preservados.\n")

def test_migrate_phase(conn):
    """Fase 2: Migrate - Backfill em lote (chunked) dos dados antigos para os novos."""
    cursor = conn.cursor()
    print("[MIGRATE] Iniciando backfill em lotes (chunks)...")
    
    # Processamento em lote para evitar locks prolongados
    batch_size = 2
    while True:
        cursor.execute("""
            SELECT id, full_name FROM users 
            WHERE first_name = 'Dummy' OR first_name IS NULL 
            LIMIT ?
        """, (batch_size,))
        rows = cursor.fetchall()
        
        if not rows:
            break
            
        for row in rows:
            user_id, full_name = row
            parts = full_name.split(" ", 1)
            fname = parts[0]
            lname = parts[1] if len(parts) > 1 else ""
            
            cursor.execute("""
                UPDATE users SET first_name = ?, last_name = ? WHERE id = ?
            """, (fname, lname, user_id))
            print(f"[MIGRATE] Processado ID {user_id}: {full_name} -> {fname} | {lname}")
            
        conn.commit()
        time.sleep(0.01) # Simula espaçamento para aliviar I/O
    
    print("[MIGRATE] Sucesso: Todos os dados migrados para o novo formato.\n")

def test_contract_phase(conn):
    """Fase 3: Contract - Remoção segura da estrutura antiga."""
    cursor = conn.cursor()
    print("[CONTRACT] Removendo coluna antiga full_name...")
    
    # Nota: SQLite não suporta DROP COLUMN diretamente em versões antigas, 
    # mas em SGBDs modernos (PostgreSQL/MySQL) faz-se DROP COLUMN. 
    # Aqui simulamos a restrição criando uma nova tabela limpa (padrão físico de contract).
    cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT INTO users_new (id, first_name, last_name) SELECT id, first_name, last_name FROM users")
    cursor.execute("DROP TABLE users")
    cursor.execute("ALTER TABLE users_new RENAME TO users")
    conn.commit()
    
    cursor.execute("SELECT * FROM users")
    print(f"[CONTRACT] Tabela final após contract: {cursor.fetchall()}")
    print("[CONTRACT] Sucesso: Estrutura antiga removida sem impacto.\n")

def test_common_pitfall_direct_rename(conn):
    """Demonstração de Equívoco Comum: Renomeação direta sem Expand-Contract."""
    print("[EQUÍVOCO COMUM] Tentando renomear coluna diretamente em produção...")
    cursor = conn.cursor()
    try:
        # Simulando que a aplicação antiga ainda tenta acessar 'full_name' após uma alteração brusca
        cursor.execute("ALTER TABLE users DROP COLUMN first_name")
        cursor.execute("SELECT full_name FROM users")
    except Exception as e:
        print(f"[FALHA CAPTURADA] A aplicação legada quebrou com erro: {e}")
        print("[JUSTIFICATIVA] Alterações estruturais diretas sem o padrão Expand-Contract causam quebra de contrato com versões de código em voo (in-flight deployment).\n")

if __name__ == "__main__":
    db = setup_database()
    test_expand_phase(db)
    test_migrate_phase(db)
    test_common_pitfall_direct_rename(db) # Demonstra o erro conceitual
    test_contract_phase(db)
    db.close()
    print("Simulação de Zero-Downtime Migration concluída com sucesso.")