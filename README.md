# PredictLoL - Sistema Integrado de Apostas e Previsões

Sistema completo para auxílio em apostas pessoais de League of Legends, com análise de value bets, gestão de bankroll e previsões pós-draft.

## 🎯 Funcionalidades

### 💰 Sistema de Apostas Pessoais
- **Bankroll Manager**: Gestão financeira com Kelly Criterion
- **Value Analyzer**: Análise manual de value bets
- **Betting Tracker**: Dashboard de performance visual
- **Pre-Game Analyzer**: Análise automatizada com dados históricos

### 🤖 Bot Telegram Integrado
- Interface completa via Telegram
- Comandos para análise de partidas
- Registro e tracking de apostas
- Dashboard em tempo real

### 🎮 Previsões Pós-Draft
- Análise de composições de times
- Probabilidades baseadas em dados históricos
- Recomendações de apostas

## 🚀 Como Usar

### Comandos do Bot Telegram

#### Comandos Principais
- `/start` - Iniciar o bot
- `/help` - Lista de comandos
- `/menu` - Menu principal

#### Gestão de Bankroll
- `/bankroll` - Status do bankroll atual
- `/apostar <valor> <odds> <descrição>` - Registrar aposta

#### Análises
- `/analisar <time1> vs <time2>` - Análise completa de match
- `/prever <time1> vs <time2>` - Previsão pós-draft

#### Performance
- `/tracker` - Dashboard de performance
- `/dashboard` - Estatísticas detalhadas

### Exemplo de Uso
```
/apostar 50 1.85 T1 vs Gen.G - T1 vencer
/analisar T1 vs Gen.G
/prever T1 vs Gen.G
/tracker
```

## 🔧 Instalação

### Dependências
```bash
pip install -r requirements.txt
```

### Variáveis de Ambiente
```bash
TELEGRAM_BOT_TOKEN=seu_token_aqui
```

### Executar
```bash
python main.py
```

## 📊 Componentes do Sistema

### 1. Personal Bankroll Manager
- Kelly Criterion para sizing otimizado
- Controle de risco por níveis
- Limites diários e por aposta
- Tracking de ROI e win rate

### 2. Manual Value Analyzer
- Análise detalhada de times
- Comparação entre casas de apostas
- Cálculo de Expected Value
- Identificação de value bets

### 3. Betting Tracker
- Dashboard visual em tempo real
- Gráficos ASCII de evolução
- Análise de streaks
- Métricas de performance

### 4. Pre-Game Analyzer
- Base de dados de 20+ times
- Análise automatizada de probabilidades
- Fatores contextuais (forma, H2H, patch)
- Recomendações baseadas em confiança

## 🎯 Características

### Gestão de Risco
- 5 níveis de risco (minimal, low, medium, high, extreme)
- Kelly Criterion para sizing
- Limites automáticos de proteção
- Controle de drawdown

### Análise Profissional
- 10 critérios de avaliação por time
- Comparação entre múltiplas casas
- Expected Value mínimo configurável
- Análise contextual completa

### Interface Intuitiva
- Bot Telegram responsivo
- Menus interativos
- Feedback em tempo real
- Comandos simples e diretos

## 📈 Deploy no Railway

### Configuração
1. Conectar repositório ao Railway
2. Configurar variável `TELEGRAM_BOT_TOKEN`
3. Deploy automático

### Health Check
- Endpoint `/health` disponível
- Monitoramento automático
- Logs detalhados

## 🔒 Segurança

- Dados locais em JSON
- Sem conexão com APIs de apostas
- Sistema de análise independente
- Controle total do usuário

## 📝 Versão

**v1.4.0** - Sistema Completo Integrado
- ✅ 4 componentes funcionais
- ✅ Bot Telegram completo
- ✅ Deploy Railway pronto
- ✅ Interface limpa e focada

## 🎮 Foco

Sistema desenvolvido especificamente para:
- Apostas pessoais em League of Legends
- Análise manual de value bets
- Gestão profissional de bankroll
- Previsões pós-draft de composições

---

**Desenvolvido para auxílio em apostas pessoais. Use com responsabilidade.**
