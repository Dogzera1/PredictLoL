# 👥 Comandos de Grupo - Bot LoL V3 Ultra Avançado

## 📝 Visão Geral

O Bot LoL V3 Ultra Avançado agora suporta **alertas automáticos de tips em grupos do Telegram**! Grupos podem receber tips profissionais de League of Legends baseadas em análise de IA e Machine Learning.

---

## 🚀 Comandos Implementados

### 1. `/activate_group` - Ativar Alertas no Grupo

**Descrição:** Ativa alertas automáticos de tips no grupo atual.

**Quem pode usar:** Apenas administradores do grupo

**Como funciona:**
1. Admin digita `/activate_group` no grupo
2. Bot verifica se usuário é administrador
3. Mostra opções de tipos de subscrição
4. Admin escolhe tipo de alerta
5. Grupo começa a receber tips!

**Tipos de Subscrição Disponíveis:**
- 🔔 **Todas as Tips** - Recebe todas as tips geradas
- 💎 **Alto Valor** - Apenas tips com EV > 10%
- 🎯 **Alta Confiança** - Apenas tips com confiança > 80%
- 👑 **Premium** - Tips exclusivas (EV > 15% + Confiança > 85%)

### 2. `/group_status` - Status do Grupo

**Descrição:** Exibe informações detalhadas sobre o status do grupo.

**Quem pode usar:** Qualquer membro do grupo

**Informações mostradas:**
- Nome e ID do grupo
- Status dos alertas (ativo/inativo)
- Tipo de subscrição atual
- Número de tips recebidas
- Data de ativação
- Admin que configurou

### 3. `/deactivate_group` - Desativar Alertas

**Descrição:** Desativa os alertas automáticos no grupo.

**Quem pode usar:** Apenas administradores do grupo

**Resultado:** Grupo para de receber tips automáticas.

---

## 🔧 Funcionalidades Técnicas

### Verificação de Permissões
- ✅ Verifica automaticamente se usuário é admin
- ✅ Suporta grupos e supergrupos
- ✅ Tratamento de erros de permissão

### Sistema de Filtros
- ✅ Filtra tips por tipo de subscrição
- ✅ Aplica mesmos critérios de qualidade
- ✅ Evita spam com cache inteligente

### Tratamento de Erros
- ✅ Bot removido do grupo
- ✅ Permissões insuficientes
- ✅ Grupo não encontrado
- ✅ Rate limiting

### Estatísticas
- ✅ Estatísticas separadas para usuários e grupos
- ✅ Contagem de tips enviadas por grupo
- ✅ Subscrições por tipo

---

## ⚡ Como Usar no Seu Grupo

### Passo 1: Adicionar o Bot
1. Convide `@SeuBotLoLV3_bot` para o grupo
2. Dê permissões de **administrador** ao bot
3. Certifique-se que o bot pode enviar mensagens

### Passo 2: Ativar Alertas
1. Como admin, digite `/activate_group`
2. Escolha o tipo de subscrição desejado
3. Confirme a ativação

### Passo 3: Verificar Status
- Use `/group_status` para ver se está funcionando
- Aguarde as próximas tips automáticas!

### Passo 4: Gerenciar (Opcional)
- Use `/deactivate_group` para pausar
- Use `/activate_group` novamente para reconfigurar

---

## 📊 Exemplo de Uso

```
👤 Admin: /activate_group

🤖 Bot: 🔔 Ativar Alertas de Tips no Grupo

📋 Grupo: Meu Grupo LoL Tips
👤 Admin: João Silva

Escolha o tipo de alerta que o grupo receberá:

[🔔 Todas as Tips] [💎 Alto Valor]
[🎯 Alta Confiança] [👑 Premium]

👤 Admin: [Clica em "💎 Alto Valor"]

🤖 Bot: ✅ Alertas ativados no grupo!

📋 Grupo: Meu Grupo LoL Tips
📊 Tipo: Alto Valor (EV > 10%)
👤 Configurado por: João Silva

O grupo receberá tips automáticas conforme o tipo selecionado.
Use /group_status para ver detalhes.
```

---

## 🔍 Exemplo de Tip Recebida

```
🚀 TIP PROFISSIONAL LoL 🚀

🎮 T1 vs Gen.G
🏆 Liga: LCK Spring
⚡ Tip: T1 Moneyline
💰 Odds: 2.15

🔥🔥 Unidades: 3.0 (Risco Alto)
⏰ Tempo: Mid Game (22min)

📊 Análise:
📈 EV: +12.5%
🎯 Confiança: 78%
🤖 Fonte: ML + Algoritmos Heurísticos
⭐ Qualidade: 85%

🔥 Bot LoL V3 Ultra Avançado
```

---

## 📈 Benefícios para Grupos

### Para Comunidades de Apostas
- 🎯 Tips profissionais automáticas
- 📊 Análise baseada em IA
- 🔥 Apenas tips de alta qualidade
- ⚡ Entrega em tempo real

### Para Grupos de League of Legends
- 📈 Insights sobre partidas ao vivo
- 🤖 Análise técnica avançada
- 📋 Acompanhamento de ligas profissionais
- 🏆 Foco nas principais competições

### Para Admins
- ⚙️ Configuração simples
- 📊 Controle total sobre tipos de alerta
- 👥 Gerenciamento fácil
- 📈 Estatísticas detalhadas

---

## 🛡️ Segurança e Privacidade

- ✅ Apenas admins podem ativar/desativar
- ✅ Bot não armazena conversas do grupo
- ✅ Dados de grupo não são compartilhados
- ✅ Cumprimento da LGPD e GDPR
- ✅ Rate limiting para evitar spam

---

## 🚨 Limitações e Considerações

### Rate Limiting
- Máximo de 10 mensagens por hora por grupo
- Sistema anti-spam ativo
- Cache de tips para evitar duplicatas

### Tipos de Grupo Suportados
- ✅ Grupos privados
- ✅ Supergrupos
- ❌ Canais (não suportado)

### Permissões Necessárias
- Bot deve ser administrador
- Bot deve poder enviar mensagens
- Admin do grupo deve ativar

---

## 📞 Suporte

**Problemas ou dúvidas?**
- Use `/help` no bot para ajuda geral
- Verifique se o bot tem permissões corretas
- Confirme que você é admin do grupo
- Use `/group_status` para diagnóstico

**Status do Sistema:**
- Sistema 100% operacional
- Monitoramento 24/7 ativo
- APIs Riot e PandaScore integradas

---

**Desenvolvido com 💚 pela equipe Bot LoL V3**  
**Versão:** 3.1.0  
**Data:** Janeiro 2025  
**Status:** Produção ✅ 
