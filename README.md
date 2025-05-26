# 🎮 BOT LOL V3 ULTRA AVANÇADO

Sistema completo de análise e value betting para League of Legends com alertas automáticos e agenda de partidas.

## 🚀 Funcionalidades Principais

### 📊 **Sistema de Monitoramento**
- ✅ **Monitoramento 24/7** - Sistema ativo em background
- ✅ **Detecção automática** - Preparado para API da Riot Games
- ✅ **Múltiplas ligas** - LCK, LPL, LEC, LCS, CBLOL, LJL, LCO, PCS
- ✅ **Health check** - Compatível com Railway e outros hosts

### 🚨 **Sistema de Alertas Automáticos**
- ✅ **Alertas em tempo real** - Notificações instantâneas para grupos
- ✅ **Anti-spam inteligente** - Máximo 1 alerta por tipo a cada 5-10 min
- ✅ **Configurações flexíveis** - EV mínimo, confiança, tipos de alerta
- ✅ **Inscrição por grupo** - Cada grupo pode se inscrever independentemente
- ✅ **Monitoramento contínuo** - Verificação a cada 1 minuto

### 📅 **Agenda de Partidas**
- ✅ **Próximas partidas** - Visualização de jogos agendados
- ✅ **Horários amigáveis** - "Em 2h30min", "Amanhã às 14:00"
- ✅ **Status visual** - Emojis indicando proximidade (🔴🟡🟢)
- ✅ **Informações completas** - Liga, torneio, stream
- ✅ **Atualização dinâmica** - Dados sempre atualizados

### 💰 **Sistema de Value Betting**
- ✅ **Unidades básicas** - Sistema profissional de gestão
- ✅ **Cálculo automático** - EV + Confiança = Unidades recomendadas
- ✅ **Gestão de risco** - Máximo 3 unidades por aposta
- ✅ **Análise detalhada** - Expected Value e probabilidades

### 🧠 **Análise Avançada**
- ✅ **Múltiplos fatores** - Rating, forma, draft, jogadores, meta
- ✅ **Base de dados completa** - Times, jogadores, champions, sinergias
- ✅ **Contexto de torneio** - Ajustes para playoffs, finais, etc.
- ✅ **Patch atual** - Meta 14.23 com champions atualizados

## 🔧 Status da API

### ⚠️ **Importante: Dados Reais vs Demonstração**

**FUNCIONALIDADES PRINCIPAIS (Aguardando API Real):**
- 🔍 **Partidas ao vivo** - Sistema preparado, aguardando API da Riot
- 🔍 **Agenda de partidas** - Estrutura pronta, aguardando dados reais
- 🔍 **Estatísticas ao vivo** - Framework implementado, aguardando API
- 🔍 **Alertas automáticos** - Sistema ativo, aguardando dados reais

**FUNCIONALIDADES ATIVAS:**
- ✅ **Sistema de unidades** - Totalmente funcional
- ✅ **Análise de value betting** - Cálculos matemáticos ativos
- ✅ **Gestão de alertas** - Inscrição/desinscrição funcionando
- ✅ **Interface completa** - Todos os comandos e menus ativos
- ✅ **Demonstrações** - Exemplos práticos disponíveis

**DEMONSTRAÇÕES DISPONÍVEIS:**
- 🎲 **Demo avançado** - Análise completa T1 vs Gen.G
- 🎲 **Demo value betting** - Exemplos de cálculo de unidades
- 🎲 **Demo composições** - Análise de draft e sinergias
- 🎲 **Demo times** - Performance detalhada dos times

## 📋 Comandos Disponíveis

### 🎯 **Comandos Principais**
```
/start - Iniciar o bot e ver menu principal
/help - Guia completo de funcionalidades
/partidas - Monitoramento de partidas ao vivo
/agenda ou /proximas - Próximas partidas agendadas
/stats - Estatísticas em tempo real
/value - Value betting com sistema de unidades
/portfolio - Dashboard do portfolio
/units - Informações sobre sistema de unidades
/tips - Dicas profissionais de betting
/demo - Demonstrações do sistema avançado
```

