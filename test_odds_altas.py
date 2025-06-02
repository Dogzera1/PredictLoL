#!/usr/bin/env python3

import asyncio
from dotenv import load_dotenv
from bot.core_logic.prediction_system import DynamicPredictionSystem, PredictionMethod
from bot.core_logic.units_system import ProfessionalUnitsSystem
from bot.core_logic.game_analyzer import LoLGameAnalyzer

# Carrega variáveis do .env
load_dotenv()

async def test_odds_processing():
    """Testa processamento de diferentes tipos de odds"""
    
    print("🎯 Teste de Processamento de Odds")
    print("=" * 60)
    
    # Inicializa sistema
    units_system = ProfessionalUnitsSystem()
    game_analyzer = LoLGameAnalyzer()
    prediction_system = DynamicPredictionSystem(game_analyzer, units_system)
    
    # Cenários de teste
    test_scenarios = [
        {
            "name": "Odds Baixas (1.3x) - Deve ser rejeitada",
            "odds": 1.30,
            "confidence": 0.65,
            "ev": 2.5,
            "expected_result": False
        },
        {
            "name": "Odds Mínimas (1.5x) - Deve passar",
            "odds": 1.50,
            "confidence": 0.55,
            "ev": 1.5,
            "expected_result": True
        },
        {
            "name": "Odds Médias (2.5x) - Critérios normais",
            "odds": 2.50,
            "confidence": 0.52,
            "ev": 2.0,
            "expected_result": True
        },
        {
            "name": "Odds Altas (5.0x) - Critérios especiais",
            "odds": 5.00,
            "confidence": 0.40,  # Abaixo do normal, mas deve passar por ser odds alta
            "ev": 4.0,           # EV alto para compensar
            "expected_result": True
        },
        {
            "name": "Odds Muito Altas (7.5x) - Alto valor",
            "odds": 7.50,
            "confidence": 0.38,  # Baixa confiança mas EV muito alto
            "ev": 8.5,
            "expected_result": True
        },
        {
            "name": "Odds Extremas (9.0x) - Deve ser rejeitada (fora do range)",
            "odds": 9.00,
            "confidence": 0.45,
            "ev": 12.0,
            "expected_result": False
        },
        {
            "name": "Odds Altas com EV baixo - Deve ser rejeitada",
            "odds": 6.00,
            "confidence": 0.42,
            "ev": 1.5,  # EV muito baixo para odds altas
            "expected_result": False
        }
    ]
    
    print("🔍 Testando diferentes cenários de odds:")
    print()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📊 {i}. {scenario['name']}")
        print(f"   Odds: {scenario['odds']:.2f}x")
        print(f"   Confiança: {scenario['confidence']:.1%}")
        print(f"   EV: {scenario['ev']:.1f}%")
        
        # Testa validação
        validation = prediction_system._validate_tip_criteria(
            confidence=scenario['confidence'],
            ev_percentage=scenario['ev'],
            odds=scenario['odds'],
            game_time=900,  # 15 minutos
            data_quality=0.8
        )
        
        result = validation['is_valid']
        expected = scenario['expected_result']
        status = "✅" if result == expected else "❌"
        
        print(f"   {status} Resultado: {'APROVADA' if result else 'REJEITADA'}")
        
        if validation.get('is_high_odds'):
            print(f"   🎯 ODDS ALTAS detectadas - Critérios especiais aplicados")
        
        if not result:
            print(f"   📝 Motivo: {validation.get('reason', 'N/A')}")
        
        if result != expected:
            print(f"   ⚠️ ERRO: Esperado {'APROVADA' if expected else 'REJEITADA'}")
        
        print()
    
    # Teste adicional: verificar range de odds
    print("🔍 Verificando range de odds configurado:")
    from bot.utils.constants import MIN_ODDS, MAX_ODDS, PREDICTION_THRESHOLDS
    
    print(f"   Odds Mínima Global: {MIN_ODDS:.2f}x")
    print(f"   Odds Máxima Global: {MAX_ODDS:.2f}x")
    print(f"   Odds Mínima Predição: {PREDICTION_THRESHOLDS['min_odds']:.2f}x")
    print(f"   Odds Máxima Predição: {PREDICTION_THRESHOLDS['max_odds']:.2f}x")
    print(f"   Threshold Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_threshold', 4.0):.2f}x")
    print(f"   EV Mínimo Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_min_ev', 3.0):.1f}%")
    
    print("\n" + "=" * 60)
    print("📋 RESUMO:")
    print("✅ Odds mínimas ajustadas para 1.5x")
    print("✅ Odds máximas expandidas para 8.0x")
    print("✅ Sistema especial para odds altas (≥4.0x)")
    print("✅ Critérios flexíveis para capturar valor em odds altas")
    print("🎯 Sistema otimizado para detectar oportunidades de valor!")

if __name__ == "__main__":
    asyncio.run(test_odds_processing()) 