# Mapeador e Simulador de Crédito Tributário - Conta Azul

Aplicação web completa para mapeamento de crédito tributário baseada na Reforma Tributária brasileira (IBS/CBS).

**🚀 Banco de dados distribuído na edge com Turso Database**

## Como usar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Turso Database

**Criar conta e banco de dados:**
```bash
# 1. Instalar Turso CLI
# macOS/Linux:
curl -sSfL https://get.tur.so/install.sh | bash

# ou com Homebrew (macOS):
brew install tursodatabase/tap/turso

# 2. Fazer login
turso auth login

# 3. Criar banco de dados
turso db create mapeador-credito-tributario

# 4. Obter URL do banco
turso db show mapeador-credito-tributario --url

# 5. Criar token de autenticação
turso db tokens create mapeador-credito-tributario
```

### 3. Configurar variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione suas credenciais
```

**Configuração do .env:**
```env
# Turso Database (obrigatório)
TURSO_DATABASE_URL=libsql://seu-database.turso.io
TURSO_AUTH_TOKEN=seu-token-aqui

# Resend Email (opcional - para envio de emails)
RESEND_API_KEY=re_sua_chave_aqui
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=Conta Azul - Crédito Tributário
```

**Obter chave do Resend:**
1. Acesse https://resend.com e crie uma conta
2. Navegue até API Keys e crie uma nova chave
3. Para testes, use `onboarding@resend.dev` como FROM_EMAIL

### 4. Importar dados de NCM para o Turso
```bash
python import_csv.py
```

Este comando irá:
- Criar as tabelas `ncm` e `leads` no Turso
- Importar todos os códigos NCM do arquivo CSV
- Criar índices para busca rápida

### 5. Iniciar o servidor
```bash
python app.py
```

### 6. Acessar a aplicação
Abra o navegador em: http://localhost:5001

## Fluxo da Aplicação

### Passo 1: Consulta NCM
- Usuário digita código NCM da mercadoria
- Sistema busca no banco de dados o Cclasstrib correspondente

### Passo 2: Captura de Lead
- Formulário com: Nome, Email, Telefone, CNPJ (validado), Senha
- Dados salvos no banco de dados com senha hash (bcrypt)
- Email de boas-vindas enviado via Resend com credenciais de acesso
- Usuário autenticado automaticamente
- Exibe resultado do NCM após captura

### Passo 3: Calculadora do Governo
- Exibe Cclasstrib encontrado
- Link para calculadora oficial: https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/calculadora/regime-geral
- Instruções de uso
- Disclaimer para usar calculadora antes de continuar

### Passo 4: Simulação de Imposto Líquido
- Input: Débito Bruto
- Input: Crédito Acumulado
- Cálculo: Imposto Líquido = Débito Bruto - Crédito Acumulado
- Interpretação do resultado

## Funcionalidades

- ✅ Consulta de código NCM
- ✅ Captura e validação de leads (CNPJ validado)
- ✅ Sistema de autenticação completo (login/logout)
- ✅ Gestão de perfil com alteração de senha
- ✅ Hash de senhas com Werkzeug (pbkdf2)
- ✅ Envio de emails via Resend API
- ✅ Email de boas-vindas com credenciais de acesso
- ✅ Integração com calculadora oficial do governo
- ✅ Cálculo de imposto líquido
- ✅ Interface moderna com branding Conta Azul
- ✅ Header componentizado e responsivo
- ✅ Sistema de sessões para navegação entre telas
- ✅ Busca exata ou por código parcial (prefixo)
- ✅ **Banco de dados Turso (SQLite distribuído na edge)**
- ✅ Skip automático de captura de lead para usuários logados

## Estrutura do Projeto

```
ncmTest/
├── app.py                          # Aplicação Flask com rotas e SQLAlchemy
├── import_csv.py                   # Script de importação de dados para Turso
├── requirements.txt                # Dependências Python
├── .env                           # Variáveis de ambiente (não versionado)
├── .env.example                   # Template de configuração
├── static/
│   ├── css/
│   │   └── style.css              # Estilos globais
│   ├── ca-logo.svg                # Logo Conta Azul
│   └── favicon.png                # Favicon
└── templates/
    ├── header.html                # Componente: Header
    ├── footer.html                # Componente: Footer
    ├── index.html                 # Tela 1: Consulta NCM
    ├── lead.html                  # Tela 2: Captura de lead
    ├── login.html                 # Tela: Login
    ├── perfil.html                # Tela: Editar perfil
    ├── resultado.html             # Tela 3: Resultado e link gov
    └── simulacao.html             # Tela 4: Cálculo imposto líquido
```

## Tecnologias

- **Backend**: Flask 3.0
- **Database**: Turso (SQLite distribuído)
- **ORM**: SQLAlchemy + sqlalchemy-libsql
- **Email**: Resend API
- **Auth**: Werkzeug (password hashing)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Fonts**: Montserrat (Google Fonts)

## Design

- **Background**: #f3f4fa
- **Headings**: #2787e9
- **Logo**: Conta Azul (SVG oficial)
- **Layout**: Responsivo e moderno
- **Indicador**: Stepper visual com 4 passos
