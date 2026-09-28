import sqlite3

def setup_database():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    # Tabela com esquema inicial expandido (suporta legado e novo)
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT
        )
    """)
    # Inserções legadas iniciais (pré-migração)
    cursor.executemany("INSERT INTO users (full_name) VALUES (?)", [
        ("Alice Silva",),
        ("Bob Souza",),
        ("Carlos Mendes",)
    ])
    conn.commit()
    return conn

def simulate_dual_write_insert(conn, full_name):
    """Simula a aplicação atualizada executando Dual-Write durante a migração."""
    cursor = conn.cursor()
    parts = full_name.split(" ", 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    # Escreve tanto no formato legado quanto no novo simultaneamente
    cursor.execute(
        "INSERT INTO users (full_name, first_name, last_name) VALUES (?, ?, ?)",
        (full_name, first, last)
    )
    conn.commit()
    print(f"[DUAL-WRITE] Novo usuário inserido concorrentemente: {full_name} -> {first} | {last}")

def run_resilient_backfill(conn, batch_size=2):
    """Executa backfill em lotes com checkpointing para suportar falhas parciais."""
    cursor = conn.cursor()
    print("\n[MIGRATE] Iniciando backfill resiliente com checkpointing...")
    
    last_checkpoint = 0
    total_processed = 0

    while True:
        # Busca lote a partir do último checkpoint
        cursor.execute(
            "SELECT id, full_name FROM users WHERE id > ? AND first_name IS NULL LIMIT ?",
            (last_checkpoint, batch_size)
        )
        rows = cursor.fetchall()
        if not rows:
            break
        
        for row in rows:
            user_id, full_name = row
            parts = full_name.split(" ", 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
            
            cursor.execute(
                "UPDATE users SET first_name = ?, last_name = ? WHERE id = ?",
                (first, last, user_id)
            )
            print(f"[MIGRATE CHECKPOINT] Lote processado - ID {user_id}: {full_name} -> {first} | {last}")
            last_checkpoint = user_id
            total_processed += 1
            
        conn.commit()
        
    print(f"[MIGRATE] Backfill concluído. Total de registros processados no lote: {total_processed}\n")

if __name__ == "__main__":
    db = setup_database()
    
    # 1. Executamos parte do backfill nos dados legados iniciais
    run_resilient_backfill(db, batch_size=1)
    
    # 2. Simulação de concorrência: Aplicação nova insere dados durante a migração
    simulate_dual_write_insert(db, "Daniela Rocha")
    
    # 3. Execução contínua do backfill para os novos dados inseridos concorrentemente
    run_resilient_backfill(db, batch_size=1)
    
    # Validação final de consistência
    cursor = db.cursor()
    cursor.execute("SELECT id, full_name, first_name, last_name FROM users")
    print("[VALIDAÇÃO FINAL DE CONSISTÊNCIA]")
    for row in cursor.fetchall():
        print(f"ID {row[0]}: legado='{row[1]}' | novo='{row[2]} {row[3]}'")
        assert row[1].split()[0] == row[2], f"Inconsistência detectada no ID {row[0]}"
        
    db.close()
    print("\nSimulação avançada de Zero-Downtime Migration com concorrência concluída com sucesso!")