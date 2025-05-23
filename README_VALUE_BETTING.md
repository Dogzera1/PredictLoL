# 🔥 Sistema de Value Betting Automático

## 📋 Visão Geral

O **Sistema de Value Betting Automático** é uma funcionalidade inovadora do Bot LoL V3 que detecta apostas de valor em tempo real durante partidas ao vivo. O sistema monitora continuamente todas as partidas, comparando as probabilidades calculadas pela nossa IA com as odds do mercado para identificar oportunidades lucrativas.

## 🎯 Como Funciona

### **Detecção Automática**
- 🔍 Monitora **TODAS** as partidas ao vivo a cada 2 minutos
- 📊 Compara probabilidades da IA vs odds simuladas do mercado
- 💰 Detecta quando há discrepância significativa (edge ≥ 15%)
- 🚨 Envia notificações automáticas para usuários inscritos

### **Critérios de Value Bet**
```python
# Uma aposta é considerada "de valor" quando:
probabilidade_real >= 55%  # Mínimo 55% de chance
odds_atuais >= 1.5         # Odds mínimas de 1.5x
edge >= 15%                # Vantagem mínima de 15%
```

## ⚡ Níveis de Urgência

### 🔥 **ALTA URGÊNCIA**
- Edge: +25% ou mais
- Probabilidade: 70%+ 
- **Ação:** Apostar imediatamente

### ⚡ **MÉDIA URGÊNCIA** 
- Edge: +20% a +24%
- Probabilidade: 60%+ 
- **Ação:** Apostar com cautela

### 💡 **BAIXA URGÊNCIA**
- Edge: +15% a +19%
- Probabilidade: 55%+ 
- **Ação:** Considerar aposta

## 🛠️ Componentes Técnicos

### **1. ValueBetDetector**
```python
class ValueBetDetector:
    - Analisa partidas em busca de value bets
    - Calcula edge e urgência
    - Filtra oportunidades válidas
```

### **2. OddsSimulator** 
```python
class OddsSimulator:
    - Simula odds dinâmicas em tempo real
    - Aplica flutuações baseadas no momentum
    - Mantém ranges realistas (1.1x - 5.0x)
```

### **3. LiveValueBetMonitor**
```python
class LiveValueBetMonitor:
    - Executa em background 24/7
    - Ciclos de análise a cada 2 minutos
    - Coleta estatísticas e logs
```

### **4. ValueBetNotificationSystem**
```python
class ValueBetNotificationSystem:
    - Gerencia inscrições de usuários
    - Envia notificações em tempo real
    - Previne spam com cache inteligente
```

## 📱 Interface do Usuario

### **Comandos Telegram**
```
/subscribe    - Ativar notificações
/unsubscribe  - Cancelar notificações  
/valuestats   - Ver estatísticas
```

### **Botões Interface**
- 🔥 **VALUE BETS** - Configurar sistema
- 📊 **Stats Value** - Ver estatísticas  
- ✅ **Ativar Notificações** - Inscrever-se
- ❌ **Cancelar Inscrição** - Desinscrever-se

## 📊 Exemplo de Notificação

```
🔥 VALUE BET DETECTADA!

🎯 T1 vs Gen.G
🏆 Liga: LCK  
⏱️ Tempo: 23:45

📊 ANÁLISE:
• Probabilidade: 72%
• Odds Atuais: 1.8x
• Edge: +27%
• Confiança: alta

💰 REASONING:
Probabilidade real: 72% vs Odds implicam: 56% (Edge: 27%)

🚨 URGÊNCIA: ALTA

⚠️ Aposte com responsabilidade
🔄 Odds podem mudar rapidamente
```

## 🔧 Configuração e Uso

### **1. Ativação no Bot**
```python
# O sistema é inicializado automaticamente quando o bot inicia
if VALUE_BETTING_AVAILABLE:
    await initialize_value_bet_system(bot, riot_api, prediction_system)
```

### **2. Inscrição de Usuários**
- Use o menu "🔥 VALUE BETS" 
- Clique em "✅ Ativar Notificações"
- Receba alerts em tempo real!

### **3. Personalização**
```python
# Parâmetros ajustáveis no código:
value_threshold = 0.15      # Edge mínimo (15%)
min_probability = 0.55      # Prob mínima (55%)
max_odds_threshold = 1.5    # Odds mínimas (1.5x)
check_interval = 120        # Intervalo (2 min)
```

## 📈 Estatísticas em Tempo Real

### **Métricas Monitoradas**
- 🎯 Value Bets Encontradas
- 📱 Notificações Enviadas  
- 🔍 Partidas Analisadas
- 👥 Usuários Inscritos
- 📈 Taxa de Detecção
- ⚙️ Status do Sistema

### **Logs Automáticos**
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "match_id": "lck_match_123", 
  "team": "T1",
  "league": "LCK",
  "probability": 0.72,
  "odds": 1.8,
  "edge": 0.27,
  "urgency": "alta"
}
```

## 🧪 Teste do Sistema

### **Executar Testes**
```bash
python test_value_betting.py
```

### **Saída Esperada**
```
🚀 INICIANDO TESTES DO SISTEMA VALUE BETTING
🔥 TESTANDO SISTEMA DE VALUE BETTING
✅ Componentes inicializados
🔍 Analisando partida para value bets...
💰 Value Bets Encontradas: 1
🎯 VALUE BET #1:
   Team: T1
   Probabilidade: 72%
   Odds: 1.8x
   Edge: +27%
   Urgência: alta
```

## ⚠️ Considerações Importantes

### **Responsabilidade**
- 🚨 **Aposte sempre com responsabilidade**
- 💰 **Nunca aposte mais do que pode perder** 
- 📊 **Use múltiplas fontes para confirmar**
- ⏰ **Odds mudam rapidamente**

### **Limitações**
- 🎲 Odds são simuladas (não reais)
- 📊 System baseado em probabilidades, não garantias
- 🔄 Requer internet estável para monitoramento
- ⚡ Notificações dependem do Telegram

### **Melhorias Futuras**
- 🏪 Integração com casas de apostas reais
- 📱 App mobile dedicado
- 🤖 ML para otimizar thresholds
- 📊 Dashboard web com gráficos

## 🚀 Roadmap

### **Versão 1.0** ✅
- [x] Detecção básica de value bets
- [x] Notificações automáticas
- [x] Interface Telegram  
- [x] Logging e estatísticas

### **Versão 1.1** 🚧
- [ ] Integração odds reais
- [ ] Filtros personalizáveis
- [ ] Histórico de performance
- [ ] API REST para external access

### **Versão 2.0** 📋
- [ ] Machine Learning para predições
- [ ] Dashboard web
- [ ] Mobile app
- [ ] Multi-idiomas

## 💡 Dicas de Uso

### **Para Iniciantes**
1. 📚 Entenda o conceito de value betting
2. 🎯 Comece com apostas pequenas
3. 📊 Monitore estatísticas regularmente
4. 🕰️ Seja paciente - value bets são raras

### **Para Avançados**  
1. 🔍 Analise patterns nos alerts
2. 📈 Compare com outras fontes
3. ⚡ Aja rapidamente em odds altas
4. 📊 Mantenha bankroll management

---

## 🔗 Links Úteis

- 📖 [Documentação Completa](README.md)
- 🤖 [Bot Principal](main_v3_riot_integrated.py)
- 🧪 [Testes](test_value_betting.py)
- 📊 [Sistema Value Betting](value_bet_system.py)

---

**🎉 O sistema está pronto para detectar value bets em tempo real!**

**💰 Aposte com responsabilidade e boa sorte!** 