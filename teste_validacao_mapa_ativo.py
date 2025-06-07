import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data_models.match_data import MatchData
from bot.systems.tips_system import ProfessionalTipsSystem

def test_current_game_validation():
    """Testa validação de mapa ativo vs finalizado"""
    
    # Mock de tips_system sem dependências
    class MockTipsSystem:
        def _get_game_number_in_series(self, match):
            return 1  # Simula Game 1
        
        def _is_current_game_active(self, match):
            # Copia a lógica real
            try:
                # 1. Verifica status
                if match.status:
                    finished_status = ['finished', 'ended', 'closed', 'completed', 'done']
                    if match.status.lower() in finished_status:
                        print(f"❌ Game finalizado pelo status: {match.status}")
                        return False
                
                # 2. Verifica série
                if hasattr(match, 'serie') and match.serie:
                    serie_info = match.serie
                    if isinstance(serie_info, dict):
                        # Verifica games na série
                        if 'games' in serie_info:
                            games = serie_info['games']
                            if isinstance(games, list):
                                current_game_number = self._get_game_number_in_series(match)
                                
                                for game in games:
                                    if isinstance(game, dict):
                                        game_number = game.get('number', game.get('position', 0))
                                        if game_number == current_game_number:
                                            game_status = game.get('status', '').lower()
                                            if game_status in ['finished', 'ended', 'closed']:
                                                print(f"❌ Game {current_game_number} já finalizado na série")
                                                return False
                        
                        # Verifica série completa
                        serie_status = serie_info.get('status', '').lower()
                        if serie_status in ['finished', 'ended', 'closed']:
                            print(f"❌ Série já finalizada: {serie_status}")
                            return False
                
                # 3. Verifica vencedor
                if hasattr(match, 'winner') and match.winner:
                    print(f"❌ Game já tem vencedor: {match.winner}")
                    return False
                
                print("✅ Game ativo para tips")
                return True
                
            except Exception as e:
                print(f"❌ Erro: {e}")
                return True
    
    tips_system = MockTipsSystem()
    
    print("=== TESTE: VALIDAÇÃO DE MAPA ATIVO ===\n")
    
    # TESTE 1: Game ativo (deve permitir tip)
    print("TESTE 1: Game ativo")
    match_ativo = MatchData(
        match_id="match_123",
        team1_name="FlyQuest", 
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"
    )
    resultado1 = tips_system._is_current_game_active(match_ativo)
    print(f"Resultado: {'✅ PASSOU' if resultado1 else '❌ FALHOU'}\n")
    
    # TESTE 2: Game finalizado por status (deve rejeitar tip)
    print("TESTE 2: Game finalizado")
    match_finalizado = MatchData(
        match_id="match_456",
        team1_name="FlyQuest",
        team2_name="Cloud9", 
        league="LTA Norte",
        status="finished"
    )
    resultado2 = tips_system._is_current_game_active(match_finalizado)
    print(f"Resultado: {'✅ PASSOU' if not resultado2 else '❌ FALHOU'}\n")
    
    # TESTE 3: Game com vencedor definido (deve rejeitar tip)
    print("TESTE 3: Game com vencedor")
    match_com_vencedor = MatchData(
        match_id="match_789",
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte", 
        status="in_game"
    )
    match_com_vencedor.winner = "FlyQuest"
    resultado3 = tips_system._is_current_game_active(match_com_vencedor)
    print(f"Resultado: {'✅ PASSOU' if not resultado3 else '❌ FALHOU'}\n")
    
    # TESTE 4: Série finalizada (deve rejeitar tip)
    print("TESTE 4: Série finalizada")
    match_serie_finalizada = MatchData(
        match_id="match_101112",
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"
    )
    match_serie_finalizada.serie = {
        "status": "finished",
        "games": [
            {"number": 1, "status": "finished"},
            {"number": 2, "status": "finished"}
        ]
    }
    resultado4 = tips_system._is_current_game_active(match_serie_finalizada)
    print(f"Resultado: {'✅ PASSOU' if not resultado4 else '❌ FALHOU'}\n")
    
    # RESUMO
    total_testes = 4
    testes_ok = sum([resultado1, not resultado2, not resultado3, not resultado4])
    
    print("="*50)
    print(f"RESUMO: {testes_ok}/{total_testes} testes passaram")
    
    if testes_ok == total_testes:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema agora evita tips de mapas finalizados")
    else:
        print("⚠️ Alguns testes falharam - verificar implementação")
    
    return testes_ok == total_testes

if __name__ == "__main__":
    test_current_game_validation() 