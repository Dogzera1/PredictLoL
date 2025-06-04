#!/usr/bin/env python3
"""
Teste do Sistema de Unidades Profissionais - Bot LoL V3 Ultra Avançado

Script para testar o cálculo de unidades em diferentes cenários.
"""

import os
import sys
from typing import List, Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.core_logic import ProfessionalUnitsSystem
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging para testes
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_units")


def test_scenario(units_system: ProfessionalUnitsSystem, scenario: Dict[str, Any]) -> None:
    """Testa um cenário específico"""
    name = scenario["name"]
    confidence = scenario["confidence"]
    ev_percentage = scenario["ev_percentage"] 
    league_tier = scenario.get("league_tier", 2)
    odds = scenario.get("odds")
    
    print(f"\n{'='*60}")
    print(f"🧪 TESTE: {name}")
    print(f"{'='*60}")
    
    print(f"📊 Parâmetros:")
    print(f"   • Confiança: {confidence:.1%}")
    print(f"   • Expected Value: {ev_percentage:.1f}%")
    print(f"   • Tier da Liga: {league_tier}")
    if odds:
        print(f"   • Odds: {odds:.2f}")
    
    # Calcula unidades
    result = units_system.calculate_units(confidence, ev_percentage, league_tier, odds)
    
    # Mostra resultado
    if result["valid"]:
        print(f"\n✅ RESULTADO VÁLIDO:")
        print(f"   • Unidades: {result['units']:.1f}")
        print(f"   • Nível de Risco: {result['risk_level']}")
        print(f"   • Valor da Aposta: R${result['bet_amount']:.2f}")
        print(f"   • % do Bankroll: {result['percentage_of_bankroll']:.1f}%")
        
        print(f"\n🔧 Modificadores aplicados:")
        for modifier, value in result["modifiers_applied"].items():
            print(f"   • {modifier}: {value:+.2f}")
        
        print(f"\n📝 Explicação:")
        print(result["reasoning"])
        
        # Avaliação de risco
        risk_assessment = units_system.get_risk_assessment(result["units"])
        print(f"\n⚠️ Avaliação: {risk_assessment}")
        
    else:
        print(f"\n❌ RESULTADO INVÁLIDO:")
        print(f"   • Motivo: {result['reason']}")
        print(f"   • Detalhes: {result['details']}")


def test_validation_scenarios(units_system: ProfessionalUnitsSystem) -> None:
    """Testa cenários de validação"""
    print(f"\n{'='*80}")
    print("🔍 TESTES DE VALIDAÇÃO")
    print(f"{'='*80}")
    
    validation_scenarios = [
        {
            "name": "Confiança muito baixa",
            "confidence": 0.50,  # 50% - abaixo do mínimo (70%)
            "ev_percentage": 10.0
        },
        {
            "name": "EV muito baixo",
            "confidence": 0.80,  # 80% - OK
            "ev_percentage": 2.0  # 2% - abaixo do mínimo (5%)
        },
        {
            "name": "Odds muito baixas",
            "confidence": 0.85,
            "ev_percentage": 8.0,
            "odds": 1.20  # Abaixo do mínimo (1.30)
        },
        {
            "name": "Odds muito altas",
            "confidence": 0.75,
            "ev_percentage": 6.0,
            "odds": 4.00  # Acima do máximo (3.50)
        }
    ]
    
    for scenario in validation_scenarios:
        test_scenario(units_system, scenario)


def test_kelly_criterion(units_system: ProfessionalUnitsSystem) -> None:
    """Testa cálculo de Kelly"""
    print(f"\n{'='*80}")
    print("📊 TESTE: KELLY CRITERION")
    print(f"{'='*80}")
    
    kelly_scenarios = [
        {"win_prob": 0.60, "odds": 2.00, "description": "Cenário equilibrado"},
        {"win_prob": 0.75, "odds": 1.80, "description": "Alta probabilidade, odds baixas"},
        {"win_prob": 0.55, "odds": 2.50, "description": "Probabilidade moderada, odds altas"},
        {"win_prob": 0.90, "odds": 1.50, "description": "Altíssima probabilidade"},
    ]
    
    for scenario in kelly_scenarios:
        win_prob = scenario["win_prob"]
        odds = scenario["odds"]
        description = scenario["description"]
        
        kelly_fraction = units_system.calculate_kelly_criterion(win_prob, odds)
        kelly_percentage = kelly_fraction * 100
        
        print(f"\n🎯 {description}:")
        print(f"   • Probabilidade: {win_prob:.1%}")
        print(f"   • Odds: {odds:.2f}")
        print(f"   • Kelly: {kelly_percentage:.2f}% do bankroll")


