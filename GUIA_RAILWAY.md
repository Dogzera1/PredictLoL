# 🚂 Guia Completo - Deploy no Railway

## 📋 Passos para Deploy

### 1️⃣ Preparar o Projeto

✅ **Arquivos já criados para você:**
- `main.py` - Aplicação principal otimizada para Railway
- `Procfile` - Configuração de execução
- `requirements.txt` - Dependências atualizadas
- `setup_railway.py` - Script para configurar webhook

### 2️⃣ Conectar ao Railway

1. **Acesse**: https://railway.app
2. **Login** com GitHub/Google
3. **Clique em "New Project"**
4. **Selecione "Deploy from GitHub repo"**
5. **Conecte seu repositório** (GPT LOL)

### 3️⃣ Configurar Variáveis de Ambiente

No painel do Railway:

1. **Vá em "Variables"**
2. **Adicione a variável:**
   - **Nome**: `TELEGRAM_TOKEN`
   - **Valor**: `7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo`

### 4️⃣ Deploy Automático

O Railway vai automaticamente:
- ✅ Detectar que é um projeto Python
- ✅ Instalar dependências do `requirements.txt`
- ✅ Executar com o `Procfile`
- ✅ Gerar uma URL pública

### 5️⃣ Configurar Webhook

Após o deploy (quando aparecer "Deploy Success"):

1. **Copie a URL do projeto** (algo como `https://seu-projeto.up.railway.app`)
2. **Execute o script**:
   ```bash
   python setup_railway.py https://sua-url-do-railway.up.railway.app
   ```

### 6️⃣ Testar o Bot

1. **Abra o Telegram**
2. **Procure por**: `@BETLOLGPT_bot`
3. **Envie**: `/start`
4. **Deve responder**: "✅ Bot ativo! Use /ajuda para ver os comandos disponíveis."

## 🔧 Verificações

### Verificar Status da Aplicação
```bash
# Acesse a URL do seu projeto no navegador
https://seu-projeto.up.railway.app

# Deve mostrar:
# 🤖 Bot LoL - Railway
# Status: 🟢 ATIVO
# Token: ✅ Configurado
```

### Verificar Webhook
```bash
# Acesse o endpoint webhook
https://seu-projeto.up.railway.app/webhook

# Deve mostrar:
# 🤖 Webhook do Bot LoL está 🟢 ATIVO!
```

### Verificar Logs no Railway
1. **No painel do Railway**
2. **Clique em "Deployments"**
3. **Clique no deploy ativo**
4. **Veja os logs em tempo real**

## ⚠️ Problemas Comuns

### Bot não responde
1. **Verificar variável `TELEGRAM_TOKEN`** nas configurações
2. **Verificar logs** no Railway
3. **Executar novamente** `setup_railway.py`

### Aplicação não inicia
1. **Verificar logs** no Railway
2. **Garantir que `Procfile` existe**
3. **Verificar `requirements.txt`**

### URL não funciona
1. **Aguardar alguns minutos** após deploy
2. **Verificar se aplicação está "Running"**
3. **Tentar fazer redeploy**

## 📊 Monitoramento

### Comandos Úteis
```bash
# Verificar webhook atual
python -c "import requests; print(requests.get('https://api.telegram.org/bot7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo/getWebhookInfo').json())"

# Testar bot manualmente
python -c "import requests; print(requests.get('https://api.telegram.org/bot7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo/getMe').json())"

# Verificar saúde da aplicação
curl https://seu-projeto.up.railway.app/health
```

## 🎯 Próximos Passos

Após o bot estar funcionando:

1. **✅ Testar todos os comandos** (`/start`, `/ajuda`, `/sobre`)
2. **📊 Monitorar logs** por algumas horas
3. **🚀 Implementar novas funcionalidades** do LoL
4. **💾 Adicionar banco de dados** se necessário

## 🔗 Links Importantes

- **Painel Railway**: https://railway.app/dashboard
- **Bot Telegram**: https://t.me/BETLOLGPT_bot
- **Documentação Railway**: https://docs.railway.app

## 🆘 Suporte

Se algo der errado:

1. **Verificar logs** no Railway primeiro
2. **Testar aplicação** acessando a URL diretamente
3. **Executar comandos de verificação** acima
4. **Me mostrar os logs** para ajudar a debugar

**Railway é muito mais confiável que Vercel para bots Python!** 🚂✨ 