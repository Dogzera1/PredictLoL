# 🚀 GUIA COMPLETO DE DEPLOY NO RAILWAY - Bot LoL V3 Ultra Avançado

## 📋 Pré-requisitos

### ✅ **1. Contas Necessárias:**
- **GitHub** - Para hospedar o código
- **Railway** - Para deploy (railway.app)
- **Telegram BotFather** - Para o token do bot

### ✅ **2. Informações Obrigatórias:**
- **Token do Bot Telegram** (do BotFather)
- **Seu Telegram User ID** (seu ID numérico)

---

## 🔧 **PASSO 1: Preparar o Repositório GitHub**

### **1.1 Subir o código para GitHub:**
```bash
# Se ainda não tem repositório
git init
git add .
git commit -m "Bot LoL V3 Ultra Avançado - Deploy Ready"

# Criar repositório no GitHub e fazer push
git remote add origin https://github.com/SEU_USUARIO/PredictLoL.git
git branch -M main
git push -u origin main
```

### **1.2 Verificar arquivos essenciais:**
- ✅ `requirements.txt` (atualizado com todas as dependências)
- ✅ `main.py` (arquivo principal do bot)
- ✅ `health_check.py` (para monitoramento do Railway)
- ✅ `Procfile` (opcional, Railway detecta automaticamente)

---

## 🌐 **PASSO 2: Configurar Railway**

### **2.1 Criar Projeto no Railway:**
1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Clique em **"New Project"**
4. Selecione **"Deploy from GitHub repo"**
5. Escolha seu repositório **PredictLoL**

### **2.2 Configurar Variáveis de Ambiente:**
**OBRIGATÓRIO:** Configure estas variáveis em **Settings → Environment**

```bash
# TOKEN DO BOT (obtenha do @BotFather no Telegram)
TELEGRAM_BOT_TOKEN=1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

# SEU TELEGRAM ID (obtenha enviando /start para @userinfobot)
TELEGRAM_ADMIN_USER_IDS=123456789

# Configurações opcionais (Railway já define automaticamente)
PORT=8080
RAILWAY_ENVIRONMENT=production
```

### **2.3 Configurar Deploy:**
O Railway detecta automaticamente que é um projeto Python e:
- ✅ Instala dependências do `requirements.txt`
- ✅ Executa `python main.py`
- ✅ Configura health checks
- ✅ Fornece URL pública

---

## ⚙️ **PASSO 3: Arquivos de Configuração (Já Incluídos)**

### **3.1 requirements.txt** (✅ Já atualizado)
```
aiohttp==3.9.1
aiohttp-cors==0.8.1
beautifulsoup4==4.12.2
python-telegram-bot==20.7
# ... mais 40+ dependências
```

### **3.2 health_check.py** (✅ Já criado)
```python
# Health check para Railway
from aiohttp import web

async def health_check(request):
    return web.Response(text="OK", status=200)

app = web.Application()
app.router.add_get("/health", health_check)
```

### **3.3 main.py** (✅ Já configurado)
```python
# Sistema principal do bot
import os
import asyncio
from bot.systems.bot_telegram import BotTelegram

# Detecção automática de ambiente
if os.getenv("RAILWAY_ENVIRONMENT"):
    # Configuração específica para Railway
    pass
```

---

## 🚀 **PASSO 4: Executar Deploy**

### **4.1 Deploy Automático:**
```bash
# Qualquer push para main dispara deploy automático
git add .
git commit -m "Deploy para Railway"
git push origin main
```

### **4.2 Acompanhar Deploy:**
1. No painel do Railway, acesse **"Deployments"**
2. Veja logs em tempo real
3. Aguarde status **"Active"**

### **4.3 Obter URL da Aplicação:**
- Railway fornece URL automática: `https://seu-app.railway.app`
- Dashboard disponível em: `https://seu-app.railway.app/dashboard`

---

## 📊 **PASSO 5: Verificar Funcionamento**

### **5.1 Verificar Health Check:**
```bash
curl https://seu-app.railway.app/health
# Deve retornar: OK
```

### **5.2 Verificar Dashboard:**
- Acesse: `https://seu-app.railway.app/dashboard`
- Deve mostrar métricas em tempo real

