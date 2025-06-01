#!/usr/bin/env python3
"""
Teste de Integração: CompositionAnalyzer + DynamicPredictionSystem

Verifica se a Semana 3 foi implementada corretamente:
- CompositionAnalyzer integrado ao sistema de predição
- Peso de 35% aplicado corretamente
- Análise de composições impacta nas predições
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


class CompositionIntegrationTester:
    """Testa integração entre CompositionAnalyzer e sistema de predição"""
    
    def __init__(self):
        self.prediction_system = None
    
    async def initialize_system(self):
        """Inicializa sistema de predição com CompositionAnalyzer"""
        print("🔧 Inicializando sistema de predição com análise de composições...")
        
        # Inicializa componentes
        game_analyzer = LoLGameAnalyzer()
        units_system = ProfessionalUnitsSystem()
        
        # Sistema de predição (agora com CompositionAnalyzer integrado)
        self.prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        
        # Aguarda inicialização das databases
        await asyncio.sleep(2)
        
        print("✅ Sistema inicializado com sucesso!")
        return True
    
    async def test_composition_integration(self):
        """Testa se análise de composições está integrada"""
        print("\n🧪 TESTE 1: Integração do CompositionAnalyzer")
        print("-" * 50)
        
        # Verifica se CompositionAnalyzer foi inicializado
        has_analyzer = hasattr(self.prediction_system, 'composition_analyzer')
        print(f"✅ CompositionAnalyzer presente: {has_analyzer}")
        
        # Verifica pesos do modelo
        weights = self.prediction_system.feature_weights
        comp_weight = weights.get('composition_analysis', 0)
        print(f"✅ Peso de composições: {comp_weight:.0%} (target: 35%)")
        
        # Verifica estatísticas
        stats = self.prediction_system.get_prediction_stats()
        has_comp_stats = 'composition_analysis' in stats
        print(f"✅ Estatísticas de composição: {has_comp_stats}")
        
        return has_analyzer and comp_weight == 0.35 and has_comp_stats
    
    async def test_prediction_with_compositions(self):
        """Testa predição incluindo análise de composições"""
        print("\n🧪 TESTE 2: Predição com Análise de Composições")
        print("-" * 50)
        
        # Cria dados de match simulados com composições
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
            
            # Debug: Verifica se ML prediction existe
            print(f"🔍 ML Prediction existe: {prediction_result.ml_prediction is not None}")
            if prediction_result.ml_prediction:
                features = prediction_result.ml_prediction.get("features", {})
                print(f"🔍 Features ML: {list(features.keys())}")
                
                # Verifica se features incluem análise de composições
                has_comp_features = "composition_analysis" in features
                if has_comp_features:
                    comp_score = features["composition_analysis"]
                    print(f"✅ Score de composição nas features: {comp_score:.1f}")
                else:
                    print("❌ Features de composição não encontradas")
            else:
                print("❌ ML Prediction não disponível")
                has_comp_features = False
            
            return True, has_comp_features
            
        except Exception as e:
            print(f"❌ Erro na predição: {e}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            return False, False
    
    async def test_composition_analysis_method(self):
        """Testa método específico de análise de composições"""
        print("\n🧪 TESTE 3: Método _analyze_team_compositions")
        print("-" * 50)
        
        match_data = self._create_mock_match_data()
        
        try:
            # Testa método diretamente
            composition_analysis = await self.prediction_system._analyze_team_compositions(match_data)
            
            print(f"✅ Análise executada com sucesso")
            print(f"✅ Score de composição: {composition_analysis['composition_score']:.1f}")
            print(f"✅ Time com vantagem: {composition_analysis['advantage_team']}")
            print(f"✅ Confiança: {composition_analysis['confidence']:.2f}")
            
            # Verifica estrutura do resultado
            required_keys = ['composition_score', 'team1_analysis', 'team2_analysis', 'advantage_team', 'confidence']
            has_all_keys = all(key in composition_analysis for key in required_keys)
            
            return True, has_all_keys
            
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
            return False, False
    
    def _create_mock_match_data(self):
        """Cria dados de match simulados para teste"""
        match_data = MagicMock(spec=MatchData)
        match_data.match_id = "test_match_001"
        match_data.team1_name = "T1"
        match_data.team2_name = "Gen.G"
        match_data.patch_version = "14.10"
        
        # Dados de composição simulados
        match_data.draft_data = {
            "team1_picks": [
                {"champion": "Gnar", "position": "top", "pick_order": 1},
                {"champion": "Graves", "position": "jungle", "pick_order": 2},
                {"champion": "Azir", "position": "mid", "pick_order": 3},
                {"champion": "Jinx", "position": "adc", "pick_order": 4},
                {"champion": "Thresh", "position": "support", "pick_order": 5}
            ],
            "team2_picks": [
                {"champion": "Jayce", "position": "top", "pick_order": 1},
                {"champion": "Kindred", "position": "jungle", "pick_order": 2},
                {"champion": "Viktor", "position": "mid", "pick_order": 3},
                {"champion": "Aphelios", "position": "adc", "pick_order": 4},
                {"champion": "Leona", "position": "support", "pick_order": 5}
            ]
        }
        
        # Dados de evento simulados mais robustos
        match_data.events = [
            {"type": "champion_kill", "timestamp": 5.0, "data": {"team": "team1"}},
            {"type": "tower_destroyed", "timestamp": 8.0, "data": {"team": "team1"}},
            {"type": "dragon_kill", "timestamp": 12.0, "data": {"team": "team2"}}
        ]
        
        # Dados de frame do jogo
        match_data.frames = [
            {
                "timestamp": 0,
                "participant_frames": {str(i): {"totalGold": 500} for i in range(1, 11)}
            },
            {
                "timestamp": 300,  # 5 minutos
                "participant_frames": {str(i): {"totalGold": 1500 + (100 if i <= 5 else 0)} for i in range(1, 11)}
            }
        ]
        
        # Mock outros métodos necessários de forma mais robusta
        match_data.calculate_data_quality.return_value = 0.8
        match_data.get_game_time_minutes.return_value = 15
        match_data.game_time_seconds = 900  # 15 minutos
        match_data.status = "live"
        match_data.league = "LCK"
        
        # Dados de participantes
        match_data.participants = [
            {"participantId": i, "teamId": 100 if i <= 5 else 200, "championName": f"Champion{i}"}
            for i in range(1, 11)
        ]
        
        # Dados de times
        match_data.teams = [
            {"teamId": 100, "win": None, "bans": []},
            {"teamId": 200, "win": None, "bans": []}
        ]
        
        return match_data
    
    async def run_all_tests(self):
        """Executa todos os testes de integração"""
        print("🚀 TESTE DE INTEGRAÇÃO: SEMANA 3 - ANÁLISE DE COMPOSIÇÕES")
        print("=" * 70)
        
        # Inicializa sistema
        init_success = await self.initialize_system()
        if not init_success:
            print("❌ Falha na inicialização")
            return False
        
        # Teste 1: Integração básica
        integration_ok = await self.test_composition_integration()
        
        # Teste 2: Predição com composições
        prediction_ok, has_comp_features = await self.test_prediction_with_compositions()
        
        # Teste 3: Método específico
        analysis_ok, has_structure = await self.test_composition_analysis_method()
        
        # Teste 4: Estatísticas
        print("\n🧪 TESTE 4: Estatísticas do Sistema")
        print("-" * 50)
        stats = self.prediction_system.get_prediction_stats()
        comp_analyses = stats['composition_analysis']['total_analyses']
        print(f"✅ Análises executadas: {comp_analyses}")
        
        # Resumo final
        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES:")
        print(f"✅ Integração básica: {'PASSOU' if integration_ok else 'FALHOU'}")
        print(f"✅ Predição funcional: {'PASSOU' if prediction_ok else 'FALHOU'}")
        print(f"✅ Features de composição: {'PASSOU' if has_comp_features else 'FALHOU'}")
        print(f"✅ Análise específica: {'PASSOU' if analysis_ok else 'FALHOU'}")
        print(f"✅ Estrutura correta: {'PASSOU' if has_structure else 'FALHOU'}")
        
        all_passed = all([integration_ok, prediction_ok, has_comp_features, analysis_ok, has_structure])
        
        if all_passed:
            print("\n🎉 TODOS OS TESTES PASSARAM - SEMANA 3 IMPLEMENTADA COM SUCESSO!")
            print("🚀 Sistema de análise de composições totalmente integrado!")
        else:
            print("\n⚠️  ALGUNS TESTES FALHARAM - INTEGRAÇÃO INCOMPLETA")
        
        return all_passed


async def main():
    """Função principal"""
    tester = CompositionIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ INTEGRAÇÃO COMPLETA - PRONTO PARA PRODUÇÃO!")
    else:
        print("\n❌ INTEGRAÇÃO INCOMPLETA - REVISAR IMPLEMENTAÇÃO")
    
    return success


if __name__ == "__main__":
    asyncio.run(main()) 