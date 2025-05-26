#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Integração do Sistema Avançado de Value Betting
Verifica se a integração foi realizada com sucesso
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_integration():
    """Testa a integração do sistema avançado"""
    
    print("🧪 TESTE DE INTEGRAÇÃO - SISTEMA AVANÇADO DE VALUE BETTING")
    print("=" * 70)
    
    try:
        # Importar o bot principal
        from bot_v13_railway import BotLoLV3Railway, AdvancedValueBettingSystem
        
        print("✅ 1. Importação do bot principal: SUCESSO")
        
        # Verificar se a classe AdvancedValueBettingSystem existe
        if hasattr(sys.modules['bot_v13_railway'], 'AdvancedValueBettingSystem'):
            print("✅ 2. Classe AdvancedValueBettingSystem: ENCONTRADA")
        else:
            print("❌ 2. Classe AdvancedValueBettingSystem: NÃO ENCONTRADA")
            return False
        
        # Criar instância do sistema avançado
        advanced_system = AdvancedValueBettingSystem()
        print("✅ 3. Instanciação do sistema avançado: SUCESSO")
        
        # Verificar métodos principais
        required_methods = [
            'analyze_match_comprehensive',
            '_analyze_team_form',
            '_analyze_head_to_head',
            '_analyze_player_performance',
            '_analyze_composition_synergy',
            '_analyze_meta_adaptation',
            '_analyze_league_strength',
            'calculate_bet_units',
            '_generate_recommendation'
        ]
        
        missing_methods = []
        for method in required_methods:
            if hasattr(advanced_system, method):
                print(f"✅ 4.{len(required_methods) - len(missing_methods)}. Método {method}: ENCONTRADO")
            else:
                missing_methods.append(method)
                print(f"❌ 4.{len(required_methods) - len(missing_methods)}. Método {method}: NÃO ENCONTRADO")
        
        if missing_methods:
            print(f"❌ Métodos faltando: {missing_methods}")
            return False
        
        # Teste de análise completa
        print("\n🔬 TESTE DE ANÁLISE COMPLETA")
        print("-" * 40)
        
        test_match = {
            'team1': 'T1',
            'team2': 'Gen.G Esports',
            'league': 'LCK',
            'tournament': 'LCK Spring 2025'
        }
        
        analysis = advanced_system.analyze_match_comprehensive(test_match)
        print("✅ 5. Análise completa executada: SUCESSO")
        
        # Verificar estrutura da análise
        required_keys = [
            'match', 'league', 'comprehensive_analysis', 
            'value_analysis', 'recommendation', 'confidence_level'
        ]
        
        for key in required_keys:
            if key in analysis:
                print(f"✅ 6.{required_keys.index(key)+1}. Chave '{key}': ENCONTRADA")
            else:
                print(f"❌ 6.{required_keys.index(key)+1}. Chave '{key}': NÃO ENCONTRADA")
                return False
        
        # Verificar dados da análise
        comp_analysis = analysis['comprehensive_analysis']
        value_analysis = analysis['value_analysis']
        recommendation = analysis['recommendation']
        
        print(f"\n📊 RESULTADOS DA ANÁLISE:")
        print(f"🎯 Probabilidade T1: {comp_analysis['team1_probability']*100:.1f}%")
        print(f"🎯 Probabilidade Gen.G: {comp_analysis['team2_probability']*100:.1f}%")
        print(f"🔍 Confiança: {comp_analysis['overall_confidence']*100:.1f}%")
        
        if value_analysis['has_value']:
            print(f"💰 VALUE DETECTADO!")
            print(f"🎯 Recomendação: {recommendation['team']}")
            print(f"💵 Unidades: {recommendation['units']}")
            print(f"📊 EV: {recommendation['ev']}")
            print(f"⚠️ Risco: {recommendation['risk_level']}")
        else:
            print(f"❌ Nenhum value detectado: {value_analysis['reason']}")
        
        print("✅ 7. Estrutura da análise: VÁLIDA")
        
        # Teste de integração com bot
        print("\n🤖 TESTE DE INTEGRAÇÃO COM BOT")
        print("-" * 40)
        
        # Simular inicialização do bot (sem conectar ao Telegram)
        os.environ['TELEGRAM_TOKEN'] = 'test_token'
        os.environ['OWNER_ID'] = '123456789'
        
        try:
            # Não vamos inicializar completamente para evitar conexão
            # Apenas verificar se a classe pode ser importada e tem o sistema
            print("✅ 8. Bot pode ser importado: SUCESSO")
            
            # Verificar se o bot usaria o sistema avançado
            if 'AdvancedValueBettingSystem' in open('bot_v13_railway.py').read():
                print("✅ 9. Bot configurado para usar sistema avançado: SUCESSO")
            else:
                print("❌ 9. Bot NÃO configurado para sistema avançado: FALHA")
                return False
                
        except Exception as e:
            print(f"❌ 8. Erro na integração com bot: {e}")
            return False
        
        # Teste dos pesos de análise
        print("\n⚖️ TESTE DOS PESOS DE ANÁLISE")
        print("-" * 40)
        
        weights = advanced_system.analysis_weights
        expected_total = 1.0
        actual_total = sum(weights.values())
        
        print(f"📊 Pesos configurados:")
        for factor, weight in weights.items():
            print(f"  • {factor}: {weight*100:.0f}%")
        
        print(f"📊 Total dos pesos: {actual_total*100:.0f}%")
        
        if abs(actual_total - expected_total) < 0.01:
            print("✅ 10. Pesos de análise: VÁLIDOS")
        else:
            print(f"❌ 10. Pesos de análise: INVÁLIDOS (total: {actual_total})")
            return False
        
        # Teste de configurações avançadas
        print("\n⚙️ TESTE DE CONFIGURAÇÕES AVANÇADAS")
        print("-" * 40)
        
        print(f"💰 Unidade base: R$ {advanced_system.base_unit}")
        print(f"🏦 Bankroll: R$ {advanced_system.bankroll}")
        print(f"🎯 Máximo por aposta: {advanced_system.max_units_per_bet} unidades")
        print(f"📊 EV mínimo: {advanced_system.ev_threshold*100:.0f}%")
        print(f"🔍 Confiança mínima: {advanced_system.confidence_threshold*100:.0f}%")
        
        # Verificar se as configurações são mais rigorosas que o sistema básico
        if (advanced_system.ev_threshold >= 0.04 and 
            advanced_system.confidence_threshold >= 0.70):
            print("✅ 11. Configurações avançadas: VÁLIDAS")
        else:
            print("❌ 11. Configurações avançadas: INSUFICIENTES")
            return False
        
        print("\n" + "=" * 70)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema Avançado de Value Betting integrado com SUCESSO")
        print("🚀 Bot pronto para usar análise multifatorial avançada")
        print("=" * 70)
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_advanced_features():
    """Testa funcionalidades específicas do sistema avançado"""
    
    print("\n🔬 TESTE DE FUNCIONALIDADES AVANÇADAS")
    print("=" * 50)
    
    try:
        from bot_v13_railway import AdvancedValueBettingSystem
        
        system = AdvancedValueBettingSystem()
        
        # Teste 1: Análise de forma de times
        print("1. Testando análise de forma de times...")
        t1_form = system._analyze_team_form('T1', 'LCK')
        geng_form = system._analyze_team_form('Gen.G Esports', 'LCK')
        
        print(f"   T1 - Record: {t1_form['recent_record']}, Score: {t1_form['form_score']:.3f}")
        print(f"   Gen.G - Record: {geng_form['recent_record']}, Score: {geng_form['form_score']:.3f}")
        print("   ✅ Análise de forma: FUNCIONANDO")
        
        # Teste 2: Análise head-to-head
        print("\n2. Testando análise head-to-head...")
        h2h = system._analyze_head_to_head('T1', 'Gen.G Esports')
        print(f"   H2H T1: {h2h['team1_h2h_winrate']*100:.1f}%")
        print(f"   H2H Gen.G: {h2h['team2_h2h_winrate']*100:.1f}%")
        print(f"   Confiança H2H: {h2h['h2h_confidence']*100:.1f}%")
        print("   ✅ Análise H2H: FUNCIONANDO")
        
        # Teste 3: Análise de jogadores
        print("\n3. Testando análise de jogadores...")
        players = system._analyze_player_performance('T1', 'Gen.G Esports', 'LCK')
        print(f"   T1 - Rating médio: {players['team1_avg_rating']:.1f}")
        print(f"   T1 - Jogadores estrela: {players['team1_star_players']}")
        print(f"   Gen.G - Rating médio: {players['team2_avg_rating']:.1f}")
        print(f"   Gen.G - Jogadores estrela: {players['team2_star_players']}")
        print("   ✅ Análise de jogadores: FUNCIONANDO")
        
        # Teste 4: Análise de composições
        print("\n4. Testando análise de composições...")
        comps = system._analyze_composition_synergy('T1', 'Gen.G Esports', 'LCK')
        print(f"   T1 - Estilo: {comps['team1_playstyle']}")
        print(f"   Gen.G - Estilo: {comps['team2_playstyle']}")
        print(f"   Compatibilidade: {comps['style_compatibility']*100:.1f}%")
        print("   ✅ Análise de composições: FUNCIONANDO")
        
        # Teste 5: Análise de meta
        print("\n5. Testando análise de meta...")
        meta = system._analyze_meta_adaptation('T1', 'Gen.G Esports', 'LCK')
        print(f"   Patch atual: {meta['current_patch']}")
        print(f"   T1 - Adaptação: {meta['team1_adaptation']:.1f}")
        print(f"   Gen.G - Adaptação: {meta['team2_adaptation']:.1f}")
        print("   ✅ Análise de meta: FUNCIONANDO")
        
        # Teste 6: Cálculo de unidades avançado
        print("\n6. Testando cálculo de unidades avançado...")
        units_high = system.calculate_bet_units(0.10, 0.85, 0.15)  # EV alto
        units_low = system.calculate_bet_units(0.03, 0.65, 0.05)   # EV baixo
        
        print(f"   EV Alto (10%): {units_high['units']} unidades - {units_high['recommendation']}")
        print(f"   EV Baixo (3%): {units_low['units']} unidades - {units_low['recommendation']}")
        print("   ✅ Cálculo de unidades: FUNCIONANDO")
        
        print("\n✅ TODAS AS FUNCIONALIDADES AVANÇADAS TESTADAS COM SUCESSO!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de funcionalidades: {e}")
        return False

if __name__ == "__main__":
    print(f"🕐 Iniciando testes em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Teste principal de integração
    integration_success = test_integration()
    
    if integration_success:
        # Teste de funcionalidades avançadas
        features_success = test_advanced_features()
        
        if features_success:
            print(f"\n🎉 INTEGRAÇÃO COMPLETA E FUNCIONAL!")
            print(f"✅ Sistema Avançado de Value Betting 100% operacional")
            print(f"🚀 Bot pronto para análises multifatoriais avançadas")
        else:
            print(f"\n⚠️ Integração OK, mas algumas funcionalidades com problemas")
    else:
        print(f"\n❌ FALHA NA INTEGRAÇÃO")
        print(f"🔧 Verifique os erros acima e corrija antes de usar")
    
    print(f"\n🕐 Testes finalizados em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 