### **5.3 Testar Bot Telegram:**
- Envie `/start` para seu bot
- Teste comando `/quick_status`
- Use `/admin_force_scan` para gerar tips

---

## 🔧 **PASSO 6: Configurações Avançadas (Opcional)**

### **6.1 Configurar Domínio Personalizado:**
```bash
# No Railway: Settings → Networking → Custom Domain
# Adicione: bot-lol.seudominio.com
```

### **6.2 Monitoramento Avançado:**
```bash
# Logs em tempo real
railway logs

# Status dos serviços
railway status

# Restart manual
railway restart
```

### **6.3 Configurar Auto-Deploy GitHub Actions:**
```yaml
# .github/workflows/railway-deploy.yml
name: Deploy to Railway
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: |
          curl -X POST ${{ secrets.RAILWAY_WEBHOOK_URL }}
```

---

## 🚨 **RESOLUÇÃO DE PROBLEMAS COMUNS**

### **❌ Erro: "No module named 'bs4'"**
**Solução:** ✅ Já corrigido no requirements.txt

### **❌ Erro: "Token inválido"**
**Solução:** 
1. Verifique se `TELEGRAM_BOT_TOKEN` está correto
2. Obtenha novo token do @BotFather se necessário

### **❌ Erro: "Memória insuficiente"**
**Solução:**
1. Use `deploy_production_lite.py` localmente para testes
2. Railway tem recursos adequados para produção

### **❌ Erro: "Port binding failed"**
**Solução:** Railway configura PORT automaticamente via variável de ambiente

### **❌ Bot não responde no Telegram**
**Solução:**
1. Verifique logs no Railway Dashboard
2. Confirme se `TELEGRAM_ADMIN_USER_IDS` está correto
3. Teste health check: `curl https://seu-app.railway.app/health`

---

## 📋 **CHECKLIST FINAL**

### ✅ **Antes do Deploy:**
- [ ] Código no GitHub atualizado
- [ ] Token do bot obtido do @BotFather
- [ ] Seu Telegram ID identificado
- [ ] requirements.txt com todas as dependências

### ✅ **Durante o Deploy:**
- [ ] Projeto criado no Railway
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy executado com sucesso
- [ ] Logs sem erros críticos

### ✅ **Após o Deploy:**
- [ ] Health check respondendo (GET /health)
- [ ] Dashboard acessível (GET /dashboard)
- [ ] Bot respondendo no Telegram (/start)
- [ ] Sistema de tips funcionando (/admin_force_scan)

---

## 🎯 **COMANDOS ÚTEIS RAILWAY**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Conectar ao projeto
railway link

# Ver logs em tempo real
railway logs

# Restart da aplicação
railway restart

# Status dos serviços
railway status

# Abrir dashboard web
railway open
```

---

## 🌟 **RESULTADO FINAL**

Após seguir este guia, você terá:

### ✅ **Sistema Completo em Produção:**
- 🤖 **Bot Telegram** funcionando 24/7
- 📊 **Dashboard Web** em tempo real
- 🎯 **Sistema de Tips** automático
- 🔍 **Monitoramento** contínuo
- 🚀 **API REST** completa

### ✅ **URLs Funcionais:**
- **App Principal:** `https://seu-app.railway.app`
- **Dashboard:** `https://seu-app.railway.app/dashboard`  
- **API Status:** `https://seu-app.railway.app/api/status`
- **Health Check:** `https://seu-app.railway.app/health`

### ✅ **Funcionalidades Ativas:**
- Geração automática de tips profissionais
- Análise ML + algoritmos híbrida
- Monitoramento de performance em tempo real
- Interface web para acompanhamento
- Integração completa com Telegram

---

## 📞 **SUPORTE**

### **🆘 Se encontrar problemas:**
1. **Verificar logs:** Railway Dashboard → Deployments → Logs
2. **Testar health check:** `curl https://seu-app.railway.app/health`
3. **Verificar variáveis:** Settings → Environment
4. **Restart manual:** Railway Dashboard → Restart

### **🎯 Para suporte específico:**
- Documentação Railway: [docs.railway.app](https://docs.railway.app)
- Status do serviço: [status.railway.app](https://status.railway.app)

---

**🎉 Deploy concluído! Seu Bot LoL V3 Ultra Avançado está agora rodando 24/7 no Railway com geração automática de tips profissionais!** 🚀 