def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do Sistema de Unidades Profissionais...")
    print(f"🔧 Python: {sys.version}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    # Inicializa sistema com bankroll de teste
    bankroll = 2000.0  # R$ 2.000
    units_system = ProfessionalUnitsSystem(bankroll=bankroll)
    
    print(f"\n🏦 Sistema inicializado:")
    print(f"   • Bankroll: R${bankroll:.2f}")
    print(f"   • 1 Unidade = R${units_system.unit_value:.2f}")
    
    # Mostra explicação do sistema
    print(f"\n{units_system.get_units_explanation()}")
    
    # Cenários de teste principais
    main_scenarios = [
        {
            "name": "Cenário ULTRA HIGH (LCK)",
            "confidence": 0.92,
            "ev_percentage": 18.0,
            "league_tier": 1,  # LCK (Tier 1)
            "odds": 2.10
        },
        {
            "name": "Cenário HIGH (CBLOL)", 
            "confidence": 0.82,
            "ev_percentage": 12.0,
            "league_tier": 2,  # CBLOL (Tier 2)
            "odds": 1.85
        },
        {
            "name": "Cenário MEDIUM (LEC)",
            "confidence": 0.74,
            "ev_percentage": 7.5,
            "league_tier": 1,  # LEC (Tier 1)
            "odds": 2.25
        },
        {
            "name": "Cenário LOW (Liga Menor)",
            "confidence": 0.68,
            "ev_percentage": 5.2,
            "league_tier": 3,  # Liga menor (Tier 3)
            "odds": 1.95
        },
        {
            "name": "Cenário MÍNIMO VÁLIDO",
            "confidence": 0.70,  # Exatamente no mínimo
            "ev_percentage": 5.0,  # Exatamente no mínimo
            "league_tier": 2
        },
        {
            "name": "Cenário EXTREMO (Odds ideais)",
            "confidence": 0.95,
            "ev_percentage": 22.0,
            "league_tier": 1,
            "odds": 2.00  # Odds ideais
        }
    ]
    
    # Executa testes principais
    for scenario in main_scenarios:
        test_scenario(units_system, scenario)
    
    # Testa cenários de validação
    test_validation_scenarios(units_system)
    
    # Testa Kelly Criterion
    test_kelly_criterion(units_system)
    
    # Teste de validação de critérios
    print(f"\n{'='*80}")
    print("✅ TESTE: VALIDAÇÃO DE CRITÉRIOS")
    print(f"{'='*80}")
    
    test_analyses = [
        {
            "confidence": 0.85,
            "ev_percentage": 12.0,
            "odds": 2.10,
            "description": "Análise válida"
        },
        {
            "confidence": 0.65,  # Muito baixa
            "ev_percentage": 8.0,
            "odds": 1.90,
            "description": "Confiança insuficiente"
        }
    ]
    
    for analysis in test_analyses:
        valid, reason = units_system.validate_tip_criteria(analysis)
        status = "✅ VÁLIDO" if valid else "❌ INVÁLIDO"
        print(f"\n{status}: {analysis['description']}")
        print(f"   Motivo: {reason}")
    
    # Teste de atualização de bankroll
    print(f"\n{'='*80}")
    print("💰 TESTE: ATUALIZAÇÃO DE BANKROLL")
    print(f"{'='*80}")
    
    print(f"Bankroll atual: R${units_system.bankroll:.2f}")
    new_bankroll = 3000.0
    units_system.update_bankroll(new_bankroll)
    print(f"Novo bankroll: R${units_system.bankroll:.2f}")
    print(f"Nova unidade: R${units_system.unit_value:.2f}")
    
    print(f"\n{'='*80}")
    print("🎉 TODOS OS TESTES CONCLUÍDOS!")
    print(f"{'='*80}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal durante os testes: {e}")
        sys.exit(1) 
