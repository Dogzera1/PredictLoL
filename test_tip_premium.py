#!/usr/bin/env python3
"""
Teste da Experiência Premium de Tips
Testa o novo formato melhorado de tips com todas as informações aprimoradas
"""

import asyncio
import os
import sys
from datetime import datetime

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurações de ambiente
os.environ["PANDASCORE_API_KEY"] = "90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["LOG_LEVEL"] = "INFO"

from bot.data_models.tip_data import ProfessionalTip
from bot.utils.constants import TIP_TEMPLATE, RISK_EMOJIS

def create_sample_premium_tip() -> ProfessionalTip:
    """Cria uma tip de amostra com experiência premium"""
    
    return ProfessionalTip(
        # Dados obrigatórios
        match_id="sample_match_123",
        team_a="G2 Esports",
        team_b="Fnatic",
        league="LEC",
        tournament="LEC Spring 2025",
        tip_on_team="G2 Esports",
        odds=1.85,
        units=2.5,
        risk_level="Risco Médio",
        confidence_percentage=72.5,
        ev_percentage=8.3,
        analysis_reasoning="Análise detalhada mostra vantagem estratégica do G2.",
        game_time_at_tip="18min",
        game_time_seconds=1080,
        prediction_source="HYBRID",
        data_quality_score=0.85,
        
        # Novos campos premium
        min_odds=1.75,
        map_number=2,
        match_status="🔴 AO VIVO",
        explanation_text="G2 Esports demonstra superioridade estratégica com controle de mapa excepcional. O time está dominando objetivos cruciais e mantendo vantagem de ouro consistente, indicando alta probabilidade de vitória.",
        game_situation_text="💰 G2 lidera com 3,200 de ouro\n🏰 G2 com vantagem de 2 torres\n🐉 G2 controla dragões (2 a mais)\n⚡ G2 com momentum após Baron",
        objectives_text="• 🐉 Alma do Dragão\n• 🐲 Baron Nashor (20min)\n• 🏰 Torres Externas",
        timing_advice="⚡ **Entre AGORA** - Situação ideal identificada",
        alerts_text="• 🐲 Baron disponível - Próximos 5min são críticos\n• 👑 Posição dominante - Chance baixa de virada",
        history_text="📊 Analisando histórico recente de G2 Esports vs Fnatic\n• G2 venceu últimos 3 confrontos diretos\n• Performance em partidas similares: 78% vitórias",
        unit_value=10.0
    )

def format_premium_message(tip: ProfessionalTip) -> str:
    """Formata mensagem premium usando o novo template"""
    
    # Determina emoji de risco
    risk_emoji = RISK_EMOJIS.get(tip.risk_level, "📊")
    
    # Constrói mensagem com novo formato premium
    message_parts = []
    
    # 1. Header
    message_parts.append(TIP_TEMPLATE["header"])
    message_parts.append("")
    
    # 2. Informações da partida
    match_info = TIP_TEMPLATE["match_info"].format(
        team_a=tip.team_a,
        team_b=tip.team_b,
        league=tip.league,
        map_number=f"Mapa {tip.map_number}",
        game_time=tip.game_time_at_tip,
        match_status=tip.match_status
    )
    message_parts.append(match_info)
    message_parts.append("")
    
    # 3. Tip principal
    tip_main = TIP_TEMPLATE["tip_main"].format(
        tip_on_team=tip.tip_on_team,
        odds=tip.odds,
        min_odds=tip.min_odds
    )
    message_parts.append(tip_main)
    message_parts.append("")
    
    # 4. Explicação didática
    if tip.explanation_text:
        explanation = TIP_TEMPLATE["tip_explanation"].format(
            explanation_text=tip.explanation_text
        )
        message_parts.append(explanation)
        message_parts.append("")
    
    # 5. Gestão de risco
    risk_management = TIP_TEMPLATE["risk_management"].format(
        risk_emoji=risk_emoji,
        units=tip.units,
        risk_level=tip.risk_level,
        unit_value=f"{tip.unit_value:.0f}",
        bet_amount=f"{tip.bet_amount:.0f}"
    )
    message_parts.append(risk_management)
    message_parts.append("")
    
    # 6. Análise técnica
    technical_analysis = TIP_TEMPLATE["technical_analysis"].format(
        confidence_percentage=f"{tip.confidence_percentage:.0f}",
        ev_percentage=f"{tip.ev_percentage:.1f}",
        data_quality_score=f"{tip.data_quality_score*100:.0f}"
    )
    message_parts.append(technical_analysis)
    message_parts.append("")
    
    # 7. Situação atual do jogo
    if tip.game_situation_text:
        game_situation = TIP_TEMPLATE["game_situation"].format(
            game_situation_text=tip.game_situation_text
        )
        message_parts.append(game_situation)
        message_parts.append("")
    
    # 8. Próximos objetivos
    if tip.objectives_text:
        next_objectives = TIP_TEMPLATE["next_objectives"].format(
            objectives_text=tip.objectives_text
        )
        message_parts.append(next_objectives)
        message_parts.append("")
    
    # 9. Timing da aposta
    if tip.timing_advice:
        bet_timing = TIP_TEMPLATE["bet_timing"].format(
            timing_advice=tip.timing_advice
        )
        message_parts.append(bet_timing)
        message_parts.append("")
    
    # 10. Histórico dos times
    if tip.history_text:
        teams_history = TIP_TEMPLATE["teams_history"].format(
            history_text=tip.history_text
        )
        message_parts.append(teams_history)
        message_parts.append("")
    
    # 11. Alertas importantes
    if tip.alerts_text:
        alerts = TIP_TEMPLATE["alerts"].format(
            alerts_text=tip.alerts_text
        )
        message_parts.append(alerts)
        message_parts.append("")
    
    # 12. Rodapé
    footer = TIP_TEMPLATE["footer"].format(
        prediction_source=tip.prediction_source,
        generated_time=tip.generated_time,
        tip_id=tip.tip_id
    )
    message_parts.append(footer)
    
    # Junta todas as partes
    return "\n".join(message_parts)

def main():
    """Função principal de teste"""
    print("🎮 Testando Experiência Premium de Tips")
    print("=" * 60)
    
    # Cria tip de amostra
    sample_tip = create_sample_premium_tip()
    
    print("✅ Tip premium criada com sucesso!")
    print(f"📊 ID da Tip: {sample_tip.tip_id}")
    print(f"💰 Valor da aposta: R$ {sample_tip.bet_amount:.2f}")
    print(f"📈 Expected Value: +{sample_tip.ev_percentage:.1f}%")
    print()
    
    # Formata e exibe mensagem
    formatted_message = format_premium_message(sample_tip)
    
    print("📱 PRÉVIA DA MENSAGEM PREMIUM:")
    print("=" * 60)
    print(formatted_message)
    print("=" * 60)
    
    # Valida tip
    is_valid, validation_msg = sample_tip.validate()
    print(f"✅ Tip válida: {is_valid}")
    if not is_valid:
        print(f"❌ Erro de validação: {validation_msg}")
    
    print("\n🎉 Teste da experiência premium concluído!")

if __name__ == "__main__":
    main() 
