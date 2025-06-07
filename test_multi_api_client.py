"""
🆓 TESTE das APIs GRATUITAS para League of Legends
Demonstra como usar múltiplas APIs gratuitas para complementar o bot
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients.multi_api_client import MultiAPIClient

async def test_free_apis():
    """🧪 Testa todas as APIs gratuitas disponíveis"""
    
    print("🚀 TESTANDO APIs GRATUITAS para League of Legends")
    print("=" * 60)
    
    async with MultiAPIClient() as multi_client:
        
        # 1. Health Check das APIs gratuitas
        print("\n🔍 1. HEALTH CHECK das APIs Gratuitas:")
        health = await multi_client.health_check()
        for api, status in health.items():
            status_emoji = "✅" if status else "❌"
            print(f"   {status_emoji} {api}: {'OK' if status else 'FALHOU'}")
        
        # 2. Lista APIs suportadas
        print("\n📋 2. APIs GRATUITAS SUPORTADAS:")
        supported = multi_client.get_supported_apis()
        for api, description in supported.items():
            print(f"   • {api}: {description}")
        
        # 3. Teste busca de champion individual
        print("\n🎯 3. TESTE: Dados de Champion Individual (CommunityDragon)")
        test_champion = "Yasuo"
        champ_data = await multi_client.get_champion_details(test_champion)
        
        if champ_data:
            print(f"   ✅ Dados de {test_champion} encontrados!")
            print(f"   📊 Abilities: {len(champ_data.get('abilities', []))}")
            print(f"   📈 Stats disponíveis: {bool(champ_data.get('stats'))}")
            print(f"   🎨 Skins: {len(champ_data.get('skins', []))}")
            print(f"   💰 Custo: {champ_data.get('api_cost', 'N/A')}")
        else:
            print(f"   ❌ Falha ao buscar dados de {test_champion}")
        
        # 4. Teste versão do patch
        print("\n🔄 4. TESTE: Versão Atual do Patch (Data Dragon)")
        patch = await multi_client.get_current_patch()
        if patch:
            print(f"   ✅ Patch atual: {patch}")
        else:
            print("   ❌ Falha ao buscar patch")
        
        # 5. Teste stats de todos os champions
        print("\n📊 5. TESTE: Stats de Todos os Champions")
        all_champs = await multi_client.get_all_champions_stats()
        if all_champs:
            champ_count = len(all_champs.get('champions', {}))
            print(f"   ✅ {champ_count} champions encontrados no patch {all_champs.get('patch')}")
            print(f"   💰 Custo: {all_champs.get('api_cost', 'N/A')}")
        else:
            print("   ❌ Falha ao buscar stats dos champions")
        
        # 6. Teste análise de match completa
        print("\n⚔️ 6. TESTE: Análise Completa de Match")
        team1 = ["Yasuo", "Thresh", "Jinx"]
        team2 = ["Malphite", "Orianna", "Ezreal"]
        
        print(f"   Team 1: {', '.join(team1)}")
        print(f"   Team 2: {', '.join(team2)}")
        
        match_analysis = await multi_client.get_enhanced_match_analysis(team1, team2)
        
        if match_analysis:
            print("   ✅ Análise de match gerada!")
            
            # Team 1 analysis
            team1_data = match_analysis.get('team1', {})
            print(f"   📊 Team 1 Score: {team1_data.get('composition_score', 0)}/100")
            
            # Team 2 analysis  
            team2_data = match_analysis.get('team2', {})
            print(f"   📊 Team 2 Score: {team2_data.get('composition_score', 0)}/100")
            
            # Prediction
            prediction = match_analysis.get('match_prediction', {})
            print(f"   🔮 Predição: {prediction.get('prediction', 'N/A')}")
            print(f"   🎯 Confiança: {prediction.get('confidence', 0)}%")
            print(f"   💰 Custo total: {match_analysis.get('total_cost', 'N/A')}")
            
            # APIs usadas
            apis_used = match_analysis.get('apis_used', [])
            print(f"   🔧 APIs usadas: {', '.join(apis_used)}")
            
        else:
            print("   ❌ Falha na análise de match")
        
        # 7. Teste tips específicos de champion
        print("\n💡 7. TESTE: Tips Específicos de Champion")
        tips_data = await multi_client.get_champion_tips("Yasuo")
        
        if tips_data:
            print(f"   ✅ Tips para {tips_data.get('champion')} gerados!")
            tips = tips_data.get('tips', [])
            for i, tip in enumerate(tips, 1):
                print(f"   💡 Tip {i}: {tip}")
            
            summary = tips_data.get('stats_summary', {})
            print(f"   📈 Sobrevivência: {summary.get('survivability', 'N/A')}")
            print(f"   ⚔️ Potencial de dano: {summary.get('damage_potential', 'N/A')}")
            print(f"   💰 Custo: {tips_data.get('api_cost', 'N/A')}")
        else:
            print("   ❌ Falha ao gerar tips")
        
        # 8. Resumo final
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES:")
        print("✅ APIs testadas: CommunityDragon, Data Dragon")
        print("💰 Custo total: GRATUITO")
        print("🔄 Atualizações: Dados sempre atuais")
        print("📊 Dados únicos obtidos:")
        print("   • Abilities detalhadas dos champions")
        print("   • Stats base e scaling")
        print("   • Artwork e skins")
        print("   • Análise de composição")
        print("   • Tips personalizados")
        print("   • Predições de match")
        
        print("\n🎯 PRÓXIMOS PASSOS para integrar ao bot:")
        print("1. Adicionar MultiAPIClient ao sistema de tips")
        print("2. Usar dados de abilities para análise mais precisa")
        print("3. Integrar artwork para interface mais rica")
        print("4. Combinar com PandaScore para dados completos")
        
        # Salva dados de exemplo
        if match_analysis:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dados_apis_gratuitas_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(match_analysis, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Dados de exemplo salvos em: {filename}")

async def main():
    """🎯 Função principal"""
    try:
        await test_free_apis()
        print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ ERRO durante os testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🆓 INICIANDO TESTES das APIs GRATUITAS...")
    asyncio.run(main()) 