import sqlite3
import hashlib
import os
import glob
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Migration:
    version: int
    name: str
    filepath: str
    up_sql: str
    down_sql: str
    checksum: str

class MigrationEngine:
    def __init__(self, db_path: str, migrations_dir: str):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self._init_history_table()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_history_table(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def _compute_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def discover_migrations(self) -> List[Migration]:
        pattern = os.path.join(self.migrations_dir, "V*__*.sql")
        files = glob.glob(pattern)
        migrations = []

        for filepath in files:
            filename = os.path.basename(filepath)
            try:
                prefix, name_ext = filename.split("__", 1)
                version_str = prefix[1:] # Remove o 'V'
                version = int(version_str)
                name = name_ext.rsplit(".", 1)[0]
            except (ValueError, IndexError):
                raise ValueError(f"Nome de arquivo de migração inválido: {filename}. Esperado: V{{version}}__{{name}}.sql")

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            up_sql, down_sql = self._parse_migration_content(content)
            checksum = self._compute_checksum(content)

            migrations.append(Migration(
                version=version,
                name=name,
                filepath=filepath,
                up_sql=up_sql,
                down_sql=down_sql,
                checksum=checksum
            ))

        # Ordenação numérica estrita por versão (evita ordem alfabética incorreta)
        migrations.sort(key=lambda m: m.version)
        return migrations

    def _parse_migration_content(self, content: str) -> Tuple[str, str]:
        parts = content.split("-- DOWN")
        up_part = parts[0].replace("-- UP", "").strip()
        down_part = parts[1].strip() if len(parts) > 1 else ""
        return up_part, down_part

    def get_applied_migrations(self) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version, checksum FROM schema_migrations;")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def migrate(self):
        migrations = self.discover_migrations()
        applied = self.get_applied_migrations()

        conn = self._get_connection()
        try:
            for mig in migrations:
                if mig.version in applied:
                    # Valida integridade (checksum)
                    if applied[mig.version] != mig.checksum:
                        raise ValueError(f"Violação de integridade: Checksum da migração V{mig.version} ({mig.name}) foi alterado após aplicação!")
                    continue

                print(f"Aplicando migração V{mig.version}: {mig.name}...")
                
                # Executa o up_sql dentro de uma transação com salvamento atômico
                try:
                    conn.execute("BEGIN TRANSACTION;")
                    conn.executescript(mig.up_sql)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, name, checksum) VALUES (?, ?, ?);",
                        (mig.version, mig.name, mig.checksum)
                    )
                    conn.commit()
                    print(f"Migração V{mig.version} aplicada com sucesso.")
                except Exception as e:
                    conn.rollback()
                    print(f"ERRO ao aplicar migração V{mig.version}. Executando ROLLBACK.")
                    raise e
        finally:
            conn.close()

if __name__ == "__main__":
    import shutil

    # Setup de diretório temporário para testes
    test_dir = "./test_migrations"
    os.makedirs(test_dir, exist_ok=True)
    db_file = "test_database.db"

    if os.path.exists(db_file):
        os.remove(db_file)

    # Migração 1: Sucesso
    with open(os.path.join(test_dir, "V1__create_users.sql"), "w") as f:
        f.write("""
        -- UP
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        );
        -- DOWN
        DROP TABLE users;
        """)

    # Migração 2: Erro intencional para testar rollback
    with open(os.path.join(test_dir, "V2__broken_migration.sql"), "w") as f:
        f.write("""
        -- UP
        CREATE TABLE posts (id INTEGER PRIMARY KEY);
        -- Comando SQL propositalmente inválido para causar falha
        SYNTAX ERROR COMAND;
        -- DOWN
        DROP TABLE posts;
        """)

    engine = MigrationEngine(db_path=db_file, migrations_dir=test_dir)

    print("--- Executando Migrações ---")
    try:
        engine.migrate()
    except Exception:
        print("Migração interrompida por erro controlado.")

    # Verificando estado do banco
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # A tabela users deve existir (V1 aplicada com sucesso)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    print(f"Tabela 'users' existe? {cursor.fetchone() is not None}")

    # A tabela posts NÃO deve existir devido ao ROLLBACK da V2
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts';")
    print(f"Tabela 'posts' existe (deve ser False)? {cursor.fetchone() is not None}")

    # Histórico deve conter apenas a versão 1
    cursor.execute("SELECT version, name FROM schema_migrations;")
    print(f"Histórico de migrações aplicadas: {cursor.fetchall()}")

    conn.close()

    # Limpeza final
    shutil.rmtree(test_dir)
    os.remove(db_file)
    print("Experimento concluído com sucesso e sem resíduos.")