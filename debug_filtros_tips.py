#!/usr/bin/env python3
"""
DEBUG: Descobrir exatamente qual filtro está rejeitando
"""

import asyncio
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
from bot.data_models.match_data import MatchData

async def debug_filtros():
    """Debug detalhado dos filtros"""
    
    print("🔍 DEBUG: FILTROS DE QUALIDADE")
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
    
    # Cria match com draft completo
    match = MatchData(
        match_id="debug_match",
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"
    )
    match.team1_composition = ["Azir", "Graves", "Thresh", "Jinx", "Jax"]
    match.team2_composition = ["Orianna", "Sejuani", "Nautilus", "Aphelios", "Gnar"]
    match.game_time = "00:01:00"  # 1 minuto
    
    print(f"🎮 Match: {match.team1_name} vs {match.team2_name}")
    print(f"🏆 Liga: {match.league}")
    print(f"⏰ Tempo: {match.game_time}")
    print(f"📊 Status: {match.status}")
    
    # Debug passo a passo dos filtros
    print(f"\n🔍 TESTANDO FILTROS...")
    
    # 1. Liga suportada
    league_name = match.league
    print(f"1️⃣ Liga: {league_name}")
    
    # 2. Status válido
    print(f"2️⃣ Status: {match.status}")
    
    # 3. Draft completo
    is_draft_complete = tips_system._is_draft_complete(match)
    print(f"3️⃣ Draft completo: {is_draft_complete}")
    
    # 4. Timing
    game_minutes = match.get_game_time_minutes()
    timing_ok = game_minutes <= 2.0
    print(f"4️⃣ Timing: {game_minutes:.1f}min (OK: {timing_ok})")
    
    # 5. Qualidade dos dados
    data_quality = match.calculate_data_quality()
    min_quality = tips_system.quality_filters["min_data_quality"]
    quality_ok = data_quality >= min_quality
    print(f"5️⃣ Qualidade: {data_quality:.1%} (min: {min_quality:.1%}, OK: {quality_ok})")
    
    # 6. Eventos
    events_count = len(match.events) if hasattr(match, 'events') else 0
    min_events = tips_system.quality_filters["required_events"]
    events_ok = events_count >= min_events
    print(f"6️⃣ Eventos: {events_count} (min: {min_events}, OK: {events_ok})")
    
    # Teste completo
    print(f"\n🎯 TESTE COMPLETO:")
    meets_criteria = tips_system._match_meets_quality_criteria(match)
    print(f"   Atende critérios: {meets_criteria}")
    
    # Se não atende, vamos ajustar
    if not meets_criteria:
        print(f"\n🔧 AJUSTANDO FILTROS...")
        
        # Reduzir qualidade mínima
        old_quality = tips_system.quality_filters["min_data_quality"]
        tips_system.quality_filters["min_data_quality"] = 0.01  # 1%
        print(f"   Qualidade mínima: {old_quality:.1%} → 1%")
        
        # Reduzir eventos necessários
        old_events = tips_system.quality_filters["required_events"]
        tips_system.quality_filters["required_events"] = 0
        print(f"   Eventos mínimos: {old_events} → 0")
        
        # Teste novamente
        meets_criteria_adjusted = tips_system._match_meets_quality_criteria(match)
        print(f"   Atende com ajustes: {meets_criteria_adjusted}")
        
        if meets_criteria_adjusted:
            print(f"\n✅ PROBLEMA IDENTIFICADO: Filtros muito restritivos")
            print(f"💡 SOLUÇÃO: Ajustar filtros para partidas reais")
        else:
            print(f"\n❌ PROBLEMA MAIS PROFUNDO")

if __name__ == "__main__":
    asyncio.run(debug_filtros()) 