### 🚨 **Comandos de Alertas**
```
/alertas - Gerenciar sistema de alertas
/inscrever - Inscrever grupo para alertas automáticos
/desinscrever - Desinscrever grupo dos alertas
```

## 🎯 Sistema de Unidades

### 💰 **Configuração Padrão**
- **Unidade base:** R$ 100
- **Banca total:** R$ 10.000
- **Máximo por aposta:** 3 unidades
- **EV mínimo:** 3%
- **Confiança mínima:** 65%

### 📊 **Critérios de Cálculo**

**Expected Value (EV):**
- EV ≥8%: 2 unidades
- EV 5-8%: 1.5 unidades  
- EV 3-5%: 1 unidade
- EV <3%: 0.5 unidade

**Confiança:**
- ≥85%: 2 unidades
- 75-85%: 1.5 unidades
- 65-75%: 1 unidade
- <65%: 0.5 unidade

**Fórmula Final:**
```
Unidades = (EV_units + Conf_units) ÷ 2
Máximo: 3 unidades por aposta
```

## 🚨 Sistema de Alertas

### 🔔 **Tipos de Alertas**
- 🎮 **Partidas ao vivo** - Detecção automática de jogos
- 💰 **Value betting** - Oportunidades com EV ≥3%
- 🚨 **EV alto** - Alertas prioritários para EV ≥8%
- 📊 **Análises** - Estatísticas e probabilidades

### ⚙️ **Configurações**
- **Frequência:** Verificação a cada 1 minuto
- **Anti-spam:** Máximo 1 alerta por tipo a cada 5-10 min
- **EV mínimo:** 3.0% (configurável)
- **Confiança mínima:** 65% (configurável)

### 📱 **Como Usar**
1. Adicione o bot ao seu grupo
2. Torne o bot administrador
3. Use `/inscrever` no grupo
4. Aguarde as notificações automáticas

## 🎮 Ligas Monitoradas

### 🌍 **Cobertura Global**
- 🇰🇷 **LCK** - League of Legends Champions Korea
- 🇨🇳 **LPL** - League of Legends Pro League
- 🇪🇺 **LEC** - League of Legends European Championship
- 🇺🇸 **LCS** - League of Legends Championship Series
- 🇧🇷 **CBLOL** - Campeonato Brasileiro de League of Legends
- 🇯🇵 **LJL** - League of Legends Japan League
- 🇦🇺 **LCO** - League of Legends Circuit Oceania
- 🌏 **PCS** - Pacific Championship Series
- 🇫🇷 **LFL** - Ligue Française de League of Legends
- 🇩🇪 **Prime League** - Deutsche League of Legends

## 🧠 Análise Avançada

### 🎯 **Fatores Analisados**
- **Rating dos times** (25%) - Força geral e histórico
- **Forma recente** (20%) - Performance nas últimas partidas
- **Draft e composição** (15%) - Sinergias e meta fit
- **Skill individual** (15%) - Qualidade dos jogadores
- **Meta adaptation** (10%) - Adaptação ao patch atual
- **Head-to-head** (10%) - Histórico entre os times
- **Contexto torneio** (5%) - Importância da partida

### 📊 **Base de Dados**
- **Times:** T1, Gen.G, JDG, BLG, G2, Fnatic, C9, LOUD, etc.
- **Jogadores:** Faker, Chovy, Canyon, Zeus, Gumayusi, etc.
- **Champions:** Meta atual com sinergias e counters
- **Patches:** Atualizações e mudanças de meta

## 🛡️ Gestão de Risco

### 💡 **Dicas Profissionais**
- 💰 Nunca aposte mais de 5% da banca por dia
- 📊 Mantenha registro detalhado de todas as apostas
- 🔄 Reavalie unidades a cada 100 apostas
- 📈 Aumente unidades apenas com ROI >10%
- 🎯 Foque em partidas com EV >5%
- 🛡️ Diversifique entre diferentes ligas
- ⚠️ Evite apostas consecutivas no mesmo time

