import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data_models.tip_data import ProfessionalTip
from bot.data_models.match_data import MatchData
from bot.systems.tips_system import ProfessionalTipsSystem

def test_map_number_formatting():
    """Testa se map_number está sendo exibido corretamente nas tips"""
    
    # Cria tip com map_number = 2 (Game 2)
    tip_game2 = ProfessionalTip(
        match_id="test_match_123",
        team_a="Team Liquid",
        team_b="Cloud9",
        league="LCS",
        tournament="LCS Spring 2024",
        tip_on_team="Team Liquid ML",
        odds=2.1,
        units=2.5,
        risk_level="Risco Médio",
        confidence_percentage=67.5,
        ev_percentage=8.3,
        analysis_reasoning="TL com draft mais forte no late game",
        game_time_at_tip="2min",
        game_time_seconds=120,
        map_number=2,  # GAME 2
        prediction_source="ML System",
        data_quality_score=0.89
    )
    
    # Testa formatação da mensagem
    message = tip_game2.format_telegram_message()
    
    print("=== TESTE: MAP NUMBER FORMATTING ===\n")
    print("Tip com map_number = 2:")
    print(message)
    print("\n" + "="*50)
    
    # Verifica se contém informação do mapa
    if "Game 2" in message:
        print("✅ SUCESSO: Map number está sendo exibido corretamente!")
    else:
        print("❌ ERRO: Map number NÃO está sendo exibido!")
        print("Procurando por 'Game 2' na mensagem...")
    
    # Cria tip com map_number = 1 (Game 1)
    tip_game1 = ProfessionalTip(
        match_id="test_match_456",
        team_a="FlyQuest",
        team_b="TSM",
        league="LCS",
        tournament="LCS Spring 2024", 
        tip_on_team="FlyQuest ML",
        odds=1.85,
        units=3.0,
        risk_level="Risco Baixo",
        confidence_percentage=72.8,
        ev_percentage=12.1,
        analysis_reasoning="FQ dominando early game",
        game_time_at_tip="1min",
        game_time_seconds=60,
        map_number=1,  # GAME 1
        prediction_source="ML System",
        data_quality_score=0.92
    )
    
    message2 = tip_game1.format_telegram_message()
    
    print("\nTip com map_number = 1:")
    print(message2)
    print("\n" + "="*50)
    
    # Verifica se contém informação do mapa
    if "Game 1" in message2:
        print("✅ SUCESSO: Map number está sendo exibido para Game 1!")
    else:
        print("❌ ERRO: Map number NÃO está sendo exibido para Game 1!")

if __name__ == "__main__":
    test_map_number_formatting() 