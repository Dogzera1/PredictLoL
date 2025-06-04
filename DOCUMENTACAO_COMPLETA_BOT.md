# 📚 DOCUMENTAÇÃO COMPLETA - Bot LoL V3 Ultra Avançado

## 🎯 **VISÃO GERAL DO SISTEMA**

**Bot de Tips Profissional para League of Legends** com sistema de unidades padrão de grupos profissionais, análise de partidas ao vivo, machine learning e integração com APIs oficiais.

### 🎮 **Especificações Técnicas:**
- **Versão:** V13 Railway
- **Foco:** Tips de Moneyline (ML) ao vivo para LoL
- **Sistema de Unidades:** Padrão profissional (0.5-5.0 unidades)
- **Dados:** 100% API oficial Riot Games + The Odds API
- **Machine Learning:** Sistema dinâmico com fallback algorítmico
- **Cobertura:** Global incluindo LPL, LCK, LEC, LCS, CBLOL, etc.

---

## 🏗️ **ARQUITETURA DO SISTEMA**

### 📦 **Classes Principais:**

1. **`ProfessionalUnitsSystem`** - Sistema de gestão de bankroll
2. **`RiotAPIClient`** - Integração com API oficial da Riot
3. **`TheOddsAPIClient`** - Gestão de odds de casas de apostas
4. **`LoLUserPreferences`** - Preferências e filtros do usuário
5. **`LoLGameAnalyzer`** - Análise de eventos cruciais de jogo
6. **`DynamicPredictionSystem`** - Sistema de predição ML + algoritmos
7. **`TelegramAlertsSystem`** - Sistema de alertas automáticos
8. **`ScheduleManager`** - Gestão de cronograma de partidas
9. **`ProfessionalTipsSystem`** - Sistema de tips profissionais
10. **`LoLBotV3UltraAdvanced`** - Interface principal do bot

---

## 💰 **1. SISTEMA DE UNIDADES PROFISSIONAIS**

### 📊 **Classe: `ProfessionalUnitsSystem`**

#### **🎯 Propósito:**
Sistema de gestão de bankroll baseado no padrão de grupos profissionais de apostas esportivas.

#### **⚙️ Funcionalidades:**

**`__init__(bankroll=1000.0)`**
- **Função:** Inicializa o sistema com bankroll base
- **Cálculo:** 1 unidade = 1% do bankroll
- **Escala:** 0.5 a 5.0 unidades conforme confiança/EV

**`calculate_units(confidence, ev_percentage, league_tier)`**
- **Entrada:** Confiança (%), EV (%), tier da liga
- **Saída:** Unidades calculadas + justificativa
- **Lógica:**
  - 90%+ confiança + 15%+ EV = 5.0 unidades (Risco Muito Alto)
  - 85%+ confiança + 12%+ EV = 4.0 unidades (Risco Alto)
  - 80%+ confiança + 10%+ EV = 3.0 unidades (Risco Alto)
  - 75%+ confiança + 8%+ EV = 2.5 unidades (Risco Médio-Alto)
  - 70%+ confiança + 6%+ EV = 2.0 unidades (Risco Médio)
  - 65%+ confiança + 5%+ EV = 1.0 unidades (Risco Baixo)
  - Mínimo absoluto = 0.5 unidades

**`_get_units_reasoning(confidence, ev_percentage, league_tier)`**
- **Função:** Gera explicação detalhada do cálculo de unidades
- **Saída:** Texto justificando a quantidade de unidades

**`get_units_explanation()`**
- **Função:** Retorna explicação completa do sistema de unidades
- **Conteúdo:** Metodologia profissional, escalas, exemplos

---

## 🌐 **2. CLIENTE API RIOT GAMES**

### 📡 **Classe: `RiotAPIClient`**

#### **🎯 Propósito:**
Interface para buscar dados oficiais de partidas LoL da API da Riot Games.

#### **⚙️ Funcionalidades:**

**`__init__()`**
- **Setup:** Configuração de URLs base e headers
- **Endpoints:** URLs oficiais da Riot para diferentes regiões

**`get_live_matches()`** ⭐ **PRINCIPAL**
- **Função:** Busca partidas ao vivo de todas as regiões
- **Cobertura:** 16 endpoints diferentes incluindo:
  - Global (en-US, pt-BR)
  - China/LPL (zh-CN)
  - Coreia/LCK (ko-KR)
  - Europa/LEC (en-GB)
  - América/LCS, CBLOL (pt-BR, es-ES)
