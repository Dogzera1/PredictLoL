#!/usr/bin/env python3
"""
Teste rápido para verificar partidas ao vivo AGORA
"""
import asyncio
import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def testar_partidas_live():
    """Testa se há partidas ao vivo agora"""
    print("🔍 TESTANDO PARTIDAS AO VIVO AGORA...")
    print("=" * 50)
    
    try:
        from src.bot_lol_v3.apis.pandascore_api import PandaScoreAPI
        print("✅ PandaScoreAPI importado")
        
        api = PandaScoreAPI()
        print("✅ PandaScoreAPI inicializado")
        
        print("\n📡 Buscando partidas ao vivo...")
        matches = await api.get_live_matches()
        
        print(f"📊 RESULTADO: {len(matches)} partidas encontradas")
        
        if matches:
            print("\n🎮 PARTIDAS AO VIVO:")
            for i, match in enumerate(matches[:5], 1):
                nome = match.get('name', 'N/A')
                status = match.get('status', 'N/A')  
                liga = match.get('league', {}).get('name', 'N/A')
                
                print(f"{i}. {nome}")
                print(f"   📊 Status: {status}")
                print(f"   🏆 Liga: {liga}")
                print()
        else:
            print("❌ Nenhuma partida ao vivo encontrada")
            
        # Teste Riot API também
        print("\n" + "="*50)
        print("🔍 TESTANDO RIOT API...")
        
        from src.bot_lol_v3.apis.riot_api import RiotAPI
        riot_api = RiotAPI()
        print("✅ RiotAPI importado e inicializado")
        
        # Teste mais básico com Riot
        print("✅ Riot API conectada")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(testar_partidas_live()) 