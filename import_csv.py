from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import csv
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def get_engine():
    """Cria engine do SQLAlchemy com Turso"""
    TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
    TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        raise Exception("⚠️  Configure TURSO_DATABASE_URL e TURSO_AUTH_TOKEN no arquivo .env")

    # Remove o protocolo libsql:// se estiver presente
    url_without_protocol = TURSO_DATABASE_URL.replace('libsql://', '')
    db_url = f"sqlite+libsql://{url_without_protocol}?secure=true"

    engine = create_engine(
        db_url,
        connect_args={
            'check_same_thread': False,
            'auth_token': TURSO_AUTH_TOKEN
        },
        poolclass=StaticPool,
        echo=False
    )
    return engine

def create_database():
    """Cria as tabelas no banco de dados Turso"""
    engine = get_engine()
    conn = engine.connect()

    try:
        # Cria tabela NCM
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS ncm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ncm TEXT NOT NULL,
                descricao TEXT,
                cclasstrib TEXT,
                cst TEXT,
                descricao_cst TEXT
            )
        '''))

        # Cria tabela de leads
        conn.execute(text('''
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
        '''))

        # Cria índice para busca rápida por NCM
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_ncm ON ncm(ncm)'))

        # Cria índice para busca por CNPJ
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cnpj ON leads(cnpj)'))

        conn.commit()
        print("✅ Tabelas criadas com sucesso no Turso!")
        return conn

    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.close()
        raise

def import_csv_to_db():
    """Importa os dados do CSV para o banco de dados Turso"""
    engine = get_engine()
    conn = create_database()

    try:
        # Limpa dados anteriores
        conn.execute(text('DELETE FROM ncm'))
        conn.commit()
        print("🗑️  Dados anteriores removidos")

        # Lê e importa o CSV
        csv_file = 'Planilha Exclusíva - NCM_NBS x Cclasstrib - Mercadorias.csv'

        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Arquivo {csv_file} não encontrado")

        print(f"📁 Lendo arquivo {csv_file}...")

        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            rows_imported = 0
            batch_size = 100  # Commit a cada 100 registros

            for row in csv_reader:
                conn.execute(
                    text('''
                        INSERT INTO ncm (ncm, descricao, cclasstrib, cst, descricao_cst)
                        VALUES (:ncm, :descricao, :cclasstrib, :cst, :descricao_cst)
                    '''),
                    {
                        'ncm': row['NCM'],
                        'descricao': row['Descrição'],
                        'cclasstrib': row['Cclasstrib'],
                        'cst': row['CST'],
                        'descricao_cst': row['Descrição CST-IBS/CBS']
                    }
                )
                rows_imported += 1

                # Commit em lotes
                if rows_imported % batch_size == 0:
                    conn.commit()
                    print(f"  ⏳ {rows_imported} registros importados...")

        # Commit final
        conn.commit()

        # Verifica total de registros
        result = conn.execute(text('SELECT COUNT(*) as count FROM ncm')).fetchone()
        count = result[0]

        print(f"✅ Importação concluída! {count} registros no banco Turso.")

    except Exception as e:
        print(f"❌ Erro durante importação: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("🚀 Iniciando importação de dados para Turso Database...")
    import_csv_to_db()
