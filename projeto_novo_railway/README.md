# 🤖 BOT LOL V3 ULTRA AVANÇADO - PROJETO NOVO

## 🚀 Projeto Railway Limpo
**Criado:** 28/05/2025  
**Motivo:** Instância anterior com problema 502 persistente

## ✅ Funcionalidades

### 🎯 Tips Profissionais
- Sistema de unidades padrão de apostas profissionais
- Análise baseada em dados reais da Riot API
- Confidence score e Expected Value (EV)
- Monitoramento automático 24/7

### 📅 Agenda de Partidas
- Partidas ao vivo e agendadas
- Dados reais da API oficial da Riot Games
- Múltiplas ligas: LCK, LPL, LEC, LCS, CBLOL, etc.
- Horários localizados

### 🔮 Predições IA
- Algoritmo baseado em performance real dos times
- Análise de forma atual e histórico
- Ajustes por região e meta atual
- Cache inteligente para performance

### 📢 Sistema de Alertas
- Alertas automáticos para grupos registrados
- Filtros por confidence e league tier
- Prevenção de spam (max 3 alertas/hora)
- Estatísticas detalhadas

## 🔧 Configuração Railway

### 1. Variáveis de Ambiente Necessárias
```env
TELEGRAM_TOKEN=seu_token_aqui
OWNER_ID=seu_id_aqui
```

### 2. Deploy
1. Criar novo projeto Railway
2. Conectar com repositório Git
3. Configurar variáveis de ambiente
4. Deploy automático

### 3. Verificação
- Health check: `https://seu-app.railway.app/health`
- Webhook será configurado automaticamente

## 📋 Comandos Disponíveis

- `/start` - Iniciar bot e menu principal
- `/tips` - Obter tip profissional atual
- `/live` - Partidas ao vivo
- `/schedule` - Agenda de partidas
- `/predictions` - Predições IA
- `/alerts` - Sistema de alertas
- `/monitoring` - Status do monitoramento

## 🔍 Características Técnicas

- **Framework:** python-telegram-bot v13.15
- **API:** Riot Games oficial
- **Hosting:** Railway
- **Builder:** Nixpacks
- **Health Check:** Integrado
- **Webhook:** Configuração automática

## 📝 Notas Importantes

1. ✅ **Dados 100% reais** - Sem simulações
2. ✅ **Sistema anti-conflitos** - Instância única
3. ✅ **Health check** - Monitoramento Railway
4. ✅ **Error handling** - Recuperação automática
5. ✅ **Logs detalhados** - Debug facilitado

## 🚨 Troubleshooting

### Health Check Falha
1. Verificar logs do Railway
2. Confirmar variáveis de ambiente
3. Verificar se porta está configurada

### Webhook Não Funciona
1. Verificar TELEGRAM_TOKEN
2. Confirmar URL pública do Railway
3. Verificar logs do bot

### Bot Não Responde
1. Verificar OWNER_ID
2. Confirmar que bot está ativo no BotFather
3. Verificar conflitos de instância 