- **Anti-duplicatas:** Sistema de deduplicação baseado em times
- **Validação:** Apenas partidas status 'inprogress', 'live', 'ongoing'

**`get_live_matches_with_details()`**
- **Função:** Busca partidas + detalhes completos
- **Dados:** Draft, estatísticas, tempo de jogo, eventos

**`_get_match_details(match)`**
- **Função:** Obtém dados detalhados de uma partida específica
- **Dados:** Champions picked/banned, gold, kills, objetivos

**`_extract_live_matches_only(data)`**
- **Função:** Filtra apenas partidas AO VIVO dos dados da API
- **Validação:** Status, times válidos, ligas reconhecidas

**`_extract_teams(event)` / `_extract_league(event)`**
- **Função:** Extrai informações de times e ligas dos dados da API
- **Tratamento:** Normalização de nomes, códigos, regiões

---

## 🎰 **3. CLIENTE THE ODDS API**

### 💸 **Classe: `TheOddsAPIClient`**

#### **🎯 Propósito:**
Integração com casas de apostas para obter odds reais de Moneyline (ML).

#### **⚙️ Funcionalidades:**

**`get_esports_odds(region="us")`**
- **Função:** Busca odds de eSports de múltiplas casas
- **Casas:** Bet365, Pinnacle, Betfair, DraftKings, etc.
- **Filtro:** Apenas jogos League of Legends

**`get_match_odds(team1, team2, league="")`**
- **Função:** Busca odds específicas para uma partida
- **Matching:** Sistema inteligente de correspondência de nomes
- **Cache:** Sistema de cache para otimizar requisições

**`_teams_match(team_name, api_team_name)`**
- **Função:** Algoritmo de matching de nomes de times
- **Lógica:** Similaridade, abreviações, sinônimos
- **Flexibilidade:** Lida com variações de nomenclatura

**`_process_match_odds(game_data, team1, team2)`**
- **Função:** Processa e normaliza dados de odds
- **Saída:** Odds formatadas, casas de apostas, spreads

**`get_odds_summary()`**
- **Função:** Relatório consolidado de todas as odds disponíveis
- **Métricas:** Melhor odd, odd média, número de casas

---

## 👤 **4. SISTEMA DE PREFERÊNCIAS DO USUÁRIO**

### ⚙️ **Classe: `LoLUserPreferences`**

#### **🎯 Propósito:**
Gestão de preferências personalizadas dos usuários.

#### **⚙️ Funcionalidades:**

**`set_favorite_teams(user_id, teams)`**
- **Função:** Define times favoritos do usuário
- **Uso:** Alertas personalizados, notificações prioritárias

**`set_league_filter(user_id, leagues)`**
- **Função:** Configura filtro de ligas de interesse
- **Opções:** LPL, LCK, LEC, LCS, CBLOL, Worlds, MSI, etc.

**`get_user_preferences(user_id)`**
- **Função:** Retorna todas as preferências do usuário
- **Dados:** Times favoritos, ligas, configurações de alerta

**`should_notify_user(user_id, match)`**
- **Função:** Decide se deve notificar usuário sobre uma partida
- **Lógica:** Times favoritos, ligas filtradas, horários

---

## 🎮 **5. ANALISADOR DE JOGOS LOL**

### 🔍 **Classe: `LoLGameAnalyzer`**

#### **🎯 Propósito:**
Análise de eventos cruciais e momentos decisivos de partidas LoL.

#### **⚙️ Funcionalidades:**

**`analyze_crucial_events(match)`**
- **Função:** Identifica eventos cruciais da partida
- **Eventos Analisados:**
  - 🐉 **Dragões:** Alma dragão, dragão ancião
  - 🦅 **Barão:** Nashor, vantagem em teamfights
  - 🏰 **Torres:** Inibidores, Nexus towers
  - ⚔️ **Teamfights:** Aces, picks importantes
  - 💰 **Ouro:** Diferenças significativas
  - 🏆 **Objetivos:** Controle de mapa

**`_calculate_timing_score(game_time, events)`**
- **Função:** Calcula pontuação de timing baseada no tempo de jogo
- **Lógica:** Eventos early/mid/late game têm pesos diferentes
- **Saída:** Score de 0-100 indicando timing da tip

---

