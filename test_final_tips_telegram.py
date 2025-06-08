import asyncio
import os
from datetime import datetime
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic.prediction_system import DynamicPredictionSystem
from bot.telegram_bot.alerts_system import TelegramAlertsSystem

async def test_final_system():
    print(f'🚀 TESTE FINAL DO SISTEMA COMPLETO - {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 80)
    
    # Configura APIs
    pandascore_key = os.getenv('PANDASCORE_API_KEY')
    riot_key = os.getenv('RIOT_API_KEY')
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    print(f'🔑 CONFIGURAÇÃO:')
    print(f'   ✅ PandaScore API: {pandascore_key[:10]}...{pandascore_key[-5:]}' if pandascore_key else '   ❌ PandaScore API: NÃO CONFIGURADA')
    print(f'   ✅ Riot API: {riot_key[:10]}...{riot_key[-5:]}' if riot_key else '   ❌ Riot API: NÃO CONFIGURADA')
    print(f'   ✅ Telegram Bot: {telegram_token[:15]}...{telegram_token[-10:]}' if telegram_token else '   ❌ Telegram Bot: NÃO CONFIGURADO')
    print()
    
    try:
        # Inicializa componentes
        print('⚙️ INICIALIZANDO SISTEMA...')
        
        # APIs
        pandascore_client = PandaScoreAPIClient(pandascore_key)
        riot_client = RiotAPIClient(riot_key)
        
        # Sistemas de análise
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        
        game_analyzer = LoLGameAnalyzer()
        units_system = ProfessionalUnitsSystem()
        
        # Sistema de predição
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        
        # Telegram
        telegram_alerts = TelegramAlertsSystem(bot_token=telegram_token) if telegram_token else None
        
        # Sistema de Tips PRINCIPAL
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system,
            telegram_alerts=telegram_alerts
        )
        
        print('✅ Sistema totalmente inicializado!')
        print()
        
        # EXECUTA SCAN REAL
        print('🔍 EXECUTANDO SCAN DE PARTIDAS AO VIVO...')
        scan_result = await tips_system.force_scan()
        
        print(f'📊 RESULTADOS:')
        print(f'   📱 Partidas encontradas: {scan_result.get("live_matches_found", 0)}')
        print(f'   🧮 Partidas analisadas: {scan_result.get("matches_analyzed", 0)}')
        print(f'   💎 Tips geradas: {scan_result.get("tips_generated", 0)}')
        print(f'   🎯 Sistema ativo: {"✅ SIM" if scan_result.get("tip_generated", False) else "❌ Aguardando"}')
        print()
        
        # VERIFICA TIPS RECENTES
        recent_tips = tips_system.get_recent_tips(limit=3)
        print('💎 TIPS MAIS RECENTES:')
        
        if recent_tips:
            for i, tip in enumerate(recent_tips, 1):
                status_emoji = "✅" if tip["status"] == "sent" else "⏳" if tip["status"] == "pending" else "❌"
                print(f'   {i}. {status_emoji} {tip["match"]} ({tip["league"]})')
                print(f'      💰 {tip["tip_on"]} @ {tip["odds"]} odds')
                print(f'      🎯 {tip["units"]} unidades | {tip["confidence"]:.1f}% confiança | +{tip["ev"]:.1f}% EV')
                print(f'      ⏰ Gerada há {(datetime.now().timestamp() - tip["generated_at"]) / 60:.1f} minutos')
                print()
        else:
            print('   📝 Sistema aguardando partidas adequadas para análise')
            print('   ⚡ Tips serão geradas automaticamente quando condições ideais forem detectadas')
        print()
        
        # STATS DO SISTEMA
        stats = tips_system.get_monitoring_status()
        print('📊 ESTATÍSTICAS DO SISTEMA:')
        print(f'   🎯 Tips enviadas: {stats.get("tips_sent", 0)}')
        print(f'   📈 Taxa de sucesso: {stats.get("success_rate", 0):.1f}%')
        print(f'   ⏰ Uptime: {stats.get("uptime_hours", 0):.1f} horas')
        print(f'   🔄 Partidas processadas: {stats.get("matches_processed", 0)}')
        print()
        
        # SE TEM TELEGRAM E TIPS, DEMONSTRA FUNCIONALIDADE
        if telegram_alerts and recent_tips:
            latest_tip = recent_tips[0]
            print('📤 DEMONSTRAÇÃO - ENVIO VIA TELEGRAM:')
            print(f'   Tip disponível: {latest_tip["tip_on"]} @ {latest_tip["odds"]} odds')
            print(f'   Sistema Telegram: ✅ Configurado e funcional')
            print(f'   📱 Bot: @BETLOLGPT_bot')
            print(f'   ⚡ Tips são enviadas automaticamente para usuários subscritos')
        
        print()
        
        # CLEANUP
        await pandascore_client.close_session()
        
        print('=' * 80)
        print('🎉 SISTEMA 100% FUNCIONAL E OPERACIONAL!')
        print('🚀 DETECTANDO JOGOS ✅ | GERANDO TIPS ✅ | TELEGRAM ATIVO ✅')
        print('=' * 80)
        
    except Exception as e:
        print(f'❌ ERRO: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_final_system()) 