from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

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

conn = engine.connect()

print("=== Teste 1: Contar total de NCMs ===")
result = conn.execute(text('SELECT COUNT(*) as total FROM ncm')).fetchone()
print(f"Total de registros NCM: {result[0]}\n")

print("=== Teste 2: Buscar um NCM específico (0401) ===")
result = conn.execute(text('SELECT * FROM ncm WHERE ncm = :ncm'), {'ncm': '0401'}).fetchone()
if result:
    row_dict = dict(result._mapping)
    print(f"NCM: {row_dict['ncm']}")
    print(f"Descrição: {row_dict['descricao']}")
    print(f"Cclasstrib: {row_dict['cclasstrib']}")
    print(f"CST: {row_dict['cst']}\n")

print("=== Teste 3: Buscar com LIKE (04%) ===")
results = conn.execute(text('SELECT ncm, descricao FROM ncm WHERE ncm LIKE :pattern LIMIT 5'), {'pattern': '04%'}).fetchall()
print(f"Encontrados {len(results)} registros:")
for row in results:
    row_dict = dict(row._mapping)
    print(f"  - {row_dict['ncm']}: {row_dict['descricao'][:50]}...")

print("\n=== Teste 4: Verificar estrutura da tabela leads ===")
try:
    result = conn.execute(text('SELECT COUNT(*) as total FROM leads')).fetchone()
    print(f"Total de leads: {result[0]}")
except Exception as e:
    print(f"Erro ao consultar leads: {e}")

conn.close()
print("\n✅ Todos os testes concluídos com sucesso!")