## 🤖 **6. SISTEMA DE PREDIÇÃO DINÂMICA**

### 🧠 **Classe: `DynamicPredictionSystem`**

#### **🎯 Propósito:**
Sistema híbrido ML + algoritmos para predições de Moneyline.

#### **⚙️ Funcionalidades:**

**`predict_live_match(match)`** ⭐ **PRINCIPAL**
- **Função:** Predição principal usando ML ou fallback algorítmico
- **Entrada:** Dados da partida ao vivo
- **Saída:** Probabilidade de vitória, confiança, análise

**`predict_live_match_with_live_data(match)`**
- **Função:** Predição aprimorada com dados em tempo real
- **Dados extras:** Draft, estatísticas, tempo de jogo
- **Precisão:** Maior precisão com dados live

**`_adjust_prediction_with_live_data(base_prediction, draft_data, match_stats, game_time)`**
- **Função:** Ajusta predição base com dados ao vivo
- **Fatores:**
  - **Draft:** Composição dos times, synergias
  - **Estatísticas:** Gold, kills, CS, vision
  - **Tempo:** Early/mid/late game advantages
  - **Objetivos:** Dragões, Barão, torres

**`_predict_with_algorithms(match)`**
- **Função:** Sistema de fallback algorítmico
- **Dados:** Histórico de times, forma recente, head-to-head
- **Confiabilidade:** Backup quando ML não disponível

**`_get_team_data(team_name, league)`**
- **Função:** Busca dados históricos de um time
- **Métricas:** Winrate, forma recente, performance por liga

**`_calculate_live_odds_from_data(match, favored_team)`**
- **Função:** Calcula odds teóricas baseadas na análise
- **Uso:** Comparação com odds reais para calcular EV

---

## 📢 **7. SISTEMA DE ALERTAS TELEGRAM**

### 📲 **Classe: `TelegramAlertsSystem`**

#### **🎯 Propósito:**
Sistema automatizado de envio de tips para grupos registrados.

#### **⚙️ Funcionalidades:**

**`send_tip_alert(tip, bot_application)`** ⭐ **PRINCIPAL**
- **Função:** Envia tip formatada para todos os grupos registrados
- **Formato:** Emoji, teams, odds, unidades, raciocínio
- **Template:**
  ```
  🔥 **TIP PROFISSIONAL LoL** 🔥
  
  🎮 **Team A vs Team B**
  🏆 **Liga:** LPL
  ⚡ **Tip:** Team A ML
  💰 **Odds:** 1.85
  📊 **Unidades:** 3.0 (Risco Alto)
  ⏰ **Tempo:** 25min
  
  📈 **Análise:**
  [Raciocínio detalhado...]
  
  🎯 **EV:** +12.5% | **Confiança:** 85%
  ```

**`add_group(chat_id)` / `remove_group(chat_id)`**
- **Função:** Gestão de grupos registrados para alertas
- **Persistência:** Salva lista de grupos ativos

**`_should_send_alert(tip)`**
- **Função:** Decide se uma tip merece ser enviada
- **Critérios:** Qualidade, EV mínimo, confiança, timing

**`get_alert_stats()`**
- **Função:** Estatísticas do sistema de alertas
- **Métricas:** Tips enviadas, grupos ativos, performance

---

## 📅 **8. GERENCIADOR DE CRONOGRAMA**

### 🗓️ **Classe: `ScheduleManager`**

#### **🎯 Propósito:**
Gestão de cronograma de partidas futuras e agendadas.

#### **⚙️ Funcionalidades:**

**`get_scheduled_matches(days_ahead=7)`**
- **Função:** Busca partidas agendadas para os próximos dias
- **Filtro:** Por data, liga, região
- **Ordenação:** Cronológica por data de início

**`get_matches_today()`**
- **Função:** Retorna apenas partidas do dia atual
- **Uso:** Comando /proximosjogoslol

**`_remove_duplicates(matches)`**
- **Função:** Remove partidas duplicadas do cronograma
- **Lógica:** Baseado em times + horário + liga

---

## 🎯 **9. SISTEMA DE TIPS PROFISSIONAIS**

### ⭐ **Classe: `ProfessionalTipsSystem`**

#### **🎯 Propósito:**
Motor principal de geração e monitoramento de tips profissionais.

#### **⚙️ Funcionalidades:**

