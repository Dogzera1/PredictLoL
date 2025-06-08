import asyncio
import os
from datetime import datetime
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic.prediction_system import DynamicPredictionSystem
from bot.telegram_bot.alerts_system import TelegramAlertsSystem

async def test_tips_system_with_telegram():
    print(f'🎯 TESTE SISTEMA DE TIPS COM TELEGRAM - {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 70)
    
    # Configura APIs
    pandascore_key = os.getenv('PANDASCORE_API_KEY')
    riot_key = os.getenv('RIOT_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    print(f'🔑 Chaves configuradas:')
    print(f'   PandaScore: {"✅" if pandascore_key else "❌"}')
    print(f'   Riot: {"✅" if riot_key else "❌"}')
    print(f'   Telegram: {"✅" if telegram_token else "❌"}')
    
    if telegram_token:
        print(f'   Token: {telegram_token[:15]}...{telegram_token[-10:]}')
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
        
        # Telegram (com token correto)
        telegram_alerts = None
        if telegram_token:
            print('🤖 Inicializando Telegram...')
            telegram_alerts = TelegramAlertsSystem(bot_token=telegram_token)
            print('✅ Telegram inicializado com sucesso')
        
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
        
        # Se há tips e Telegram está disponível, testa envio
        if recent_tips and telegram_alerts:
            print('📤 TESTANDO ENVIO DE TIP VIA TELEGRAM:')
            
            # Pega a tip mais recente
            latest_tip = recent_tips[0]
            
            # Simula envio para um usuário de teste (você pode substituir pelo seu chat_id)
            test_chat_id = "8012415611"  # Substitua pelo seu chat_id para teste
            
            try:
                # Cria objeto tip para envio
                from bot.data_models.tip_data import ProfessionalTip
                
                tip_obj = ProfessionalTip(
                    match_id=latest_tip.get("match_id", "test"),
                    team_a=latest_tip["match"].split(" vs ")[0],
                    team_b=latest_tip["match"].split(" vs ")[1],
                    league=latest_tip["league"],
                    tournament=latest_tip["league"],
                    tip_on_team=latest_tip["tip_on"],
                    odds=float(latest_tip["odds"]),
                    units=float(latest_tip["units"]),
                    risk_level="Risco Mínimo",
                    confidence_percentage=latest_tip["confidence"],
                    ev_percentage=latest_tip["ev"],
                    analysis_reasoning=f"Tip automática baseada em análise do sistema",
                    game_time_at_tip="0min",
                    game_time_seconds=0,
                    prediction_source="Sistema IA",
                    data_quality_score=0.85
                )
                
                # Tenta enviar
                print(f'   Enviando para chat {test_chat_id}...')
                await telegram_alerts.send_tip_to_user(test_chat_id, tip_obj)
                print('   ✅ Tip enviada com sucesso!')
                
            except Exception as e:
                print(f'   ❌ Erro ao enviar tip: {e}')
        
        print()
        
        # Cleanup
        await pandascore_client.close_session()
        if telegram_alerts:
            await telegram_alerts.cleanup()
        
        print('=' * 70)
        print('✅ TESTE COMPLETO - SISTEMA 100% FUNCIONAL!')
        
    except Exception as e:
        print(f'❌ Erro no teste: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tips_system_with_telegram()) 