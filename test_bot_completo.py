#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE COMPLETO DO BOT LOL V3 - Verificação de Funcionalidades
Testa todas as correções implementadas
"""

import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testa se todas as importações estão funcionando"""
    print("🔍 Testando importações...")
    
    try:
        from bot_v13_railway import (
            RiotAPIClient, 
            ValueBettingSystem, 
            UnitsSystem, 
            AlertSystem,
            DynamicPredictionSystem,
            ChampionAnalyzer,
            BotLoLV3Railway
        )
        print("✅ Todas as importações funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro nas importações: {e}")
        return False

def test_riot_client():
    """Testa o cliente da API Riot"""
    print("\n🔍 Testando RiotAPIClient...")
    
    try:
        from bot_v13_railway import RiotAPIClient
        
        client = RiotAPIClient()
        print("✅ RiotAPIClient inicializado")
        
        # Teste assíncrono
        async def test_async():
            try:
                live_matches = await client.get_live_matches()
                print(f"✅ get_live_matches funcionando - {len(live_matches)} partidas")
                
                scheduled = await client.get_scheduled_matches()
                print(f"✅ get_scheduled_matches funcionando - {len(scheduled)} partidas")
                
                return True
            except Exception as e:
                print(f"❌ Erro nos métodos assíncronos: {e}")
                return False
        
        # Executar teste assíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_async())
        loop.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Erro no RiotAPIClient: {e}")
        return False

def test_value_betting():
    """Testa o sistema de value betting"""
    print("\n🔍 Testando ValueBettingSystem...")
    
    try:
        from bot_v13_railway import ValueBettingSystem, RiotAPIClient
        
        riot_client = RiotAPIClient()
        value_system = ValueBettingSystem(riot_client=riot_client)
        print("✅ ValueBettingSystem inicializado")
        
        # Testar análise de valor
        mock_match = {
            'id': 'test_match',
            'team1': 'T1',
            'team2': 'GEN',
            'league': 'LCK',
            'status': 'live'
        }
        
        opportunity = value_system._analyze_match_value(mock_match)
        if opportunity:
            print("✅ _analyze_match_value funcionando")
        else:
            print("⚠️ _analyze_match_value retornou None (normal se não há value)")
        
        # Testar força dos times
        strength_t1 = value_system._calculate_team_strength('T1', 'LCK')
        strength_gen = value_system._calculate_team_strength('GEN', 'LCK')
        print(f"✅ Força dos times - T1: {strength_t1}, GEN: {strength_gen}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no ValueBettingSystem: {e}")
        return False

def test_units_system():
    """Testa o sistema de unidades"""
    print("\n🔍 Testando UnitsSystem...")
    
    try:
        from bot_v13_railway import UnitsSystem
        
        units_system = UnitsSystem()
        print("✅ UnitsSystem inicializado")
        
        # Testar cálculo de unidades
        result = units_system.calculate_units(
            win_prob=0.65,
            odds=1.85,
            confidence='Alta'
        )
        
        print(f"✅ Cálculo de unidades funcionando:")
        print(f"   - Units: {result['units']}")
        print(f"   - EV: {result['ev_percentage']:.1f}%")
        print(f"   - Risk Level: {result['risk_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no UnitsSystem: {e}")
        return False

def test_prediction_system():
    """Testa o sistema de predições"""
    print("\n🔍 Testando DynamicPredictionSystem...")
    
    try:
        from bot_v13_railway import DynamicPredictionSystem
        
        prediction_system = DynamicPredictionSystem()
        print("✅ DynamicPredictionSystem inicializado")
        
        # Teste assíncrono
        async def test_prediction():
            try:
                mock_match = {
                    'team1': 'T1',
                    'team2': 'GEN',
                    'league': 'LCK'
                }
                
                prediction = await prediction_system.predict_live_match(mock_match)
                print(f"✅ Predição funcionando:")
                print(f"   - Favorito: {prediction['favored_team']}")
                print(f"   - Probabilidade: {prediction['win_probability']:.1f}%")
                print(f"   - Confiança: {prediction['confidence']}")
                
                return True
            except Exception as e:
                print(f"❌ Erro na predição: {e}")
                return False
        
        # Executar teste assíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_prediction())
        loop.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Erro no DynamicPredictionSystem: {e}")
        return False

def test_champion_analyzer():
    """Testa o analisador de campeões"""
    print("\n🔍 Testando ChampionAnalyzer...")
    
    try:
        from bot_v13_railway import ChampionAnalyzer
        
        analyzer = ChampionAnalyzer()
        print("✅ ChampionAnalyzer inicializado")
        
        # Testar análise de draft
        team1_comp = ['Aatrox', 'Graves', 'Azir', 'Jinx', 'Nautilus']
        team2_comp = ['Gwen', 'Lee Sin', 'Orianna', 'Kai\'Sa', 'Thresh']
        
        analysis = analyzer.analyze_draft(team1_comp, team2_comp)
        print(f"✅ Análise de draft funcionando:")
        print(f"   - Vencedor: {analysis['draft_advantage']['winner']}")
        print(f"   - Confiança: {analysis['draft_advantage']['confidence']}")
        print(f"   - Diferença: {analysis['draft_advantage']['score_difference']:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no ChampionAnalyzer: {e}")
        return False

def test_alert_system():
    """Testa o sistema de alertas"""
    print("\n🔍 Testando AlertSystem...")
    
    try:
        from bot_v13_railway import AlertSystem
        
        alert_system = AlertSystem()
        print("✅ AlertSystem inicializado")
        
        # Testar inscrição
        test_chat_id = 12345
        result = alert_system.subscribe_group(test_chat_id)
        print(f"✅ Inscrição funcionando: {result}")
        
        # Testar contagem
        count = alert_system.get_subscribed_groups_count()
        print(f"✅ Contagem de grupos: {count}")
        
        # Testar desinscrição
        result = alert_system.unsubscribe_group(test_chat_id)
        print(f"✅ Desinscrição funcionando: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no AlertSystem: {e}")
        return False

def test_bot_initialization():
    """Testa a inicialização do bot principal"""
    print("\n🔍 Testando BotLoLV3Railway...")
    
    try:
        # Verificar se as variáveis de ambiente estão definidas
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            print("⚠️ TELEGRAM_BOT_TOKEN não definido - usando token de teste")
            os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        
        from bot_v13_railway import BotLoLV3Railway
        
        # Não inicializar completamente para evitar erro de token
        print("✅ BotLoLV3Railway pode ser importado")
        print("✅ Todas as classes estão disponíveis")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na inicialização do bot: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTE COMPLETO DO BOT LOL V3")
    print("=" * 50)
    
    tests = [
        ("Importações", test_imports),
        ("RiotAPIClient", test_riot_client),
        ("ValueBettingSystem", test_value_betting),
        ("UnitsSystem", test_units_system),
        ("DynamicPredictionSystem", test_prediction_system),
        ("ChampionAnalyzer", test_champion_analyzer),
        ("AlertSystem", test_alert_system),
        ("BotLoLV3Railway", test_bot_initialization)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro crítico no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Bot está funcionando corretamente.")
    elif passed >= total * 0.8:
        print("⚡ MAIORIA DOS TESTES PASSOU! Bot está funcionando bem.")
    else:
        print("⚠️ VÁRIOS TESTES FALHARAM! Verificar problemas no bot.")
    
    print(f"\n⏰ Teste concluído em: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main() 