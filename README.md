# 🤖 LoL-GPT Betting Assistant

Bot do Telegram para análise e previsões de partidas de League of Legends usando modelos de machine learning.

## 🚀 Funcionalidades

- ✅ **Comandos básicos**: `/start`, `/ajuda`, `/sobre`
- 🔮 **Previsões LoL**: Análise de partidas usando ML
- 📊 **Estatísticas**: Dados históricos e probabilidades
- 🤖 **Telegram Bot**: Interface amigável

## 📋 Estrutura do Projeto

```
├── main.py              # Aplicação principal Flask + Bot
├── config.py            # Configurações do bot
├── requirements.txt     # Dependências Python
├── Dockerfile          # Container para deploy
├── Procfile            # Comando Railway/Heroku
├── handlers/           # Handlers do bot Telegram
├── services/           # Serviços de ML e APIs
├── utils/              # Utilitários
└── data/               # Modelos e dados treinados
```

## 🛠️ Configuração Local

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Token
```bash
# Editar config.py ou definir variável de ambiente
export TELEGRAM_TOKEN="seu_token_aqui"
```

### 3. Executar Localmente
```bash
python main.py
```

## 🚂 Deploy no Railway

### 1. Conectar Repositório
1. Acesse [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Conecte este repositório

### 2. Configurar Variáveis
No painel Railway, adicione:
```
TELEGRAM_TOKEN = 7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo
PORT = 8080
```

### 3. Deploy Automático
O Railway detectará automaticamente:
- `Dockerfile` (método preferido)
- `Procfile` (método alternativo)
- `nixpacks.toml` (configuração explícita)

### 4. Configurar Webhook
Após deploy bem-sucedido:
```bash
python setup_railway.py https://sua-url.up.railway.app
```

## 📖 Documentação

- **[GUIA_RAILWAY.md](GUIA_RAILWAY.md)** - Guia completo de deploy
- **[PLANO_DE_ATAQUE_RAILWAY.md](PLANO_DE_ATAQUE_RAILWAY.md)** - Soluções para problemas

## 🔧 Comandos Úteis

### Testar Bot
```bash
python test_bot.py
```

### Configurar Webhook
```bash
python set_webhook.py
```

### Verificar Status
```bash
python -c "import requests; print(requests.get('https://api.telegram.org/bot{TOKEN}/getMe').json())"
```

## 🤖 Bot Telegram

**Nome**: @BETLOLGPT_bot  
**Status**: Ativo  
**Comandos**:
- `/start` - Iniciar bot
- `/ajuda` - Lista de comandos
- `/sobre` - Informações do bot

## 🛟 Suporte

Se tiver problemas:
1. Verifique logs no Railway
2. Teste localmente primeiro
3. Consulte os guias de documentação
4. Verifique se o token está configurado

## 📄 Licença

Este projeto é desenvolvido para fins educacionais e de demonstração.

---

**Desenvolvido com ❤️ para a comunidade LoL** 🎮

## Status
- ✅ Funcionando no Railway
- 🤖 @BETLOLGPT_bot
- 🔧 Event loop corrigido - Build 2025.05.23 