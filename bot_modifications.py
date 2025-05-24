# MODIFICAÇÕES PARA O BOT LOL V3 - Sistema de Notificações e Predições

"""
1. SISTEMA DE NOTIFICAÇÃO DE VALUE BETTING - STATUS: ✅ FUNCIONANDO
   - O sistema já está implementado no value_bet_system.py
   - Inclui ValueBetNotificationSystem que gerencia inscrições
   - Envia notificações automáticas em tempo real
   - Comandos: /subscribe_vb, /unsubscribe_vb, /value_stats

2. MODIFICAÇÕES PARA PARTIDAS CLICÁVEIS
   - Remover botão separado de predição
   - Fazer cada partida clicável
   - Mostrar predição + análise de value betting
   - Incluir "porquê apostar" na análise
"""

# NOVO MÉTODO PARA show_matches (substituir no bot_v13_railway.py)
def show_matches_modified(self, update, context):
    """Mostra partidas ao vivo REAIS da API com botões clicáveis"""
    self.health_manager.update_activity()
    
    # Buscar partidas reais
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        real_matches = loop.run_until_complete(self.riot_client.get_live_matches())
        loop.close()
    except Exception as e:
        logger.error(f"❌ Erro ao buscar partidas reais: {e}")
        real_matches = []
    
    if not real_matches:
        matches_text = """ℹ️ **NENHUMA PARTIDA AO VIVO**

🔍 **Não há partidas de LoL Esports acontecendo agora**

🔄 **Monitoramento ativo em:**
🏆 LCK, LPL, LEC, LCS
🥈 CBLOL, LJL, LCO, LFL

⏰ **Verifique novamente em alguns minutos**"""

        keyboard = [
            [InlineKeyboardButton("🔄 Atualizar", callback_data="show_matches"),
             InlineKeyboardButton("💰 Value Bets", callback_data="value_bets")],
            [InlineKeyboardButton("📊 Portfolio", callback_data="portfolio")]
        ]
    else:
        matches_text = f"🔴 **PARTIDAS AO VIVO** ({len(real_matches)} encontradas)\n\n"
        
        # Criar botões para cada partida
        keyboard = []
        
        for i, match in enumerate(real_matches[:6]):  # Máximo 6 partidas
            try:
                teams = match.get('teams', [])
                if len(teams) >= 2:
                    team1 = teams[0].get('name', 'Team 1')
                    team2 = teams[1].get('name', 'Team 2')
                    league = match.get('league', 'Unknown')
                    status = match.get('status', 'Ao vivo')
                    
                    # Emoji da liga
                    league_emoji = {
                        'LCK': '🇰🇷', 'LPL': '🇨🇳', 'LEC': '🇪🇺', 
                        'LCS': '🇺🇸', 'CBLOL': '🇧🇷'
                    }.get(league, '🎮')
                    
                    matches_text += f"{league_emoji} **{league}** • {status}\n"
                    matches_text += f"🎮 **{team1} vs {team2}**\n\n"
                    
                    # Criar botão clicável para cada partida
                    button_text = f"🔮 {team1} vs {team2}"
                    callback_data = f"predict_match_{i}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
                    
            except Exception as e:
                logger.error(f"❌ Erro ao processar partida {i}: {e}")
                continue
        
        matches_text += f"⏰ Atualizado: {datetime.now().strftime('%H:%M:%S')}\n\n"
        matches_text += "💡 **Clique numa partida acima para ver:**\n"
        matches_text += "🔮 Predição completa com probabilidades\n"
        matches_text += "💰 Análise de value betting\n"
        matches_text += "📊 Porquê apostar ou não apostar"
        
        # Adicionar botões de ação
        keyboard.extend([
            [InlineKeyboardButton("🔄 Atualizar", callback_data="show_matches"),
             InlineKeyboardButton("💰 Value Bets", callback_data="value_bets")],
            [InlineKeyboardButton("📊 Portfolio", callback_data="portfolio")]
        ])
    
    update.message.reply_text(
        matches_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# NOVO CALLBACK PARA PREDICT_MATCH (adicionar no handle_callback)
def handle_predict_match_callback(self, query, match_index):
    """Callback para predição específica de uma partida"""
    try:
        # Buscar partidas
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        real_matches = loop.run_until_complete(self.riot_client.get_live_matches())
        loop.close()
        
        if not real_matches or match_index >= len(real_matches):
            query.edit_message_text(
                "❌ **Partida não encontrada**\n\nTente /partidas novamente.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        match = real_matches[match_index]
        teams = match.get('teams', [])
        
        if len(teams) < 2:
            query.edit_message_text(
                "❌ **Dados incompletos**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        team1 = teams[0].get('name', 'Team 1')
        team2 = teams[1].get('name', 'Team 2')
        league = match.get('league', 'Unknown')
        
        # Fazer predição
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        prediction = loop.run_until_complete(self.dynamic_prediction.predict_live_match(match))
        loop.close()
        
        prob1 = prediction.get('team1_win_probability', 0.5)
        prob2 = prediction.get('team2_win_probability', 0.5)
        odds1 = prediction.get('team1_odds', 2.0)
        odds2 = prediction.get('team2_odds', 2.0)
        confidence = prediction.get('confidence', 'Média')
        analysis = prediction.get('analysis', 'Análise baseada em dados históricos')
        
        # Emoji da liga
        league_emoji = {
            'LCK': '🇰🇷', 'LPL': '🇨🇳', 'LEC': '🇪🇺', 
            'LCS': '🇺🇸', 'CBLOL': '🇧🇷'
        }.get(league, '🎮')
        
        # Análise de value betting
        value1 = (prob1 * odds1) - 1
        value2 = (prob2 * odds2) - 1
        
        if max(value1, value2) > 0.05:  # 5% de value mínimo
            if value1 > value2:
                value_team = team1
                edge = value1
                bet_prob = prob1
                bet_odds = odds1
            else:
                value_team = team2
                edge = value2
                bet_prob = prob2
                bet_odds = odds2
            
            value_analysis = f"""✅ **APOSTAR EM {value_team.upper()}**

🎯 **Razões para apostar:**
• Probabilidade real: {bet_prob:.1%}
• Odds implícitas: {1/bet_odds:.1%}
• Edge positivo: +{edge:.1%}
• Value betting detectado

💰 **Vantagem:** +{edge:.1%}
🎲 **Odds:** {bet_odds:.2f}
📊 **Confiança:** {confidence}"""
            
            recommendation = f"💰 **RECOMENDAÇÃO: APOSTAR EM {value_team.upper()}**"
            risk_level = "🟢 BAIXO" if confidence == 'Alta' else "🟡 MÉDIO"
            
        else:
            value_analysis = f"""❌ **NÃO APOSTAR**

📊 **Razões para não apostar:**
• Odds alinhadas com probabilidades
• Margem da casa desfavorável
• Sem edge positivo significativo
• Risk/reward desfavorável

💡 **Sugestão:** Aguardar melhor oportunidade"""
            
            recommendation = "❌ **RECOMENDAÇÃO: NÃO APOSTAR**"
            risk_level = "🔴 ALTO (sem value)"
        
        detailed_text = f"""🔮 **ANÁLISE COMPLETA**

{league_emoji} **{team1} vs {team2}**
🏆 Liga: {league}

📊 **PROBABILIDADES:**
• **{team1}**: {prob1*100:.1f}% de vitória
• **{team2}**: {prob2*100:.1f}% de vitória

💰 **ODDS:**
• **{team1}**: {odds1:.2f}
• **{team2}**: {odds2:.2f}

🎯 **CONFIANÇA:** {confidence}

🧠 **ANÁLISE TÉCNICA:**
{analysis}

💡 **ANÁLISE DE VALUE BETTING:**
{value_analysis}

{recommendation}

⚠️ **RISCO:** {risk_level}

⚡ **Baseado em dados reais da API Riot Games**"""
        
        keyboard = [
            [InlineKeyboardButton("💰 Ver Value Bets", callback_data="value_bets"),
             InlineKeyboardButton("🎮 Voltar", callback_data="show_matches")],
            [InlineKeyboardButton("📊 Portfolio", callback_data="portfolio")]
        ]
        
        query.edit_message_text(
            detailed_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"❌ Erro na predição: {e}")
        query.edit_message_text(
            f"❌ **Erro ao carregar**\n\n{str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )

print("✅ Modificações definidas - aplicar no bot_v13_railway.py") 