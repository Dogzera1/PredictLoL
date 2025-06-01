# 🚀 Deploy Bot LoL V3 no Railway

## 📋 **Guia Completo de Deploy**

### 🎯 **Pré-requisitos**

1. **Conta no Railway:** [railway.app](https://railway.app)
2. **Bot do Telegram:** Token obtido via [@BotFather](https://t.me/BotFather)
3. **APIs configuradas:**
   - PandaScore API Key (opcional - tem padrão)
   - Riot API Key (opcional - tem padrão)

---

## 🔧 **Passo a Passo**

### **1. Preparar o Projeto**

✅ **Arquivos já configurados:**
- `railway.toml` → Configuração Railway
- `nixpacks.toml` → Build configuration
- `requirements.txt` → Dependências Python
- `Procfile` → Comando de start
- `runtime.txt` → Versão Python
- `health_check.py` → Health monitoring
- `env.template` → Template de variáveis

### **2. Deploy no Railway**

#### **Opção A: Via GitHub (Recomendado)**

1. **Push para GitHub:**
   ```bash
   git add .
   git commit -m "Deploy Railway - Bot LoL V3"
   git push origin main
   ```

2. **Conectar no Railway:**
   - Acesse [railway.app](https://railway.app)
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Escolha seu repositório

#### **Opção B: Via Railway CLI**

1. **Instalar Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login e Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

### **3. Configurar Variáveis de Ambiente**

No dashboard do Railway, vá em **Variables** e configure:

#### **🔑 Obrigatórias:**
```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_ADMIN_USER_IDS=123456789,987654321
```

#### **📡 APIs (Opcionais - já tem padrão):**
```env
PANDASCORE_API_KEY=sua_key_aqui
RIOT_API_KEY=sua_key_aqui
```

#### **⚙️ Configurações (Automáticas):**
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
PORT=8080
TZ=America/Sao_Paulo
PYTHONUNBUFFERED=1
```

### **4. Verificar Deploy**

1. **Logs do Deploy:**
   - No Railway dashboard → **Deployments** → **View Logs**

2. **Health Check:**
   - Acesse: `https://seu-app.railway.app/health`
   - Deve retornar: `{"status": "healthy"}`

3. **Status Detalhado:**
   - Acesse: `https://seu-app.railway.app/status`

---

## 🔍 **Monitoramento**

### **Health Check Endpoints:**

- **`/health`** → Status básico para Railway
- **`/status`** → Status detalhado do bot
- **`/`** → Informações gerais

### **Logs Importantes:**
```
🏥 Health check server iniciado na porta 8080
🚀 Iniciando Bot LoL V3 Ultra Avançado...
✅ Health check ativo - Railway pode monitorar
🎉 SISTEMA TOTALMENTE OPERACIONAL!
```

---

## ⚡ **Configurações Railway**

### **Configuração Automática:**
- **Build:** Nixpacks (Python 3.11.7)
- **Start Command:** `python main.py`
- **Health Check:** `/health` endpoint
- **Restart Policy:** On failure (3 retries)
- **Region:** Automático (mais próximo)

### **Recursos:**
- **CPU:** Shared
- **RAM:** 512MB (suficiente)
- **Storage:** Ephemeral
- **Network:** HTTPS automático

---

## 🧪 **Teste Local (Opcional)**

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp env.template .env
# Editar .env com seus tokens

# Executar
python main.py
```

---

## 🎯 **Funcionalidades Ativas**

### **✅ Sistema Completo:**
- 🤖 **Bot Telegram:** Interface completa com 61 botões
- 📊 **Tips Profissionais:** ML + algoritmos heurísticos
- 🔄 **Monitoramento 24/7:** Automático
- 📱 **Comandos Admin:** Controle total via Telegram
- 🏥 **Health Check:** Monitoramento Railway

### **✅ APIs Integradas:**
- 📡 **PandaScore:** Dados de partidas
- 🎮 **Riot API:** Dados oficiais (modo mock)
- 📤 **Telegram API:** Comunicação

### **✅ Comandos Disponíveis:**
- `/start` → Menu principal
- `/help` → Ajuda completa
- `/subscribe` → Configurar alertas
- `/status` → Status do sistema
- `/admin` → Painel administrativo (admins)

---

## 🔧 **Troubleshooting**

### **Deploy Falha:**
1. Verificar logs no Railway dashboard
2. Confirmar `TELEGRAM_BOT_TOKEN` configurado
3. Verificar se requirements.txt está correto

### **Bot Não Responde:**
1. Verificar health check: `/health`
2. Verificar logs: "SISTEMA TOTALMENTE OPERACIONAL!"
3. Testar `/start` no Telegram

### **Health Check Falha:**
1. Verificar se porta 8080 está livre
2. Confirmar Flask instalado
3. Verificar logs de inicialização

---

## 📊 **Monitoramento Contínuo**

### **Railway Dashboard:**
- **Metrics:** CPU, RAM, Network
- **Logs:** Real-time
- **Deployments:** Histórico
- **Health:** Status automático

### **Telegram Admin:**
- `/system` → Status completo
- `/health` → Health check manual
- `/logs` → Logs recentes

---

## 🎉 **Deploy Concluído!**

Após o deploy bem-sucedido:

1. ✅ **Bot online 24/7**
2. ✅ **Health check ativo**
3. ✅ **Monitoramento automático**
4. ✅ **Interface completa**
5. ✅ **Tips profissionais**

### **🚀 Próximos Passos:**
1. Teste `/start` no Telegram
2. Configure alertas com `/subscribe`
3. Use `/admin` para controle total
4. Monitore via Railway dashboard

---

**🔥 Bot LoL V3 Ultra Avançado rodando no Railway!**

*Sistema profissional de tips para League of Legends*  
*Powered by ML + Algoritmos + Railway Deploy* 🚀 