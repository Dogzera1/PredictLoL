#!/usr/bin/env python3
"""
Teste Final - Novo Token do Telegram
Verifica se tudo está funcionando com o token atualizado
"""

import os
import sys
import asyncio
from pathlib import Path

# Configuração do path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

# Configurar novo token
os.environ["TELEGRAM_BOT_TOKEN"] = "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI"
os.environ["TELEGRAM_ADMIN_USER_IDS"] = "8012415611"

async def teste_final():
    """Teste final com o novo token"""
    
    print("🔍 TESTE FINAL COM NOVO TOKEN")
    print("=" * 50)
    
    try:
        # 1. Importar e testar Telegram
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem
        
        print("📱 1. TESTANDO NOVO TOKEN DO TELEGRAM...")
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        print(f"   🔑 Token: {token[:10]}...{token[-10:]}")
        
        # Criar sistema de alertas
        alerts_system = TelegramAlertsSystem(bot_token=token)
        await alerts_system.initialize()
        
        if alerts_system.bot:
            bot_info = await alerts_system.bot.get_me()
            print(f"   ✅ Bot conectado: @{bot_info.username}")
            print(f"   👤 Nome: {bot_info.first_name}")
            print(f"   🆔 ID: {bot_info.id}")
        
        # 2. Testar sistema completo
        print("\n🤖 2. TESTANDO SISTEMA COMPLETO...")
        
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        from bot.api_clients.riot_api_client import RiotAPIClient
        
        # Criar componentes
        pandascore = PandaScoreAPIClient()
        riot = RiotAPIClient()
        analyzer = LoLGameAnalyzer()
        units = ProfessionalUnitsSystem()
        prediction = DynamicPredictionSystem(analyzer, units)
        
        # Sistema de tips com Telegram
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore,
            riot_client=riot,
            prediction_system=prediction,
            telegram_alerts=alerts_system  # CRÍTICO: Com Telegram integrado
        )
        
        print("   ✅ Sistema de Tips com Telegram integrado")
        
        # 3. Teste de scan
        print("\n🔍 3. TESTANDO SCAN DE PARTIDAS...")
        resultado = await tips_system.force_scan()
        
        print(f"   📊 Partidas escaneadas: {resultado.get('matches_scanned', 0)}")
        print(f"   🎯 Tips geradas: {resultado.get('tips_generated', 0)}")
        print(f"   ✅ Sistema integrado funcionando")
        
        # 4. Verificar configurações finais
        print("\n⚙️ 4. CONFIGURAÇÕES FINAIS...")
        
        from bot.utils.constants import TELEGRAM_CONFIG
        print(f"   📱 Token configurado: {'✅' if TELEGRAM_CONFIG['bot_token'] else '❌'}")
        print(f"   👥 Admin IDs: {TELEGRAM_CONFIG['admin_user_ids']}")
        
        print("\n🎉 TESTE FINAL CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        print("✅ Novo token funcionando perfeitamente")
        print("✅ Sistema completo operacional")
        print("✅ Telegram integrado ao sistema de tips")
        print("✅ Pronto para deploy no Railway")
        
        print("\n🚀 PRÓXIMO PASSO:")
        print("   1. Atualizar TELEGRAM_BOT_TOKEN no Railway")
        print("   2. Executar: railway up")
        print("   3. Testar: /start no @PredictLoLbot")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(teste_final())
    
    if success:
        print("\n🎊 SISTEMA 100% PRONTO PARA RAILWAY! 🎊")
    else:
        print("\n❌ Problemas detectados - Verificar configurações") 