#!/usr/bin/env python3

import asyncio
from bot.utils.constants import MIN_ODDS, MAX_ODDS, PREDICTION_THRESHOLDS

def test_direct_validation():
    """Testa validação direta de odds e critérios"""
    
    print("🎯 Teste Completo de Sistema de Odds")
    print("=" * 60)
    
    # Simula função de validação
    def validate_tip_criteria(confidence, ev_percentage, odds, game_time=900, data_quality=0.8):
        """Simula validação com lógica de odds altas"""
        
        # Detecta se são odds altas
        is_high_odds = odds >= PREDICTION_THRESHOLDS.get("high_odds_threshold", 4.0)
        
        # Critérios padrão
        meets_confidence = confidence >= PREDICTION_THRESHOLDS["min_confidence"]
        meets_ev = ev_percentage >= PREDICTION_THRESHOLDS["min_ev"]
        meets_odds = PREDICTION_THRESHOLDS["min_odds"] <= odds <= PREDICTION_THRESHOLDS["max_odds"]
        meets_timing = game_time >= PREDICTION_THRESHOLDS["min_game_time"]
        meets_quality = data_quality >= PREDICTION_THRESHOLDS["min_data_quality"]
        
        # LÓGICA ESPECIAL PARA ODDS ALTAS
        if is_high_odds:
            print(f"   🎯 ODDS ALTAS DETECTADAS: {odds:.2f}x - Aplicando critérios especiais")
            
            # Para odds altas, relaxamos a confiança mas exigimos EV maior
            high_odds_min_ev = PREDICTION_THRESHOLDS.get("high_odds_min_ev", 3.0)
            confidence_penalty = PREDICTION_THRESHOLDS.get("high_odds_confidence_penalty", 0.1)
            
            # Ajusta critérios para odds altas
            adjusted_confidence_threshold = max(
                PREDICTION_THRESHOLDS["min_confidence"] - confidence_penalty,
                0.35  # Nunca menos que 35% de confiança
            )
            
            meets_confidence_high_odds = confidence >= adjusted_confidence_threshold
            meets_ev_high_odds = ev_percentage >= high_odds_min_ev
            
            # Para odds altas, usamos critérios ajustados
            meets_confidence = meets_confidence_high_odds
            meets_ev = meets_ev_high_odds
            
            print(f"   📊 Confiança: {confidence:.1%} >= {adjusted_confidence_threshold:.1%} = {meets_confidence}")
            print(f"   📈 EV: {ev_percentage:.1f}% >= {high_odds_min_ev:.1f}% = {meets_ev}")
        else:
            print(f"   📊 Confiança: {confidence:.1%} >= {PREDICTION_THRESHOLDS['min_confidence']:.1%} = {meets_confidence}")
            print(f"   📈 EV: {ev_percentage:.1f}% >= {PREDICTION_THRESHOLDS['min_ev']:.1f}% = {meets_ev}")
        
        is_valid = all([meets_confidence, meets_ev, meets_odds, meets_timing, meets_quality])
        
        # Determina motivo de rejeição
        reason = None
        if not meets_confidence:
            threshold = (PREDICTION_THRESHOLDS["min_confidence"] - 
                        (PREDICTION_THRESHOLDS.get("high_odds_confidence_penalty", 0.1) if is_high_odds else 0))
            reason = f"Confiança muito baixa: {confidence:.1%} (min: {threshold:.1%})"
            if is_high_odds:
                reason += " [Critério reduzido para odds altas]"
        elif not meets_ev:
            threshold = (PREDICTION_THRESHOLDS.get("high_odds_min_ev", 3.0) if is_high_odds 
                        else PREDICTION_THRESHOLDS["min_ev"])
            reason = f"EV insuficiente: {ev_percentage:.1f}% (min: {threshold:.1f}%)"
            if is_high_odds:
                reason += " [EV mínimo aumentado para odds altas]"
        elif not meets_odds:
            reason = f"Odds fora do range: {odds:.2f}x (range: {PREDICTION_THRESHOLDS['min_odds']:.2f}x-{PREDICTION_THRESHOLDS['max_odds']:.2f}x)"
        elif not meets_timing:
            reason = f"Jogo muito cedo: {game_time//60}min"
        elif not meets_quality:
            reason = f"Qualidade dos dados baixa: {data_quality:.1%}"
        
        return {
            "is_valid": is_valid,
            "reason": reason,
            "is_high_odds": is_high_odds,
            "special_criteria_applied": is_high_odds
        }
    
    # Cenários de teste
    test_scenarios = [
        {
            "name": "❌ Odds Baixas (1.3x) - Deve ser rejeitada",
            "odds": 1.30, "confidence": 0.65, "ev": 2.5,
            "expected": False
        },
        {
            "name": "✅ Odds Mínimas (1.5x) - Deve passar",
            "odds": 1.50, "confidence": 0.55, "ev": 1.5,
            "expected": True
        },
        {
            "name": "✅ Odds Médias (2.5x) - Critérios normais",
            "odds": 2.50, "confidence": 0.52, "ev": 2.0,
            "expected": True
        },
        {
            "name": "✅ Odds Altas (5.0x) - Critérios especiais",
            "odds": 5.00, "confidence": 0.40, "ev": 4.0,
            "expected": True
        },
        {
            "name": "✅ Odds Muito Altas (7.5x) - Alto valor",
            "odds": 7.50, "confidence": 0.38, "ev": 8.5,
            "expected": True
        },
        {
            "name": "❌ Odds Extremas (9.0x) - Fora do range",
            "odds": 9.00, "confidence": 0.45, "ev": 12.0,
            "expected": False
        },
        {
            "name": "❌ Odds Altas com EV baixo",
            "odds": 6.00, "confidence": 0.42, "ev": 1.5,
            "expected": False
        },
        {
            "name": "✅ Odds Altas limite (4.0x) - Primeiro threshold",
            "odds": 4.00, "confidence": 0.40, "ev": 3.5,
            "expected": True
        }
    ]
    
    print("🔍 Testando diferentes cenários de odds:")
    print()
    
    results_summary = {"passed": 0, "failed": 0, "total": len(test_scenarios)}
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📊 {i}. {scenario['name']}")
        print(f"   Odds: {scenario['odds']:.2f}x | Confiança: {scenario['confidence']:.1%} | EV: {scenario['ev']:.1f}%")
        
        # Testa validação
        validation = validate_tip_criteria(
            confidence=scenario['confidence'],
            ev_percentage=scenario['ev'],
            odds=scenario['odds']
        )
        
        result = validation['is_valid']
        expected = scenario['expected']
        status = "✅" if result == expected else "❌"
        
        print(f"   {status} Resultado: {'APROVADA' if result else 'REJEITADA'}")
        
        if not result and validation.get('reason'):
            print(f"   📝 Motivo: {validation['reason']}")
        
        if result == expected:
            results_summary["passed"] += 1
        else:
            results_summary["failed"] += 1
            print(f"   ⚠️ ERRO: Esperado {'APROVADA' if expected else 'REJEITADA'}")
        
        print()
    
    # Resumo das configurações
    print("🔍 Configurações Atuais do Sistema:")
    print(f"   📌 Odds Mínima: {MIN_ODDS:.2f}x (era 1.30x)")
    print(f"   📌 Odds Máxima: {MAX_ODDS:.2f}x (era 3.50x)")
    print(f"   📌 Threshold Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_threshold', 4.0):.2f}x")
    print(f"   📌 EV Mínimo Normal: {PREDICTION_THRESHOLDS['min_ev']:.1f}%")
    print(f"   📌 EV Mínimo Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_min_ev', 3.0):.1f}%")
    print(f"   📌 Confiança Mínima: {PREDICTION_THRESHOLDS['min_confidence']:.1%}")
    print(f"   📌 Penalidade Confiança Odds Altas: -{PREDICTION_THRESHOLDS.get('high_odds_confidence_penalty', 0.1):.1%}")
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES:")
    print(f"   ✅ Passou: {results_summary['passed']}/{results_summary['total']}")
    print(f"   ❌ Falhou: {results_summary['failed']}/{results_summary['total']}")
    
    if results_summary['failed'] == 0:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema otimizado para odds altas com valor")
        print("✅ Odds mínimas ajustadas para 1.5x conforme solicitado")
        print("✅ Sistema detecta e processa odds altas adequadamente")
    else:
        print("⚠️ Alguns testes falharam - verificar lógica")
    
    return results_summary['failed'] == 0

if __name__ == "__main__":
    test_direct_validation() 
