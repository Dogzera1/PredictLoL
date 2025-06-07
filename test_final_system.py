#!/usr/bin/env python3
"""
Teste final do sistema com novo token
"""

import os
import sys
import asyncio
from datetime import datetime

# Configura encoding para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

async def test_final_system():
    """Teste final do sistema"""
    
    print("🎯 TESTE FINAL DO SISTEMA PREDICTLOL")
    print("=" * 50)
    
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # 1. Verifica token do Telegram
    print("\n🔍 Verificando token do Telegram...")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        print(f"✅ Token encontrado: {token[:10]}...{token[-10:]}")
        
        # Testa token
        import aiohttp
        url = f"https://api.telegram.org/bot{token}/getMe"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    if response.status == 200 and data.get('ok'):
                        bot_info = data['result']
                        print(f"✅ Token válido!")
                        print(f"   Bot: @{bot_info.get('username', 'N/A')}")
                        print(f"   Nome: {bot_info.get('first_name', 'N/A')}")
                        print(f"   ID: {bot_info.get('id', 'N/A')}")
                        telegram_ok = True
                    else:
                        print(f"❌ Token inválido: {data}")
                        telegram_ok = False
        except Exception as e:
            print(f"❌ Erro ao testar token: {e}")
            telegram_ok = False
    else:
        print("❌ Token não encontrado")
        telegram_ok = False
    
    # 2. Testa componentes principais
    print("\n🧠 Testando componentes principais...")
    try:
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.utils.constants import PANDASCORE_API_KEY
        
        # Inicializa componentes
        pandascore_client = PandaScoreAPIClient(PANDASCORE_API_KEY)
        riot_client = RiotAPIClient()
        units_system = ProfessionalUnitsSystem()
        game_analyzer = LoLGameAnalyzer()
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system,
            telegram_alerts=None
        )
        
        print("✅ Todos os componentes inicializados com sucesso!")
        components_ok = True
        
    except Exception as e:
        print(f"❌ Erro nos componentes: {e}")
        components_ok = False
    
    # 3. Testa busca de partidas
    print("\n🔍 Testando busca de partidas...")
    try:
        live_matches = await tips_system._get_live_matches()
        print(f"✅ Encontradas {len(live_matches)} partidas ao vivo")
        
        if live_matches:
            print("📋 Partidas encontradas:")
            for i, match in enumerate(live_matches[:3]):
                print(f"   {i+1}. {match.team1_name} vs {match.team2_name} ({match.league})")
        
        matches_ok = True
        
    except Exception as e:
        print(f"❌ Erro ao buscar partidas: {e}")
        matches_ok = False
    
    # 4. Resultado final
    print("\n" + "=" * 50)
    print("📊 RESULTADO FINAL")
    print("=" * 50)
    
    total_tests = 3
    passed_tests = sum([telegram_ok, components_ok, matches_ok])
    
    print(f"✅ Testes passaram: {passed_tests}/{total_tests}")
    print(f"📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")
    
    if telegram_ok:
        print("✅ Token do Telegram: VÁLIDO")
    else:
        print("❌ Token do Telegram: INVÁLIDO")
    
    if components_ok:
        print("✅ Componentes do sistema: FUNCIONANDO")
    else:
        print("❌ Componentes do sistema: COM PROBLEMAS")
    
    if matches_ok:
        print("✅ Busca de partidas: FUNCIONANDO")
    else:
        print("❌ Busca de partidas: COM PROBLEMAS")
    
    print("\n" + "=" * 50)
    
    if passed_tests == total_tests:
        print("🎉 SISTEMA 100% FUNCIONAL!")
        print("🚀 Pronto para produção!")
        print("\n📋 Para usar:")
        print("1. Execute: python main.py")
        print("2. Acesse: http://localhost:8080/health")
        print("3. Use comandos do Telegram: /start, /subscribe")
    else:
        print("⚠️ Sistema parcialmente funcional")
        print(f"📊 {passed_tests}/{total_tests} componentes OK")
        
        if not telegram_ok:
            print("\n🔧 Para corrigir o Telegram:")
            print("1. Vá ao @BotFather")
            print("2. Use /newbot ou /token")
            print("3. Atualize o .env")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    result = asyncio.run(test_final_system())
    
    if result:
        print("\n✅ Verificação concluída com SUCESSO!")
    else:
        print("\n⚠️ Verificação concluída com PROBLEMAS") 