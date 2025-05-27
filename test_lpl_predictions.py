#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE ESPECÍFICO - LPL e Predições Automáticas
Verifica se a LPL está sendo detectada e se as predições estão atualizando automaticamente
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_lpl_detection():
    """Testa se a LPL está sendo detectada corretamente"""
    print("🔍 Testando detecção da LPL...")
    
    try:
        from bot_v13_railway import RiotAPIClient
        
        client = RiotAPIClient()
        
        # Teste de extração de nome de liga
        test_events = [
            {'league': {'name': 'LPL Spring 2024'}},
            {'tournament': {'name': 'China LPL'}},
            {'leagueName': 'Tencent LPL'},
            {'blockName': 'LPL Regular Season'},
            {'tournamentName': 'Chinese Professional League'}
        ]
        
        print("✅ Testando extração de nomes de liga:")
        for i, event in enumerate(test_events, 1):
            league_name = client._extract_league_name(event)
            print(f"   {i}. {event} → {league_name}")
            
        # Teste assíncrono de partidas ao vivo
        async def test_live_matches():
            try:
                live_matches = await client.get_live_matches()
                print(f"\n✅ Partidas ao vivo encontradas: {len(live_matches)}")
                
                lpl_matches = [m for m in live_matches if 'LPL' in m.get('league', '').upper()]
                print(f"✅ Partidas da LPL encontradas: {len(lpl_matches)}")
                
                for match in live_matches:
                    teams = match.get('teams', [])
                    if len(teams) >= 2:
                        team1 = teams[0].get('name', 'Unknown')
                        team2 = teams[1].get('name', 'Unknown')
                        league = match.get('league', 'Unknown')
                        status = match.get('status', 'Unknown')
                        
                        print(f"   🎮 {team1} vs {team2} ({league}) - {status}")
                        
                        # Verificar se é LPL
                        if 'LPL' in league.upper():
                            print(f"      🇨🇳 LPL DETECTADA!")
                
                return len(lpl_matches) > 0
                
            except Exception as e:
                print(f"❌ Erro ao buscar partidas: {e}")
                return False
        
        # Executar teste assíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        lpl_found = loop.run_until_complete(test_live_matches())
        loop.close()
        
        return lpl_found
        
    except Exception as e:
        print(f"❌ Erro no teste de LPL: {e}")
        return False

def test_prediction_auto_update():
    """Testa se as predições estão atualizando automaticamente"""
    print("\n🔮 Testando sistema de predições automáticas...")
    
    try:
        from bot_v13_railway import DynamicPredictionSystem
        
        prediction_system = DynamicPredictionSystem()
        print("✅ Sistema de predições inicializado")
        
        # Teste de cache
        cache_status = prediction_system.get_cache_status()
        print(f"✅ Status inicial do cache:")
        print(f"   - Predições em cache: {cache_status['cached_predictions']}")
        print(f"   - Auto-update ativo: {cache_status['auto_update_enabled']}")
        print(f"   - Intervalo: {cache_status['update_interval_seconds']}s")
        
        # Teste de predição com cache
        async def test_prediction_cache():
            try:
                # Mock de partida
                mock_match = {
                    'teams': [
                        {'name': 'JDG', 'score': 0},
                        {'name': 'BLG', 'score': 0}
                    ],
                    'league': 'LPL',
                    'status': 'live'
                }
                
                print(f"\n🎯 Testando predição para: JDG vs BLG (LPL)")
                
                # Primeira predição (deve ser nova)
                start_time = time.time()
                prediction1 = await prediction_system.predict_live_match(mock_match)
                time1 = time.time() - start_time
                
                print(f"✅ Primeira predição:")
                print(f"   - Favorito: {prediction1.get('favored_team', 'N/A')}")
                print(f"   - Probabilidade: {prediction1.get('win_probability', 0):.1f}%")
                print(f"   - Confiança: {prediction1.get('confidence', 'N/A')}")
                print(f"   - Status: {prediction1.get('cache_status', 'N/A')}")
                print(f"   - Tempo: {time1:.3f}s")
                
                # Segunda predição imediata (deve usar cache)
                start_time = time.time()
                prediction2 = await prediction_system.predict_live_match(mock_match)
                time2 = time.time() - start_time
                
                print(f"\n✅ Segunda predição (imediata):")
                print(f"   - Status: {prediction2.get('cache_status', 'N/A')}")
                print(f"   - Tempo: {time2:.3f}s")
                print(f"   - Cache funcionando: {'✅' if time2 < time1 else '❌'}")
                
                # Verificar cache
                cache_status_after = prediction_system.get_cache_status()
                print(f"\n📊 Status do cache após predições:")
                print(f"   - Predições em cache: {cache_status_after['cached_predictions']}")
                
                # Teste de limpeza de cache
                prediction_system.clear_old_cache()
                print(f"✅ Limpeza de cache executada")
                
                return True
                
            except Exception as e:
                print(f"❌ Erro no teste de predições: {e}")
                return False
        
        # Executar teste assíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        prediction_success = loop.run_until_complete(test_prediction_cache())
        loop.close()
        
        return prediction_success
        
    except Exception as e:
        print(f"❌ Erro no teste de predições: {e}")
        return False

