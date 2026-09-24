import sqlite3

# Criação da conexão com o banco de dados
conn = sqlite3.connect('banco_de_dados.db')

# Adição de coluna
conn.execute('''
    ALTER TABLE tabela ADD COLUMN cidade TEXT NOT NULL
''')

# Inserção de dados
conn.execute('''
    INSERT INTO tabela (cidade) VALUES ('São Paulo')
''')

# Fechamento da conexão
conn.close()