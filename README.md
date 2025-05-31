# 🔥 Bot LoL V3 Ultra Avançado

**Sistema profissional de tips para League of Legends com machine learning e análise ao vivo**

## 🎯 Visão Geral

Bot de Telegram especializado em tips de **Moneyline (ML)** para League of Legends, utilizando:
- 📊 **Sistema de unidades profissional** (0.5-5.0 unidades)
- 🤖 **Machine Learning** + fallback algorítmico
- 📡 **APIs oficiais** (Riot Games + The Odds API)
- 🌍 **Cobertura global** (LPL, LCK, LEC, LCS, CBLOL, etc.)
- ⚡ **Monitoramento ao vivo** 24/7
- 📈 **Expected Value** calculado com odds reais

## ✨ Características Principais

### 🎮 Tips Profissionais
- ✅ **Critério rigoroso**: Confiança ≥ 70%, EV ≥ 5%
- ✅ **Timing perfeito**: Baseado em eventos cruciais
- ✅ **Análise completa**: Draft + estatísticas + tempo real
- ✅ **Sistema de unidades**: Padrão de grupos profissionais

### 📊 Análise Avançada
- 🐉 **Eventos cruciais**: Dragões, Barão, Torres, Teamfights
- 💰 **Diferença de ouro**: Monitoramento em tempo real
- 🏆 **Controle de objetivos**: Análise de map control
- ⏱️ **Timing score**: Early/Mid/Late game advantages

### 🌐 Cobertura Global
- **16 endpoints** da API da Riot Games
- **Todas as principais ligas**: LPL, LCK, LEC, LCS, CBLOL
- **Anti-duplicatas**: Sistema inteligente de deduplicação
- **Múltiplos idiomas**: en-US, pt-BR, zh-CN, ko-KR, etc.

## 🚀 Instalação e Configuração

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/lol_bot_v3_ultra_advanced.git
cd lol_bot_v3_ultra_advanced
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
# Copie o arquivo template
cp .env.template .env

# Edite o arquivo .env com suas chaves:
# - RIOT_API_KEY: Sua chave da API da Riot Games
# - THE_ODDS_API_KEY: Sua chave da The Odds API
# - TELEGRAM_BOT_TOKEN: Token do seu bot do Telegram
# - ADMIN_TELEGRAM_USER_ID: Seu ID de usuário do Telegram
```

### 5. Execute o bot
```bash
python main.py
```

## 📋 Comandos Disponíveis

### 🎮 Comandos Principais
- `/start` - Boas-vindas e menu principal
- `/menu` - Menu interativo completo
- `/tips` - Tips profissionais recentes
- `/livematches` - Partidas ao vivo com análises
- `/schedule` - Cronograma de partidas futuras

### 💰 Gestão e Análise
- `/predictions` - Sistema de predições ML
- `/units` - Informações sobre sistema de unidades
- `/performance` - Estatísticas e ROI
- `/history` - Histórico de tips
- `/odds` - Resumo de odds atuais

### ⚙️ Configurações
- `/alerts` - Configurar alertas automáticos
- `/filtrarligas` - Filtrar ligas de interesse
- `/timesfavoritos` - Definir times favoritos
- `/statuslol` - Status geral do sistema

### 🔧 Admin (apenas administradores)
- `/forcescan` - Força scan manual de partidas
- `/monitoring` - Status do sistema de monitoramento

## 🏗️ Arquitetura do Sistema

```
bot/
├── api_clients/           # Integração com APIs externas
│   ├── riot_api_client.py    # Cliente da API da Riot Games
│   └── the_odds_api_client.py # Cliente da The Odds API
│
├── core_logic/            # Lógica principal de análise
│   ├── game_analyzer.py      # Análise de eventos cruciais
│   ├── prediction_system.py  # Sistema de predição ML
│   └── units_system.py       # Sistema de unidades profissional
│
├── telegram_bot/          # Interface do Telegram
│   ├── bot_interface.py      # Comandos e handlers
│   ├── alerts_system.py      # Sistema de alertas automáticos
│   └── user_preferences.py   # Preferências do usuário
│
├── systems/               # Sistemas operacionais
│   ├── tips_system.py        # Motor principal de tips
│   └── schedule_manager.py   # Gerenciamento de cronograma
│
├── utils/                 # Utilitários compartilhados
│   ├── constants.py          # Constantes globais
│   ├── helpers.py            # Funções auxiliares
│   └── logger_config.py      # Configuração de logs
│
└── web/                   # Interface web (health check)
    └── app.py                # Rotas Flask
```

## 🔄 Fluxo Operacional

O sistema executa um ciclo principal a cada **3 minutos**:

1. **Busca partidas ao vivo** de 16 endpoints globais
2. **Filtra partidas em andamento** e remove duplicatas
3. **Valida dados completos** (draft, stats, timing)
4. **Executa predição ML/algorítmica** (confiança + probabilidade)
5. **Busca odds reais** de casas de apostas
6. **Calcula Expected Value** (fórmula EV)
7. **Valida critérios profissionais** (EV ≥ 5%, confiança ≥ 70%)
8. **Calcula unidades** (sistema 0.5-5.0)
9. **Gera tip formatada** com template profissional
10. **Envia alertas** para grupos registrados
11. **Registra histórico** para análise de performance

## 📊 Sistema de Unidades

O bot utiliza o **sistema profissional de unidades**:

- **1 unidade = 1% do bankroll**
- **Escala**: 0.5 a 5.0 unidades
- **Critérios**:
  - 90%+ confiança + 15%+ EV = **5.0 unidades** (Risco Muito Alto)
  - 85%+ confiança + 12%+ EV = **4.0 unidades** (Risco Alto)
  - 80%+ confiança + 10%+ EV = **3.0 unidades** (Risco Alto)
  - 75%+ confiança + 8%+ EV = **2.5 unidades** (Risco Médio-Alto)
  - 70%+ confiança + 6%+ EV = **2.0 unidades** (Risco Médio)
  - 65%+ confiança + 5%+ EV = **1.0 unidades** (Risco Baixo)

## 🔧 Health Check

O sistema inclui um servidor Flask para monitoramento:

- **`/health`** - Status completo do sistema
- **`/ping`** - Teste básico de conectividade
- **`/`** - Informações gerais

## 📈 Critérios de Qualidade

Uma tip é considerada **profissional** quando atende:

- ✅ **Confiança**: ≥ 70%
- ✅ **Expected Value**: ≥ 5%
- ✅ **Odds range**: 1.30 - 3.50
- ✅ **Dados completos**: Draft + stats + timing
- ✅ **Liga reconhecida**: Tier 1/2/3
- ✅ **Timing adequado**: Não muito cedo/tarde

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

- 📧 **Email**: seu-email@example.com
- 💬 **Telegram**: @seu_usuario
- 🐛 **Issues**: [GitHub Issues](https://github.com/seu-usuario/lol_bot_v3_ultra_advanced/issues)

---

**⚡ Desenvolvido para profissionais que levam apostas esportivas a sério** 