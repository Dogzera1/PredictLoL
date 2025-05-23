#!/usr/bin/env python3
"""
Teste rápido do sistema Riot API para verificar times carregados
"""

import asyncio
from riot_api_integration import riot_prediction_system

async def main():
    print("🔍 VERIFICANDO TIMES CARREGADOS DA RIOT API")
    print("=" * 60)
    
    # Inicializar
    await riot_prediction_system.initialize()
    
    # Mostrar todos os times carregados
    print(f"\n📋 TODOS OS TIMES CARREGADOS ({len(riot_prediction_system.teams_data)}):")
    
    for key, team in riot_prediction_system.teams_data.items():
        print(f"   • {key}: {team['name']} ({team['region']}) - Rating {team['rating']}")
    
    # Testar alguns mapeamentos
    print(f"\n🔍 TESTANDO MAPEAMENTOS:")
    
    test_names = ['t1', 'g2', 'faker', 'fnc', 'jdg', 'gen.g', 'c9', 'tl']
    
    for name in test_names:
        team = riot_prediction_system.get_team_by_key(name)
        if team:
            print(f"   ✅ {name} -> {team['name']} ({team['region']})")
        else:
            print(f"   ❌ {name} -> Não encontrado")
    
    # Times por região
    print(f"\n🌍 DETALHES POR REGIÃO:")
    
    for region in ['LCK', 'LPL', 'LEC', 'LCS']:
        teams = riot_prediction_system.get_teams_by_region(region)
        print(f"\n   {region} ({len(teams)} times):")
        for team in teams:
            record_info = ""
            if 'record' in team and team['record'] and 'wins' in team['record']:
                wins = team['record']['wins']
                losses = team['record']['losses']
                record_info = f" ({wins}W-{losses}L)"
            
            position_info = f" #{team.get('position', '?')}" if team.get('position') else ""
            
            print(f"     - {team['name']} | {team['tier']} | {team['rating']}{record_info}{position_info}")

if __name__ == "__main__":
    asyncio.run(main()) 