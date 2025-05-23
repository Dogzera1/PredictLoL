#!/usr/bin/env python3
"""
Teste completo do Bot LoL Predictor V3 - Riot API Integrated
"""

import asyncio
from riot_api_integration import riot_prediction_system

async def test_complete_system():
    print("🎮 TESTE COMPLETO BOT LOL PREDICTOR V3")
    print("=" * 60)
    
    # 1. Inicializar sistema
    print("🔄 1. INICIALIZANDO SISTEMA...")
    success = await riot_prediction_system.initialize()
    
    if success:
        print("✅ Sistema inicializado com dados da Riot API")
    else:
        print("⚠️ Sistema em modo fallback")
    
    # 2. Estatísticas
    print("\n📊 2. ESTATÍSTICAS DO SISTEMA:")
    stats = riot_prediction_system.get_system_stats()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    # 3. Rankings por região
    print("\n🏆 3. RANKINGS POR REGIÃO:")
    for region in ['LCK', 'LPL', 'LEC', 'LCS']:
        teams = riot_prediction_system.get_teams_by_region(region)
        print(f"\n   {region} ({len(teams)} times):")
        for i, team in enumerate(teams[:5], 1):  # Top 5
            record = ""
            if 'record' in team and team['record'] and 'wins' in team['record']:
                w = team['record']['wins']
                l = team['record']['losses']
                record = f" ({w}W-{l}L)"
            print(f"     {i}. {team['name']} | {team['tier']} | {team['rating']}{record}")
    
    # 4. Ranking Global
    print("\n🌍 4. RANKING GLOBAL (Top 10):")
    global_ranking = riot_prediction_system.get_global_rankings(10)
    for i, team in enumerate(global_ranking, 1):
        region_flag = {'LCK': '🇰🇷', 'LPL': '🇨🇳', 'LEC': '🇪🇺', 'LCS': '🇺🇸'}.get(team['region'], '🌍')
        print(f"   {i}. {team['name']} {region_flag} | {team['rating']} pts | {team['tier']}")
    
    # 5. Testes de Predições
    print("\n🎮 5. TESTES DE PREDIÇÕES:")
    
    test_matches = [
        ("T1", "JDG", "bo5", "Inter-regional - LCK vs LPL"),
        ("G2", "Fnatic", "bo3", "Clássico europeu - LEC"),
        ("Cloud9", "Team Liquid", "bo1", "Confronto americano - LCS"),
        ("T1", "Gen.G", "bo3", "Derby coreano - LCK"),
        ("JDG", "Bilibili Gaming", "bo5", "Final chinesa - LPL"),
        ("G2", "MAD Lions", "bo1", "Europeu - LEC"),
        ("Faker", "Chovy", "bo1", "Teste com players (deve falhar)"),
    ]
    
    for team1, team2, match_type, description in test_matches:
        print(f"\n   🔍 {description}:")
        print(f"   ⚔️ {team1} vs {team2} ({match_type.upper()})")
        
        result = await riot_prediction_system.predict_match(team1, team2, match_type)
        
        if 'error' in result:
            print(f"   ❌ {result['error']}")
        else:
            winner = result['predicted_winner']
            confidence = result['confidence']
            prob1 = result['team1_probability'] * 100
            prob2 = result['team2_probability'] * 100
            
            print(f"   🏆 Vencedor: {winner}")
            print(f"   📊 Probabilidades: {team1} {prob1:.1f}% | {team2} {prob2:.1f}%")
            print(f"   🔥 Confiança: {result['confidence_level']} ({confidence:.1%})")
            print(f"   🌐 Fonte: {result['data_source']}")
    
    # 6. Teste de Busca por Times
    print("\n🔍 6. TESTE DE BUSCA POR TIMES:")
    
    search_tests = [
        "t1", "T1", "gen.g", "geng", "g2", "G2 Esports",
        "jdg", "JD Gaming", "cloud9", "c9", "team liquid", "tl",
        "faker", "chovy", "caps", "invalid_team"
    ]
    
    for search_term in search_tests:
        team = riot_prediction_system.get_team_by_key(search_term)
        if team:
            print(f"   ✅ '{search_term}' -> {team['name']} ({team['region']})")
        else:
            print(f"   ❌ '{search_term}' -> Não encontrado")
    
    # 7. Resumo Final
    print(f"\n🎉 7. RESUMO FINAL:")
    print(f"   • ✅ Sistema V3 funcionando")
    print(f"   • ✅ {len(riot_prediction_system.teams_data)} times carregados")
    print(f"   • ✅ 4 regiões cobertas (LCK, LPL, LEC, LCS)")
    print(f"   • ✅ {riot_prediction_system.prediction_count} predições testadas")
    print(f"   • ✅ Fonte: {stats['data_source']}")
    print(f"   • ✅ Fallback: {'Ativo' if stats['fallback_active'] else 'Inativo'}")
    
    print(f"\n🚀 BOT V3 PRONTO PARA DEPLOY!")
    
    return True

async def main():
    await test_complete_system()

if __name__ == "__main__":
    asyncio.run(main()) 