# TESTE E CORREÇÃO: PROBLEMA DE DETECÇÃO DE MAPA
# Demonstra o problema de mostrar "Game 1" quando está no "Game 4"

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data_models.match_data import MatchData

def demo_current_problem():
    """Demonstra o problema atual"""
    
    print("🚨 PROBLEMA REPORTADO: Tips mostrando 'Game 1' quando está no 'Game 4'")
    print("=" * 60)
    
    # Simula um match que está no Game 4 da série
    match_game4 = MatchData(
        match_id="lta_north_series_game4_live",
        team1_name="FlyQuest",
        team2_name="Cloud9", 
        league="LTA Norte",
        status="in_game"
    )
    
    # Dados da série indicando que estamos no Game 4
    match_game4.serie = {
        "opponent1": {"wins": 2},  # FlyQuest ganhou 2 games
        "opponent2": {"wins": 1},  # Cloud9 ganhou 1 game
        "games": [
            {"number": 1, "status": "finished"},  # Game 1 finalizado
            {"number": 2, "status": "finished"},  # Game 2 finalizado  
            {"number": 3, "status": "finished"},  # Game 3 finalizado
            {"number": 4, "status": "live"}       # Game 4 AO VIVO (atual)
        ]
    }
    
    print(f"📊 DADOS DA SÉRIE:")
    print(f"   • FlyQuest wins: 2")
    print(f"   • Cloud9 wins: 1") 
    print(f"   • Total games jogados: 3")
    print(f"   • Game atual deveria ser: 4")
    print(f"   • Status dos games: 3 finalizados + 1 ao vivo")
    
    return match_game4

def enhanced_game_detection(match: MatchData) -> int:
    """
    VERSÃO CORRIGIDA: Detecção robusta do mapa atual
    """
    
    print(f"\n🔍 DETECTANDO MAPA ATUAL:")
    print(f"   Match: {match.team1_name} vs {match.team2_name}")
    print(f"   Match_ID: {match.match_id}")
    
    # ESTRATÉGIA 1: Análise da série (wins dos times)
    if hasattr(match, 'serie') and match.serie:
        serie_info = match.serie
        if isinstance(serie_info, dict):
            
            # Contagem de wins para determinar game atual
            if 'opponent1' in serie_info and 'opponent2' in serie_info:
                team1_wins = int(serie_info['opponent1'].get('wins', 0))
                team2_wins = int(serie_info['opponent2'].get('wins', 0))
                total_games_played = team1_wins + team2_wins
                current_game = total_games_played + 1
                
                if 1 <= current_game <= 5:
                    print(f"   ✅ Análise wins: {team1_wins}-{team2_wins} = Game {current_game}")
                    return current_game
            
            # Análise detalhada dos games da série
            if 'games' in serie_info:
                games = serie_info['games']
                if isinstance(games, list) and games:
                    current_live_game = None
                    finished_count = 0
                    
                    for game in games:
                        if isinstance(game, dict):
                            status = str(game.get('status', '')).lower()
                            game_number = game.get('number', 0)
                            
                            if status in ['finished', 'ended', 'closed']:
                                finished_count += 1
                            elif status in ['live', 'running', 'in_progress']:
                                current_live_game = game_number
                    
                    if current_live_game:
                        print(f"   ✅ Game AO VIVO detectado: Game {current_live_game}")
                        return current_live_game
                    
                    if finished_count > 0:
                        next_game = finished_count + 1
                        print(f"   ✅ {finished_count} games finalizados = Game {next_game}")
                        return next_game
    
    # ESTRATÉGIA 2: Análise do match_id
    match_id_str = str(match.match_id).lower()
    patterns = [
        ('game5', 5), ('game4', 4), ('game3', 3), ('game2', 2), ('game1', 1)
    ]
    
    for pattern, game_num in patterns:
        if pattern in match_id_str:
            print(f"   ✅ Pattern no match_id: '{pattern}' = Game {game_num}")
            return game_num
    
    print(f"   ⚠️ Não conseguiu determinar - assumindo Game 1")
    return 1

