#!/usr/bin/env python3
"""
Teste completo do sistema - Verificar se tudo está funcionando
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Configuração do path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

async def teste_sistema_completo():
    """Testa se o sistema está funcionando completamente"""
    
    print("🔍 TESTE COMPLETO DO SISTEMA DE TIPS")
    print("=" * 60)
    print(f"🕐 Horário: {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}")
    print()
    
    # 1. Verificar se consegue importar os módulos principais
    print("📦 1. VERIFICANDO IMPORTS...")
    try:
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.systems.schedule_manager import ScheduleManager
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        print("   ✅ Todos os imports funcionando")
    except Exception as e:
        print(f"   ❌ Erro nos imports: {e}")
        return
    
    # 2. Verificar conectividade das APIs
    print("\n🌐 2. VERIFICANDO CONECTIVIDADE DAS APIS...")
    
    # PandaScore API
    try:
        pandascore = PandaScoreAPIClient()
        partidas_pandascore = await pandascore.get_lol_live_matches()
        print(f"   ✅ PandaScore API: {len(partidas_pandascore)} partidas encontradas")
    except Exception as e:
        print(f"   ❌ PandaScore API: {e}")
        pandascore = None
    
    # Riot API
    try:
        riot = RiotAPIClient()
        eventos_riot = await riot.get_live_events()
        print(f"   ✅ Riot API: {len(eventos_riot)} eventos encontrados")
    except Exception as e:
        print(f"   ❌ Riot API: {e}")
        riot = None
    
    # 3. Verificar se o sistema de tips pode ser inicializado
    print("\n💎 3. VERIFICANDO SISTEMA DE TIPS...")
    if pandascore and riot:
        try:
            analyzer = LoLGameAnalyzer()
            units = ProfessionalUnitsSystem()
            prediction = DynamicPredictionSystem(analyzer, units)
            
            tips_system = ProfessionalTipsSystem(
                pandascore_client=pandascore,
                riot_client=riot,
                prediction_system=prediction
            )
            print("   ✅ Sistema de Tips inicializado com sucesso")
            
            # Teste de scan
            print("\n🔍 4. TESTANDO SCAN DE PARTIDAS...")
            resultado = await tips_system.force_scan()
            print(f"   📊 Partidas escaneadas: {resultado.get('matches_scanned', 0)}")
            print(f"   🎯 Tips geradas: {resultado.get('tips_generated', 0)}")
            print(f"   ✅ Tips válidas: {resultado.get('valid_tips', 0)}")
            
            if resultado.get('tips_generated', 0) > 0:
                print("   🎉 SISTEMA ESTÁ GERANDO TIPS!")
            else:
                print("   ⚠️ Nenhuma tip gerada (normal quando não há jogos)")
                
        except Exception as e:
            print(f"   ❌ Erro no sistema de tips: {e}")
    else:
        print("   ❌ Não foi possível testar - APIs não funcionaram")
    
    # 4. Verificar configurações do sistema
    print("\n⚙️ 5. VERIFICANDO CONFIGURAÇÕES...")
    
    # Verificar variáveis de ambiente importantes
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    admin_ids = os.getenv("TELEGRAM_ADMIN_USER_IDS", "")
    
    print(f"   📱 Telegram Token: {'✅ Configurado' if telegram_token else '❌ Não configurado'}")
    print(f"   👥 Admin IDs: {'✅ Configurado' if admin_ids else '❌ Não configurado'}")
    
    # 5. Status geral do sistema
    print("\n📊 6. STATUS GERAL DO SISTEMA...")
    
    # Verificar se há algum processo do sistema rodando
    if os.path.exists("bot.lock"):
        print("   🔒 Sistema parece estar rodando (arquivo de lock existe)")
    else:
        print("   🔓 Sistema não está rodando localmente")
    
    # Verificar se está no Railway
    railway_env = os.getenv("RAILWAY_ENVIRONMENT_ID")
    if railway_env:
        print(f"   🚂 Rodando no Railway: {railway_env}")
    else:
        print("   💻 Rodando localmente")
    
    # 6. Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO FINAL")
    print("=" * 60)
    
    if pandascore and riot:
        print("🟢 SISTEMA ESTÁ FUNCIONANDO")
        print("✅ APIs conectadas")
        print("✅ Sistema de tips operacional")
        if resultado.get('tips_generated', 0) > 0:
            print("✅ Gerando tips ativamente")
        else:
            print("⚠️ Aguardando jogos para gerar tips")
    else:
        print("🔴 SISTEMA COM PROBLEMAS")
        print("❌ APIs não conectaram")
        print("❌ Verificar internet/configurações")
    
    print("\n💡 MOTIVOS PARA NÃO RECEBER TIPS:")
    print("1. 🕐 Não há jogos profissionais no momento")
    print("2. 📊 Jogos não atendem critérios de qualidade")
    print("3. 🎯 Confiança das tips está baixa (< 65%)")
    print("4. 💰 Odds muito baixas (< 1.50)")
    print("5. ⏰ Rate limit ativo (máx 5 tips/hora)")
    print("6. 🤖 Bot não está rodando no Railway")
    
    print("\n🔧 PARA RECEBER TIPS:")
    print("1. ✅ Aguardar jogos profissionais (LEC, LCS, LCK)")
    print("2. ✅ Verificar se bot está rodando no Railway")
    print("3. ✅ Configurar token do Telegram")
    print("4. ✅ Adicionar seu ID aos administradores")

if __name__ == "__main__":
    asyncio.run(teste_sistema_completo()) 