# 🚀 Deploy no Railway - Bot LoL V3 Ultra Avançado

## 📋 Pré-requisitos

### 1. **Criar Bot no Telegram**
```bash
1. Abra o Telegram e procure por @BotFather
2. Envie /newbot
3. Escolha um nome para o bot
4. Copie o TOKEN fornecido
```

### 2. **Obter seu User ID**
```bash
1. Procure por @userinfobot no Telegram
2. Envie /start
3. Copie o número do seu ID
```

### 3. **Conta no Railway** (opcional - PandaScore API)
```bash
1. Acesse https://pandascore.co/
2. Crie uma conta gratuita
3. Obtenha sua API key (15,000 requests/mês grátis)
```

---

## 🎯 Deploy no Railway

### **Passo 1: Conectar Repositório**

1. Acesse [Railway.app](https://railway.app/)
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha o repositório `PredictLoL`

### **Passo 2: Configurar Variáveis de Ambiente**

No dashboard do Railway, vá em **Variables** e adicione:

#### **🔑 OBRIGATÓRIAS (para produção):**
```env
TELEGRAM_BOT_TOKEN=7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg
TELEGRAM_ADMIN_USER_IDS=8012415611
ENVIRONMENT=production
```

#### **📡 OPCIONAIS (já têm padrão configurado):**
```env
PANDASCORE_API_KEY=90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ
LOG_LEVEL=INFO
SCAN_INTERVAL_MINUTES=3
```

> **📝 Nota:** O sistema já tem valores padrão configurados nas constantes, então essas variáveis são opcionais. O bot funcionará mesmo sem elas configuradas.

### **Passo 3: Deploy Automático**

O Railway fará deploy automaticamente quando detectar:
- ✅ `requirements.txt` ← Dependências Python
- ✅ `Procfile` ← Comando de execução  
- ✅ `runtime.txt` ← Versão do Python
- ✅ `railway.json` ← Configurações específicas

**🔄 Re-deploy:** Se o primeiro deploy falhou por erro de configuração, simplesmente configure as variáveis de ambiente e clique em "Deploy" novamente.

---

## 🔧 Configuração Detalhada

### **Variáveis de Ambiente Completas:**

```env
# ===== TELEGRAM (já configurado como padrão) =====
TELEGRAM_BOT_TOKEN=7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg
TELEGRAM_ADMIN_USER_IDS=8012415611

# ===== APIs (já configurado como padrão) =====
PANDASCORE_API_KEY=90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ

# ===== SISTEMA (opcional) =====
LOG_LEVEL=INFO
ENVIRONMENT=production
SCAN_INTERVAL_MINUTES=3
```

### **Múltiplos Administradores:**
```env
# Um admin:
TELEGRAM_ADMIN_USER_IDS=123456789

# Múltiplos admins:
TELEGRAM_ADMIN_USER_IDS=123456789,987654321,555666777
```

---

## ✅ Verificação do Deploy

### **1. Logs do Railway**
No dashboard, clique em **Deployments** → **View Logs**

**Procure por:**
```bash
✅ Bot LoL V3 Ultra Avançado totalmente operacional!
🔄 Monitoramento automático ativo
📱 Interface Telegram disponível
⚡ ScheduleManager executando
```

### **2. Teste no Telegram**
```bash
1. Procure seu bot no Telegram (@seu_bot_name)
2. Envie /start
3. Deve receber mensagem de boas-vindas
4. Teste /status para verificar sistema
```

### **3. Comandos de Teste**
```bash
/start    ← Mensagem inicial
/help     ← Lista de comandos
/status   ← Status do sistema
/admin    ← Painel admin (apenas admins)
```

---

## 🎯 Funcionalidades Ativas

### **🤖 Automação Completa:**
- ✅ Monitoramento de partidas a cada 3 minutos
- ✅ Geração automática de tips profissionais
- ✅ Envio para usuários via Telegram
- ✅ Health check do sistema
- ✅ Limpeza automática de cache

### **📱 Interface Telegram:**
- ✅ Comandos básicos (/start, /help, /status)
- ✅ Sistema de subscrições (4 tipos)
- ✅ Comandos administrativos
- ✅ Botões interativos
- ✅ Estatísticas em tempo real

### **🔧 Sistema Robusto:**
- ✅ Recuperação automática de erros
- ✅ Rate limiting anti-spam
- ✅ Logs detalhados
- ✅ Monitoramento de saúde
- ✅ Performance otimizada

---

## 🆘 Resolução de Problemas

### **❌ Bot não inicia:**
```bash
Verifique:
1. TELEGRAM_BOT_TOKEN está correto
2. Bot foi criado corretamente no @BotFather
3. Não há espaços no token
```

### **❌ Comandos admin não funcionam:**
```bash
Verifique:
1. TELEGRAM_ADMIN_USER_IDS está configurado
2. Seu User ID está na lista
3. IDs estão separados por vírgula (sem espaços)
```

### **❌ Deploy falha:**
```bash
Verifique logs no Railway:
1. Dashboard → Deployments → View Logs
2. Procure por mensagens de erro
3. Verifique se todas as dependências estão em requirements.txt
```

### **⚠️ Tips não são geradas:**
```bash
Normal nos primeiros momentos:
1. Sistema precisa encontrar partidas ao vivo
2. Partidas devem atender critérios de qualidade
3. Verifique /admin → /system para stats
```

---

## 📊 Monitoramento

### **Logs Importantes:**
```bash
✅ ScheduleManager inicializado
✅ Todos os componentes inicializados  
✅ Bot LoL V3 Ultra Avançado totalmente operacional!
🔍 Executando monitoramento de partidas...
💓 Health check: ✅ Saudável
```

### **Comandos de Monitoramento:**
```bash
/status   ← Status geral
/admin    ← Painel administrativo (admins)
/system   ← Status detalhado (admins)
/health   ← Health check (admins)
/force    ← Forçar scan (admins)
```

---

## 🎉 Sucesso!

Se tudo funcionou:

1. ✅ **Bot respondendo no Telegram**
2. ✅ **Monitoramento automático ativo**  
3. ✅ **Tips sendo geradas automaticamente**
4. ✅ **Comandos administrativos funcionando**
5. ✅ **Sistema 100% operacional no Railway**

**🚀 Seu Bot LoL V3 Ultra Avançado está ONLINE e funcionando 24/7!**

---

## 💡 Próximos Passos

1. **Compartilhe seu bot** com outros usuários
2. **Configure subscrições** via /subscribe  
3. **Monitore performance** via comandos admin
4. **Acompanhe tips** geradas automaticamente
5. **Aproveite o sistema profissional!**

## 🆘 Suporte

Em caso de problemas:
1. Verifique logs no Railway
2. Teste comandos básicos no Telegram
3. Use /admin → /health para diagnóstico
4. Consulte este guia de deploy

**🔥 Sistema desenvolvido para apostas profissionais - Use com responsabilidade!** 