def test_correction():
    """Testa a correção"""
    
    print("\n" + "="*60)
    print("🧪 TESTANDO CORREÇÃO")
    print("="*60)
    
    # Teste com o match problemático
    match = demo_current_problem()
    
    # Aplica detecção corrigida
    detected_game = enhanced_game_detection(match)
    
    print(f"\n📋 RESULTADO:")
    print(f"   Game detectado: {detected_game}")
    
    if detected_game == 4:
        print("   ✅ SUCESSO! Detectou corretamente Game 4")
        return True
    else:
        print(f"   ❌ FALHOU! Deveria ser Game 4, mas detectou Game {detected_game}")
        return False

def generate_fix_implementation():
    """Gera a implementação da correção"""
    
    print("\n" + "="*60)
    print("🔧 IMPLEMENTAÇÃO DA CORREÇÃO")
    print("="*60)
    
    fix_code = '''
# CORREÇÃO PARA APLICAR NO MÉTODO _get_game_number_in_series():

def _get_game_number_in_series(self, match: MatchData) -> int:
    """VERSÃO CORRIGIDA - Detecta corretamente o mapa atual da série"""
    try:
        # PRIORIDADE 1: Análise da série (wins dos times)
        if hasattr(match, 'serie') and match.serie:
            serie_info = match.serie
            if isinstance(serie_info, dict):
                
                # Contagem PRECISA de wins
                if 'opponent1' in serie_info and 'opponent2' in serie_info:
                    team1_wins = int(serie_info['opponent1'].get('wins', 0))
                    team2_wins = int(serie_info['opponent2'].get('wins', 0))
                    total_games_played = team1_wins + team2_wins
                    current_game = total_games_played + 1
                    
                    if 1 <= current_game <= 5:
                        logger.debug(f"Wins analysis: {team1_wins}-{team2_wins} = Game {current_game}")
                        return current_game
                
                # Análise dos games da série
                if 'games' in serie_info:
                    games = serie_info['games']
                    if isinstance(games, list) and games:
                        current_live_game = None
                        finished_count = 0
                        
                        for game in games:
                            if isinstance(game, dict):
                                status = str(game.get('status', '')).lower()
                                game_number = game.get('number', 0)
                                
                                if status in ['finished', 'ended', 'closed']:
                                    finished_count += 1
                                elif status in ['live', 'running', 'in_progress']:
                                    current_live_game = game_number
                        
                        if current_live_game and 1 <= current_live_game <= 5:
                            logger.debug(f"Game ao vivo: Game {current_live_game}")
                            return current_live_game
                        
                        if finished_count > 0 and finished_count < 5:
                            next_game = finished_count + 1
                            logger.debug(f"{finished_count} finalizados = Game {next_game}")
                            return next_game
        
        # PRIORIDADE 2: Análise do match_id (resto do código original...)
        # [restante da implementação existente]
        
        return 1
        
    except Exception as e:
        logger.error(f"Erro ao determinar game number: {e}")
        return 1
'''
    
    print(fix_code)
    
    print("\n📝 PASSOS PARA APLICAR:")
    print("1. Localizar método _get_game_number_in_series() no arquivo tips_system.py")
    print("2. Substituir por esta versão corrigida")
    print("3. Testar com dados reais")
    print("4. Deploy no Railway")

async def main():
    """Execução principal"""
    
    print("🔍 DIAGNÓSTICO: PROBLEMA DE DETECÇÃO DE MAPA")
    print("Tip mostra 'Game 1' quando deveria mostrar 'Game 4'")
    
    # Demonstra o problema
    demo_current_problem()
    
    # Testa a correção
    if test_correction():
        print("\n✅ CORREÇÃO VALIDADA!")
        print("A solução proposta resolve o problema.")
        
        # Gera implementação
        generate_fix_implementation()
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. Aplicar correção no código")
        print("2. Fazer deploy no Railway")  
        print("3. Monitorar tips para verificar se mostram mapas corretos")
    else:
        print("\n❌ CORREÇÃO FALHOU!")
        print("Precisa revisar a lógica de detecção.")

if __name__ == "__main__":
    asyncio.run(main()) 