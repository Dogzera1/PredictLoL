#!/usr/bin/env python3
"""
Teste rápido das APIs - Bot LoL V3
"""
import asyncio
import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients.riot_api_client import RiotAPIClient
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient

async def test_riot_api():
    """Testa a Riot API"""
    print("🔍 Testando Riot API...")
    
    try:
        async with RiotAPIClient() as client:
            # Teste básico de health check
            result = await client.health_check()
            if result:
                print("✅ Riot API: Conexão OK")
                
                # Tenta buscar partidas ao vivo
                matches = await client.get_live_matches()
                print(f"📊 Riot API: {len(matches)} partidas encontradas")
                
            else:
                print("❌ Riot API: Falha na conexão")
                
    except Exception as e:
        print(f"❌ Riot API: Erro - {e}")

async def test_pandascore_api():
    """Testa a PandaScore API"""
    print("\n🔍 Testando PandaScore API...")
    
    try:
        async with PandaScoreAPIClient() as client:
            # Teste básico de health check
            result = await client.health_check()
            if result:
                print("✅ PandaScore API: Conexão OK")
                
                # Tenta buscar partidas ao vivo
                matches = await client.get_lol_live_matches()
                print(f"📊 PandaScore API: {len(matches)} partidas encontradas")
                
            else:
                print("❌ PandaScore API: Falha na conexão")
                
    except Exception as e:
        print(f"❌ PandaScore API: Erro - {e}")

async def main():
    """Teste principal"""
    print("🚀 Testando APIs do Bot LoL V3 Ultra Avançado")
    print("=" * 50)
    
    await test_riot_api()
    await test_pandascore_api()
    
    print("\n" + "=" * 50)
    print("✅ Teste de APIs concluído!")

if __name__ == "__main__":
    asyncio.run(main()) 