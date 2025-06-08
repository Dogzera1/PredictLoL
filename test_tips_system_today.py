import asyncio
import os
from datetime import datetime
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic.prediction_system import DynamicPredictionSystem
from bot.telegram_bot.alerts_system import TelegramAlertsSystem

async def test_tips_system_today():
    print(f'🎯 TESTE SISTEMA DE TIPS - {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    # Configura APIs
    pandascore_key = os.getenv('PANDASCORE_API_KEY')
    riot_key = os.getenv('RIOT_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    print(f'🔑 Chaves configuradas: PandaScore: {"✅" if pandascore_key else "❌"}, Riot: {"✅" if riot_key else "❌"}, Telegram: {"✅" if telegram_token else "❌"}')
    print()
    
    try:
        # Inicializa componentes
        print('🚀 Inicializando componentes...')
        
        # APIs
        pandascore_client = PandaScoreAPIClient(pandascore_key)
        riot_client = RiotAPIClient(riot_key)
        
        # Sistemas de análise necessários
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        
        game_analyzer = LoLGameAnalyzer()
        units_system = ProfessionalUnitsSystem()
        
        # Sistema de predição
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        
        # Telegram (se disponível)
        telegram_alerts = None
        if telegram_token:
            telegram_alerts = TelegramAlertsSystem(bot_token=telegram_token)
        
        # Sistema de Tips
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system,
            telegram_alerts=telegram_alerts
        )
        
        print('✅ Todos os componentes inicializados')
        print()
        
        # Força scan de partidas
        print('🔍 Executando scan forçado de partidas...')
        scan_result = await tips_system.force_scan()
        
        print(f'📊 Resultado do Scan:')
        print(f'   Partidas ao vivo encontradas: {scan_result.get("live_matches_found", 0)}')
        print(f'   Partidas analisadas: {scan_result.get("matches_analyzed", 0)}')
        print(f'   Tips geradas: {scan_result.get("tips_generated", 0)}')
        print(f'   Tip principal gerada: {"✅ Sim" if scan_result.get("tip_generated", False) else "❌ Não"}')
        print()
        
        # Verifica estatísticas do sistema
        stats = tips_system.get_monitoring_status()
        print('📈 Estatísticas do Sistema:')
        print(f'   Tips geradas (total): {stats.get("tips_generated", 0)}')
        print(f'   Tips enviadas: {stats.get("tips_sent", 0)}')
        print(f'   Tips inválidas: {stats.get("tips_invalid", 0)}')
        print(f'   Matches processados: {stats.get("matches_processed", 0)}')
        print(f'   Uptime: {stats.get("uptime_hours", 0):.1f}h')
        print()
        
        # Verifica tips recentes
        recent_tips = tips_system.get_recent_tips(limit=5)
        print('💎 Tips Recentes:')
        if recent_tips:
            for i, tip in enumerate(recent_tips, 1):
                print(f'   {i}. {tip["match"]} ({tip["league"]})')
                print(f'      Tip: {tip["tip_on"]} @ {tip["odds"]} - {tip["units"]} unidades')
                print(f'      Confiança: {tip["confidence"]:.1f}% | EV: {tip["ev"]:.2f}% | Status: {tip["status"]}')
                print(f'      Gerada há: {(datetime.now().timestamp() - tip["generated_at"]) / 60:.1f} min')
                print()
        else:
            print('   ❌ Nenhuma tip encontrada')
        
        print()
        
        # Testa geração manual se não há tips
        if not recent_tips or len(recent_tips) == 0:
            print('🛠️  DIAGNÓSTICO: Por que não há tips?')
            print('-' * 40)
            
            # Verifica rate limiting
            can_generate = tips_system._can_generate_tip()
            print(f'1. Rate limiting OK: {"✅" if can_generate else "❌"}')
            
            if not can_generate:
                print(f'   Tips na última hora: {len(tips_system.last_tip_times)}')
                print(f'   Limite por hora: {tips_system.max_tips_per_hour}')
            
            # Verifica partidas ao vivo
            print('2. Buscando partidas ao vivo manualmente...')
            live_matches_panda = await pandascore_client.get_lol_live_matches()
            live_matches_riot = await riot_client.get_live_matches()
            
            print(f'   PandaScore: {len(live_matches_panda)} partidas')
            print(f'   Riot: {len(live_matches_riot)} eventos')
            
            # Testa processamento de uma partida específica
            if live_matches_panda:
                print('3. Testando processamento de partida específica...')
                test_match = live_matches_panda[0]
                
                # Extrai dados básicos
                team1 = test_match.get('opponents', [{}])[0].get('opponent', {}).get('name', 'Team1')
                team2 = test_match.get('opponents', [{}])[1].get('opponent', {}).get('name', 'Team2') if len(test_match.get('opponents', [])) > 1 else 'Team2'
                league = test_match.get('league', {}).get('name', 'Unknown')
                
                print(f'   Partida: {team1} vs {team2} ({league})')
                
                # Converte para MatchData e testa análise
                from bot.data_models.match_data import MatchData
                
                match_data = MatchData(
                    match_id=str(test_match.get('id', 'test')),
                    team1_name=team1,
                    team2_name=team2,
                    league=league,
                    game_time_seconds=600,  # 10 minutos simulados
                    status='running'
                )
                
                # Testa geração de tip
                tip = await tips_system._generate_tip_for_match(match_data)
                
                if tip:
                    print(f'   ✅ Tip gerada: {tip.tip_on_team} @ {tip.odds}')
                    print(f'   Confiança: {tip.confidence_percentage:.1f}% | EV: {tip.ev_percentage:.2f}%')
                else:
                    print('   ❌ Tip não foi gerada')
                    print('   Possíveis motivos:')
                    print('     - Dados insuficientes de draft')
                    print('     - Confiança abaixo do limite')
                    print('     - EV insuficiente')
                    print('     - Odds fora dos critérios')
        
        # Cleanup
        await pandascore_client.close_session()
        if telegram_alerts:
            await telegram_alerts.cleanup()
        
        print('=' * 60)
        print('DIAGNÓSTICO COMPLETO')
        
    except Exception as e:
        print(f'❌ Erro no teste: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tips_system_today()) 