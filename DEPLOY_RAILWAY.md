# 🚀 Deploy PredictLoL no Railway

## ✅ Sistema Pronto para Deploy

### 📁 Arquivos Necessários
- ✅ `main.py` - Sistema principal
- ✅ `requirements.txt` - Dependências mínimas
- ✅ `Procfile` - Configuração Railway
- ✅ `bot/` - Código do sistema
- ✅ `README.md` - Documentação

### 🔧 Configuração no Railway

#### 1. Conectar Repositório
1. Acesse [Railway.app](https://railway.app)
2. Conecte seu repositório GitHub
3. Selecione o projeto PredictLoL

#### 2. Configurar Variáveis
Adicione apenas esta variável obrigatória:
```
TELEGRAM_BOT_TOKEN=8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI
```

#### 3. Deploy Automático
- Railway detectará automaticamente o `Procfile`
- Instalará dependências do `requirements.txt`
- Iniciará o sistema via `main.py`

### 🎯 Após Deploy

#### ✅ Sistema Funcionando
- Health check disponível em `/health`
- Bot Telegram ativo e responsivo
- Sistema de apostas operacional

#### 🤖 Comandos do Bot
```
/start          - Iniciar bot
/bankroll       - Status do bankroll
/analisar T1 vs Gen.G - Análise de partida  
/apostar 50 1.85 T1 vencer - Registrar aposta
/tracker        - Dashboard de performance
/prever T1 vs Gen.G - Previsão pós-draft
```

### 🔒 Segurança
- ✅ Dados locais em JSON
- ✅ Sem APIs externas de apostas
- ✅ Sistema independente
- ✅ Controle total do usuário

### 📊 Monitoramento
- Logs disponíveis no Railway
- Health check automático
- Sistema auto-recuperativo

---

**🎉 Deploy concluído! Seu bot está pronto para uso.** 