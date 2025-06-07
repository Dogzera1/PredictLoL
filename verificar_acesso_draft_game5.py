# VERIFICAÇÃO: ACESSO AO DRAFT DO GAME 5 FINALIZADO
# Verifica se sistema está captando dados do draft que acabou de terminar

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients.pandascore_client import PandaScoreAPIClient
from bot.api_clients.riot_client import RiotAPIClient
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.systems.prediction_system import DynamicPredictionSystem

async def check_game5_draft_access():
    """Verifica se sistema tem acesso ao draft do Game 5"""
    
    print("🔍 VERIFICANDO ACESSO AO DRAFT DO GAME 5")
    print("=" * 50)
    
    try:
        # Inicializa clientes
        pandascore = PandaScoreAPIClient()
        riot = RiotAPIClient()
        prediction = DynamicPredictionSystem(pandascore, riot)
        tips_system = ProfessionalTipsSystem(pandascore, riot, prediction)
        
        print("✅ Sistemas inicializados")
        
        # Busca matches ativos
        print("\n📡 BUSCANDO MATCHES ATIVOS...")
        live_matches = await tips_system._get_live_matches()
        
        print(f"   📊 Total matches encontrados: {len(live_matches)}")
        
        if not live_matches:
            print("   ⚠️ Nenhum match ativo encontrado")
            return
        
        # Analisa cada match para encontrar Game 5
        game5_found = False
        
        for i, match in enumerate(live_matches):
            print(f"\n🎮 MATCH {i+1}:")
            print(f"   Teams: {match.team1_name} vs {match.team2_name}")
            print(f"   League: {match.league}")
            print(f"   Status: {match.status}")
            print(f"   Match ID: {match.match_id}")
            
            # Detecta número do game
            game_number = tips_system._get_game_number_in_series(match)
            print(f"   🗺️ Game detectado: {game_number}")
            
            # Verifica se é Game 5
            if game_number == 5:
                game5_found = True
                print(f"   🎯 GAME 5 ENCONTRADO!")
                
                # Verifica draft completo
                draft_complete = tips_system._is_draft_complete(match)
                print(f"   📝 Draft completo: {draft_complete}")
                
                # Verifica composições
                if hasattr(match, 'team1_composition') and match.team1_composition:
                    team1_champs = len(match.team1_composition)
                    print(f"   🔵 {match.team1_name}: {team1_champs} champions")
                    if team1_champs > 0:
                        champ_names = [c.get('name', 'Unknown') for c in match.team1_composition[:3]]
                        print(f"      Champions: {', '.join(champ_names)}...")
                else:
                    print(f"   🔵 {match.team1_name}: Sem dados de composição")
                
                if hasattr(match, 'team2_composition') and match.team2_composition:
                    team2_champs = len(match.team2_composition)
                    print(f"   🔴 {match.team2_name}: {team2_champs} champions")
                    if team2_champs > 0:
                        champ_names = [c.get('name', 'Unknown') for c in match.team2_composition[:3]]
                        print(f"      Champions: {', '.join(champ_names)}...")
                else:
                    print(f"   🔴 {match.team2_name}: Sem dados de composição")
                
                # Verifica se pode gerar tip
                can_generate = tips_system._match_meets_quality_criteria(match)
                print(f"   ✅ Atende critérios: {can_generate}")
                
                # Verifica se game está ativo
                game_active = tips_system._is_current_game_active(match)
                print(f"   🎮 Game ativo: {game_active}")
                
                # Verifica tempo de jogo
                game_time = match.get_game_time_minutes()
                print(f"   ⏱️ Tempo de jogo: {game_time} minutos")
                
                if draft_complete and can_generate and game_active:
                    print("   🚀 PRONTO PARA TIP!")
                    
                    # Tenta gerar tip
                    print("\n   🧠 TENTANDO GERAR TIP...")
                    tip = await tips_system._generate_tip_for_match(match)
                    
                    if tip:
                        print(f"   ✅ TIP GERADA!")
                        print(f"      Tipo: {tip.tip_type}")
                        print(f"      Confiança: {tip.confidence:.1f}%")
                        print(f"      EV: {tip.expected_value:.1f}%")
                        print(f"      Odds: {tip.odds}")
                    else:
                        print(f"   ❌ TIP NÃO GERADA")
                else:
                    print("   ⏳ Aguardando condições ideais")
                    if not draft_complete:
                        print("      - Draft ainda não completo")
                    if not can_generate:
                        print("      - Não atende critérios de qualidade")
                    if not game_active:
                        print("      - Game não está ativo")
        
        if not game5_found:
            print("\n⚠️ GAME 5 NÃO ENCONTRADO")
            print("   Verifique se:")
            print("   • Há uma série 2-2 em andamento")
            print("   • O Game 5 já começou")
            print("   • APIs estão retornando dados corretos")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

async def check_series_status():
    """Verifica status das séries em andamento"""
    
    print("\n" + "=" * 50)
    print("📊 STATUS DAS SÉRIES EM ANDAMENTO")
    print("=" * 50)
    
    try:
        pandascore = PandaScoreAPIClient()
        
        # Busca séries em andamento
        url = "https://api.pandascore.co/lol/series/running"
        params = {
            'token': pandascore.api_key,
            'per_page': 10
        }
        
        async with pandascore.session.get(url, params=params) as response:
            if response.status == 200:
                series = await response.json()
                
                print(f"📈 Séries ativas: {len(series)}")
                
                for i, serie in enumerate(series):
                    print(f"\n🏆 SÉRIE {i+1}:")
                    print(f"   Nome: {serie.get('name', 'N/A')}")
                    print(f"   Liga: {serie.get('league', {}).get('name', 'N/A')}")
                    
                    # Verifica games da série
                    if 'games' in serie:
                        games = serie['games']
                        total_games = len(games)
                        finished_games = len([g for g in games if g.get('status') == 'finished'])
                        
                        print(f"   Games: {finished_games}/{total_games} finalizados")
                        
                        if finished_games == 4:  # Série 2-2
                            print(f"   🔥 SÉRIE EMPATADA 2-2 - GAME 5 ESPERADO!")
                    
                    # Verifica opponents
                    if 'opponents' in serie:
                        opponents = serie['opponents']
                        if len(opponents) >= 2:
                            team1 = opponents[0].get('opponent', {}).get('name', 'Team1')
                            team2 = opponents[1].get('opponent', {}).get('name', 'Team2')
                            wins1 = opponents[0].get('wins', 0)
                            wins2 = opponents[1].get('wins', 0)
                            
                            print(f"   Placar: {team1} {wins1}-{wins2} {team2}")
                            
                            if wins1 == 2 and wins2 == 2:
                                print(f"   🎯 SÉRIE 2-2 CONFIRMADA!")
            else:
                print(f"❌ Erro ao buscar séries: {response.status}")
                
    except Exception as e:
        print(f"❌ ERRO: {e}")

async def main():
    """Execução principal"""
    
    print("🎮 VERIFICAÇÃO DE ACESSO AO DRAFT DO GAME 5")
    print("Verificando se sistema detecta o draft que acabou de terminar...")
    
    await check_game5_draft_access()
    await check_series_status()
    
    print("\n" + "=" * 50)
    print("📋 RESUMO:")
    print("• Se Game 5 foi encontrado → Sistema tem acesso ✅")
    print("• Se draft está completo → Pode gerar tips ✅") 
    print("• Se tip foi gerada → Sistema funcionando ✅")
    print("• Se não encontrou → Aguardar ou verificar APIs ⏳")

if __name__ == "__main__":
    asyncio.run(main()) 