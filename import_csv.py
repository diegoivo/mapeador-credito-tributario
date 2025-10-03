import sqlite3
import csv

def create_database():
    """Cria o banco de dados e a tabela NCM"""
    conn = sqlite3.connect('ncm.db')
    cursor = conn.cursor()

    # Cria tabela NCM
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ncm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ncm TEXT NOT NULL,
            descricao TEXT,
            cclasstrib TEXT,
            cst TEXT,
            descricao_cst TEXT
        )
    ''')

    # Cria tabela de leads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefone TEXT NOT NULL,
            cnpj TEXT NOT NULL,
            senha TEXT NOT NULL,
            ncm TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Cria índice para busca rápida por NCM
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ncm ON ncm(ncm)')

    # Cria índice para busca por CNPJ
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cnpj ON leads(cnpj)')

    conn.commit()
    return conn

def import_csv_to_db():
    """Importa os dados do CSV para o banco de dados"""
    conn = create_database()
    cursor = conn.cursor()

    # Limpa dados anteriores
    cursor.execute('DELETE FROM ncm')

    # Lê e importa o CSV
    with open('Planilha Exclusíva - NCM_NBS x Cclasstrib - Mercadorias.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            cursor.execute('''
                INSERT INTO ncm (ncm, descricao, cclasstrib, cst, descricao_cst)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                row['NCM'],
                row['Descrição'],
                row['Cclasstrib'],
                row['CST'],
                row['Descrição CST-IBS/CBS']
            ))

    conn.commit()
    count = cursor.execute('SELECT COUNT(*) FROM ncm').fetchone()[0]
    conn.close()

    print(f'Importação concluída! {count} registros importados.')

if __name__ == '__main__':
    import_csv_to_db()
