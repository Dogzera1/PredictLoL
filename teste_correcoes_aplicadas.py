#!/usr/bin/env python3
"""
TESTE: Verificar se as correções foram aplicadas
"""

import asyncio
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
from bot.data_models.match_data import MatchData
from bot.utils.constants import SUPPORTED_LEAGUES, VALID_LIVE_STATUSES

async def test_corrections():
    """Testa se as correções foram aplicadas"""
    
    print("🔍 VERIFICANDO CORREÇÕES APLICADAS")
    print("="*50)
    
    # 1. Verifica se LTA Norte está nas ligas
    print("1️⃣ VERIFICANDO LIGAS SUPORTADAS:")
    lta_found = False
    for league in SUPPORTED_LEAGUES:
        if "LTA" in league.upper():
            print(f"   ✅ Encontrada: {league}")
            lta_found = True
    
    if "LTA Norte" in SUPPORTED_LEAGUES:
        print("   ✅ LTA Norte CONFIRMADA na lista")
    else:
        print("   ❌ LTA Norte NÃO ENCONTRADA")
    
    print(f"   📊 Total ligas: {len(SUPPORTED_LEAGUES)}")
    
    # 2. Verifica se in_game está nos status
    print("\n2️⃣ VERIFICANDO STATUS VÁLIDOS:")
    if "in_game" in VALID_LIVE_STATUSES:
        print("   ✅ in_game CONFIRMADO na lista")
    else:
        print("   ❌ in_game NÃO ENCONTRADO")
    
    print(f"   📊 Status válidos: {sorted(VALID_LIVE_STATUSES)}")
    
    # 3. Testa sistema completo
    print("\n3️⃣ TESTANDO SISTEMA COMPLETO:")
    
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
    
    # Match igual ao da tip problemática
    match = MatchData(
        match_id="test_lta_norte",
        team1_name="FlyQuest",
        team2_name="Cloud9 Kia",
        league="LTA Norte",
        status="in_game"
    )
    match.team1_composition = ["Azir", "Graves", "Thresh", "Jinx", "Jax"]
    match.team2_composition = ["Orianna", "Sejuani", "Nautilus", "Aphelios", "Gnar"]
    match.game_time = "00:01:00"
    
    # Testa filtros
    is_draft_complete = tips_system._is_draft_complete(match)
    meets_criteria = tips_system._match_meets_quality_criteria(match)
    map_id = tips_system._get_map_identifier(match)
    
    print(f"   🎮 Match: {match.team1_name} vs {match.team2_name}")
    print(f"   🏆 Liga: {match.league}")
    print(f"   📊 Status: {match.status}")
    print(f"   📋 Draft completo: {is_draft_complete}")
    print(f"   ✅ Atende critérios: {meets_criteria}")
    print(f"   🗺️ Map ID: {map_id}")
    
    # 4. Testa cache anti-repetição
    print("\n4️⃣ TESTANDO CACHE ANTI-REPETIÇÃO:")
    
    # Primeira verificação
    suitable_before = tips_system._filter_suitable_matches([match])
    print(f"   📊 Adequadas (antes): {len(suitable_before)}")
    
    # Marca como processado
    tips_system.processed_maps.add(map_id)
    print(f"   📝 Marcado como processado: {map_id}")
    
    # Segunda verificação
    suitable_after = tips_system._filter_suitable_matches([match])
    print(f"   📊 Adequadas (depois): {len(suitable_after)}")
    print(f"   🚫 Anti-repetição funcionando: {len(suitable_after) == 0}")
    
    # 5. Resultado final
    print("\n" + "="*50)
    print("📊 RESULTADO DA VERIFICAÇÃO:")
    
    all_good = all([
        lta_found,
        "in_game" in VALID_LIVE_STATUSES,
        is_draft_complete,
        meets_criteria
    ])
    
    if all_good:
        print("🎉 TODAS AS CORREÇÕES APLICADAS CORRETAMENTE!")
        print("✅ Sistema deveria estar funcionando")
        print("⚠️  Se ainda não funciona, é problema de cache do Railway")
    else:
        print("❌ ALGUMAS CORREÇÕES NÃO FORAM APLICADAS")
        if not lta_found:
            print("   ❌ LTA Norte não encontrada")
        if "in_game" not in VALID_LIVE_STATUSES:
            print("   ❌ in_game não encontrado")
        if not is_draft_complete:
            print("   ❌ Draft não sendo detectado como completo")
        if not meets_criteria:
            print("   ❌ Critérios de qualidade falhando")
    
    # 6. Informações de debug
    print(f"\n🔧 DEBUG INFO:")
    print(f"   📁 Processed maps: {len(tips_system.processed_maps)}")
    print(f"   ⏰ Uptime: {tips_system.get_uptime_hours():.2f}h")

if __name__ == "__main__":
    asyncio.run(test_corrections()) 