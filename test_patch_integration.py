#!/usr/bin/env python3
"""
Teste de Integração: PatchAnalyzer + DynamicPredictionSystem (Fase 2)

Verifica se a Fase 2 foi implementada corretamente:
- PatchAnalyzer integrado ao sistema de predição
- Peso de 15% aplicado corretamente
- Análise de patch/meta impacta nas predições
- Sistema híbrido com 4 fatores balanceados
"""

import asyncio
import sys
import os
from unittest.mock import MagicMock

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.core_logic.prediction_system import DynamicPredictionSystem, PredictionMethod
from bot.core_logic.game_analyzer import LoLGameAnalyzer
from bot.core_logic.units_system import ProfessionalUnitsSystem
from bot.data_models.match_data import MatchData


class PatchIntegrationTester:
    """Testa integração entre PatchAnalyzer e sistema de predição"""
    
    def __init__(self):
        self.prediction_system = None
    
    async def initialize_system(self):
        """Inicializa sistema de predição com PatchAnalyzer"""
        print("🔧 Inicializando sistema de predição com análise de patch/meta...")
        
        # Inicializa componentes
        game_analyzer = LoLGameAnalyzer()
        units_system = ProfessionalUnitsSystem()
        
        # Sistema de predição (agora com PatchAnalyzer integrado)
        self.prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        
        # Inicializa PatchAnalyzer
        await self.prediction_system.patch_analyzer.initialize()
        
        # Aguarda inicialização das databases
        await asyncio.sleep(1)
        
        print("✅ Sistema inicializado com sucesso!")
        return True
    
    async def test_patch_analyzer_integration(self):
        """Testa se PatchAnalyzer está integrado"""
        print("\n🧪 TESTE 1: Integração do PatchAnalyzer")
        print("-" * 50)
        
        # Verifica se PatchAnalyzer foi inicializado
        has_analyzer = hasattr(self.prediction_system, 'patch_analyzer')
        print(f"✅ PatchAnalyzer presente: {has_analyzer}")
        
        # Verifica pesos do modelo (Fase 2 completa)
        weights = self.prediction_system.feature_weights
        expected_weights = {
            "real_time_data": 0.40,
            "composition_analysis": 0.35,
            "patch_meta_analysis": 0.15,  # NOVO
            "contextual_factors": 0.10
        }
        
        weights_correct = weights == expected_weights
        print(f"✅ Pesos do modelo corretos: {weights_correct}")
        
        if not weights_correct:
            print(f"   Esperado: {expected_weights}")
            print(f"   Atual: {weights}")
        
        # Verifica se patch analyzer foi inicializado
        current_patch = self.prediction_system.patch_analyzer.current_patch
        print(f"✅ Patch atual detectado: {current_patch}")
        
        # Verifica estatísticas
        stats = self.prediction_system.get_prediction_stats()
        has_patch_stats = 'patch_analysis' in stats
        print(f"✅ Estatísticas de patch: {has_patch_stats}")
        
        return has_analyzer and weights_correct and has_patch_stats
    
    async def test_patch_analysis_method(self):
        """Testa método específico de análise de patch"""
        print("\n🧪 TESTE 2: Método _analyze_patch_impact")
        print("-" * 50)
        
        match_data = self._create_mock_match_data()
        
        try:
            # Testa método diretamente
            patch_analysis = await self.prediction_system._analyze_patch_impact(match_data)
            
            print(f"✅ Análise de patch executada com sucesso")
            print(f"✅ Score de patch/meta: {patch_analysis['patch_meta_score']:.1f}")
            print(f"✅ Patch version: {patch_analysis.get('patch_version', 'N/A')}")
            print(f"✅ Team1 impact: {patch_analysis['team1_patch_impact']:.2f}")
            print(f"✅ Team2 impact: {patch_analysis['team2_patch_impact']:.2f}")
            print(f"✅ Confiança: {patch_analysis['confidence']:.2f}")
            
            # Verifica estrutura do resultado
            required_keys = ['patch_meta_score', 'team1_patch_impact', 'team2_patch_impact', 'meta_shift', 'confidence']
            has_all_keys = all(key in patch_analysis for key in required_keys)
            
            return True, has_all_keys
            
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
            return False, False
    
    async def test_prediction_with_patch_analysis(self):
        """Testa predição incluindo análise de patch/meta"""
        print("\n🧪 TESTE 3: Predição com Análise de Patch/Meta")
        print("-" * 50)
        
        match_data = self._create_mock_match_data()
        
        try:
            # Executa predição
            prediction_result = await self.prediction_system.predict_live_match(
                match_data=match_data,
                method=PredictionMethod.HYBRID
            )
            
            print(f"✅ Predição executada: {prediction_result.predicted_winner}")
            print(f"✅ Probabilidade: {prediction_result.win_probability:.1%}")
            print(f"✅ Confiança: {prediction_result.confidence_level.value}")
            
            # Verifica se ML prediction inclui patch analysis
            has_patch_features = False
            if prediction_result.ml_prediction:
                features = prediction_result.ml_prediction.get("features", {})
                has_patch_features = "patch_meta_analysis" in features
                
                if has_patch_features:
                    patch_score = features["patch_meta_analysis"]
                    print(f"✅ Score de patch nas features ML: {patch_score:.1f}")
                else:
                    print("❌ Features de patch não encontradas no ML")
            
            # Verifica se algorithm prediction inclui patch analysis
            has_patch_algorithm = False
            if prediction_result.algorithm_prediction:
                algo_pred = prediction_result.algorithm_prediction
                has_patch_algorithm = "patch_meta_advantage" in algo_pred
                
                if has_patch_algorithm:
                    patch_advantage = algo_pred["patch_meta_advantage"]
                    print(f"✅ Vantagem de patch no algoritmo: {patch_advantage:.3f}")
                else:
                    print("❌ Dados de patch não encontrados no algoritmo")
            
            return True, has_patch_features, has_patch_algorithm
            
        except Exception as e:
            print(f"❌ Erro na predição: {e}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            return False, False, False
    
    async def test_champion_strength_adjustments(self):
        """Testa ajustes de força dos campeões baseados no patch"""
        print("\n🧪 TESTE 4: Ajustes de Força por Patch")
        print("-" * 50)
        
        # Testa campeões conhecidos do patch 14.10
        test_champions = [
            ("azir", 2.5),      # Buff no patch
            ("viktor", -1.8),   # Nerf no patch
            ("jinx", 3.2),      # Buff significativo
            ("yasuo", -2.8),    # Nerf significativo
            ("unknown_champ", 0.0)  # Campeão sem dados
        ]
        
        adjustments_working = True
        
        for champion, expected_change in test_champions:
            actual_change = self.prediction_system.patch_analyzer.get_champion_strength_adjustment(champion)
            
            if abs(actual_change - expected_change) < 0.1:
                print(f"✅ {champion}: {actual_change:+.1f} (esperado: {expected_change:+.1f})")
            else:
                print(f"❌ {champion}: {actual_change:+.1f} (esperado: {expected_change:+.1f})")
                adjustments_working = False
        
        return adjustments_working
    
    async def test_meta_strength_analysis(self):
        """Testa análise de força das classes no meta"""
        print("\n🧪 TESTE 5: Análise de Força no Meta")
        print("-" * 50)
        
        # Testa classes conhecidas do patch 14.10
        test_classes = [
            ("marksmen", 3.1),   # Buffs em ADCs
            ("mages", 0.35),     # Pequeno buff
            ("assassins", -1.4), # Nerf geral
            ("tanks", 1.1),      # Pequeno buff
            ("supports", 0.9)    # Pequeno buff
        ]
        
        meta_analysis_working = True
        
        for class_name, expected_strength in test_classes:
            actual_strength = self.prediction_system.patch_analyzer.get_meta_strength(class_name)
            
            if abs(actual_strength - expected_strength) < 0.1:
                print(f"✅ {class_name}: {actual_strength:+.1f} (esperado: {expected_strength:+.1f})")
            else:
                print(f"❌ {class_name}: {actual_strength:+.1f} (esperado: {expected_strength:+.1f})")
                meta_analysis_working = False
        
        return meta_analysis_working
    
    def _create_mock_match_data(self):
        """Cria dados de match simulados com patch version"""
        match_data = MagicMock(spec=MatchData)
        match_data.match_id = "test_patch_match_001"
        match_data.team1_name = "T1"
        match_data.team2_name = "Gen.G"
        match_data.patch_version = "14.10"  # Patch com dados de teste
        
        # Dados de composição com campeões que têm mudanças no patch
        match_data.draft_data = {
            "team1_picks": [
                {"champion": "Gnar", "position": "top", "pick_order": 1},      # Sem mudanças
                {"champion": "Graves", "position": "jungle", "pick_order": 2}, # Buff +2.0
                {"champion": "Azir", "position": "mid", "pick_order": 3},      # Buff +2.5
                {"champion": "Jinx", "position": "adc", "pick_order": 4},      # Buff +3.2
                {"champion": "Thresh", "position": "support", "pick_order": 5} # Buff +1.8
            ],
            "team2_picks": [
                {"champion": "Jayce", "position": "top", "pick_order": 1},     # Sem mudanças
                {"champion": "Kindred", "position": "jungle", "pick_order": 2}, # Sem mudanças
                {"champion": "Viktor", "position": "mid", "pick_order": 3},    # Nerf -1.8
                {"champion": "Aphelios", "position": "adc", "pick_order": 4},  # Sem mudanças
                {"champion": "Leona", "position": "support", "pick_order": 5}  # Sem mudanças
            ]
        }
        
        # Outros dados necessários
        match_data.calculate_data_quality.return_value = 0.8
        match_data.get_game_time_minutes.return_value = 15
        match_data.game_time_seconds = 900
        match_data.status = "live"
        match_data.league = "LCK"
        
        return match_data
    
    async def run_all_tests(self):
        """Executa todos os testes da Fase 2"""
        print("🚀 TESTE DE INTEGRAÇÃO: FASE 2 - ANÁLISE DE PATCH/META")
        print("=" * 70)
        
        # Inicializa sistema
        init_success = await self.initialize_system()
        if not init_success:
            print("❌ Falha na inicialização")
            return False
        
        # Teste 1: Integração básica
        integration_ok = await self.test_patch_analyzer_integration()
        
        # Teste 2: Método específico
        analysis_ok, has_structure = await self.test_patch_analysis_method()
        
        # Teste 3: Predição com patch
        prediction_ok, has_patch_ml, has_patch_algo = await self.test_prediction_with_patch_analysis()
        
        # Teste 4: Ajustes de campeões
        adjustments_ok = await self.test_champion_strength_adjustments()
        
        # Teste 5: Meta analysis
        meta_ok = await self.test_meta_strength_analysis()
        
        # Teste 6: Estatísticas
        print("\n🧪 TESTE 6: Estatísticas do Sistema")
        print("-" * 50)
        stats = self.prediction_system.get_prediction_stats()
        patch_analyses = stats['patch_analysis']['total_analyses']
        print(f"✅ Análises de patch executadas: {patch_analyses}")
        
        # Resumo final
        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES - FASE 2:")
        print(f"✅ Integração PatchAnalyzer: {'PASSOU' if integration_ok else 'FALHOU'}")
        print(f"✅ Análise específica: {'PASSOU' if analysis_ok else 'FALHOU'}")
        print(f"✅ Estrutura correta: {'PASSOU' if has_structure else 'FALHOU'}")
        print(f"✅ Predição funcional: {'PASSOU' if prediction_ok else 'FALHOU'}")
        print(f"✅ Features ML patch: {'PASSOU' if has_patch_ml else 'FALHOU'}")
        print(f"✅ Algoritmo patch: {'PASSOU' if has_patch_algo else 'FALHOU'}")
        print(f"✅ Ajustes campeões: {'PASSOU' if adjustments_ok else 'FALHOU'}")
        print(f"✅ Análise de meta: {'PASSOU' if meta_ok else 'FALHOU'}")
        
        all_passed = all([
            integration_ok, analysis_ok, has_structure, prediction_ok,
            has_patch_ml, has_patch_algo, adjustments_ok, meta_ok
        ])
        
        if all_passed:
            print("\n🎉 TODOS OS TESTES PASSARAM - FASE 2 IMPLEMENTADA COM SUCESSO!")
            print("🚀 Sistema de análise de patch/meta totalmente integrado!")
            print("📊 Modelo híbrido com 4 fatores balanceados:")
            print("   • Real-time data: 40%")
            print("   • Composition analysis: 35%")
            print("   • Patch/meta analysis: 15%")
            print("   • Contextual factors: 10%")
        else:
            print("\n⚠️  ALGUNS TESTES FALHARAM - INTEGRAÇÃO INCOMPLETA")
        
        return all_passed


async def main():
    """Função principal"""
    tester = PatchIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ FASE 2 COMPLETA - PRONTO PARA SEMANA 4!")
    else:
        print("\n❌ FASE 2 INCOMPLETA - REVISAR IMPLEMENTAÇÃO")
    
    return success


if __name__ == "__main__":
    asyncio.run(main()) 
