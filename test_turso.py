from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

print(f"URL (sem token): {TURSO_DATABASE_URL}")
print(f"Token length: {len(TURSO_AUTH_TOKEN) if TURSO_AUTH_TOKEN else 0}")

# Remove o protocolo libsql:// se estiver presente
url_without_protocol = TURSO_DATABASE_URL.replace('libsql://', '')
db_url = f"sqlite+libsql://{url_without_protocol}?secure=true"

print(f"Connection URL: {db_url}")

try:
    engine = create_engine(
        db_url,
        connect_args={
            'check_same_thread': False,
            'auth_token': TURSO_AUTH_TOKEN
        },
        poolclass=StaticPool,
        echo=True
    )

    print("✅ Engine criado")

    conn = engine.connect()
    print("✅ Conexão estabelecida")

    # Testa criação de tabela
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    '''))
    conn.commit()
    print("✅ Tabela de teste criada")

    # Testa inserção
    conn.execute(text("INSERT INTO test_table (name) VALUES (:name)"), {'name': 'teste'})
    conn.commit()
    print("✅ Registro inserido")

    # Testa consulta
    result = conn.execute(text("SELECT * FROM test_table")).fetchone()
    print(f"✅ Consulta bem-sucedida: {dict(result._mapping) if result else None}")

    conn.close()
    print("✅ Conexão fechada com sucesso")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
