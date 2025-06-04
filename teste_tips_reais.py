#!/usr/bin/env python3
"""
Teste Específico: Verificar se o sistema está gerando tips com partidas reais
Foco: Problema do campo 'units' na validação final
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adicionar diretório ao path (mesmo do main.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def verificar_tips_reais():
    """Verificar se o sistema está gerando tips com partidas reais"""
    print("🎯 TESTE ESPECÍFICO: GERAÇÃO DE TIPS REAIS")
    print("=" * 60)
    
    try:
        # Importar usando exatamente a mesma estrutura do main.py
        from bot.systems.schedule_manager import ScheduleManager
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
        from bot.utils.constants import PANDASCORE_API_KEY
        
        print("✅ Imports realizados com sucesso")
        
        # Inicializar componentes (mesma estrutura do main.py)
        print("🔧 Inicializando componentes...")
        
        # API Clients
        pandascore_client = PandaScoreAPIClient(PANDASCORE_API_KEY)
        riot_client = RiotAPIClient()
        
        # Sistema de predição
        units_system = ProfessionalUnitsSystem()
        game_analyzer = LoLGameAnalyzer()
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        
        # Sistema de Tips
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system
        )
        
        print("✅ Componentes inicializados")
        
        # Executa force scan para encontrar e processar partidas ao vivo
        print("\n🔍 Executando force scan do sistema de tips...")
        
        scan_result = await tips_system.force_scan()
        
        print(f"📊 Resultado do scan:")
        print(f"   🎮 Partidas analisadas: {scan_result.get('matches_analyzed', 0)}")
        print(f"   🎯 Tips geradas: {scan_result.get('tips_generated', 0)}")
        print(f"   ❌ Tips rejeitadas: {scan_result.get('tips_rejected', 0)}")
        print(f"   📊 Partidas encontradas: {scan_result.get('matches_found', 0)}")
        
        # Obter estatísticas do sistema
        system_status = tips_system.get_monitoring_status()
        print(f"\n📈 Status do sistema:")
        print(f"   🕐 Uptime: {system_status.get('uptime_hours', 0):.2f}h")
        print(f"   🎯 Total tips geradas: {system_status.get('tips_generated', 0)}")
        print(f"   📊 Partidas monitoradas: {system_status.get('matches_monitored', 0)}")
        
        # Verificar tips recentes
        recent_tips = tips_system.get_recent_tips(limit=5)
        
        if recent_tips:
            print(f"\n📋 Tips recentes encontradas: {len(recent_tips)}")
            
            for i, tip in enumerate(recent_tips, 1):
                print(f"\n   {i}. TIP ENCONTRADA:")
                print(f"      Match: {tip.get('match_info', 'N/A')}")
                print(f"      Tip: {tip.get('recommendation', 'N/A')}")
                print(f"      Confidence: {tip.get('confidence', 0):.1f}%")
                print(f"      Expected Value: {tip.get('expected_value', 0):.2f}")
                
                # VERIFICAR ESPECIFICAMENTE O CAMPO 'UNITS'
                units = tip.get('units', 'NÃO ENCONTRADO')
                print(f"      🔍 UNITS: {units}")
                
                if units and units != 'NÃO ENCONTRADO' and units != 0:
                    print(f"      ✅ Campo 'units' preenchido corretamente")
                else:
                    print(f"      ❌ PROBLEMA: Campo 'units' não preenchido ou zero!")
                    
                status = tip.get('status', 'N/A')
                print(f"      Status: {status}")
        else:
            print("\n❌ Nenhuma tip recente encontrada")
        
        # Resultado final
        print("\n" + "=" * 60)
        print("📊 RESULTADO FINAL:")
        
        tips_no_scan = scan_result.get('tips_generated', 0)
        total_tips = len(recent_tips)
        
        print(f"   🎯 Tips geradas no scan: {tips_no_scan}")
        print(f"   📋 Total tips no sistema: {total_tips}")
        print(f"   🎮 Partidas analisadas: {scan_result.get('matches_analyzed', 0)}")
        
        if tips_no_scan > 0 or total_tips > 0:
            print("✅ SISTEMA ESTÁ FUNCIONANDO!")
            print("   - Sistema encontra partidas")
            print("   - Sistema gera/gerou tips")
            if any(tip.get('units', 0) for tip in recent_tips):
                print("   - Campo 'units' sendo preenchido ✅")
            else:
                print("   - PROBLEMA: Campo 'units' não preenchido ❌")
        else:
            print("❌ SISTEMA NÃO ESTÁ GERANDO TIPS")
            print("   Possíveis causas:")
            print("   - Nenhuma partida ao vivo no momento")
            print("   - Critérios muito rigorosos")
            print("   - Qualidade de dados insuficiente")
            print("   - Problema no campo 'units'")
        
        return tips_no_scan > 0 or total_tips > 0
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Função principal"""
    print(f"🕐 Início do teste: {datetime.now().strftime('%H:%M:%S')}")
    
    resultado = await verificar_tips_reais()
    
    print(f"\n🕐 Fim do teste: {datetime.now().strftime('%H:%M:%S')}")
    
    if resultado:
        print("🎉 TESTE CONCLUÍDO: Sistema funcionando!")
    else:
        print("⚠️ TESTE CONCLUÍDO: Sistema com problemas")

if __name__ == "__main__":
    asyncio.run(main()) 