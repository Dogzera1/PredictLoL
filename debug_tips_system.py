#!/usr/bin/env python3
"""
Script de Diagnóstico - Sistema de Tips
Verifica por que o sistema não está gerando tips
"""

import asyncio
import os
import sys
from typing import Dict, Any, List

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurações de ambiente
os.environ["PANDASCORE_API_KEY"] = "90jCQbmni5dVyZnvr6iF9XesBRVSb3rG1L47T5sjR1_4_t8_JqQ"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"
os.environ["LOG_LEVEL"] = "DEBUG"

from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.core_logic.units_system import ProfessionalUnitsSystem
from bot.core_logic.game_analyzer import LoLGameAnalyzer
from bot.core_logic.prediction_system import DynamicPredictionSystem
from bot.systems.tips_system import ProfessionalTipsSystem

class TipsSystemDebugger:
    """Ferramenta de diagnóstico do sistema de tips"""
    
    def __init__(self):
        self.pandascore_client = None
        self.riot_client = None
        self.units_system = None
        self.game_analyzer = None
        self.prediction_system = None
        self.tips_system = None
    
    async def initialize_systems(self):
        """Inicializa todos os sistemas"""
        print("🔧 Inicializando sistemas...")
        
        # Clientes de API
        self.pandascore_client = PandaScoreAPIClient()
        self.riot_client = RiotAPIClient()
        
        # Core systems
        self.units_system = ProfessionalUnitsSystem()
        self.game_analyzer = LoLGameAnalyzer()
        self.prediction_system = DynamicPredictionSystem(
            self.game_analyzer,
            self.units_system
        )
        
        # Sistema de tips
        self.tips_system = ProfessionalTipsSystem(
            self.pandascore_client,
            self.riot_client,
            self.prediction_system
        )
        
        print("✅ Sistemas inicializados")

    async def diagnose_api_connectivity(self):
        """Diagnóstica conectividade das APIs"""
        print("\n📡 Testando conectividade das APIs...")
        
        # Testa PandaScore
        try:
            live_pandascore = await self.pandascore_client.get_lol_live_matches()
            print(f"✅ PandaScore: {len(live_pandascore)} partidas encontradas")
            
            if live_pandascore:
                match = live_pandascore[0]
                print(f"   Exemplo: {match.get('name', 'Sem nome')} - Status: {match.get('status', 'N/A')}")
        except Exception as e:
            print(f"❌ PandaScore: Erro - {e}")
        
        # Testa Riot API
        try:
            live_riot = await self.riot_client.get_live_matches()
            print(f"✅ Riot API: {len(live_riot)} eventos encontrados")
            
            if live_riot:
                event = live_riot[0]
                print(f"   Exemplo: {event.get('id', 'mock_1')} - Tipo: {event.get('type', 'N/A')}")
        except Exception as e:
            print(f"❌ Riot API: Erro - {e}")

    async def diagnose_match_processing(self):
        """Diagnóstica processamento de partidas"""
        print("\n🔍 Testando processamento de partidas...")
        
        try:
            # Busca partidas
            live_matches = await self.tips_system._get_live_matches()
            print(f"📊 Total de partidas encontradas: {len(live_matches)}")
            
            if not live_matches:
                print("⚠️  Nenhuma partida encontrada - isso pode explicar a falta de tips")
                return
            
            # Analisa primeira partida
            match = live_matches[0]
            print(f"\n🎮 Analisando partida: {match.team1_name} vs {match.team2_name}")
            print(f"   Liga: {match.league}")
            print(f"   Status: {match.status}")
            print(f"   Game Time: {match.get_game_time_minutes():.1f} min")
            
            # Verifica critérios de qualidade
            suitable_matches = self.tips_system._filter_suitable_matches(live_matches)
            print(f"📋 Partidas adequadas após filtros: {len(suitable_matches)}")
            
            if not suitable_matches:
                print("⚠️  Nenhuma partida passou pelos filtros de qualidade")
                await self._analyze_filter_failures(live_matches)
                return
            
            # Tenta gerar tip
            await self._test_tip_generation(suitable_matches[0])
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            import traceback
            traceback.print_exc()

    async def _analyze_filter_failures(self, matches: List):
        """Analisa por que as partidas falharam nos filtros"""
        print("\n🔍 Analisando falhas nos filtros...")
        
        for i, match in enumerate(matches[:3]):  # Analisa até 3 partidas
            print(f"\n📊 Partida {i+1}: {match.team1_name} vs {match.team2_name}")
            
            # Verifica cada critério
            meets_criteria = self.tips_system._match_meets_quality_criteria(match)
            print(f"   Passou nos critérios: {meets_criteria}")
            
            # Detalhes dos critérios
            time_ok = match.get_game_time_minutes() >= 5
            print(f"   ⏰ Tempo de jogo: {match.get_game_time_minutes():.1f}min (≥5min: {time_ok})")
            
            status_ok = match.status in ["live", "inProgress", "in_progress"]
            print(f"   🔴 Status: {match.status} (válido: {status_ok})")
            
            league_ok = match.league and len(match.league) > 0
            print(f"   🏆 Liga: '{match.league}' (válida: {league_ok})")

    async def _test_tip_generation(self, match):
        """Testa geração de tip para uma partida específica"""
        print(f"\n🎯 Testando geração de tip para: {match.team1_name} vs {match.team2_name}")
        
        try:
            # Verifica rate limiting
            can_generate = self.tips_system._can_generate_tip()
            print(f"   ⚡ Pode gerar tip (rate limit): {can_generate}")
            
            if not can_generate:
                print(f"   ⚠️  Rate limit atingido: {len(self.tips_system.last_tip_times)} tips na última hora")
                return
            
            # Busca odds para a partida
            print("   📊 Buscando odds...")
            odds_data = await self._get_odds_for_match(match)
            
            if not odds_data:
                print("   ⚠️  Nenhuma odd encontrada para esta partida")
                return
            
            print(f"   💰 Odds encontradas: {odds_data}")
            
            # Tenta gerar tip
            print("   🤖 Gerando predição...")
            tip = await self.tips_system._generate_tip_for_match(match)
            
            if tip:
                print(f"   ✅ TIP GERADA!")
                print(f"      Time: {tip.tip_on_team}")
                print(f"      Odds: {tip.odds}")
                print(f"      Unidades: {tip.units}")
                print(f"      Confiança: {tip.confidence_percentage:.1f}%")
                print(f"      EV: {tip.ev_percentage:.2f}%")
            else:
                print("   ❌ Tip não foi gerada")
                await self._analyze_tip_failure(match, odds_data)
                
        except Exception as e:
            print(f"   ❌ Erro na geração: {e}")
            import traceback
            traceback.print_exc()

    async def _get_odds_for_match(self, match) -> Dict:
        """Busca odds para uma partida usando o sistema completo"""
        try:
            # 1. Busca odds reais do PandaScore por ID
            odds = await self.pandascore_client.get_match_odds(match.match_id)
            if odds:
                print(f"   ✅ Odds reais encontradas por ID no PandaScore")
                return odds
                
            # 2. Busca odds reais por nomes dos times
            odds = await self.pandascore_client.find_match_odds_by_teams(
                match.team1_name, 
                match.team2_name
            )
            if odds:
                print(f"   ✅ Odds reais encontradas por nomes no PandaScore")
                return odds
            
            # 3. Usa sistema de odds estimadas do TipsSystem
            print(f"   📊 Gerando odds estimadas...")
            estimated_odds = self.tips_system._generate_estimated_odds(match)
            
            if estimated_odds:
                print(f"   ✅ Odds estimadas geradas com sucesso")
                # Mostra as odds geradas
                for outcome in estimated_odds.get("outcomes", []):
                    print(f"      {outcome.get('name', 'Team')}: {outcome.get('odd', 0):.2f}")
                return estimated_odds
            
            print(f"   ❌ Falha ao gerar odds estimadas")
            return None
            
        except Exception as e:
            print(f"   ⚠️  Erro ao buscar odds: {e}")
            return None

    async def _analyze_tip_failure(self, match, odds_data):
        """Analisa por que a tip não foi gerada"""
        print("   🔍 Analisando falha na geração...")
        
        try:
            # Gera análise do jogo
            game_analysis = await self.game_analyzer.analyze_live_match(match)
            print(f"      Análise do jogo: {game_analysis is not None}")
            
            if game_analysis:
                print(f"      Vantagem time 1: {game_analysis.team1_advantage.overall_advantage:.1%}")
                print(f"      Fase do jogo: {game_analysis.current_phase}")
                print(f"      Confiança: {game_analysis.confidence_score:.1%}")
            
            # Testa predição
            prediction = await self.prediction_system.predict_live_match(match, odds_data)
            print(f"      Predição gerada: {prediction is not None}")
            
            if prediction:
                print(f"      Vencedor previsto: {prediction.predicted_winner}")
                print(f"      Probabilidade: {prediction.win_probability:.1%}")
                print(f"      Confiança: {prediction.confidence_level.value}")
            
            # Testa geração de tip
            if prediction:
                tip_result = await self.prediction_system.generate_professional_tip(
                    match, odds_data, prediction
                )
                print(f"      Tip válida: {tip_result.is_valid}")
                if not tip_result.is_valid:
                    print(f"      Motivo rejeição: {tip_result.rejection_reason}")
            
        except Exception as e:
            print(f"      Erro na análise: {e}")

    async def run_full_diagnosis(self):
        """Executa diagnóstico completo"""
        print("🚀 Iniciando Diagnóstico Completo do Sistema de Tips")
        print("=" * 60)
        
        await self.initialize_systems()
        await self.diagnose_api_connectivity()
        await self.diagnose_match_processing()
        
        print("\n" + "=" * 60)
        print("📋 Diagnóstico concluído!")

async def main():
    """Função principal"""
    debugger = TipsSystemDebugger()
    await debugger.run_full_diagnosis()

if __name__ == "__main__":
    asyncio.run(main()) 
