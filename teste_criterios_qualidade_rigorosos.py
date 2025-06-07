import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data_models.tip_data import ProfessionalTip

def test_rigorous_quality_criteria():
    """Testa os novos critérios rigorosos de qualidade"""
    
    print("=== TESTE: CRITÉRIOS RIGOROSOS DE QUALIDADE ===\n")
    
    # TESTE 1: Tip de BAIXA qualidade (deve ser rejeitada)
    print("TESTE 1: Tip de baixa qualidade (como a que foi enviada)")
    tip_baixa_qualidade = ProfessionalTip(
        match_id="match_123",
        team_a="FlyQuest",
        team_b="Cloud9 Kia",
        league="LTA Norte",
        tournament="LTA Norte 2024",
        tip_on_team="FlyQuest ML",
        odds=2.00,
        units=0.5,
        risk_level="Risco Mínimo",
        confidence_percentage=51.9,  # BAIXA (< 65%)
        ev_percentage=3.7,           # BAIXO (< 5%)
        analysis_reasoning="FlyQuest predicted winner",
        game_time_at_tip="LIVE",
        game_time_seconds=0,
        prediction_source="HYBRID",
        data_quality_score=0.10     # MUITO BAIXA (< 70%)
    )
    
    valido1, erro1 = tip_baixa_qualidade.validate()
    print(f"   Resultado: {'❌ ERRO - Foi aceita!' if valido1 else '✅ REJEITADA corretamente'}")
    if not valido1:
        print(f"   Motivo: {erro1}")
    
    # TESTE 2: Tip de ALTA qualidade (deve ser aceita)
    print("\nTESTE 2: Tip de alta qualidade")
    tip_alta_qualidade = ProfessionalTip(
        match_id="match_456",
        team_a="Team Liquid",
        team_b="TSM",
        league="LCS",
        tournament="LCS Spring 2024",
        tip_on_team="Team Liquid ML",
        odds=1.85,
        units=2.0,
        risk_level="Risco Médio",
        confidence_percentage=72.5,  # ALTA (≥ 65%)
        ev_percentage=8.3,           # BOM (≥ 5%)
        analysis_reasoning="Team Liquid shows superior draft composition and macro play. Strong mid-game focus expected.",
        game_time_at_tip="2min",
        game_time_seconds=120,
        prediction_source="ML System",
        data_quality_score=0.85     # ALTA (≥ 70%)
    )
    
    valido2, erro2 = tip_alta_qualidade.validate()
    print(f"   Resultado: {'✅ ACEITA corretamente' if valido2 else '❌ ERRO - Foi rejeitada!'}")
    if not valido2:
        print(f"   Motivo: {erro2}")
    
    # TESTE 3: Tip borderline (no limite)
    print("\nTESTE 3: Tip no limite dos critérios")
    tip_limite = ProfessionalTip(
        match_id="match_789",
        team_a="FlyQuest",
        team_b="100 Thieves",
        league="LCS",
        tournament="LCS Spring 2024",
        tip_on_team="FlyQuest ML",
        odds=2.10,
        units=1.5,
        risk_level="Risco Médio",
        confidence_percentage=65.0,  # Exatamente no limite
        ev_percentage=5.0,           # Exatamente no limite
        analysis_reasoning="Close match but FlyQuest has slight early game advantage in current meta.",
        game_time_at_tip="1min",
        game_time_seconds=60,
        prediction_source="Hybrid Analysis",
        data_quality_score=0.70     # Exatamente no limite
    )
    
    valido3, erro3 = tip_limite.validate()
    print(f"   Resultado: {'✅ ACEITA no limite' if valido3 else '❌ Rejeitada no limite'}")
    if not valido3:
        print(f"   Motivo: {erro3}")
    
    # RESUMO
    testes_corretos = [
        not valido1,  # Baixa qualidade deve ser rejeitada
        valido2,      # Alta qualidade deve ser aceita
        valido3       # Limite deve ser aceita
    ]
    
    total_testes = len(testes_corretos)
    testes_ok = sum(testes_corretos)
    
    print("\n" + "="*60)
    print(f"RESUMO: {testes_ok}/{total_testes} testes passaram")
    
    if testes_ok == total_testes:
        print("🎉 SUCESSO: Critérios rigorosos funcionando!")
        print("✅ Tips de baixa qualidade são rejeitadas")
        print("✅ Tips de alta qualidade são aceitas")
        print("❌ A tip que foi enviada (10% qualidade) agora seria REJEITADA")
    else:
        print("⚠️ PROBLEMA: Alguns critérios não funcionam")
    
    print("\n📊 NOVOS CRITÉRIOS ATIVOS:")
    print("   • Confiança mínima: 65% (era 45%)")
    print("   • EV mínimo: 5.0% (era 0.5%)")
    print("   • Qualidade dos dados: 70% (novo)")
    print("   • Qualidade mínima sistema: 65-70% (era 30-40%)")
    
    return testes_ok == total_testes

if __name__ == "__main__":
    test_rigorous_quality_criteria() 