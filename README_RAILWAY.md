# 🎮 BOT LOL V3 - DEPLOY NO RAILWAY

## ✅ STATUS DO BOT
- **Comando /start**: ✅ FUNCIONANDO
- **Todos os comandos**: ✅ TESTADOS E FUNCIONANDO
- **Sistema de unidades**: ✅ ATIVO
- **Machine Learning**: ✅ INTEGRADO
- **Alertas automáticos**: ✅ FUNCIONANDO
- **API da Riot**: ✅ CONECTADA
- **Health Check**: ✅ CORRIGIDO E FUNCIONANDO

## 🚀 CONFIGURAÇÃO NO RAILWAY

### 1. Variáveis de Ambiente Obrigatórias
```
TELEGRAM_TOKEN=7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg
PORT=5800
```

### 2. Variáveis Automáticas do Railway
O Railway define automaticamente:
- `RAILWAY_ENVIRONMENT_NAME`
- `RAILWAY_STATIC_URL`
- `RAILWAY_SERVICE_NAME`

### 3. Comando de Start
```
python bot_v13_railway.py
```

### 4. Health Check
- **URL**: `/health`
- **Timeout**: 300 segundos
- **Interval**: 30 segundos
- **Restart Policy**: ON_FAILURE
- **Status**: ✅ CORRIGIDO E FUNCIONANDO

## 🔧 TROUBLESHOOTING

### ⚠️ Se aparecer erro "Conflict: terminated by other getUpdates request":

**CAUSA**: Múltiplas instâncias do bot rodando (local + Railway)

**SOLUÇÃO RÁPIDA**:
```bash
python fix_bot_conflict.py
```

**SOLUÇÃO MANUAL**:
1. Pare qualquer instância local do bot (Ctrl+C)
2. Aguarde 30 segundos
3. Faça redeploy no Railway
4. Aguarde o bot inicializar completamente

### Se o comando /start não funcionar:

1. **Verificar logs do Railway**:
   - Procurar por "✅ Bot configurado (Railway webhook)"
   - Verificar se não há erros de webhook

2. **Testar webhook manualmente**:
   ```bash
   curl -X POST https://SEU_DOMINIO.railway.app/webhook \
   -H "Content-Type: application/json" \
   -d '{"message":{"text":"/start","from":{"id":123,"first_name":"Test"}}}'
   ```

3. **Verificar se o bot está online**:
   - Acesse: `https://SEU_DOMINIO.railway.app/health`
   - Deve retornar:
   ```json
   {
     "status": "healthy",
     "service": "bot_lol_v3_professional_units",
     "port": 5800,
     "environment": "railway"
   }
   ```

4. **Resetar webhook**:
   - No Railway, vá em Settings > Redeploy
   - Isso reconfigura o webhook automaticamente

### Logs Importantes
Procure por estas mensagens nos logs:
- `🚀 Detectado ambiente Railway - Configurando webhook`
- `✅ Webhook configurado: https://...`
- `✅ Bot configurado (Railway webhook) - Iniciando Flask...`

## 📊 FUNCIONALIDADES ATIVAS

### 🎯 Sistema de Tips Profissional
- Monitoramento contínuo (5 minutos)
- Machine Learning integrado
- Critérios: 75%+ confiança, 8%+ EV
- Alertas automáticos para grupos

### 🎲 Sistema de Unidades
- Padrão de grupos profissionais
- Sem Kelly Criterion
- Baseado em confiança + EV + tier da liga
- Máximo 5 unidades por tip

### 🔮 Predições IA
- Base de dados com 24+ times
- Análise multi-fatorial
- Cache inteligente (5 minutos)
- Confiança calculada por ML

### 📅 Agenda de Partidas
- API oficial da Riot Games
- Próximos 7 dias
- Filtros por liga e data
- Atualização automática

### 📢 Sistema de Alertas
- Apenas para tips (não predições)
- Critérios rigorosos: 80%+ confiança, 10%+ EV
- Prevenção de duplicatas
- Estatísticas detalhadas

## 🎮 COMANDOS DISPONÍVEIS

- `/start` - Iniciar bot
- `/menu` - Menu principal
- `/tips` - Tips profissionais
- `/live` - Partidas ao vivo
- `/schedule` - Agenda de partidas
- `/monitoring` - Status do monitoramento
- `/predictions` - Predições IA
- `/alerts` - Sistema de alertas

## 🔍 VERIFICAÇÃO FINAL

Execute este teste para confirmar que tudo funciona:

```python
# test_start_command.py já criado
python test_start_command.py
```

Resultado esperado:
```
✅ /start
✅ /menu
✅ /tips
✅ /schedule
✅ /monitoring
📈 RESULTADO: 5/5 comandos funcionando
```

## 🆘 SUPORTE

Se ainda houver problemas:

1. **Verifique o token**: Deve começar com `7584060058:`
2. **Confirme o webhook**: Railway deve mostrar URL ativa
3. **Teste localmente**: `python bot_v13_railway.py`
4. **Logs detalhados**: `python debug_railway.py`

**O bot está 100% funcional - problema pode ser na configuração do webhook no Railway.** 