**`start_monitoring()`** ⭐ **MOTOR PRINCIPAL**
- **Função:** Inicia monitoramento contínuo de partidas
- **Frequência:** Scan a cada 3 minutos
- **Thread:** Execução em background

**`_scan_live_matches_only()`**
- **Função:** Busca e analisa apenas partidas ao vivo
- **Validação:** Dados completos, qualidade da tip
- **Filtros:** Remove partidas já analisadas, tips recentes

**`_analyze_live_match_with_data(match)`**
- **Função:** Análise completa de uma partida ao vivo
- **Dados:** Predição ML, odds reais, cálculo EV
- **Saída:** Tip completa se atender critérios profissionais

**`_meets_professional_criteria(analysis)`**
- **Função:** Valida se análise atende padrão profissional
- **Critérios:**
  - **Confiança:** ≥ 70%
  - **EV:** ≥ 5%
  - **Odds:** Entre 1.30 e 3.50
  - **Qualidade dos dados:** Completos e confiáveis

**`_create_professional_tip(analysis)`**
- **Função:** Cria tip formatada com padrão profissional
- **Conteúdo:** Times, odds, unidades, raciocínio, métricas

**`_calculate_ev_with_live_data(win_probability, live_odds, match)`**
- **Função:** Calcula Expected Value com dados ao vivo
- **Fórmula:** EV = (Prob × Odds) - 1
- **Ajustes:** Considera margem da casa, volatilidade

**`get_monitoring_status()`**
- **Função:** Status do sistema de monitoramento
- **Info:** Partidas monitoradas, tips geradas, performance

---

## 🤖 **10. BOT TELEGRAM PRINCIPAL**

### 📱 **Classe: `LoLBotV3UltraAdvanced`**

#### **🎯 Propósito:**
Interface principal do usuário via Telegram com todos os comandos.

---

## 📋 **COMANDOS DISPONÍVEIS**

### 🎮 **Comandos Principais:**

**`/start`** ⭐
- **Função:** Mensagem de boas-vindas + menu principal
- **Conteúdo:** Explicação do bot, sistema de unidades, features

**`/menu`**
- **Função:** Menu interativo com todos os comandos
- **Layout:** Keyboard inline organizado por categorias

**`/tips`** ⭐
- **Função:** Mostra tips profissionais recentes
- **Dados:** Tips ativas, histórico, performance

**`/livematches`** ⭐
- **Função:** Lista partidas ao vivo com análises
- **Formato:** Times, liga, tempo, predição, odds

**`/schedule` / `/proximosjogoslol`**
- **Função:** Cronograma de partidas futuras
- **Filtro:** Por data, liga, região

**`/monitoring`**
- **Função:** Status do sistema de monitoramento
- **Info:** Partidas ativas, tips geradas, performance

**`/forcescan`** 🔧
- **Função:** Força scan manual de partidas (Admin)
- **Uso:** Debugging, teste de sistema

### 💰 **Comandos de Gestão:**

**`/predictions`**
- **Função:** Sistema de predições e análises
- **Dados:** ML, algoritmos, confiança

**`/alerts`**
- **Função:** Configuração de alertas automáticos
- **Opções:** Registrar/desregistrar grupo

**`/units`**
- **Função:** Informações sobre sistema de unidades
- **Conteúdo:** Explicação, escalas, exemplos

**`/performance`**
- **Função:** Estatísticas de performance das tips
- **Métricas:** ROI, strike rate, unidades profit

**`/history`**
- **Função:** Histórico de tips e resultados
- **Filtro:** Por período, liga, performance

**`/odds`**
- **Função:** Resumo de odds atuais
- **Dados:** Melhores odds, casas, spreads

### ⚙️ **Comandos de Configuração:**

**`/filtrarligas`**
- **Função:** Configurar filtro de ligas
- **Opções:** LPL, LCK, LEC, LCS, CBLOL, etc.

**`/timesfavoritos`**
- **Função:** Definir times favoritos
- **Uso:** Alertas personalizados

**`/statuslol`**
- **Função:** Status geral do sistema
- **Info:** APIs, conexões, saúde do bot

---

## 🔧 **SISTEMA TÉCNICO**

### 🌐 **Flask Health Check:**
- **Rota:** `/health` - Status do sistema
- **Rota:** `/ping` - Teste básico de conectividade
- **Rota:** `/` - Informações gerais

