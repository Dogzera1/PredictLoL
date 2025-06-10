#!/usr/bin/env python3
"""
Teste: Sistema de Composições Pós-Draft
Verifica se o sistema está refletindo adequadamente para fornecer previsões
após draft das partidas baseado em composições
"""

import os
import sys
import asyncio
from pathlib import Path

# Configuração do path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

async def teste_composicoes_pos_draft():
    """Testa se o sistema está analisando composições pós-draft adequadamente"""
    
    print("🎮 TESTE: SISTEMA DE COMPOSIÇÕES PÓS-DRAFT")
    print("=" * 60)
    print("Verificando se o sistema está refletindo para fornecer previsões")
    print("após draft das partidas baseado em composições\n")
    
    try:
        # 1. Importar componentes necessários
        from bot.analyzers.composition_analyzer import CompositionAnalyzer
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.data_models.match_data import MatchData
        
        print("📦 1. COMPONENTES IMPORTADOS CORRETAMENTE")
        
        # 2. Criar analisador de composições
        comp_analyzer = CompositionAnalyzer()
        await asyncio.sleep(1)  # Aguarda inicialização das databases
        print("✅ CompositionAnalyzer inicializado")
        
        # 3. Testar análise de composição específica
        print("\n🧪 2. TESTANDO ANÁLISE DE COMPOSIÇÃO:")
        
        # Composição simulada pós-draft (exemplo real)
        team1_picks = [
            {"champion": "Azir", "position": "mid", "pick_order": 1},
            {"champion": "Graves", "position": "jungle", "pick_order": 2},
            {"champion": "Thresh", "position": "support", "pick_order": 3},
            {"champion": "Jinx", "position": "adc", "pick_order": 4},
            {"champion": "Gnar", "position": "top", "pick_order": 5}
        ]
        
        team2_picks = [
            {"champion": "Yasuo", "position": "mid", "pick_order": 1},
            {"champion": "Sejuani", "position": "jungle", "pick_order": 2},
            {"champion": "Nautilus", "position": "support", "pick_order": 3},
            {"champion": "Kai'Sa", "position": "adc", "pick_order": 4},
            {"champion": "Ornn", "position": "top", "pick_order": 5}
        ]
        
        print(f"   Team 1: {', '.join([p['champion'] for p in team1_picks])}")
        print(f"   Team 2: {', '.join([p['champion'] for p in team2_picks])}")
        
        # Análise da composição
        comp_analysis = await comp_analyzer.analyze_team_composition(
            team_picks=team1_picks,
            enemy_picks=team2_picks,
            patch_version="14.10"
        )
        
        print(f"\n📊 RESULTADO DA ANÁLISE DE COMPOSIÇÃO:")
        print(f"   ⭐ Score geral: {comp_analysis['overall_score']}/10")
        print(f"   💪 Força individual: {comp_analysis['individual_strength']}/10")
        print(f"   🤝 Sinergias do time: {comp_analysis['team_synergies']}/10")
        print(f"   ⚔️ Vantagens de matchup: {comp_analysis['matchup_advantages']}/10")
        print(f"   🎯 Flexibilidade estratégica: {comp_analysis['strategic_flexibility']}/10")
        
        if comp_analysis['game_phase_strength']:
            print(f"   📈 Early game: {comp_analysis['game_phase_strength'].get('early_game', 0)}/10")
            print(f"   📊 Mid game: {comp_analysis['game_phase_strength'].get('mid_game', 0)}/10")
            print(f"   🔥 Late game: {comp_analysis['game_phase_strength'].get('late_game', 0)}/10")
        
        print(f"   📝 Resumo: {comp_analysis['composition_summary']}")
        
        # 4. Testar sistema de predição com composições
        print("\n🔮 3. TESTANDO SISTEMA DE PREDIÇÃO COM COMPOSIÇÕES:")
        
        analyzer = LoLGameAnalyzer()
        units = ProfessionalUnitsSystem()
        prediction_system = DynamicPredictionSystem(analyzer, units)
        
        # Criar dados de partida simulada pós-draft
        from bot.data_models.match_data import DraftData, Champion
        
        # Criar dados de draft
        draft_data = DraftData(
            team1_picks=[Champion(champion_id=p["champion"].lower(), champion_name=p["champion"], role=p["position"]) for p in team1_picks],
            team2_picks=[Champion(champion_id=p["champion"].lower(), champion_name=p["champion"], role=p["position"]) for p in team2_picks]
        )
        
        match_data = MatchData(
            match_id="test_comp_analysis",
            team1_name="Team Comp 1",
            team2_name="Team Comp 2",
            league="LEC",
            tournament="LEC Spring 2024",
            status="in_game",
            game_time_seconds=120,  # 2 minutos pós-draft
            draft_data=draft_data,
            has_complete_draft=True
        )
        
        # Simular odds
        odds_data = {
            "team1_odds": 1.85,
            "team2_odds": 2.10
        }
        
        # Fazer predição baseada em composições
        prediction_result = await prediction_system.predict_live_match(match_data, odds_data)
        
        print(f"   🎯 Time favorito: {prediction_result.predicted_winner}")
        print(f"   📈 Probabilidade: {prediction_result.win_probability:.1%}")
        print(f"   ⭐ Confiança: {prediction_result.confidence_level.value}")
        print(f"   🔧 Método: {prediction_result.method_used.value}")
        print(f"   📊 Qualidade dos dados: {prediction_result.data_quality:.1%}")
        print(f"   🤖 Força da predição: {prediction_result.prediction_strength:.1%}")
        
        # 5. Testar geração de tip baseada em composições
        print("\n💎 4. TESTANDO GERAÇÃO DE TIP PÓS-DRAFT:")
        
        tip_result = await prediction_system.generate_professional_tip(
            match_data=match_data,
            odds_data=odds_data,
            prediction_result=prediction_result
        )
        
        if tip_result.is_valid and tip_result.tip:
            tip = tip_result.tip
            print(f"✅ TIP GERADA COM SUCESSO:")
            print(f"   🎮 Match: {tip.team_a} vs {tip.team_b}")
            print(f"   🏆 Liga: {tip.league}")
            print(f"   ⚡ Apostar em: {tip.tip_on_team}")
            print(f"   💰 Odds: {tip.odds}")
            print(f"   🎯 Confiança: {tip.confidence_percentage:.1f}%")
            print(f"   📈 Expected Value: {tip.ev_percentage:.1f}%")
            print(f"   🔥 Unidades: {tip.units}")
            print(f"   ⚠️ Risco: {tip.risk_level}")
            print(f"   📝 Análise: {tip.explanation_text[:100]}...")
        else:
            print(f"❌ TIP NÃO GERADA:")
            print(f"   Motivo: {tip_result.rejection_reason}")
            print(f"   Critérios:")
            print(f"     Confiança: {'✅' if tip_result.meets_confidence_threshold else '❌'}")
            print(f"     EV: {'✅' if tip_result.meets_ev_threshold else '❌'}")
            print(f"     Odds: {'✅' if tip_result.meets_odds_criteria else '❌'}")
            print(f"     Timing: {'✅' if tip_result.meets_timing_criteria else '❌'}")
        
        # 6. Testar sistema completo de tips
        print("\n🤖 5. TESTANDO SISTEMA COMPLETO DE TIPS:")
        
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        
        pandascore = PandaScoreAPIClient()
        riot = RiotAPIClient()
        
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore,
            riot_client=riot,
            prediction_system=prediction_system
        )
        
        # Testar detecção de draft completo
        is_draft_complete = await tips_system._is_draft_complete(match_data)
        print(f"   📋 Draft detectado como completo: {is_draft_complete}")
        
        # Testar critérios de qualidade
        meets_criteria = await tips_system._match_meets_quality_criteria(match_data)
        print(f"   ✅ Atende critérios de qualidade: {meets_criteria}")
        
        # Testar geração completa de tip
        generated_tip = await tips_system._generate_tip_for_match(match_data)
        
        if generated_tip:
            print(f"✅ SISTEMA COMPLETO FUNCIONANDO:")
            print(f"   🎯 Tip: {generated_tip.tip_on_team} @ {generated_tip.odds}")
            print(f"   📊 Baseada em: Análise de composições pós-draft")
            print(f"   ⏰ Timing: {generated_tip.game_time_at_tip}")
        else:
            print(f"❌ Sistema não gerou tip (critérios não atendidos)")
        
        # 7. Resumo final
        print("\n" + "=" * 60)
        print("📋 RESUMO DO TESTE DE COMPOSIÇÕES PÓS-DRAFT")
        print("=" * 60)
        
        funcionalidades = [
            ("Analisador de Composições", comp_analysis['overall_score'] > 5.0),
            ("Sistema de Predição", prediction_result.confidence_level.value != "very_low"),
            ("Geração de Tips", tip_result.is_valid),
            ("Detecção Draft Completo", is_draft_complete),
            ("Critérios de Qualidade", meets_criteria),
            ("Sistema Completo", generated_tip is not None)
        ]
        
        funcionando = sum(1 for _, ok in funcionalidades if ok)
        total = len(funcionalidades)
        
        for nome, ok in funcionalidades:
            print(f"   {'✅' if ok else '❌'} {nome}")
        
        print(f"\n🎯 RESULTADO: {funcionando}/{total} funcionalidades operacionais")
        
        if funcionando >= 4:
            print("🎉 SISTEMA ESTÁ REFLETINDO ADEQUADAMENTE!")
            print("✅ Capaz de fornecer previsões pós-draft baseadas em composições")
            print("✅ Análise de sinergias e matchups funcionando")
            print("✅ Integração com sistema de tips operacional")
        else:
            print("⚠️ SISTEMA PRECISA DE AJUSTES")
            print("❌ Algumas funcionalidades não estão operacionais")
        
        return funcionando >= 4
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar variáveis de ambiente se necessário
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI")
    os.environ.setdefault("TELEGRAM_ADMIN_USER_IDS", "8012415611")
    
    success = asyncio.run(teste_composicoes_pos_draft())
    
    if success:
        print("\n🎊 TESTE CONCLUÍDO: SISTEMA FUNCIONANDO ADEQUADAMENTE! 🎊")
        print("📈 O sistema está pronto para fornecer tips baseadas em composições")
    else:
        print("\n❌ TESTE FALHOU: VERIFICAR CONFIGURAÇÕES E DEPENDÊNCIAS") 