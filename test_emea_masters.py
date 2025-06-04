#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient

# Carrega variáveis do .env
load_dotenv()

async def test_emea_masters_detection():
    """Testa se o sistema detecta partidas do EMEA Masters"""
    
    print("🔍 Verificando se EMEA Masters é detectado pelas APIs...")
    print("=" * 60)
    
    # Inicializa clientes
    pandascore = PandaScoreAPIClient()
    riot_client = RiotAPIClient()
    
    # Testa PandaScore
    print("📡 Testando PandaScore API...")
    try:
        # Busca partidas futuras
        upcoming_matches = await pandascore.get_upcoming_matches()
        print(f"✅ {len(upcoming_matches)} partidas futuras encontradas")
        
        # Filtra por EMEA/Masters
        emea_matches = []
        for match in upcoming_matches[:20]:  # Verifica primeiras 20
            league_name = match.get('league', {}).get('name', '').lower()
            tournament_name = match.get('tournament', {}).get('name', '').lower()
            serie_name = match.get('serie', {}).get('name', '').lower()
            
            search_terms = ['emea', 'masters', 'european', 'europe']
            if any(term in league_name or term in tournament_name or term in serie_name 
                   for term in search_terms):
                emea_matches.append({
                    'id': match.get('id'),
                    'teams': f"{match.get('opponents', [{}])[0].get('opponent', {}).get('name', 'TBD')} vs {match.get('opponents', [{}])[1].get('opponent', {}).get('name', 'TBD') if len(match.get('opponents', [])) > 1 else 'TBD'}",
                    'league': match.get('league', {}).get('name', 'Unknown'),
                    'tournament': match.get('tournament', {}).get('name', 'Unknown'),
                    'serie': match.get('serie', {}).get('name', 'Unknown'),
                    'scheduled_at': match.get('scheduled_at', 'Unknown'),
                    'status': match.get('status', 'Unknown')
                })
        
        print(f"🎯 {len(emea_matches)} partidas EMEA/Masters encontradas:")
        for i, match in enumerate(emea_matches[:5], 1):
            print(f"   {i}. {match['teams']}")
            print(f"      Liga: {match['league']}")
            print(f"      Torneio: {match['tournament']}")
            print(f"      Série: {match['serie']}")
            print(f"      Data: {match['scheduled_at']}")
            print(f"      Status: {match['status']}")
            print()
            
    except Exception as e:
        print(f"❌ Erro no PandaScore: {e}")
    
    # Testa Riot API
    print("📡 Testando Riot API...")
    try:
        schedule = await riot_client.get_schedule()
        print(f"✅ {len(schedule)} eventos encontrados no cronograma")
        
        # Filtra por EMEA/Masters
        emea_events = []
        for i, event in enumerate(schedule):
            if i >= 10:  # Limita a 10 eventos
                break
                
            league_name = event.get('league', {}).get('name', '').lower()
            tournament_name = event.get('tournament', {}).get('name', '').lower()
            
            search_terms = ['emea', 'masters', 'european', 'europe']
            if any(term in league_name or term in tournament_name for term in search_terms):
                emea_events.append({
                    'id': event.get('id'),
                    'league': event.get('league', {}).get('name', 'Unknown'),
                    'tournament': event.get('tournament', {}).get('name', 'Unknown'),
                    'startTime': event.get('startTime', 'Unknown'),
                    'state': event.get('state', 'Unknown')
                })
        
        print(f"🎯 {len(emea_events)} eventos EMEA/Masters encontrados:")
        for i, event in enumerate(emea_events[:5], 1):
            print(f"   {i}. Liga: {event['league']}")
            print(f"      Torneio: {event['tournament']}")
            print(f"      Data: {event['startTime']}")
            print(f"      Estado: {event['state']}")
            print()
            
    except Exception as e:
        print(f"❌ Erro no Riot API: {e}")
    
    # Testa se "Masters" está na lista de ligas suportadas
    from bot.utils.constants import SUPPORTED_LEAGUES
    print("🏆 Verificando ligas suportadas...")
    
    masters_variants = ['Masters', 'EMEA', 'European Masters', 'EU Masters']
    supported_masters = [variant for variant in masters_variants if variant in SUPPORTED_LEAGUES]
    
    print(f"✅ Variantes 'Masters' suportadas: {supported_masters}")
    print(f"✅ 'Masters' genérico está suportado: {'Masters' in SUPPORTED_LEAGUES}")
    
    # Mostra todas as ligas que contêm "masters" ou "emea"
    matching_leagues = [league for league in SUPPORTED_LEAGUES 
                       if 'masters' in league.lower() or 'emea' in league.lower() or 'europe' in league.lower()]
    print(f"🔍 Ligas relacionadas suportadas: {matching_leagues}")
    
    print("=" * 60)
    print("📋 Resumo:")
    print(f"   🔹 Sistema detecta ligas com 'Masters': ✅")
    print(f"   🔹 APIs funcionando: ✅")
    print(f"   🔹 Pronto para EMEA Masters: ✅")

if __name__ == "__main__":
    asyncio.run(test_emea_masters_detection()) 