## 🔧 Instalação e Deploy

### 📋 **Requisitos**
```
python >= 3.8
python-telegram-bot >= 13.0
numpy
flask
requests
```

### 🚀 **Deploy Railway**
1. Fork este repositório
2. Conecte ao Railway
3. Configure as variáveis de ambiente:
   - `TELEGRAM_TOKEN`: Token do bot
   - `OWNER_ID`: ID do proprietário
4. Deploy automático

### ⚙️ **Variáveis de Ambiente**
```bash
TELEGRAM_TOKEN=seu_token_aqui
OWNER_ID=seu_id_aqui
```

## 📈 Roadmap

### 🔄 **Próximas Implementações**
- [ ] **API da Riot Games** - Integração completa
- [ ] **Dados de odds** - Casas de apostas reais
- [ ] **Machine Learning** - Predições mais precisas
- [ ] **Dashboard web** - Interface visual
- [ ] **Histórico de apostas** - Tracking completo
- [ ] **Múltiplas moedas** - USD, EUR, etc.

### 🎯 **Melhorias Planejadas**
- [ ] **Análise de meta** - Patches automáticos
- [ ] **Alertas personalizados** - Filtros avançados
- [ ] **API própria** - Endpoints para desenvolvedores
- [ ] **Mobile app** - Aplicativo nativo
- [ ] **Integração Discord** - Suporte a servidores

## 📞 Suporte

### 🆘 **Status Atual**
- ✅ **API da Riot Games integrada** - Endpoints oficiais implementados
- 🔄 **Sistema híbrido** - API oficial + dados estáticos como fallback
- ⚠️ Dados de odds aguardando integração
- ⚠️ Algumas funcionalidades em modo demonstração

### 💬 **Contato**
- 📧 Email: suporte@botlol.com
- 💬 Telegram: @BotLoLSupport
- 🐛 Issues: GitHub Issues

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

## 🔄 Changelog

### v3.0.2 - API da Riot Games Integrada (25/05/2025)
- ✅ **API oficial da Riot Games implementada** - Endpoints /getLive, /getSchedule, /getLeagues
- ✅ **Sistema híbrido inteligente** - API oficial como fonte primária + dados estáticos como fallback
- ✅ **Indicador de fonte** - Mostra se dados vêm da API oficial ou dados estáticos
- ✅ **Chave de API oficial** - Usando chave documentada: 0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z
- ✅ **Headers otimizados** - User-Agent e headers para máxima compatibilidade
- ✅ **Tratamento de erros robusto** - Fallback automático em caso de falha da API
- ✅ **Dependência aiohttp adicionada** - Para requisições assíncronas
- ✅ **Teste de integração criado** - Script test_riot_api_integrada.py

### v3.0.1 - Dados Reais Apenas
- ✅ **REMOÇÃO COMPLETA de dados fictícios** das funcionalidades principais
- ✅ **Alertas automáticos** agora aguardam apenas dados reais da API
- ✅ **Agenda de partidas** preparada para dados reais
- ✅ **Estatísticas ao vivo** aguardando API da Riot Games
- ✅ **Demonstrações mantidas** para testes e exemplos
- ✅ **Sistema preparado** para integração completa com API real

### v3.0.0 - Sistema Completo
- ✅ Sistema de alertas automáticos implementado
- ✅ Comando de agenda de partidas adicionado
- ✅ Sistema de unidades básicas funcional
- ✅ Análise avançada com múltiplos fatores
- ✅ Compatibilidade total com Railway

### v2.0.0 - Sistema de Unidades
- ✅ Sistema de value betting implementado
- ✅ Cálculo automático de unidades
- ✅ Gestão de risco avançada
- ✅ Portfolio management

### v1.0.0 - Base do Sistema
- ✅ Bot Telegram funcional
- ✅ Comandos básicos
- ✅ Interface com botões
- ✅ Health check system

---

**🎮 Bot LoL V3 Ultra Avançado - Sua ferramenta profissional para value betting em League of Legends!** 