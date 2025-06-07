#!/usr/bin/env python3
"""
DEBUG: Linha por linha do _match_meets_quality_criteria
"""

import asyncio
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
from bot.data_models.match_data import MatchData

def debug_quality_criteria_step_by_step(tips_system, match):
    """Debug cada passo do método _match_meets_quality_criteria"""
    
    print("🔍 DEBUG PASSO A PASSO:")
    print("-" * 40)
    
    try:
        # 1. Liga suportada
        league_name = match.league
        if isinstance(match.league, dict):
            league_name = match.league.get('name', '')
        
        league_key = league_name.upper()
        is_supported_league = False
        
        # Primeiro tenta match exato
        for supported_league in tips_system.quality_filters["supported_leagues"]:
            if supported_league.upper() in league_key or league_key in supported_league.upper():
                is_supported_league = True
                break
        
        print(f"1️⃣ Liga '{league_name}' suportada: {is_supported_league}")
        if not is_supported_league:
            print("   ❌ FALHOU na verificação de liga")
            return False
        
        # 2. Status válido
        from bot.utils.constants import VALID_LIVE_STATUSES
        has_valid_status = match.status in VALID_LIVE_STATUSES
        is_riot_live_match = (not match.status or match.status == "") and hasattr(match, 'match_id') and match.match_id
        
        print(f"2️⃣ Status válido: {has_valid_status} ou Riot live: {is_riot_live_match}")
        if not (has_valid_status or is_riot_live_match):
            print(f"   ❌ FALHOU na verificação de status: {match.status}")
            return False
        
        # 3. Draft completo
        is_draft_complete = tips_system._is_draft_complete(match)
        print(f"3️⃣ Draft completo: {is_draft_complete}")
        if not is_draft_complete:
            print("   ❌ FALHOU na verificação de draft")
            return False
        
        # 4. Tempo de jogo
        game_minutes = match.get_game_time_minutes()
        print(f"4️⃣ Tempo de jogo: {game_minutes:.1f} minutos")
        
        if game_minutes > 2.0:
            print(f"   ❌ FALHOU no timing: {game_minutes}min > 2min")
            return False
        
        if game_minutes == 0.0 and is_draft_complete:
            print("   ✅ Momento ideal: draft completo, jogo começando")
            # Continue para próximos checks
        
        # 5. Qualidade dos dados
        data_quality = match.calculate_data_quality()
        min_quality = tips_system.quality_filters["min_data_quality"]
        
        # Se tem composição completa, reduz requisito
        has_composition = (hasattr(match, 'team1_composition') and match.team1_composition and
                          hasattr(match, 'team2_composition') and match.team2_composition)
        
        if has_composition:
            min_quality = max(0.4, min_quality - 0.2)
        
        print(f"5️⃣ Qualidade: {data_quality:.1%} (mín: {min_quality:.1%})")
        print(f"   Tem composição: {has_composition}")
        
        # Para partidas da Riot API, aceita qualidade menor
        if is_riot_live_match and data_quality >= 0.3:
            print("   ✅ Riot API com qualidade aceitável")
            # Continue
        elif data_quality < min_quality:
            print(f"   ❌ FALHOU na qualidade: {data_quality:.1%} < {min_quality:.1%}")
            return False
        
        # 6. Eventos cruciais
        events_count = len(match.events) if hasattr(match, 'events') else 0
        min_events = tips_system.quality_filters["required_events"]
        
        # Se é partida recente, não exige muitos eventos
        if game_minutes <= 10:
            min_events = max(0, min_events - 2)
        
        print(f"6️⃣ Eventos: {events_count} (mín: {min_events})")
        
        if events_count < min_events:
            # Para partidas da Riot, aceita mesmo sem eventos se tem dados básicos
            if is_riot_live_match and match.team1_name and match.team2_name:
                print("   ✅ Riot API aceita sem eventos - tem dados básicos")
            else:
                print(f"   ❌ FALHOU nos eventos: {events_count} < {min_events}")
                return False
        
        print("✅ PASSOU EM TODOS OS FILTROS!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO durante debug: {e}")
        return False

async def main():
    """Main debug"""
    
    print("🚨 DEBUG LINHA POR LINHA")
    print("="*50)
    
    # Inicializa sistema
    pandascore_client = PandaScoreAPIClient()
    riot_client = RiotAPIClient()
    game_analyzer = LoLGameAnalyzer()
    units_system = ProfessionalUnitsSystem()
    prediction_system = DynamicPredictionSystem(
        game_analyzer=game_analyzer,
        units_system=units_system
    )
    
    tips_system = ProfessionalTipsSystem(
        pandascore_client=pandascore_client,
        riot_client=riot_client,
        prediction_system=prediction_system
    )
    
    # Match de teste
    match = MatchData(
        match_id="debug_match",
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"
    )
    match.team1_composition = ["Azir", "Graves", "Thresh", "Jinx", "Jax"]
    match.team2_composition = ["Orianna", "Sejuani", "Nautilus", "Aphelios", "Gnar"]
    match.game_time = "00:01:00"
    
    # Debug
    result = debug_quality_criteria_step_by_step(tips_system, match)
    
    print(f"\n🎯 RESULTADO FINAL: {result}")
    
    # Comparar com método original
    original_result = tips_system._match_meets_quality_criteria(match)
    print(f"🔄 Método original: {original_result}")
    
    if result != original_result:
        print("⚠️  DISCREPÂNCIA ENCONTRADA!")
    else:
        print("✅ Debug confere com método original")

if __name__ == "__main__":
    asyncio.run(main()) 