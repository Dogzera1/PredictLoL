#!/usr/bin/env python3
"""
DEBUG ESPECÍFICO: Encontrar discrepância no método _match_meets_quality_criteria
"""

import asyncio
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
from bot.data_models.match_data import MatchData

def debug_method_line_by_line(tips_system, match):
    """Debug cada linha do método real"""
    
    print("🔍 DEBUGGING MÉTODO REAL LINHA POR LINHA")
    print("-" * 50)
    
    # Vou copiar o método real e adicionar prints
    try:
        # 1. Liga suportada
        league_name = match.league
        if isinstance(match.league, dict):
            league_name = match.league.get('name', '')
        
        print(f"🏆 Liga recebida: '{league_name}'")
        
        # Verifica se está na lista
        is_supported = False
        league_key = league_name.upper()
        
        for supported_league in tips_system.quality_filters["supported_leagues"]:
            if supported_league.upper() in league_key or league_key in supported_league.upper():
                is_supported = True
                print(f"   ✅ Match encontrado: '{supported_league}'")
                break
        
        print(f"   📊 Liga suportada: {is_supported}")
        if not is_supported:
            print("   ❌ RETURN FALSE: Liga não suportada")
            return False
        
        # 2. Status válido
        from bot.utils.constants import VALID_LIVE_STATUSES
        has_valid_status = match.status in VALID_LIVE_STATUSES
        
        # Verifica se é Riot live match (sem status mas com match_id)
        is_riot_live = (not match.status or match.status == "") and hasattr(match, 'match_id') and match.match_id
        
        print(f"📊 Status: '{match.status}' → Válido: {has_valid_status}")
        print(f"📊 Riot Live: {is_riot_live}")
        
        if not (has_valid_status or is_riot_live):
            print("   ❌ RETURN FALSE: Status inválido")
            return False
        
        # 3. Draft completo
        is_draft_complete = tips_system._is_draft_complete(match)
        print(f"📋 Draft completo: {is_draft_complete}")
        if not is_draft_complete:
            print("   ❌ RETURN FALSE: Draft incompleto")
            return False
        
        # 4. Timing
        game_minutes = match.get_game_time_minutes()
        print(f"⏰ Game time: {game_minutes:.1f} minutos")
        
        if game_minutes > 2.0:
            print("   ❌ RETURN FALSE: Muito tarde")
            return False
        
        # 5. QUALIDADE - AQUI PODE ESTAR A DIFERENÇA
        data_quality = match.calculate_data_quality()
        min_quality = tips_system.quality_filters["min_data_quality"]
        
        print(f"📊 Qualidade calculada: {data_quality:.1%}")
        print(f"📊 Qualidade mínima: {min_quality:.1%}")
        
        # Verifica se tem composição completa
        has_composition = (hasattr(match, 'team1_composition') and match.team1_composition and
                          hasattr(match, 'team2_composition') and match.team2_composition)
        
        print(f"🎮 Tem composição: {has_composition}")
        
        # REDUZ REQUISITO SE TEM COMPOSIÇÃO
        if has_composition:
            old_min = min_quality
            min_quality = max(0.4, min_quality - 0.2)  # Reduz 20%
            print(f"   📉 Qualidade ajustada: {old_min:.1%} → {min_quality:.1%}")
        
        # Para partidas da Riot API, aceita qualidade menor
        if is_riot_live and data_quality >= 0.3:
            print("   ✅ RIOT API: Qualidade aceita para Riot (≥30%)")
        elif data_quality < min_quality:
            print(f"   ❌ QUALIDADE BAIXA: {data_quality:.1%} < {min_quality:.1%}")
            
            # MAS AQUI PODE TER MAIS LÓGICA!
            # Vou verificar se o método real tem mais condições
            
            # Se é partida recente E tem draft completo, pode aceitar qualidade menor
            if game_minutes <= 2.0 and is_draft_complete:
                print("   💡 CONDIÇÃO ESPECIAL: Partida recente + draft completo")
                print("   ✅ ACEITA qualidade menor para situação ideal")
                # Continue para próximos checks
            else:
                print("   ❌ RETURN FALSE: Qualidade insuficiente")
                return False
        
        # 6. Eventos
        events_count = len(match.events) if hasattr(match, 'events') else 0
        min_events = tips_system.quality_filters["required_events"]
        
        print(f"📊 Eventos: {events_count} (mín: {min_events})")
        
        if events_count < min_events:
            # Para partidas Riot com dados básicos, aceita
            if is_riot_live and match.team1_name and match.team2_name:
                print("   ✅ RIOT API: Aceita sem eventos (tem nomes dos times)")
            elif game_minutes <= 2.0 and is_draft_complete:
                print("   ✅ TIMING IDEAL: Aceita sem eventos (draft recém completo)")
            else:
                print("   ❌ RETURN FALSE: Eventos insuficientes")
                return False
        
        print("✅ PASSOU EM TODOS OS FILTROS!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

async def main():
    """Main debug"""
    
    print("🚨 DEBUG DISCREPÂNCIA")
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
        match_id="debug_discrepancia",
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"
    )
    match.team1_composition = ["Azir", "Graves", "Thresh", "Jinx", "Jax"]
    match.team2_composition = ["Orianna", "Sejuani", "Nautilus", "Aphelios", "Gnar"]
    match.game_time = "00:01:00"
    
    print(f"🎮 TESTE: {match.team1_name} vs {match.team2_name}")
    print(f"🏆 Liga: {match.league}")
    print(f"📊 Status: {match.status}")
    print(f"⏰ Tempo: {match.game_time}")
    
    # Debug manual detalhado
    print(f"\n" + "="*50)
    manual_result = debug_method_line_by_line(tips_system, match)
    
    # Método original
    print(f"\n" + "="*50)
    print("🔄 MÉTODO ORIGINAL:")
    original_result = tips_system._match_meets_quality_criteria(match)
    
    print(f"\n📊 RESULTADOS:")
    print(f"   🛠️  Debug manual: {manual_result}")
    print(f"   ⚙️  Método original: {original_result}")
    
    if manual_result != original_result:
        print(f"\n⚠️  DISCREPÂNCIA CONFIRMADA!")
        print(f"❓ O método original tem lógica que não estou capturando")
        
        # Vou tentar descobrir o que mais tem no método original
        print(f"\n🔍 INVESTIGANDO MÉTODO ORIGINAL...")
        
        # Vou chamar o método original em modo debug
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        try:
            # Força debug
            original_result2 = tips_system._match_meets_quality_criteria(match)
            print(f"   Segunda chamada: {original_result2}")
        except Exception as e:
            print(f"   Erro na segunda chamada: {e}")
            
    else:
        print(f"\n✅ RESULTADOS CONSISTENTES")
        print(f"✅ Debug manual capturou toda a lógica")

if __name__ == "__main__":
    asyncio.run(main()) 