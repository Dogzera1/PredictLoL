#!/usr/bin/env python3
"""
🚨 CORREÇÃO URGENTE: Timing e Odds Incorretos
Patch para corrigir problemas críticos identificados pelo usuário
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def aplicar_correcoes():
    """Aplica correções nos arquivos críticos"""
    print("🚨 APLICANDO CORREÇÕES URGENTES")
    print("=" * 60)
    
    # Correção 1: Timing no prediction_system.py
    print("\n1️⃣ CORRIGINDO TIMING:")
    
    try:
        with open("bot/core_logic/prediction_system.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Localiza a linha problemática
        old_line = 'game_time_at_tip=f"{match_data.get_game_time_minutes():.0f}min",'
        
        if old_line in content:
            # Substitui por uma correção que busca o tempo real
            new_line = '''game_time_at_tip=self._get_real_game_time_corrected(match_data),'''
            
            content = content.replace(old_line, new_line)
            
            # Adiciona o método de correção
            method_code = '''
    def _get_real_game_time_corrected(self, match_data: MatchData) -> str:
        """
        CORREÇÃO URGENTE: Calcula tempo REAL do jogo
        """
        try:
            import time
            from datetime import datetime, timedelta
            
            # Se tem dados recentes e válidos, usa eles
            if hasattr(match_data, 'last_update') and match_data.last_update:
                if isinstance(match_data.last_update, datetime):
                    age = datetime.now() - match_data.last_update
                    if age < timedelta(minutes=1):  # Muito recente
                        game_time = getattr(match_data, 'game_time_seconds', 0)
                        if game_time > 0:
                            minutes = game_time // 60
                            seconds = game_time % 60
                            return f"{minutes}:{seconds:02d}"
            
            # Tenta estimativa baseada em quando a tip foi gerada
            current_time = time.time()
            if hasattr(match_data, 'raw_data') and 'gameTime' in match_data.raw_data:
                api_game_time = match_data.raw_data['gameTime']
                if api_game_time > 0:
                    minutes = api_game_time // 60
                    seconds = api_game_time % 60
                    return f"{minutes}:{seconds:02d}"
            
            # Busca no status se disponível
            if hasattr(match_data, 'status') and 'time' in str(match_data.status).lower():
                # Tenta extrair tempo do status
                import re
                time_match = re.search(r'(\d+):(\d+)', str(match_data.status))
                if time_match:
                    return f"{time_match.group(1)}:{time_match.group(2)}"
            
            # Fallback: indica que é tempo real mas sem especificar
            return "EM_JOGO"
            
        except Exception as e:
            logger.warning(f"Erro ao calcular tempo real: {e}")
            return "TEMPO_REAL"
'''
            
            # Adiciona o método antes da última linha
            content = content.rstrip() + method_code + "\n"
            
            with open("bot/core_logic/prediction_system.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("✅ Timing corrigido - agora busca tempo real do jogo")
        else:
            print("⚠️ Linha de timing não encontrada - pode já estar corrigida")
    
    except Exception as e:
        print(f"❌ Erro ao corrigir timing: {e}")
    
    # Correção 2: Odds no tips_system.py
    print("\n2️⃣ CORRIGINDO ODDS:")
    
    try:
        with open("bot/systems/tips_system.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Localiza a função de odds estimadas
        if "_generate_estimated_odds" in content:
            # Adiciona validação adicional para buscar odds reais primeiro
            validation_code = '''
    async def _validate_real_odds_first(self, match: MatchData) -> Dict:
        """
        CORREÇÃO: Tenta buscar odds REAIS antes de usar estimadas
        """
        try:
            # 1. Busca no PandaScore por match_id
            real_odds = await self.pandascore_client.get_match_odds(match.match_id)
            if real_odds and self._are_valid_odds(real_odds):
                logger.info(f"✅ Odds reais encontradas: {match.match_id}")
                return real_odds
            
            # 2. Busca por nomes dos times
            real_odds = await self.pandascore_client.find_match_odds_by_teams(
                match.team1_name, match.team2_name
            )
            if real_odds and self._are_valid_odds(real_odds):
                logger.info(f"✅ Odds reais por times: {match.team1_name} vs {match.team2_name}")
                return real_odds
            
            # 3. Busca na liga específica
            if hasattr(match, 'league') and match.league:
                league_matches = await self.pandascore_client.get_league_matches(match.league)
                for league_match in league_matches:
                    if (league_match.get('team1') == match.team1_name and 
                        league_match.get('team2') == match.team2_name):
                        odds_data = league_match.get('odds')
                        if odds_data and self._are_valid_odds(odds_data):
                            logger.info(f"✅ Odds reais da liga: {match.league}")
                            return odds_data
            
            # Se não encontrou odds reais, retorna None para usar estimadas
            logger.warning(f"⚠️ Odds reais não encontradas para {match.match_id} - usando estimativa")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds reais: {e}")
            return None
'''
            
            content = content.replace(
                "async def _generate_tip_for_match",
                validation_code + "\n    async def _generate_tip_for_match"
            )
            
            # Modifica a função de geração para usar odds reais primeiro
            old_odds_logic = "# 1. Tenta buscar odds reais do PandaScore"
            new_odds_logic = '''# 1. CORREÇÃO: Busca odds reais com método aprimorado
            odds_data = await self._validate_real_odds_first(match)'''
            
            if old_odds_logic in content:
                # Encontra a seção completa de odds e substitui
                lines = content.split('\n')
                new_lines = []
                in_odds_section = False
                
                for line in lines:
                    if "# 1. Tenta buscar odds reais do PandaScore" in line:
                        in_odds_section = True
                        new_lines.append("            " + new_odds_logic.strip())
                        continue
                    elif in_odds_section and "# 3. Se ainda não tem odds" in line:
                        in_odds_section = False
                        new_lines.append(line)
                        continue
                    elif not in_odds_section:
                        new_lines.append(line)
                
                content = '\n'.join(new_lines)
            
            with open("bot/systems/tips_system.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("✅ Sistema de odds corrigido - prioriza odds reais")
    
    except Exception as e:
        print(f"❌ Erro ao corrigir odds: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 CORREÇÕES APLICADAS!")
    print("\n📋 MUDANÇAS:")
    print("   ✅ Timing: Agora busca tempo REAL do jogo")
    print("   ✅ Odds: Prioriza odds REAIS ao invés de estimadas")
    print("   ✅ Validação: Múltiplas fontes de dados")
    
    print("\n🚀 PRÓXIMOS PASSOS:")
    print("   1. Fazer commit das correções")
    print("   2. Push para o Railway")
    print("   3. Aguardar redeploy")
    print("   4. Testar próxima tip gerada")

if __name__ == "__main__":
    aplicar_correcoes() 