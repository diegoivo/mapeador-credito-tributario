from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import secrets
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuração do Turso Database
TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

# Cria engine do SQLAlchemy com Turso
if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
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
    print("✅ Conectado ao Turso Database")
else:
    print("⚠️  Variáveis TURSO_DATABASE_URL e TURSO_AUTH_TOKEN não configuradas")
    print("⚠️  Configure o .env com suas credenciais do Turso")
    engine = None

# Configuração do Resend
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'onboarding@resend.dev')
FROM_NAME = os.getenv('FROM_NAME', 'Conta Azul - Crédito Tributário')

# Importa Resend apenas se a chave estiver configurada
resend_available = False
if RESEND_API_KEY:
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend_available = True
    except ImportError:
        print("⚠️  Resend não instalado. Execute: pip install resend")

def get_db_connection():
    """Conecta ao banco de dados Turso via SQLAlchemy"""
    if engine is None:
        raise Exception("Database engine não configurado. Verifique as variáveis de ambiente TURSO_DATABASE_URL e TURSO_AUTH_TOKEN")
    return engine.connect()

def row_to_dict(row):
    """Converte Row do SQLAlchemy para dicionário"""
    if row is None:
        return None
    return dict(row._mapping)

def send_welcome_email(email, nome, senha_original, ncm_data):
    """Envia email de boas-vindas com credenciais"""
    if not resend_available:
        print(f"⚠️  Email não enviado (Resend não configurado) para {email}")
        return False

    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #2787e9; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Conta Azul</h1>
                <p style="color: white; margin: 5px 0 0 0;">Crédito Tributário</p>
            </div>

            <div style="padding: 30px; background-color: #f9f9f9;">
                <h2 style="color: #333;">Bem-vindo, {nome}!</h2>

                <p style="color: #666; line-height: 1.6;">
                    Sua conta foi criada com sucesso no Mapeador e Simulador de Crédito Tributário da Conta Azul.
                </p>

                <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2787e9; margin-top: 0;">Seus dados de acesso:</h3>
                    <p style="margin: 10px 0;"><strong>E-mail:</strong> {email}</p>
                    <p style="margin: 10px 0;"><strong>Senha:</strong> {senha_original}</p>
                </div>

                <div style="background-color: #e6f4ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2787e9; margin-top: 0;">NCM Consultado:</h3>
                    <p style="margin: 10px 0;"><strong>Código:</strong> {ncm_data.get('ncm', 'N/A')}</p>
                    <p style="margin: 10px 0;"><strong>Descrição:</strong> {ncm_data.get('descricao', 'N/A')}</p>
                    <p style="margin: 10px 0;"><strong>Cclasstrib:</strong> {ncm_data.get('cclasstrib', 'N/A')}</p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5001/login"
                       style="background-color: #2787e9; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 50px; display: inline-block;">
                        Acessar Plataforma
                    </a>
                </div>

                <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                    Esta é uma mensagem automática. Por favor, não responda este e-mail.
                </p>
            </div>
        </div>
        """

        params = {
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": [email],
            "subject": "Bem-vindo ao Simulador de Crédito Tributário - Conta Azul",
            "html": html_content
        }

        response = resend.Emails.send(params)
        print(f"✅ Email enviado com sucesso para {email} (ID: {response.get('id')})")
        return True

    except Exception as e:
        print(f"❌ Erro ao enviar email: {str(e)}")
        return False

@app.route('/')
def index():
    """Página principal"""
    # Não limpa a sessão se o usuário já estiver autenticado
    if not session.get('user_authenticated'):
        session.clear()
    return render_template('index.html')

@app.route('/consultar', methods=['POST'])
def consultar():
    """Endpoint para consultar NCM"""
    data = request.get_json()
    ncm_code = data.get('ncm', '').strip()

    if not ncm_code:
        return jsonify({'error': 'Código NCM é obrigatório'}), 400

    conn = get_db_connection()

    # Busca exata por NCM
    result = conn.execute(
        text('SELECT * FROM ncm WHERE ncm = :ncm'),
        {'ncm': ncm_code}
    ).fetchone()

    # Se não encontrar, busca por NCM que começa com o código informado
    if not result:
        result = conn.execute(
            text('SELECT * FROM ncm WHERE ncm LIKE :pattern'),
            {'pattern': f'{ncm_code}%'}
        ).fetchone()

    conn.close()

    if result:
        result_dict = row_to_dict(result)
        # Salva dados do NCM na sessão
        session['ncm_data'] = {
            'ncm': result_dict['ncm'],
            'descricao': result_dict['descricao'],
            'cclasstrib': result_dict['cclasstrib'],
            'cst': result_dict['cst'],
            'descricao_cst': result_dict['descricao_cst']
        }
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': 'NCM não encontrado'
        }), 404

@app.route('/lead')
def lead():
    """Página de captura de lead"""
    # Verifica se há dados do NCM na sessão
    if 'ncm_data' not in session:
        return redirect(url_for('index'))

    # Se usuário já está autenticado, busca seus dados e vai direto para resultado
    if session.get('user_authenticated'):
        conn = get_db_connection()

        try:
            user = conn.execute(
                text('SELECT nome, email, telefone, cnpj FROM leads WHERE email = :email'),
                {'email': session.get('user_email')}
            ).fetchone()

            if user:
                user_dict = row_to_dict(user)
                # Salva dados do lead na sessão
                session['lead_data'] = {
                    'nome': user_dict['nome'],
                    'email': user_dict['email'],
                    'telefone': user_dict['telefone'],
                    'cnpj': user_dict['cnpj']
                }
                return redirect(url_for('resultado'))
        finally:
            conn.close()

    return render_template('lead.html')

@app.route('/salvar-lead', methods=['POST'])
def salvar_lead():
    """Endpoint para salvar lead"""
    data = request.get_json()

    # Validação básica
    required_fields = ['nome', 'email', 'telefone', 'cnpj', 'senha']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400

    # Valida tamanho mínimo da senha
    if len(data.get('senha', '')) < 6:
        return jsonify({'error': 'Senha deve ter no mínimo 6 caracteres'}), 400

    # Salva lead no banco de dados
    conn = get_db_connection()

    try:
        ncm = session.get('ncm_data', {}).get('ncm', '')
        senha_original = data['senha']  # Guarda senha original para enviar no email
        senha_hash = generate_password_hash(data['senha'])

        conn.execute(
            text('''
                INSERT INTO leads (nome, email, telefone, cnpj, senha, ncm)
                VALUES (:nome, :email, :telefone, :cnpj, :senha, :ncm)
            '''),
            {
                'nome': data['nome'],
                'email': data['email'],
                'telefone': data['telefone'],
                'cnpj': data['cnpj'],
                'senha': senha_hash,
                'ncm': ncm
            }
        )

        conn.commit()

        # Autentica o usuário automaticamente após o cadastro
        session['user_authenticated'] = True
        session['user_email'] = data['email']
        session['user_name'] = data['nome']

        # Salva dados do lead na sessão
        session['lead_data'] = {
            'nome': data['nome'],
            'email': data['email'],
            'telefone': data['telefone'],
            'cnpj': data['cnpj']
        }

        # Envia email de boas-vindas
        send_welcome_email(
            email=data['email'],
            nome=data['nome'],
            senha_original=senha_original,
            ncm_data=session.get('ncm_data', {})
        )

        return jsonify({'success': True})

    except Exception as e:
        # Verifica se é erro de constraint UNIQUE (email duplicado)
        if 'UNIQUE constraint failed' in str(e) or 'email' in str(e).lower():
            return jsonify({'error': 'E-mail já cadastrado'}), 400
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/login')
def login_page():
    """Página de login"""
    # Se já estiver autenticado, redireciona para home
    if session.get('user_authenticated'):
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Endpoint de autenticação"""
    data = request.get_json()

    email = data.get('email', '').strip()
    senha = data.get('senha', '')

    if not email or not senha:
        return jsonify({'error': 'E-mail e senha são obrigatórios'}), 400

    conn = get_db_connection()

    try:
        # Busca usuário pelo email
        user = conn.execute(
            text('SELECT * FROM leads WHERE email = :email'),
            {'email': email}
        ).fetchone()

        if not user:
            return jsonify({'error': 'E-mail ou senha inválidos'}), 401

        user_dict = row_to_dict(user)

        # Verifica a senha
        if not check_password_hash(user_dict['senha'], senha):
            return jsonify({'error': 'E-mail ou senha inválidos'}), 401

        # Autentica o usuário
        session['user_authenticated'] = True
        session['user_email'] = user_dict['email']
        session['user_name'] = user_dict['nome']

        return jsonify({
            'success': True,
            'user': {
                'nome': user_dict['nome'],
                'email': user_dict['email']
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/perfil')
def perfil():
    """Página de edição de perfil"""
    # Verifica se o usuário está autenticado
    if not session.get('user_authenticated'):
        return redirect(url_for('login_page'))

    # Busca dados do usuário
    conn = get_db_connection()

    try:
        user = conn.execute(
            text('SELECT nome, email, telefone, cnpj FROM leads WHERE email = :email'),
            {'email': session.get('user_email')}
        ).fetchone()

        if not user:
            session.clear()
            return redirect(url_for('login_page'))

        user_dict = row_to_dict(user)
        return render_template('perfil.html', user=user_dict)

    finally:
        conn.close()

@app.route('/api/perfil', methods=['POST'])
def api_perfil():
    """Endpoint para atualizar perfil"""
    # Verifica se o usuário está autenticado
    if not session.get('user_authenticated'):
        return jsonify({'error': 'Não autenticado'}), 401

    data = request.get_json()

    # Validação básica
    required_fields = ['nome', 'email', 'telefone', 'cnpj']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400

    conn = get_db_connection()

    try:
        # Se está tentando mudar senha
        if data.get('senha_atual') and data.get('senha_nova'):
            # Busca senha atual do usuário
            user = conn.execute(
                text('SELECT senha FROM leads WHERE email = :email'),
                {'email': session.get('user_email')}
            ).fetchone()

            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404

            user_dict = row_to_dict(user)

            # Verifica se a senha atual está correta
            if not check_password_hash(user_dict['senha'], data['senha_atual']):
                return jsonify({'error': 'Senha atual incorreta'}), 400

            # Atualiza com nova senha
            senha_hash = generate_password_hash(data['senha_nova'])
            conn.execute(
                text('''
                    UPDATE leads
                    SET nome = :nome, email = :email, telefone = :telefone, cnpj = :cnpj, senha = :senha
                    WHERE email = :old_email
                '''),
                {
                    'nome': data['nome'],
                    'email': data['email'],
                    'telefone': data['telefone'],
                    'cnpj': data['cnpj'],
                    'senha': senha_hash,
                    'old_email': session.get('user_email')
                }
            )
        else:
            # Atualiza sem mudar senha
            conn.execute(
                text('''
                    UPDATE leads
                    SET nome = :nome, email = :email, telefone = :telefone, cnpj = :cnpj
                    WHERE email = :old_email
                '''),
                {
                    'nome': data['nome'],
                    'email': data['email'],
                    'telefone': data['telefone'],
                    'cnpj': data['cnpj'],
                    'old_email': session.get('user_email')
                }
            )

        conn.commit()

        # Atualiza sessão se o email ou nome mudaram
        nome_atualizado = False
        if data['email'] != session.get('user_email'):
            session['user_email'] = data['email']
        if data['nome'] != session.get('user_name'):
            session['user_name'] = data['nome']
            nome_atualizado = True

        return jsonify({
            'success': True,
            'nome_atualizado': nome_atualizado
        })

    except Exception as e:
        # Verifica se é erro de constraint UNIQUE (email duplicado)
        if 'UNIQUE constraint failed' in str(e) or 'email' in str(e).lower():
            return jsonify({'error': 'E-mail já cadastrado por outro usuário'}), 400
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/resultado')
def resultado():
    """Página de resultado com dados do NCM"""
    # Verifica se há dados necessários na sessão
    if 'ncm_data' not in session or 'lead_data' not in session:
        return redirect(url_for('index'))

    return render_template('resultado.html', ncm_data=session['ncm_data'])

@app.route('/simulacao')
def simulacao():
    """Página de simulação de imposto líquido"""
    # Verifica se há dados necessários na sessão
    if 'ncm_data' not in session or 'lead_data' not in session:
        return redirect(url_for('index'))

    return render_template('simulacao.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
