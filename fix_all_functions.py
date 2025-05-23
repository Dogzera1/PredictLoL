#!/usr/bin/env python3
"""
Script para corrigir TODAS as funções com problemas
"""

def fix_all_functions():
    """Corrige todas as funções com problemas de estrutura"""
    
    # Ler arquivo
    with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corrigir predict_match_callback
    predict_start = "    async def predict_match_callback(self, query, match_id: str):"
    predict_end = "    def _format_match_prediction(self, prediction: Dict, match_data: Dict) -> str:"
    
    start_idx = content.find(predict_start)
    end_idx = content.find(predict_end)
    
    if start_idx != -1 and end_idx != -1:
        new_predict_function = '''    async def predict_match_callback(self, query, match_id: str):
        """Callback para predição de partida específica"""
        try:
            await query.edit_message_text("🔄 Analisando partida e gerando predição...")
            
            # Buscar dados da partida
            live_matches = await self.riot_api.get_all_live_matches()
            match_data = None
            
            for match in live_matches:
                if match['id'] == match_id:
                    match_data = match
                    break
            
            if not match_data:
                await query.edit_message_text("❌ Partida não encontrada")
                return
            
            # Gerar predição
            prediction = await self.prediction_system.predict_live_match(match_data)
            
            # Formatar resultado
            text = self._format_match_prediction(prediction, match_data)
            
            # Botões de ação
            keyboard = [
                [
                    InlineKeyboardButton("🏆 Ver Draft", callback_data=f"draft_{match_id}"),
                    InlineKeyboardButton("💰 Análise Odds", callback_data=f"odds_{match_id}")
                ],
                [
                    InlineKeyboardButton("🔄 Atualizar", callback_data=f"predict_match_{match_id}"),
                    InlineKeyboardButton("📊 Comparar Times", callback_data=f"compare_{match_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Voltar", callback_data="live_matches_all"),
                    InlineKeyboardButton("🏠 Menu", callback_data="start")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Erro na predição: {e}")
            await query.edit_message_text(f"❌ Erro na predição: {str(e)}")

    '''
        
        # Substituir função
        before = content[:start_idx]
        after = content[end_idx:]
        content = before + new_predict_function + after
    
    # Corrigir show_draft_analysis
    draft_start = "    async def show_draft_analysis(self, query, match_id: str):"
    draft_end = "    def _format_draft_analysis(self, draft_analysis: Dict, match_data: Dict) -> str:"
    
    start_idx = content.find(draft_start)
    end_idx = content.find(draft_end)
    
    if start_idx != -1 and end_idx != -1:
        new_draft_function = '''    async def show_draft_analysis(self, query, match_id: str):
        """Mostra análise detalhada do draft"""
        try:
            await query.edit_message_text("🔄 Analisando draft da partida...")
            
            # Buscar dados da partida
            live_matches = await self.riot_api.get_all_live_matches()
            match_data = None
            
            for match in live_matches:
                if match['id'] == match_id:
                    match_data = match
                    break
            
            if not match_data:
                await query.edit_message_text("❌ Partida não encontrada")
                return
            
            # Análise de draft
            team1_comp = match_data.get('team1_composition', [])
            team2_comp = match_data.get('team2_composition', [])
            
            if not team1_comp or not team2_comp:
                text = "❌ Dados de draft não disponíveis para esta partida"
            else:
                draft_analysis = self.prediction_system.champion_analyzer.analyze_draft(team1_comp, team2_comp)
                text = self._format_draft_analysis(draft_analysis, match_data)
            
            # Botões
            keyboard = [
                [
                    InlineKeyboardButton("🔮 Ver Predição", callback_data=f"predict_match_{match_id}"),
                    InlineKeyboardButton("📊 Fases do Jogo", callback_data=f"phases_{match_id}")
                ],
                [
                    InlineKeyboardButton("🔙 Voltar", callback_data=f"predict_match_{match_id}"),
                    InlineKeyboardButton("🏠 Menu", callback_data="start")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de draft: {e}")
            await query.edit_message_text(f"❌ Erro: {str(e)}")

    '''
        
        # Substituir função
        before = content[:start_idx]
        after = content[end_idx:]
        content = before + new_draft_function + after
    
    # Salvar arquivo
    with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Todas as funções corrigidas!")

if __name__ == "__main__":
    fix_all_functions() 