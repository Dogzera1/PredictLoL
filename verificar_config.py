from bot.utils.constants import MIN_ODDS, MAX_ODDS, PREDICTION_THRESHOLDS

print("📊 CONFIGURAÇÕES ATUAIS DO SISTEMA:")
print("=" * 50)
print(f"Odds Mínima: {MIN_ODDS}x")
print(f"Odds Máxima: {MAX_ODDS}x")
print(f"Threshold Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_threshold', 'N/A')}x")
print(f"EV Mínimo Normal: {PREDICTION_THRESHOLDS['min_ev']}%")
print(f"EV Mínimo Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_min_ev', 'N/A')}%")
print(f"Confiança Mínima: {PREDICTION_THRESHOLDS['min_confidence']:.1%}")
print("=" * 50)
print("✅ Sistema otimizado para detectar odds altas com valor!")
print("✅ Range expandido de 1.5x até 8.0x")
print("✅ Critérios especiais para odds ≥ 4.0x") 