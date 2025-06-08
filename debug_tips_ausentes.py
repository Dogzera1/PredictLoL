#!/usr/bin/env python3
import asyncio
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_tips_ausentes():
    """Debug: Por que não há tips saindo?"""
    
    print("🔍 DEBUG: POR QUE NÃO HÁ TIPS?")
    print("=" * 50)
    
    try:
        # 1. Verificar se sistema de tips carrega
        print("\n📋 1. Testando sistema de tips...")
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        
        # Inicializar dependências
        pandascore = PandaScoreAPIClient()
        riot = RiotAPIClient()
        analyzer = LoLGameAnalyzer()
        units = ProfessionalUnitsSystem()
        prediction = DynamicPredictionSystem(analyzer, units)
        
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore,
            riot_client=riot,
            prediction_system=prediction
        )
        print("✅ Sistema de tips carregado")
        
        # 2. Verificar partidas detectadas
        print("\n🎮 2. Verificando partidas detectadas...")
        partidas = await pandascore.get_lol_live_matches()
        print(f"📊 Total de partidas encontradas: {len(partidas)}")
        
        if partidas:
            print("🎯 Primeiras 3 partidas:")
            for i, partida in enumerate(partidas[:3]):
                nome = partida.get('name', 'Nome desconhecido')
                torneio = partida.get('tournament', {}).get('name', 'Torneio desconhecido')
                status = partida.get('status', 'Status desconhecido')
                print(f"   {i+1}. {torneio} - {nome} ({status})")
        else:
            print("❌ Nenhuma partida encontrada")
        
        # 3. Verificar critérios de qualidade
        print("\n⚖️ 3. Verificando critérios de tips...")
        
        # Simular análise de uma partida
        if partidas:
            primeira_partida = partidas[0]
            print(f"🧪 Analisando: {primeira_partida.get('name', 'Partida teste')}")
            
            # Verificar se tem odds
            odds = primeira_partida.get('bookmakers', [])
            print(f"💰 Odds disponíveis: {len(odds)} bookmakers")
            
            if odds:
                for bookmaker in odds[:2]:  # Primeiras 2 casas
                    nome_casa = bookmaker.get('name', 'Casa desconhecida')
                    markets = bookmaker.get('markets', [])
                    print(f"   📈 {nome_casa}: {len(markets)} mercados")
            else:
                print("❌ Nenhuma odd encontrada")
        
        # 4. Testar força de tips usando force_scan
        print("\n🎯 4. Testando geração de tips...")
        try:
            resultado_scan = await tips_system.force_scan()
            print(f"📊 Resultado do scan forçado:")
            print(f"   - Partidas analisadas: {resultado_scan.get('matches_scanned', 0)}")
            print(f"   - Tips geradas: {resultado_scan.get('tips_generated', 0)}")
            print(f"   - Tips válidas: {resultado_scan.get('valid_tips', 0)}")
            
            if resultado_scan.get('tips_generated', 0) > 0:
                print("✅ Sistema está gerando tips!")
            else:
                print("❌ Nenhuma tip foi gerada")
                print("\n🔍 Possíveis motivos:")
                print("   - Odds muito baixas (< 1.50)")
                print("   - Confiança insuficiente (< 75%)")
                print("   - Partidas fora dos critérios de qualidade")
                print("   - Rate limit ativo (máx 5 tips/hora)")
                
        except Exception as e:
            print(f"❌ Erro ao fazer scan: {e}")
        
        # 5. Verificar configurações do sistema
        print("\n⚙️ 5. Verificando configurações...")
        status = tips_system.get_monitoring_status()
        print(f"   - Sistema ativo: {status.get('is_monitoring', False)}")
        print(f"   - Tips por hora permitidas: {tips_system.max_tips_per_hour}")
        print(f"   - Tips na última hora: {len([t for t in tips_system.last_tip_times if time.time() - t < 3600])}")
        
        # 6. Verificar filtros de qualidade
        print("\n🔧 6. Filtros de qualidade atuais:")
        filtros = tips_system.quality_filters
        for nome, valor in filtros.items():
            print(f"   - {nome}: {valor}")
        
        await pandascore.close()
        await riot.close()
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🏁 DEBUG CONCLUÍDO")

if __name__ == "__main__":
    asyncio.run(debug_tips_ausentes())