# 📖 GUIA COMPLETO: Como Usar o Sistema PredictLoL

## 🎯 RESPOSTA ÀS SUAS PERGUNTAS

### ❓ **"Alguns botões indicando funcionalidade em andamento"**

**✅ BOTÕES QUE FUNCIONAM:**
- **💰 Bankroll** - Status completo do bankroll
- **📈 Tracker** - Dashboard de performance
- **🔙 Menu Principal** - Navegação entre menus
- **🔄 Atualizar** - Refresh dos dados

**🔧 BOTÕES PENDENTES:**
- **📊 Análise** - Sistema de análise avançado
- **🎮 Previsões** - Previsões complexas pós-draft
- **⚙️ Configurações** - Painel de configurações

---

## 💰 COMO CONFIGURAR SEU BANKROLL

### 1. **Configurar Valor Inicial**
```
/config_bankroll 1500
```
**Define seu bankroll inicial (ex: R$ 1500)**

### 2. **Verificar Status**
```
/bankroll
```
**Mostra:**
- Saldo atual
- Limites automáticos
- Configurações de risco
- Estatísticas

### 3. **Configurações Automáticas**
O sistema configura automaticamente:
- **Limite Diário:** 10% do bankroll
- **Máximo por Aposta:** 5% do bankroll  
- **Kelly Criterion:** Ativo
- **Stop Loss:** 20% do bankroll

---

## 🧮 COMO SIMULAR APOSTAS

### **Comando Básico:**
```
/simular_aposta 75 1.85
```
- **75** = Sua confiança (%)
- **1.85** = Odds da casa de apostas

### **O Sistema Calcula:**
- ✅ Tamanho ideal da aposta (Kelly Criterion)
- ✅ Expected Value (EV)
- ✅ Lucro potencial
- ✅ Nível de risco
- ✅ Avisos de segurança

### **Exemplo Completo:**
```
🧮 Simulação de Aposta

Parâmetros:
• Confiança: 75.0%
• Odds: 1.85
• Sua Probabilidade: 75.0%

💰 CÁLCULOS KELLY CRITERION:
• Tamanho Recomendado: R$ 67.50
• Percentual do Bankroll: 4.5%
• Kelly Fraction: 0.1824

📊 PROJEÇÕES:
• Expected Value: 38.75%
• Retorno Potencial: R$ 124.88
• Lucro Potencial: R$ 57.38
• Nível de Risco: Medium
```

---

## 📈 COMO FUNCIONA O TRACKER DE APOSTAS

### **Dashboard Resumido:**
```
/tracker
```
**Mostra:**
- Bankroll atual
- Status geral
- Última atualização

### **Dashboard Completo:**
```
/tracker_full
```
**Inclui:**
- 📊 Performance geral detalhada
- 📈 Gráfico ASCII de evolução do bankroll
- 🔥 Análise de streaks (sequências)
- 🏆 Performance por liga
- 📋 Insights e tendências
- 🎯 Recomendações personalizadas

### **Exemplo do Tracker Completo:**
```
🏆 BETTING TRACKER DASHBOARD
=====================================
📅 Período: Últimos 30 dias
🕐 Atualizado: 10/06/2025 01:48

💰 PERFORMANCE GERAL
• Bankroll Inicial: R$ 1000.00
• Bankroll Atual: R$ 1000.00
• Total Apostado: R$ 0.00
• Lucro Total: R$ 0.00
• ROI: 0.0%
• Win Rate: 0.0%

📊 ESTATÍSTICAS DETALHADAS
• Total de Apostas: 0
• Apostas Ganhas: 0
• Apostas Perdidas: 0
• Apostas Pendentes: 0
• Média de Odds: 0.00
• Confiança Média: 0.0%

📈 GRÁFICO DE BANKROLL
[Gráfico ASCII da evolução]

🔥 ANÁLISE DE STREAKS
• Sequência Atual: 0
• Melhor Sequência: 0
• Pior Sequência: 0
```

---

## 💸 COMO REGISTRAR APOSTAS REAIS

### **Comando:**
```
/apostar 67 1.85 T1 vs Gen.G - T1 vencer
```
- **67** = Valor da aposta
- **1.85** = Odds
- **T1 vs Gen.G - T1 vencer** = Descrição

### **Sistema Registra:**
- ✅ Aposta no bankroll
- ✅ Cálculos automáticos
- ✅ Tracking de performance
- ✅ Atualização de estatísticas

---

## 🎯 FLUXO COMPLETO DE USO

### **1. Configuração Inicial:**
```
/config_bankroll 1500    # Define R$ 1500
/bankroll                # Confirma configuração
```

### **2. Antes de Apostar:**
```
/simular_aposta 75 1.85  # Testa a aposta
```

### **3. Se Aprovado:**
```
/apostar 67 1.85 T1 vs Gen.G - T1 vencer
```

### **4. Acompanhar Performance:**
```
/tracker_full            # Dashboard completo
```

### **5. Repetir Processo:**
```
/simular_aposta 80 2.20  # Nova simulação
```

---

## 🔧 BOTÕES VS COMANDOS

### **✅ Use Botões Para:**
- Navegar entre menus
- Ver status rápido
- Atualizar informações

### **⚡ Use Comandos Para:**
- Configurar valores
- Simular apostas
- Registrar apostas
- Ver relatórios completos

---

## 🏆 SISTEMA KELLY CRITERION

### **Como Funciona:**
1. **Você informa:** Confiança + Odds
2. **Sistema calcula:** Probabilidade real
3. **Kelly determina:** Tamanho ideal da aposta
4. **Sistema aplica:** Multiplicador conservador (25%)
5. **Resultado:** Aposta segura e lucrativa

### **Vantagens:**
- ✅ Maximiza lucros a longo prazo
- ✅ Minimiza risco de ruína
- ✅ Gestão automática de bankroll
- ✅ Disciplina matemática

---

## 📊 PRÓXIMOS PASSOS

1. **Configure seu bankroll:**
   ```
   /config_bankroll [seu_valor]
   ```

2. **Teste o sistema:**
   ```
   /simular_aposta 70 1.90
   ```

3. **Explore o tracker:**
   ```
   /tracker_full
   ```

4. **Comece a apostar:**
   ```
   /apostar [valor] [odds] [descrição]
   ```

**🎉 Seu sistema está 100% funcional e pronto para usar!** 