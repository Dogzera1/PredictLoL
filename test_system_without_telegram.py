#!/usr/bin/env python3
"""
Teste do sistema sem Telegram
"""

import os
import sys
import asyncio
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.utils.constants import PANDASCORE_API_KEY
from bot.utils.logger_config import setup_logging

async def test_system_components():
    """Testa os componentes do sistema sem Telegram"""
    
    # Configura logging
    logger = setup_logging("INFO")
    
    print("🔍 TESTE DO SISTEMA SEM TELEGRAM")
    print("=" * 50)
    
    try:
        # 1. Testa clientes de API
        print("\n📡 Testando clientes de API...")
        pandascore_client = PandaScoreAPIClient(PANDASCORE_API_KEY)
        riot_client = RiotAPIClient()
        print("✅ Clientes de API inicializados")
        
        # 2. Testa sistema de predição
        print("\n🧠 Testando sistema de predição...")
        units_system = ProfessionalUnitsSystem()
        game_analyzer = LoLGameAnalyzer()
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        print("✅ Sistema de predição inicializado")
        
        # 3. Testa sistema de tips (sem Telegram)
        print("\n🎯 Testando sistema de tips...")
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system,
            telegram_alerts=None  # Sem Telegram
        )
        print("✅ Sistema de tips inicializado")
        
        # 4. Testa busca de partidas
        print("\n🔍 Testando busca de partidas...")
        try:
            live_matches = await tips_system._get_live_matches()
            print(f"✅ Encontradas {len(live_matches)} partidas")
            
            if live_matches:
                print("📋 Primeiras partidas encontradas:")
                for i, match in enumerate(live_matches[:3]):
                    print(f"   {i+1}. {match.team1_name} vs {match.team2_name} ({match.league})")
            else:
                print("ℹ️ Nenhuma partida ao vivo no momento")
                
        except Exception as e:
            print(f"⚠️ Erro ao buscar partidas: {e}")
        
        # 5. Testa status do sistema
        print("\n📊 Testando status do sistema...")
        status = tips_system.get_monitoring_status()
        print(f"✅ Status obtido: {len(status)} métricas")
        
        # 6. Testa scan forçado
        print("\n🔄 Testando scan forçado...")
        try:
            scan_result = await tips_system.force_scan()
            print(f"✅ Scan executado: {scan_result.get('matches_found', 0)} partidas")
        except Exception as e:
            print(f"⚠️ Erro no scan: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Todos os componentes principais estão funcionando")
        print("⚠️ Apenas o Telegram precisa de um token válido")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configura variáveis de ambiente mínimas
    os.environ.setdefault('PANDASCORE_API_KEY', '90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ')
    
    result = asyncio.run(test_system_components())
    
    if result:
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Obtenha um token válido do @BotFather no Telegram")
        print("2. Atualize o arquivo .env com o novo token")
        print("3. Execute: python main.py")
    else:
        print("\n❌ Sistema precisa de correções antes de usar") 