### 🔄 **Sistema de Webhook:**
- **Compatibilidade:** Telegram Bot API v13 e v20
- **Auto-detecção:** Versão da biblioteca telegram
- **Fallback:** Polling se webhook falhar

### 🛡️ **Sistema de Segurança:**
- **Verificação de conflitos:** Evita múltiplas instâncias
- **Admin only:** Comandos sensíveis apenas para admin
- **Rate limiting:** Proteção contra spam
- **Error handling:** Tratamento robusto de erros

### 📊 **Sistema de Cache:**
- **Odds:** Cache de 5 minutos para otimização
- **Partidas:** Cache inteligente de dados live
- **Cleanup:** Limpeza automática de cache antigo

### 🔄 **Sistema de Threads:**
- **Monitoramento:** Thread dedicada para scan contínuo
- **Flask:** Thread separada para health check
- **Async:** Operações assíncronas para performance

---

## 🎯 **FLUXO OPERACIONAL**

### 🔄 **Ciclo Principal (a cada 3 minutos):**

1. **Busca partidas ao vivo** (16 endpoints globais)
2. **Filtra apenas partidas em andamento** (status validation)
3. **Remove duplicatas** (algoritmo de deduplicação)
4. **Valida dados completos** (draft, stats, timing)
5. **Executa predição ML/algoritmica** (confidence + probability)
6. **Busca odds reais** (The Odds API)
7. **Calcula Expected Value** (EV formula)
8. **Valida critérios profissionais** (EV ≥ 5%, confidence ≥ 70%)
9. **Calcula unidades** (sistema profissional 0.5-5.0)
10. **Gera tip formatada** (template profissional)
11. **Envia para grupos registrados** (Telegram alerts)
12. **Registra para histórico** (performance tracking)

### 📈 **Critérios de Qualidade:**

**Tip Profissional deve ter:**
- ✅ **Confiança:** ≥ 70%
- ✅ **Expected Value:** ≥ 5%
- ✅ **Odds range:** 1.30 - 3.50
- ✅ **Dados completos:** Draft + stats + timing
- ✅ **Liga reconhecida:** Tier 1/2/3
- ✅ **Timing adequado:** Não muito cedo/tarde
- ✅ **Sem tip recente:** Para mesmo matchup

---

## 🚀 **TECNOLOGIAS UTILIZADAS**

### 📚 **Bibliotecas Principais:**
- **telegram** - Interface Telegram Bot API
- **flask** - Health check e webhook
- **aiohttp** - Requisições HTTP assíncronas
- **numpy** - Cálculos matemáticos
- **asyncio** - Programação assíncrona
- **threading** - Execução paralela
- **datetime/pytz** - Gestão de tempo/timezone

### 🌐 **APIs Integradas:**
- **Riot Games API** - Dados oficiais LoL
- **The Odds API** - Odds de casas de apostas
- **Telegram Bot API** - Interface do usuário

### 🔧 **Padrões de Código:**
- **PEP 8** - Estilo Python
- **Type hints** - Tipagem estática
- **Async/await** - Programação assíncrona
- **Error handling** - Tratamento robusto
- **Logging** - Sistema de logs detalhado

---

## 🎯 **RESUMO EXECUTIVO**

O **Bot LoL V3 Ultra Avançado** é um sistema completo e profissional para tips de League of Legends que:

✅ **Usa apenas dados reais** da API oficial da Riot Games
✅ **Implementa sistema de unidades profissional** (0.5-5.0 unidades)
✅ **Fornece tips de alta qualidade** (EV ≥ 5%, confiança ≥ 70%)
✅ **Monitora partidas globalmente** (LPL, LCK, LEC, LCS, CBLOL, etc.)
✅ **Calcula Expected Value real** com odds de casas de apostas
✅ **Oferece interface completa** via Telegram
✅ **Mantém histórico e performance** para análise
✅ **Executa em modo profissional** 24/7 no Railway

**Diferenciais únicos:**
- 🎯 Foco específico em **Moneyline (ML)** ao vivo
- ⏱️ **Timing perfeito** baseado em eventos cruciais
- 🔍 **Análise ao vivo** com draft + estatísticas + tempo
- 💰 **Sistema de unidades** padrão de grupos profissionais
- 🌍 **Cobertura global** incluindo LPL, LCK, LEC
- 🤖 **Machine Learning** + fallback algorítmico
- 📊 **Expected Value** calculado com odds reais
- 🚀 **Alertas automáticos** para grupos registrados 
