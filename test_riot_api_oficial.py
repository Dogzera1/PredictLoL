#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da API oficial da Riot Games
Baseado na documentação OpenAPI fornecida
"""

import asyncio
import logging
import sys
import os

# Adicionar o diretório atual ao path para importar o bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_v13_railway import RiotAPIClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_riot_api():
    """Testa a nova implementação da API da Riot"""
    print("🔍 TESTE DA API OFICIAL DA RIOT GAMES")
    print("=" * 50)
    
    # Inicializar cliente
    riot_client = RiotAPIClient()
    
    print(f"🔑 Chave de API: {riot_client.api_key}")
    print(f"🌐 URLs base: {riot_client.base_urls}")
    print()
    
    # Testar busca de partidas ao vivo
    print("🎮 Buscando partidas ao vivo...")
    try:
        matches = await riot_client.get_live_matches()
        
        if matches:
            print(f"✅ {len(matches)} partidas encontradas!")
            print()
            
            for i, match in enumerate(matches, 1):
                print(f"📊 PARTIDA {i}:")
                print(f"   ID: {match.get('id', 'N/A')}")
                print(f"   Liga: {match.get('league', 'N/A')}")
                print(f"   Status: {match.get('status', 'N/A')}")
                
                teams = match.get('teams', [])
                if len(teams) >= 2:
                    team1 = teams[0]
                    team2 = teams[1]
                    print(f"   Times: {team1.get('name', 'N/A')} vs {team2.get('name', 'N/A')}")
                    
                    # Mostrar records se disponível
                    if team1.get('record'):
                        record1 = team1['record']
                        print(f"   Record {team1['name']}: {record1.get('wins', 0)}W-{record1.get('losses', 0)}L")
                    
                    if team2.get('record'):
                        record2 = team2['record']
                        print(f"   Record {team2['name']}: {record2.get('wins', 0)}W-{record2.get('losses', 0)}L")
                
                print(f"   Fonte: {match.get('source', 'API oficial')}")
                print()
        else:
            print("ℹ️ Nenhuma partida ao vivo encontrada")
            
    except Exception as e:
        print(f"❌ Erro ao buscar partidas: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Função principal"""
    print("🚀 Iniciando teste da API oficial da Riot...")
    
    # Executar teste assíncrono
    asyncio.run(test_riot_api())
    
    print("✅ Teste concluído!")

if __name__ == "__main__":
    main() 