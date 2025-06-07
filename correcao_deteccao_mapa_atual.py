# CORREÇÃO CRÍTICA: DETECÇÃO CORRETA DO MAPA ATUAL
# Resolve problema de tips mostrando "Mapa 1" quando jogo está no mapa 4

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data_models.match_data import MatchData

def enhanced_game_number_detection(match: MatchData) -> int:
    """
    DETECÇÃO APRIMORADA DO NÚMERO DO MAPA ATUAL
    
    Usa múltiplas estratégias para detectar corretamente qual mapa está sendo jogado
    """
    
    print(f"🔍 DETECTANDO MAPA ATUAL PARA: {match.team1_name} vs {match.team2_name}")
    
    # ESTRATÉGIA 1: Informação direta da API
    direct_sources = [
        getattr(match, 'game_number', None),
        getattr(match, 'number_of_game', None), 
        getattr(match, 'serie_game_number', None),
        getattr(match, 'current_game', None),
        getattr(match, 'game_in_series', None)
    ]
    
    for i, source in enumerate(direct_sources):
        if source and isinstance(source, (int, str)):
            try:
                game_num = int(source)
                if 1 <= game_num <= 5:
                    print(f"   ✅ Fonte direta {i+1}: Game {game_num}")
                    return game_num
            except (ValueError, TypeError):
                continue
    
    # ESTRATÉGIA 2: Análise da série (wins dos times)
    if hasattr(match, 'serie') and match.serie:
        serie_info = match.serie
        if isinstance(serie_info, dict):
            
            # 2a: Contagem de wins
            if 'opponent1' in serie_info and 'opponent2' in serie_info:
                team1_wins = serie_info['opponent1'].get('wins', 0)
                team2_wins = serie_info['opponent2'].get('wins', 0)
                total_games_played = team1_wins + team2_wins
                current_game = total_games_played + 1
                
                if 1 <= current_game <= 5:
                    print(f"   ✅ Análise wins: {team1_wins}-{team2_wins} = Game {current_game}")
                    return current_game
            
            # 2b: Lista de games da série
            if 'games' in serie_info:
                games = serie_info['games']
                if isinstance(games, list) and games:
                    # Conta games finalizados
                    finished_count = 0
                    current_live_game = None
                    
                    for game in games:
                        if isinstance(game, dict):
                            status = game.get('status', '').lower()
                            game_number = game.get('number', game.get('position', 0))
                            
                            if status in ['finished', 'ended', 'closed']:
                                finished_count += 1
                            elif status in ['live', 'running', 'in_progress']:
                                current_live_game = game_number
                    
                    if current_live_game:
                        print(f"   ✅ Game ao vivo detectado: Game {current_live_game}")
                        return current_live_game
                    
                    if finished_count < 5:  # Série ainda não acabou
                        next_game = finished_count + 1
                        print(f"   ✅ {finished_count} games finalizados = Game {next_game}")
                        return next_game
    
    # ESTRATÉGIA 3: Análise temporal (tempo decorrido desde início da série)
    if hasattr(match, 'begin_at') and match.begin_at:
        try:
            import datetime
            if isinstance(match.begin_at, str):
                begin_time = datetime.datetime.fromisoformat(match.begin_at.replace('Z', '+00:00'))
            else:
                begin_time = match.begin_at
            
            time_diff = datetime.datetime.now(datetime.timezone.utc) - begin_time
            hours_elapsed = time_diff.total_seconds() / 3600
            
            # Estimativa baseada em tempo médio por game (~45min = 0.75h)
            estimated_game = min(5, max(1, int(hours_elapsed / 0.75) + 1))
            
            if hours_elapsed > 0.5:  # Só usa se passou tempo suficiente
                print(f"   ⏰ Análise temporal: {hours_elapsed:.1f}h = Game {estimated_game}")
                return estimated_game
        except Exception as e:
            print(f"   ❌ Erro análise temporal: {e}")
    
    # ESTRATÉGIA 4: Análise do match_id
    match_id_str = str(match.match_id).lower()
    
    # Padrões mais específicos
    patterns = [
        ('game5', 5), ('g5', 5), ('_5_', 5), ('map5', 5),
        ('game4', 4), ('g4', 4), ('_4_', 4), ('map4', 4),
        ('game3', 3), ('g3', 3), ('_3_', 3), ('map3', 3), 
        ('game2', 2), ('g2', 2), ('_2_', 2), ('map2', 2),
        ('game1', 1), ('g1', 1), ('_1_', 1), ('map1', 1)
    ]
    
    for pattern, game_num in patterns:
        if pattern in match_id_str:
            print(f"   🔍 Padrão no match_id: '{pattern}' = Game {game_num}")
            return game_num
    
    # ESTRATÉGIA 5: Análise do nome da partida
    if hasattr(match, 'name') and match.name:
        name_lower = match.name.lower()
        for pattern, game_num in patterns:
            if pattern.replace('_', ' ') in name_lower:
                print(f"   📝 Padrão no nome: '{pattern}' = Game {game_num}")
                return game_num
    
    # ESTRATÉGIA 6: Contexto do tempo de jogo
    game_minutes = getattr(match, 'game_time_minutes', 0) or 0
    if callable(game_minutes):
        game_minutes = game_minutes()
    
    # Se o jogo tem muito tempo (>40min), provavelmente não é Game 1
    if game_minutes > 40:
        estimated_game = min(3, 2)  # Provavelmente Game 2 ou 3
        print(f"   ⏱️ Tempo de jogo {game_minutes}min = provavelmente Game {estimated_game}")
        return estimated_game
    
    # ÚLTIMA OPÇÃO: Se todas falharam, tenta inferir do contexto
    print("   ⚠️ TODAS as estratégias falharam - usando fallback")
    
    # Se tem dados de série mas não conseguiu detectar, assume que é um game posterior
    if hasattr(match, 'serie') and match.serie:
        print("   🔄 Tem dados de série = assumindo Game 2")
        return 2
    
    # Se não tem dados de série, pode ser Game 1
    print("   🔄 Sem dados de série = assumindo Game 1")
    return 1

def test_game_detection():
    """Testa detecção de mapa com diferentes cenários"""
    
    print("=== TESTE: DETECÇÃO APRIMORADA DO MAPA ===\n")
    
    # Teste 1: Match com dados de wins
    print("TESTE 1: Match com dados de wins na série")
    match_wins = MatchData(
        match_id="match_123",
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"
    )
    match_wins.serie = {
        "opponent1": {"wins": 2},  # 2 wins para team1
        "opponent2": {"wins": 1}   # 1 win para team2
    }
    # Total: 3 games jogados = próximo é Game 4
    
    game_num1 = enhanced_game_number_detection(match_wins)
    print(f"   Resultado: Game {game_num1} {'✅' if game_num1 == 4 else '❌'}\n")
    
    # Teste 2: Match_id com padrão
    print("TESTE 2: Match_id com padrão de game")
    match_pattern = MatchData(
        match_id="series_flyquest_vs_cloud9_game4", 
        team1_name="FlyQuest",
        team2_name="Cloud9",
        league="LTA Norte",
        status="in_game"
    )
    
    game_num2 = enhanced_game_number_detection(match_pattern)
    print(f"   Resultado: Game {game_num2} {'✅' if game_num2 == 4 else '❌'}\n")
    
    print("🎯 SOLUÇÃO: Sistema agora usa múltiplas estratégias")
    print("   • Dados diretos da API")
    print("   • Análise de wins na série") 
    print("   • Análise temporal")
    print("   • Padrões no match_id")
    print("   • Contexto do tempo de jogo")

if __name__ == "__main__":
    test_game_detection() 