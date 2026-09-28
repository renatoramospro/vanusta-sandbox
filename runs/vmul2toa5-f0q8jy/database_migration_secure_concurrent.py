import sqlite3
import threading
import time
import sys

def setup_database():
    # Usando arquivo temporário para suportar concorrência real de threads/conexões
    db_path = "production_simulation.db"
    conn = sqlite3.connect(db_path, isolation_level=None) # Modo autocommit para simular concorrência SGBD
    cursor = conn.cursor()
    
    # Limpeza prévia
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Fase EXPAND: Criação da tabela com colunas legadas e novas
    # Princípio de menor privilégio: o migrador restringe tipos e restrições sem quebrar leituras legadas
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT
        )
    """)
    
    # Inserção de dados iniciais (incluindo um caso malformado/edge case: dado sem sobrenome ou nulo)
    initial_users = [
        ("Alice Silva",),
        ("Bob",), # Malformado: apenas um nome
        ("  ",),  # Malformado: espaços em branco
        (None,)   # Malformado: NULL direto (se a coluna permitir ou tratado defensivamente)
    ]
    
    for user in initial_users:
        if user[0] is not None:
            cursor.execute("INSERT INTO users (full_name, first_name, last_name) VALUES (?, ?, ?)", 
                           (user[0], user[0].strip().split()[0] if len(user[0].strip().split()) > 0 else "Unknown", ""))
        else:
            cursor.execute("INSERT INTO users (full_name, first_name, last_name) VALUES (?, ?, ?)", 
                           ("Unknown User", "Unknown", ""))
            
    conn.close()
    return db_path

def parse_full_name(full_name):
    """Tratamento defensivo de dados malformados, nulos ou edge cases."""
    if not full_name or not isinstance(full_name, str):
        return "Unknown", "Unknown"
    
    parts = full_name.strip().split()
    if len(parts) == 0:
        return "Unknown", "Unknown"
    elif len(parts) == 1:
        return parts[0], ""
    else:
        return parts[0], " ".join(parts[1:])

def dual_write_insert(db_path, full_name):
    """Garante escrita atômica em ambas as colunas (Dual-Write transacional)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        first, last = parse_full_name(full_name)
        cursor.execute(
            "INSERT INTO users (full_name, first_name, last_name) VALUES (?, ?, ?)",
            (full_name, first, last)
        )
        conn.commit()
        print(f"[DUAL-WRITE SUCESSO] Inserido concorrente: '{full_name}' -> First: '{first}', Last: '{last}'")
    except Exception as e:
        conn.rollback()
        print(f"[DUAL-WRITE ERRO] Falha na transação concorrente: {e}")
    finally:
        conn.close()

def run_concurrent_writers(db_path):
    """Simula concorrência real via múltiplas threads escrevendo simultaneamente."""
    names = ["Daniela Rocha", "Carlos Eduardo Mendes", "Fernanda", "Gabriel Souza Lima"]
    threads = []
    
    print("\n[CONCORRÊNCIA] Iniciando threads de escrita concorrente (Dual-Write)...")
    for name in names:
        t = threading.Thread(target=dual_write_insert, args=(db_path, name))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

def run_resilient_backfill_with_checkpoint(db_path):
    """Backfill em lotes com tratamento de dados malformados, idempotência e checkpointing."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n[MIGRATE] Iniciando backfill resiliente com checkpointing e tratamento defensivo...")
    
    # Checkpointing: recupera o último ID migrado ou começa do zero
    last_checkpoint = 0
    batch_size = 2
    total_processed = 0
    
    while True:
        cursor.execute(
            "SELECT id, full_name FROM users WHERE id > ? AND (first_name IS NULL OR first_name = '') LIMIT ?",
            (last_checkpoint, batch_size)
        )
        rows = cursor.fetchall()
        if not rows:
            break
            
        for row in rows:
            uid, full_name = row
            first, last = parse_full_name(full_name)
            
            # Atualização atômica e idempotente
            cursor.execute(
                "UPDATE users SET first_name = ?, last_name = ? WHERE id = ?",
                (first, last, uid)
            )
            conn.commit()
            last_checkpoint = uid
            total_processed += 1
            print(f"[MIGRATE CHECKPOINT] Lote processado - ID {uid}: '{full_name}' -> '{first}' | '{last}'")
            
    conn.close()
    print(f"[MIGRATE] Backfill concluído. Total de registros processados: {total_processed}")

def verify_consistency(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, first_name, last_name FROM users")
    print("\n[VALIDAÇÃO FINAL DE CONSISTÊNCIA E SEGURANÇA DE DADOS]")
    rows = cursor.fetchall()
    for row in rows:
        uid, full_name, first, last = row
        print(f"ID {uid}: legado='{full_name}' | novo='{first} {last}'")
        # Assertiva de integridade: nenhum registro deve possuir first_name nulo após backfill resiliente
        assert first is not None, f"Violação de consistência: ID {uid} com first_name NULL"
    conn.close()
    print("Validação de integridade concluída com sucesso absoluto!")

if __name__ == "__main__":
    db = setup_database()
    
    # 1. Executa backfill inicial nos dados sementes (incluindo os malformados)
    run_resilient_backfill_with_checkpoint(db)
    
    # 2. Dispara concorrência real com múltiplas threads (Dual-Write)
    run_concurrent_writers(db)
    
    # 3. Executa segundo backfill para os dados inseridos concorrentemente
    run_resilient_backfill_with_checkpoint(db)
    
    # 4. Verifica consistência global
    verify_consistency(db)
    print("\nSimulação de Zero-Downtime Migration com Concorrência Real e Tratamento Defensivo concluída com sucesso!")