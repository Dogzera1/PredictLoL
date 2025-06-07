#!/usr/bin/env python3
"""
TESTE URGENTE: Validar se correções foram aplicadas
"""

import asyncio
import time
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
from bot.data_models.match_data import MatchData

async def teste_urgente():
    """Teste urgente das correções"""
    
    print("🚨 TESTE URGENTE - VALIDANDO CORREÇÕES")
    print("="*50)
    
    # Inicializa sistema
    pandascore_client = PandaScoreAPIClient()
    riot_client = RiotAPIClient()
    
    # Sistemas ML necessários
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
    
    print("✅ Sistema inicializado")
    
    # Teste 1: Draft incompleto deve ser rejeitado
    print("\n🧪 TESTE 1: Draft incompleto")
    match_draft = MatchData(
        match_id="test_draft_incomplete",
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte",
        status="draft"  # Status de draft
    )
    match_draft.team1_composition = ["Azir", "", "", "", ""]  # 1/5
    match_draft.team2_composition = ["", "", "", "", ""]      # 0/5
    
    is_complete = tips_system._is_draft_complete(match_draft)
    meets_criteria = tips_system._match_meets_quality_criteria(match_draft)
    
    print(f"   Draft completo: {is_complete}")
    print(f"   Atende critérios: {meets_criteria}")
    print(f"   ✅ Resultado esperado: FALSE (draft incompleto)")
    
    # Teste 2: Draft completo deve ser aceito
    print("\n🧪 TESTE 2: Draft completo")
    match_complete = MatchData(
        match_id="test_draft_complete_game1",
        team1_name="FlyQuest", 
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"  # Status de jogo iniciado
    )
    match_complete.team1_composition = ["Azir", "Graves", "Thresh", "Jinx", "Jax"]
    match_complete.team2_composition = ["Orianna", "Sejuani", "Nautilus", "Aphelios", "Gnar"]
    match_complete.game_time = "00:01:00"  # 1 minuto de jogo
    
    is_complete = tips_system._is_draft_complete(match_complete)
    meets_criteria = tips_system._match_meets_quality_criteria(match_complete)
    map_id = tips_system._get_map_identifier(match_complete)
    
    print(f"   Draft completo: {is_complete}")
    print(f"   Atende critérios: {meets_criteria}")
    print(f"   Map ID: {map_id}")
    print(f"   ✅ Resultado esperado: TRUE (draft completo)")
    
    # Teste 3: Anti-repetição
    print("\n🧪 TESTE 3: Sistema anti-repetição")
    suitable_before = tips_system._filter_suitable_matches([match_complete])
    print(f"   Primeira verificação: {len(suitable_before)} adequadas")
    
    # Marca como processado
    tips_system.processed_maps.add(map_id)
    print(f"   Mapa marcado como processado")
    
    suitable_after = tips_system._filter_suitable_matches([match_complete])
    print(f"   Segunda verificação: {len(suitable_after)} adequadas")
    print(f"   ✅ Anti-repetição funcionando: {len(suitable_after) == 0}")
    
    # Teste 4: Game 2 deve ser aceito
    print("\n🧪 TESTE 4: Game 2 (diferente)")
    match_game2 = MatchData(
        match_id="test_draft_complete_game2",
        team1_name="FlyQuest",
        team2_name="Cloud9", 
        league="LTA Norte",
        status="in_game"
    )
    match_game2.team1_composition = ["Syndra", "Kindred", "Leona", "Kai'Sa", "Renekton"]
    match_game2.team2_composition = ["Viktor", "Hecarim", "Braum", "Ezreal", "Ornn"]
    match_game2.game_time = "00:01:30"
    
    map_id_2 = tips_system._get_map_identifier(match_game2)
    suitable_game2 = tips_system._filter_suitable_matches([match_game2])
    
    print(f"   Map ID Game 2: {map_id_2}")
    print(f"   Game 2 adequado: {len(suitable_game2)} partidas")
    print(f"   ✅ Game 2 aceito: {len(suitable_game2) > 0}")
    
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES:")
    print(f"1. ❌ Draft incompleto rejeitado: {not meets_criteria}")
    print(f"2. ✅ Draft completo aceito: {meets_criteria}")  
    print(f"3. ❌ Anti-repetição funcionando: {len(suitable_after) == 0}")
    print(f"4. ✅ Game 2 aceito: {len(suitable_game2) > 0}")
    
    if all([
        not meets_criteria,  # Draft incompleto rejeitado
        meets_criteria,      # Draft completo aceito  
        len(suitable_after) == 0,  # Anti-repetição funcionando
        len(suitable_game2) > 0    # Game 2 aceito
    ]):
        print("\n🎉 TODAS AS CORREÇÕES FUNCIONANDO!")
        print("✅ Sistema está corrigido localmente")
        print("⚠️  Railway precisa aplicar o deploy")
    else:
        print("\n⚠️  ALGUMAS CORREÇÕES NÃO ESTÃO FUNCIONANDO")
        print("❌ Revisar implementação")

if __name__ == "__main__":
    asyncio.run(teste_urgente()) 