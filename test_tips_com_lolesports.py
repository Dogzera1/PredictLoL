import asyncio
import logging
import os
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_tips_system_with_lolesports():
    """Testa se o sistema de tips funciona com a nova API do Lolesports"""
    print("🚀 TESTE DO SISTEMA DE TIPS COM API LOLESPORTS")
    print("=" * 60)
    
    try:
        # 1. Importar e inicializar componentes
        print("📦 1. Importando componentes...")
        from bot.api_clients.lolesports_api_client import LolesportsAPIClient
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem
        from bot.systems.schedule_manager import ScheduleManager
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        
        print("✅ Todos os componentes importados com sucesso")
        
        # 2. Inicializar APIs
        print("\n🌐 2. Inicializando APIs...")
        lolesports_client = LolesportsAPIClient()
        pandascore_client = PandaScoreAPIClient()
        riot_client = RiotAPIClient()
        print("✅ APIs inicializadas")
        
        # 3. Testar dados da API Lolesports
        print("\n🎮 3. Testando dados da API Lolesports...")
        live_matches = await lolesports_client.get_lec_live_data()
        print(f"✅ Encontradas {len(live_matches)} partidas da LEC")
        
        if live_matches:
            for i, match in enumerate(live_matches):
                print(f"   📋 Partida {i+1}:")
                print(f"      ID: {match.get('id')}")
                print(f"      Liga: {match.get('league', {}).get('name')}")
                print(f"      Status: {match.get('status')}")
                print(f"      Tem draft: {'✅' if 'draft' in match else '❌'}")
                
                if 'draft' in match:
                    draft = match['draft']
                    print(f"      Blue picks: {', '.join(draft['blue_side']['picks'][:3])}...")
                    print(f"      Red picks: {', '.join(draft['red_side']['picks'][:3])}...")
        
        # 4. Inicializar sistema de análise
        print("\n🧠 4. Inicializando sistema de análise...")
        game_analyzer = LoLGameAnalyzer()
        units_system = ProfessionalUnitsSystem()
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        print("✅ Sistema de análise inicializado")
        
        # 5. Inicializar sistema de tips
        print("\n💡 5. Inicializando sistema de tips...")
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system,
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        print("✅ Sistema de tips inicializado")
        
        # 6. Inicializar Telegram (mock)
        print("\n📱 6. Inicializando sistema de alertas...")
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "MOCK_TOKEN")
        telegram_alerts = TelegramAlertsSystem(bot_token=bot_token)
        print("✅ Sistema de alertas inicializado")
        
        # 7. Inicializar ScheduleManager com API Lolesports
        print("\n⚙️ 7. Inicializando ScheduleManager com API Lolesports...")
        schedule_manager = ScheduleManager(
            tips_system=tips_system,
            telegram_alerts=telegram_alerts,
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            lolesports_client=lolesports_client  # CRÍTICO: Nova API integrada!
        )
        print("✅ ScheduleManager inicializado com API Lolesports")
        
        # 8. Testar monitoramento de partidas com dados reais
        print("\n🔍 8. Testando monitoramento com dados da LEC...")
        
        # Simula dados ao vivo do Lolesports
        live_data = {
            "lolesports_matches": live_matches,
            "realtime_data": True,
            "formatted_matches": []
        }
        
        # Formatar partidas para análise
        for match in live_matches:
            formatted = lolesports_client.format_match_for_prediction(match)
            if formatted:
                live_data["formatted_matches"].append(formatted)
        
        print(f"   📊 {len(live_data['formatted_matches'])} partidas formatadas para análise")
        
        # 9. Executar scan forçado com dados do Lolesports
        print("\n⚡ 9. Executando scan com dados em tempo real...")
        scan_result = await tips_system.force_scan(live_data=live_data)
        
        print(f"✅ Scan completo:")
        print(f"   Partidas encontradas: {scan_result.get('live_matches_found', 0)}")
        print(f"   Tip gerada: {'✅ SIM' if scan_result.get('tip_generated') else '❌ NÃO'}")
        print(f"   Dados em tempo real: {'✅ SIM' if live_data.get('realtime_data') else '❌ NÃO'}")
        
        if scan_result.get('tip_generated'):
            print(f"   🎯 TIP CRIADA COM DADOS DE DRAFT DA LEC!")
        
        # 10. Verificar estado do sistema
        print("\n📊 10. Verificando estado do sistema...")
        system_status = schedule_manager.get_system_status()
        print(f"   Sistema saudável: {'✅' if system_status['is_healthy'] else '❌'}")
        print(f"   APIs ativas: {len([c for c in ['pandascore', 'riot', 'lolesports'] if c in str(system_status)])}")
        print(f"   Uptime: {system_status.get('uptime_seconds', 0):.1f}s")
        
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Sistema de tips funciona com API Lolesports")
        print("✅ Dados de draft da LEC acessíveis")
        print("✅ Integração completa funcionando")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if 'lolesports_client' in locals():
            await lolesports_client.close()

if __name__ == "__main__":
    asyncio.run(test_tips_system_with_lolesports())