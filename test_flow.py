#!/usr/bin/env python3
"""Script para testar o fluxo completo da aplicação"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_consulta_ncm():
    """Testa a consulta de NCM"""
    print("\n🔍 Testando consulta NCM...")

    response = requests.post(
        f"{BASE_URL}/consultar",
        json={"ncm": "100630"},
        allow_redirects=False
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200 and response.json().get('success'):
        print("✅ Consulta NCM funcionando!")
        return True
    else:
        print("❌ Erro na consulta NCM")
        return False

def test_salvar_lead():
    """Testa o salvamento de lead"""
    print("\n💾 Testando salvamento de lead...")

    # Primeiro faz a consulta NCM para criar sessão
    session = requests.Session()

    response = session.post(
        f"{BASE_URL}/consultar",
        json={"ncm": "100630"}
    )

    if not response.json().get('success'):
        print("❌ Erro ao criar sessão com NCM")
        return False

    # Agora tenta salvar o lead
    lead_data = {
        "nome": "Teste da Silva",
        "email": "teste@exemplo.com",
        "telefone": "(11) 98765-4321",
        "cnpj": "11.222.333/0001-81"
    }

    response = session.post(
        f"{BASE_URL}/salvar-lead",
        json=lead_data
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200 and response.json().get('success'):
        print("✅ Salvamento de lead funcionando!")
        return True
    else:
        print(f"❌ Erro ao salvar lead: {response.json()}")
        return False

def test_database():
    """Verifica o banco de dados"""
    print("\n🗄️  Verificando banco de dados...")

    import sqlite3
    conn = sqlite3.connect('ncm.db')
    cursor = conn.cursor()

    # Verifica tabela NCM
    count_ncm = cursor.execute("SELECT COUNT(*) FROM ncm").fetchone()[0]
    print(f"Registros na tabela NCM: {count_ncm}")

    # Verifica tabela leads
    count_leads = cursor.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    print(f"Registros na tabela leads: {count_leads}")

    # Mostra último lead cadastrado
    if count_leads > 0:
        last_lead = cursor.execute(
            "SELECT nome, email, cnpj, created_at FROM leads ORDER BY id DESC LIMIT 1"
        ).fetchone()
        print(f"Último lead: {last_lead[0]} - {last_lead[1]} - {last_lead[2]} - {last_lead[3]}")

    conn.close()

    if count_ncm > 0:
        print("✅ Banco de dados configurado corretamente!")
        return True
    else:
        print("❌ Tabela NCM vazia")
        return False

def main():
    print("="*60)
    print("🧪 TESTE COMPLETO DO SISTEMA")
    print("="*60)

    results = []

    # Testa banco de dados
    results.append(("Banco de Dados", test_database()))

    # Testa consulta NCM
    results.append(("Consulta NCM", test_consulta_ncm()))

    # Testa salvamento de lead
    results.append(("Salvamento Lead", test_salvar_lead()))

    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")

    total_passed = sum(1 for _, result in results if result)
    print(f"\nTotal: {total_passed}/{len(results)} testes passaram")

    if total_passed == len(results):
        print("\n🎉 Todos os testes passaram!")
    else:
        print(f"\n⚠️  {len(results) - total_passed} teste(s) falharam")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro ao executar testes: {e}")
        import traceback
        traceback.print_exc()
