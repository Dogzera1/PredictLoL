#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bot_v13_railway import AdvancedValueBettingSystem

print("🧪 Teste Simples do Sistema Avançado")
print("=" * 40)

try:
    # Criar sistema
    system = AdvancedValueBettingSystem()
    print("✅ Sistema criado com sucesso")
    
    # Teste de análise
    test_match = {
        'team1': 'T1',
        'team2': 'Gen.G Esports',
        'league': 'LCK',
        'tournament': 'LCK Spring 2025'
    }
    
    analysis = system.analyze_match_comprehensive(test_match)
    print("✅ Análise executada com sucesso")
    
    # Verificar resultados
    comp_analysis = analysis['comprehensive_analysis']
    value_analysis = analysis['value_analysis']
    
    print(f"\n📊 RESULTADOS:")
    print(f"T1 Probabilidade: {comp_analysis['team1_probability']*100:.1f}%")
    print(f"Gen.G Probabilidade: {comp_analysis['team2_probability']*100:.1f}%")
    print(f"Confiança: {comp_analysis['overall_confidence']*100:.1f}%")
    
    if value_analysis['has_value']:
        recommendation = analysis['recommendation']
        print(f"\n💰 VALUE DETECTADO!")
        print(f"Time: {recommendation['team']}")
        print(f"Unidades: {recommendation['units']}")
        print(f"EV: {recommendation['ev']}")
        print(f"Risco: {recommendation['risk_level']}")
    else:
        print(f"\n❌ Nenhum value: {value_analysis['reason']}")
    
    print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc() 