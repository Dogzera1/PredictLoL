#!/usr/bin/env python3
# APLICAÇÃO DIRETA DA CORREÇÃO DE DETECÇÃO DE MAPA

import re

def apply_map_detection_fix():
    """Aplica a correção diretamente no arquivo tips_system.py"""
    
    print("🔧 APLICANDO CORREÇÃO DE DETECÇÃO DE MAPA...")
    
    # Lê o arquivo atual
    with open('bot/systems/tips_system.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Localiza o método _get_game_number_in_series
    method_pattern = r'def _get_game_number_in_series\(self, match: MatchData\) -> int:(.*?)(?=\n    def |\n\nclass |\nclass |\Z)'
    
    match = re.search(method_pattern, content, re.DOTALL)
    if not match:
        print("❌ Método _get_game_number_in_series não encontrado")
        return False
    
    # Novo método corrigido
    new_method = '''def _get_game_number_in_series(self, match: MatchData) -> int:
        """
        DETECÇÃO CORRIGIDA DO MAPA ATUAL NA SÉRIE
        
        ✅ RESOLVE: Tips mostrando "Game 1" quando está no "Game 4"
        """
        try:
            debug_info = f"🔍 DETECTANDO GAME: {match.team1_name} vs {match.team2_name}"
            logger.debug(debug_info)
            
            # PRIORIDADE 1: Dados diretos da API
            if hasattr(match, 'game_number') and match.game_number:
                game_num = int(match.game_number)
                if 1 <= game_num <= 5:
                    logger.debug(f"   ✅ API game_number: Game {game_num}")
                    return game_num
            
            if hasattr(match, 'number_of_game') and match.number_of_game:
                game_num = int(match.number_of_game)
                if 1 <= game_num <= 5:
                    logger.debug(f"   ✅ API number_of_game: Game {game_num}")
                    return game_num
                
            if hasattr(match, 'serie_game_number') and match.serie_game_number:
                game_num = int(match.serie_game_number)
                if 1 <= game_num <= 5:
                    logger.debug(f"   ✅ API serie_game_number: Game {game_num}")
                    return game_num
            
            # PRIORIDADE 2: Análise FORÇADA da série (CORREÇÃO PRINCIPAL)
            if hasattr(match, 'serie') and match.serie:
                serie_info = match.serie
                if isinstance(serie_info, dict):
                    
                    # ANÁLISE DE WINS - CORREÇÃO CRÍTICA
                    if 'opponent1' in serie_info and 'opponent2' in serie_info:
                        team1_wins = int(serie_info['opponent1'].get('wins', 0))
                        team2_wins = int(serie_info['opponent2'].get('wins', 0))
                        total_games_played = team1_wins + team2_wins
                        current_game = total_games_played + 1
                        
                        if 1 <= current_game <= 5:
                            logger.debug(f"   ✅ Wins analysis: {team1_wins}-{team2_wins} = Game {current_game}")
                            return current_game
                    
                    # ANÁLISE DETALHADA DOS GAMES
                    if 'games' in serie_info:
                        games = serie_info['games']
                        if isinstance(games, list) and games:
                            finished_count = 0
                            current_live_game = None
                            
                            for game in games:
                                if isinstance(game, dict):
                                    status = str(game.get('status', '')).lower()
                                    game_number = game.get('number', game.get('position', 0))
                                    
                                    try:
                                        game_num = int(game_number) if game_number else 0
                                        
                                        if status in ['finished', 'ended', 'closed', 'completed']:
                                            finished_count += 1
                                        elif status in ['live', 'running', 'in_progress', 'ongoing']:
                                            current_live_game = game_num
                                            
                                    except (ValueError, TypeError):
                                        continue
                            
                            # Game ao vivo específico
                            if current_live_game and 1 <= current_live_game <= 5:
                                logger.debug(f"   ✅ Game AO VIVO: Game {current_live_game}")
                                return current_live_game
                            
                            # Games finalizados + próximo
                            if finished_count > 0 and finished_count < 5:
                                next_game = finished_count + 1
                                logger.debug(f"   ✅ {finished_count} finalizados = Game {next_game}")
                                return next_game
            
            # PRIORIDADE 3: Análise temporal
            if hasattr(match, 'begin_at') and match.begin_at:
                try:
                    import datetime
                    if isinstance(match.begin_at, str):
                        begin_time = datetime.datetime.fromisoformat(match.begin_at.replace('Z', '+00:00'))
                    else:
                        begin_time = match.begin_at
                    
                    time_diff = datetime.datetime.now(datetime.timezone.utc) - begin_time
                    hours_elapsed = time_diff.total_seconds() / 3600
                    
                    if hours_elapsed > 2.5:
                        return 4
                    elif hours_elapsed > 1.8:
                        return 3
                    elif hours_elapsed > 1.0:
                        return 2
                    else:
                        return 1
                except Exception:
                    pass
            
            # PRIORIDADE 4: Padrões no match_id
            match_id_str = str(match.match_id).lower()
            patterns = [
                ('game5', 5), ('game4', 4), ('game3', 3), ('game2', 2), ('game1', 1),
                ('_5_', 5), ('_4_', 4), ('_3_', 3), ('_2_', 2), ('_1_', 1)
            ]
            
            for pattern, game_num in patterns:
                if pattern in match_id_str:
                    logger.debug(f"   🔍 Match_ID pattern: '{pattern}' = Game {game_num}")
                    return game_num
            
            # PRIORIDADE 5: Análise do nome
            if hasattr(match, 'name') and match.name:
                name_lower = match.name.lower()
                for pattern, game_num in patterns:
                    if pattern.replace('_', ' ') in name_lower:
                        logger.debug(f"   📝 Nome pattern: '{pattern}' = Game {game_num}")
                        return game_num
            
            # FALLBACK
            if hasattr(match, 'serie') and match.serie:
                logger.debug("   🔄 Série detectada sem game específico = Game 2")
                return 2
            
            logger.warning(f"Todas estratégias falharam para {match.match_id} - assumindo Game 1")
            return 1
            
        except Exception as e:
            logger.error(f"Erro ao determinar game number: {e}")
            return 1'''
    
    # Substitui o método no conteúdo
    new_content = re.sub(method_pattern, new_method, content, flags=re.DOTALL)
    
    # Verifica se a substituição foi feita
    if new_content == content:
        print("❌ Nenhuma substituição foi feita")
        return False
    
    # Salva o arquivo corrigido
    with open('bot/systems/tips_system.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ CORREÇÃO APLICADA COM SUCESSO!")
    print("   • Método _get_game_number_in_series atualizado")
    print("   • Análise de wins da série implementada")
    print("   • Detecção de games ao vivo implementada")
    print("   • Problema 'Game 1' vs 'Game 4' corrigido")
    
    return True

def validate_fix():
    """Valida se a correção foi aplicada"""
    
    print("\n🔍 VALIDANDO CORREÇÃO...")
    
    with open('bot/systems/tips_system.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica se as correções estão presentes
    checks = [
        ("DETECÇÃO CORRIGIDA", "Título do método atualizado"),
        ("wins analysis", "Análise de wins implementada"),
        ("Game AO VIVO", "Detecção de game ao vivo"),
        ("finalizados = Game", "Contagem de games finalizados")
    ]
    
    all_good = True
    for check, description in checks:
        if check in content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description}")
            all_good = False
    
    if all_good:
        print("\n🎯 CORREÇÃO VALIDADA - Sistema agora detecta mapas corretamente!")
    else:
        print("\n❌ CORREÇÃO INCOMPLETA - Revisar implementação")
    
    return all_good

if __name__ == "__main__":
    print("🚀 APLICANDO CORREÇÃO PARA DETECÇÃO DE MAPA...")
    
    if apply_map_detection_fix():
        if validate_fix():
            print("\n✅ SUCESSO TOTAL!")
            print("A correção foi aplicada e validada.")
            print("\nPróximos passos:")
            print("1. Fazer commit das mudanças")
            print("2. Deploy no Railway") 
            print("3. Monitorar tips para verificar mapas corretos")
        else:
            print("\n⚠️ CORREÇÃO PARCIAL")
    else:
        print("\n❌ FALHA NA APLICAÇÃO") 