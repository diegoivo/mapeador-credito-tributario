# Mapeador e Simulador de Crédito Tributário - Conta Azul

Aplicação web completa para mapeamento de crédito tributário baseada na Reforma Tributária brasileira (IBS/CBS).

## Como usar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente (Resend)
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione sua chave do Resend
# Obtenha em: https://resend.com/api-keys
```

**Configuração do Resend:**
1. Acesse https://resend.com e crie uma conta
2. Navegue até API Keys e crie uma nova chave
3. Adicione a chave no arquivo `.env`:
   ```
   RESEND_API_KEY=re_sua_chave_aqui
   FROM_EMAIL=noreply@seudominio.com
   ```
4. Para ambiente de testes, use `onboarding@resend.dev` como FROM_EMAIL

### 3. Importar a planilha CSV para o banco de dados
```bash
python import_csv.py
```

### 4. Iniciar o servidor
```bash
python app.py
```

### 5. Acessar a aplicação
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
- ✅ Hash de senhas com Werkzeug (pbkdf2)
- ✅ Envio de emails via Resend API
- ✅ Email de boas-vindas com credenciais de acesso
- ✅ Integração com calculadora oficial do governo
- ✅ Cálculo de imposto líquido
- ✅ Interface moderna com branding Conta Azul
- ✅ Header componentizado e responsivo
- ✅ Sistema de sessões para navegação entre telas
- ✅ Busca exata ou por código parcial (prefixo)
- ✅ Banco de dados SQLite local

## Estrutura do Projeto

```
ncmTest/
├── app.py                          # Aplicação Flask com rotas
├── import_csv.py                   # Script de importação de dados
├── requirements.txt                # Dependências Python
├── ncm.db                          # Banco de dados SQLite (criado após importação)
├── static/
│   └── css/
│       └── style.css              # Estilos globais
└── templates/
    ├── index.html                 # Tela 1: Consulta NCM
    ├── lead.html                  # Tela 2: Captura de lead
    ├── resultado.html             # Tela 3: Resultado e link gov
    └── simulacao.html             # Tela 4: Cálculo imposto líquido
```

## Design

- **Background**: #f3f4fa
- **Headings**: #2787e9
- **Logo**: Conta Azul (SVG oficial)
- **Layout**: Responsivo e moderno
- **Indicador**: Stepper visual com 4 passos
