import sqlite3

# Criação da conexão com o banco de dados
conn = sqlite3.connect('banco_de_dados.db')

# Criação da tabela
conn.execute('''
    CREATE TABLE tabela (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        idade INTEGER NOT NULL
    )
''')

# Inserção de dados
conn.execute('''
    INSERT INTO tabela (nome, idade) VALUES ('João', 25)
''')

# Fechamento da conexão
conn.close()