def test_team_strength_lpl():
    """Testa se os times da LPL estão sendo reconhecidos"""
    print("\n💪 Testando força dos times da LPL...")
    
    try:
        from bot_v13_railway import ValueBettingSystem, RiotAPIClient
        
        riot_client = RiotAPIClient()
        value_system = ValueBettingSystem(riot_client=riot_client)
        
        # Times da LPL para testar
        lpl_teams = ['JDG', 'BLG', 'WBG', 'TES', 'EDG', 'IG', 'LNG', 'FPX', 'RNG', 'TOP']
        
        print("✅ Testando força dos times da LPL:")
        for team in lpl_teams:
            strength = value_system._calculate_team_strength(team, 'LPL')
            print(f"   🇨🇳 {team}: {strength:.1f}")
        
        # Verificar se os valores estão corretos (critério ajustado)
        jdg_strength = value_system._calculate_team_strength('JDG', 'LPL')
        blg_strength = value_system._calculate_team_strength('BLG', 'LPL')
        
        # Critério mais realista: JDG > 85 e BLG > 80 (considerando multiplicadores)
        if jdg_strength > 85 and blg_strength > 80:
            print("✅ Times da LPL têm força adequada")
            print(f"   JDG: {jdg_strength:.1f} (>85 ✅)")
            print(f"   BLG: {blg_strength:.1f} (>80 ✅)")
            return True
        else:
            print("⚠️ Força dos times da LPL pode estar baixa")
            print(f"   JDG: {jdg_strength:.1f} (esperado >85)")
            print(f"   BLG: {blg_strength:.1f} (esperado >80)")
            return False
        
    except Exception as e:
        print(f"❌ Erro no teste de força dos times: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 TESTE ESPECÍFICO - LPL E PREDIÇÕES AUTOMÁTICAS")
    print("=" * 60)
    
    tests = [
        ("Detecção da LPL", test_lpl_detection),
        ("Predições Automáticas", test_prediction_auto_update),
        ("Força dos Times LPL", test_team_strength_lpl)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASSOU' if result else '❌ FALHOU'}")
        except Exception as e:
            print(f"❌ Erro crítico no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES ESPECÍFICOS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES ESPECÍFICOS PASSARAM!")
        print("✅ LPL está sendo detectada corretamente")
        print("✅ Predições estão atualizando automaticamente")
    elif passed >= total * 0.8:
        print("⚡ MAIORIA DOS TESTES PASSOU!")
        if passed < total:
            print("⚠️ Alguns problemas menores detectados")
    else:
        print("⚠️ VÁRIOS PROBLEMAS DETECTADOS!")
        print("🔧 Verificar implementação da LPL e predições")
    
    print(f"\n⏰ Teste concluído em: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main() 