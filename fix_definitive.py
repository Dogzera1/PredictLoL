#!/usr/bin/env python3
"""
Script DEFINITIVO para corrigir a estrutura try/except quebrada
"""

def fix_definitive():
    """Corrige definitivamente a estrutura do código"""
    
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar e substituir a função show_all_live_matches inteira
    start_marker = "    async def show_all_live_matches(self, update_or_query, is_callback=False):"
    end_marker = "    async def predict_match_callback(self, query, match_id: str):"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        # Função corrigida completa
        new_function = '''    async def show_all_live_matches(self, update_or_query, is_callback=False):
        """Mostra todas as partidas ao vivo com botões funcionais"""
        try:
            # Mostrar loading
            if is_callback:
                await update_or_query.edit_message_text("🔄 Buscando TODAS as partidas ao vivo...")
            else:
                loading_msg = await update_or_query.message.reply_text("🔄 Buscando TODAS as partidas ao vivo...")
            
            # Buscar partidas ao vivo
            live_matches = await self.riot_api.get_all_live_matches()
            
            if not live_matches:
                text = """🔴 **PARTIDAS AO VIVO**

Não há partidas acontecendo neste momento.

✨ O bot monitora constantemente:
• 🇰🇷 LCK (Coreia)
• 🇨🇳 LPL (China)
• 🇪🇺 LEC (Europa)
• 🇺🇸 LCS (América do Norte)
• 🌍 Torneios internacionais
• 🏆 Ligas regionais menores

🔄 Atualize em alguns minutos!"""
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Atualizar", callback_data="live_matches_all")],
                    [InlineKeyboardButton("🏠 Menu Principal", callback_data="start")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if is_callback:
                    await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await loading_msg.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                return
            
            # Formatar lista de partidas
            text = f"🔴 **PARTIDAS AO VIVO ({len(live_matches)})**\\n\\n"
            text += "👆 **Clique em uma partida para ver:**\\n"
            text += "• 🔮 Predição detalhada em tempo real\\n"
            text += "• 🏆 Análise completa do draft\\n"
            text += "• 💰 Recomendação de aposta com justificativa\\n"
            text += "• 📊 Probabilidades dinâmicas\\n\\n"
            
            # Adicionar preview das partidas
            for i, match in enumerate(live_matches[:6], 1):  # Mostrar até 6
                teams = match.get('teams', [])
                if len(teams) >= 2:
                    team1 = teams[0]
                    team2 = teams[1]
                    
                    league = match.get('league', 'LoL Esports')
                    state_emoji = '🔴' if match.get('state') == 'inProgress' else '⏳'
                    
                    # Placar se disponível
                    score_text = ""
                    if 'result' in team1 and 'result' in team2:
                        wins1 = team1['result'].get('gameWins', 0)
                        wins2 = team2['result'].get('gameWins', 0)
                        score_text = f" ({wins1}-{wins2})"
                    
                    text += f"{state_emoji} **{league}**\\n"
                    text += f"⚔️ {team1.get('code', team1.get('name', 'Team1'))} vs "
                    text += f"{team2.get('code', team2.get('name', 'Team2'))}{score_text}\\n\\n"
            
            # Criar botões para cada partida
            keyboard = []
            for match in live_matches[:8]:  # Máximo 8 partidas
                teams = match.get('teams', [])
                if len(teams) >= 2:
                    team1_name = teams[0].get('code', teams[0].get('name', 'T1'))
                    team2_name = teams[1].get('code', teams[1].get('name', 'T2'))
                    
                    button_text = f"🔮 {team1_name} vs {team2_name}"
                    callback_data = f"predict_match_{match['id']}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Botões de ação
            keyboard.append([
                InlineKeyboardButton("🔄 Atualizar", callback_data="live_matches_all"),
                InlineKeyboardButton("📊 Ver Rankings", callback_data="current_rankings")
            ])
            keyboard.append([InlineKeyboardButton("🏠 Menu Principal", callback_data="start")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_callback:
                await update_or_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await loading_msg.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        except Exception as e:
            logger.error(f"❌ Erro ao mostrar partidas: {e}")
            error_text = f"❌ Erro ao buscar partidas: {str(e)}"
            
            if is_callback:
                await update_or_query.edit_message_text(error_text)
            else:
                await update_or_query.message.reply_text(error_text)

    '''
        
        # Substituir a função quebrada pela corrigida
        before = content[:start_idx]
        after = content[end_idx:]
        content = before + new_function + after
        
        # Salvar arquivo
        with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Função show_all_live_matches corrigida definitivamente!")
    else:
        print("❌ Não foi possível encontrar a função para corrigir")

if __name__ == "__main__":
    fix_definitive() 