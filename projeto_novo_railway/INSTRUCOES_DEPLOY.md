# 🚀 INSTRUÇÕES DE DEPLOY - RAILWAY NOVO

## 📋 Passo a Passo Completo

### 1. 🆕 Criar Novo Projeto Railway
1. Acesse [railway.app](https://railway.app)
2. Clique em "New Project"
3. Escolha "Deploy from GitHub repo"
4. Conecte com repositório ou faça upload manual

### 2. 📂 Upload dos Arquivos
Certifique-se de que os seguintes arquivos estão no projeto:
- ✅ `main.py` (código principal do bot)
- ✅ `requirements.txt` (dependências)
- ✅ `railway.json` (configuração Railway)
- ✅ `nixpacks.toml` (configuração build)
- ✅ `.gitignore` (arquivos ignorados)
- ✅ `README.md` (documentação)

### 3. 🔧 Configurar Variáveis de Ambiente

**OBRIGATÓRIAS:**
```env
TELEGRAM_TOKEN=1234567890:AAAA-seu-token-do-botfather
OWNER_ID=123456789
```

**Como configurar:**
1. No painel Railway, vá em "Variables"
2. Adicione cada variável clicando em "New Variable"
3. Nome: `TELEGRAM_TOKEN`, Valor: seu token
4. Nome: `OWNER_ID`, Valor: seu ID do Telegram

### 4. 🔍 Verificar Configurações

**railway.json deve conter:**
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py",
    "healthcheckPath": "/health"
  }
}
```

**requirements.txt deve conter apenas:**
```txt
python-telegram-bot==13.15
flask>=2.3.0
requests>=2.31.0
```

### 5. 🚀 Deploy Inicial
1. Railway fará build automático
2. Aguarde logs de "Building..."
3. Aguarde logs de "Deploying..."
4. Anote a URL gerada (ex: `https://xxx.railway.app`)

### 6. ✅ Verificar Funcionamento

**Teste 1: Health Check**
```bash
curl https://sua-url.railway.app/health
```
**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "...",
  "bot_status": "active"
}
```

**Teste 2: Root**
```bash
curl https://sua-url.railway.app/
```
**Resposta esperada:**
```json
{
  "message": "Bot LoL V3 Ultra Avançado",
  "status": "online"
}
```

### 7. 🤖 Testar Bot no Telegram
1. Procure seu bot no Telegram
2. Envie `/start`
3. Deve receber menu de boas-vindas
4. Teste comando `/tips`

## 🚨 Resolução de Problemas

### ❌ Build Falha
- Verifique `requirements.txt` (sem versões conflitantes)
- Verifique `railway.json` (sintaxe válida)
- Verifique logs de build no Railway

### ❌ Health Check 502
- **IMPORTANTE:** Se der 502, é problema da instância Railway
- Tente criar NOVO projeto do zero
- Não é problema do código

### ❌ Bot Não Responde
- Verifique `TELEGRAM_TOKEN` nas variáveis
- Verifique se bot está ativo no BotFather
- Verifique logs do Railway

### ❌ Webhook Não Configura
- Verifique se Railway gerou URL HTTPS
- Verifique se health check funciona primeiro
- Verifique logs do bot

## 📊 Logs Importantes

**Logs de sucesso esperados:**
```
INFO - 🤖 Bot LoL V3 Ultra Avançado inicializado
INFO - 🚀 Detectado ambiente Railway - Configurando webhook
INFO - ✅ Webhook configurado: https://sua-url.railway.app/webhook
INFO - 🌐 Iniciando Flask na porta 5000
```

**Se aparecer:**
```
INFO - 🏠 Ambiente local detectado - Usando polling
```
**Significa:** Variáveis de ambiente não configuradas

## 🔄 Redeploy
Se precisar fazer alterações:
1. Modifique arquivos no repositório
2. Commit e push
3. Railway redeploya automaticamente
4. Aguarde novos logs

## 📞 Suporte
Se tudo seguiu corretamente e ainda não funciona:
- Verifique se não é problema específico do Railway
- Tente outro serviço (Heroku, Render)
- Verifique status do Railway: status.railway.app 