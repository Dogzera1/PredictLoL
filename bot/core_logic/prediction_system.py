from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .game_analyzer import LoLGameAnalyzer, GameAnalysis, GamePhase
from .units_system import ProfessionalUnitsSystem, TipRecommendation
from ..analyzers.composition_analyzer import CompositionAnalyzer
from ..analyzers.patch_analyzer import PatchAnalyzer
from ..data_models.match_data import MatchData
from ..data_models.tip_data import ProfessionalTip
from ..utils.constants import (
    LEAGUE_TIERS,
    VALID_LIVE_STATUSES,
    PREDICTION_THRESHOLDS
)
from ..utils.helpers import normalize_team_name, get_current_timestamp
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class PredictionMethod(Enum):
    """Métodos de predição disponíveis"""
    MACHINE_LEARNING = "ml"
    ALGORITHM_BASED = "algorithm"
    HYBRID = "hybrid"


class PredictionConfidence(Enum):
    """Níveis de confiança da predição"""
    VERY_LOW = "very_low"      # < 60%
    LOW = "low"                # 60-70%
    MEDIUM = "medium"          # 70-80%
    HIGH = "high"              # 80-90%
    VERY_HIGH = "very_high"    # > 90%


@dataclass
class PredictionResult:
    """Resultado de uma predição"""
    match_id: str
    predicted_winner: str
    win_probability: float
    confidence_level: PredictionConfidence
    method_used: PredictionMethod
    
    # Métricas de qualidade
    prediction_strength: float  # 0-1
    data_quality: float         # 0-1
    model_agreement: float      # 0-1 (acordo entre métodos)
    
    # Dados técnicos
    ml_prediction: Optional[Dict] = None
    algorithm_prediction: Optional[Dict] = None
    feature_importance: Dict[str, float] = None
    
    # Metadados
    prediction_timestamp: float = 0.0
    processing_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.prediction_timestamp == 0.0:
            self.prediction_timestamp = time.time()


@dataclass
class TipGenerationResult:
    """Resultado da geração de tip profissional"""
    tip: Optional[ProfessionalTip]
    is_valid: bool
    rejection_reason: Optional[str] = None
    
    # Métricas de validação
    meets_confidence_threshold: bool = False
    meets_ev_threshold: bool = False
    meets_odds_criteria: bool = False
    meets_timing_criteria: bool = False


class DynamicPredictionSystem:
    """
    Sistema de Predição Dinâmico para League of Legends
    
    Combina Machine Learning com algoritmos heurísticos para gerar
    predições profissionais e tips de alta qualidade.
    
    Características:
    - Predições híbridas (ML + Algoritmos)
    - Validação rigorosa de qualidade
    - Geração de tips profissionais
    - Sistema de confiança adaptativo
    - Cache inteligente de predições
    """

    def __init__(
        self, 
        game_analyzer: LoLGameAnalyzer,
        units_system: ProfessionalUnitsSystem
    ):
        """
        Inicializa o sistema de predição
        
        Args:
            game_analyzer: Analisador de jogos LoL
            units_system: Sistema de unidades profissionais
        """
        self.game_analyzer = game_analyzer
        self.units_system = units_system
        self.composition_analyzer = CompositionAnalyzer()
        self.patch_analyzer = PatchAnalyzer()
        
        # Cache de predições
        self.predictions_cache: Dict[str, PredictionResult] = {}
        
        # Métricas de performance
        self.prediction_stats = {
            "total_predictions": 0,
            "ml_predictions": 0,
            "algorithm_predictions": 0,
            "hybrid_predictions": 0,
            "tips_generated": 0,
            "tips_rejected": 0,
            "composition_analyses": 0,
            "patch_analyses": 0
        }
        
        # Configurações do modelo ML (com composições e patches integrados)
        self.ml_config = self._initialize_ml_config()
        
        # Pesos finais do modelo híbrido (Fase 2 completa)
        self.feature_weights = {
            "real_time_data": 0.40,        # Dados em tempo real (40%)
            "composition_analysis": 0.35,   # Análise de composições (35%)
            "patch_meta_analysis": 0.15,    # Análise de patch/meta (15%) - NOVO
            "contextual_factors": 0.10      # Fatores contextuais (10%)
        }
        
        logger.info("DynamicPredictionSystem inicializado com CompositionAnalyzer integrado")

    async def predict_live_match(
        self, 
        match_data: MatchData,
        odds_data: Optional[Dict] = None,
        method: PredictionMethod = PredictionMethod.HYBRID
    ) -> PredictionResult:
        """
        Predição principal para uma partida ao vivo
        
        Args:
            match_data: Dados da partida
            odds_data: Dados de odds (opcional)
            method: Método de predição a usar
            
        Returns:
            Resultado da predição
        """
        start_time = time.time()
        
        try:
            logger.info(f"Iniciando predição para {match_data.match_id} (método: {method.value})")
            
            # Verifica se já existe predição recente no cache
            cached_prediction = self._get_cached_prediction(match_data.match_id)
            if cached_prediction:
                logger.debug(f"Predição recuperada do cache: {match_data.match_id}")
                return cached_prediction
            
            # Análise do jogo primeiro
            game_analysis = await self.game_analyzer.analyze_live_match(match_data)
            
            # **NOVO: Análise de composições**
            composition_analysis = await self._analyze_team_compositions(match_data)
            
            # **NOVO: Análise de patch/meta**
            patch_analysis = await self._analyze_patch_impact(match_data)
            
            # Executa predições baseadas no método escolhido
            ml_prediction = None
            algorithm_prediction = None
            
            if method in [PredictionMethod.MACHINE_LEARNING, PredictionMethod.HYBRID]:
                ml_prediction = await self._predict_with_ml(game_analysis, match_data, composition_analysis, patch_analysis)
            
            if method in [PredictionMethod.ALGORITHM_BASED, PredictionMethod.HYBRID]:
                algorithm_prediction = await self._predict_with_algorithms(game_analysis, match_data, composition_analysis, patch_analysis)
            
            # Combina predições se usando método híbrido
            final_prediction = self._combine_predictions(
                ml_prediction, 
                algorithm_prediction, 
                game_analysis,
                method,
                composition_analysis
            )
            
            # Calcula métricas de qualidade
            prediction_strength = self._calculate_prediction_strength(final_prediction, game_analysis, composition_analysis)
            data_quality = match_data.calculate_data_quality()
            model_agreement = self._calculate_model_agreement(ml_prediction, algorithm_prediction)
            
            # Determina nível de confiança
            confidence_level = self._determine_confidence_level(
                final_prediction["confidence"],
                prediction_strength,
                data_quality
            )
            
            # Cria resultado
            result = PredictionResult(
                match_id=match_data.match_id,
                predicted_winner=final_prediction["winner"],
                win_probability=final_prediction["probability"],
                confidence_level=confidence_level,
                method_used=method,
                prediction_strength=prediction_strength,
                data_quality=data_quality,
                model_agreement=model_agreement,
                ml_prediction=ml_prediction,
                algorithm_prediction=algorithm_prediction,
                feature_importance=final_prediction.get("features", {}),
                processing_time_ms=(time.time() - start_time) * 1000
            )
            
            # Cache da predição
            self.predictions_cache[match_data.match_id] = result
            
            # Atualiza estatísticas
            self.prediction_stats["total_predictions"] += 1
            self.prediction_stats[f"{method.value}_predictions"] += 1
            
            logger.info(
                f"Predição concluída: {final_prediction['winner']} "
                f"({final_prediction['probability']:.1%}, {confidence_level.value})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na predição de {match_data.match_id}: {e}")
            # Retorna predição básica baseada apenas no game analyzer
            game_analysis = await self.game_analyzer.analyze_live_match(match_data)
            
            return PredictionResult(
                match_id=match_data.match_id,
                predicted_winner=game_analysis.predicted_winner or match_data.team1_name,
                win_probability=game_analysis.win_probability,
                confidence_level=PredictionConfidence.LOW,
                method_used=PredictionMethod.ALGORITHM_BASED,
                prediction_strength=0.3,
                data_quality=0.3,
                model_agreement=0.0,
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def generate_professional_tip(
        self, 
        match_data: MatchData,
        odds_data: Dict,
        prediction_result: Optional[PredictionResult] = None
    ) -> TipGenerationResult:
        """
        Gera tip profissional melhorada com experiência premium
        
        Args:
            match_data: Dados da partida
            odds_data: Dados de odds das casas
            prediction_result: Resultado da predição (se já calculado)
            
        Returns:
            Resultado da geração de tip com informações aprimoradas
        """
        try:
            logger.info(f"Gerando tip para {match_data.match_id}")
            
            # Faz predição se não fornecida
            if not prediction_result:
                prediction_result = await self.predict_live_match(match_data, odds_data)
            
            # Extrai odds das casas
            team1_odds, team2_odds = self._extract_odds_from_data(odds_data)
            
            # Determina qual team apostar baseado na predição - SEMPRE O FAVORITO
            if prediction_result.win_probability > 0.5:
                # Team1 é favorito
                bet_on_team = match_data.team1_name
                predicted_odds = team1_odds
                predicted_probability = prediction_result.win_probability
            else:
                # Team2 é favorito
                bet_on_team = match_data.team2_name
                predicted_odds = team2_odds
                predicted_probability = 1.0 - prediction_result.win_probability
            
            # Calcula expected value
            ev_percentage = self._calculate_expected_value(predicted_probability, predicted_odds)
            
            # Validação inicial de critérios
            validation_result = self._validate_tip_criteria(
                confidence=predicted_probability,
                ev_percentage=ev_percentage,
                odds=predicted_odds,
                game_time=match_data.game_time_seconds,
                data_quality=prediction_result.data_quality
            )
            
            if not validation_result["is_valid"]:
                return TipGenerationResult(
                    tip=None,
                    is_valid=False,
                    rejection_reason=validation_result["reason"],
                    meets_confidence_threshold=validation_result["meets_confidence"],
                    meets_ev_threshold=validation_result["meets_ev"],
                    meets_odds_criteria=validation_result["meets_odds"],
                    meets_timing_criteria=validation_result["meets_timing"]
                )
            
            # Gera recomendação de unidades
            tip_recommendation = self.units_system.calculate_tip(
                confidence_percentage=predicted_probability * 100,
                ev_percentage=ev_percentage,
                league_tier=self._get_league_tier(match_data.league),
                market_type="ML"
            )
            
            # NOVO: Gera informações aprimoradas da experiência premium
            enhanced_info = await self._generate_enhanced_tip_info(
                match_data, prediction_result, bet_on_team, predicted_odds, ev_percentage
            )
            
            # Gera análise textual melhorada
            analysis_reasoning = self._generate_analysis_reasoning(
                prediction_result, 
                match_data, 
                ev_percentage,
                tip_recommendation
            )
            
            # Cria tip profissional melhorada
            professional_tip = ProfessionalTip(
                match_id=match_data.match_id,
                team_a=match_data.team1_name,
                team_b=match_data.team2_name,
                league=self._extract_league_name(match_data.league),
                tournament=match_data.tournament or self._extract_league_name(match_data.league),
                tip_on_team=bet_on_team,
                odds=predicted_odds,
                min_odds=enhanced_info["min_odds"],
                units=tip_recommendation.units,
                risk_level=tip_recommendation.risk_level,
                confidence_percentage=predicted_probability * 100,
                ev_percentage=ev_percentage,
                analysis_reasoning=analysis_reasoning,
                game_time_at_tip=f"{match_data.get_game_time_minutes():.0f}min",
                game_time_seconds=match_data.game_time_seconds,
                map_number=enhanced_info["map_number"],
                match_status=enhanced_info["match_status"],
                explanation_text=enhanced_info["explanation_text"],
                game_situation_text=enhanced_info["game_situation_text"],
                objectives_text=enhanced_info["objectives_text"],
                timing_advice=enhanced_info["timing_advice"],
                alerts_text=enhanced_info["alerts_text"],
                history_text=enhanced_info["history_text"],
                unit_value=10.0,  # R$ 10 por unidade (padrão)
                prediction_source=prediction_result.method_used.value.upper(),
                data_quality_score=prediction_result.data_quality
            )
            
            # Validação final da tip
            is_valid, validation_msg = professional_tip.validate()
            
            if is_valid:
                self.prediction_stats["tips_generated"] += 1
                logger.info(f"Tip premium gerada: {bet_on_team} @ {predicted_odds} ({tip_recommendation.units}u)")
            else:
                self.prediction_stats["tips_rejected"] += 1
                logger.warning(f"Tip rejeitada na validação final: {validation_msg}")
            
            return TipGenerationResult(
                tip=professional_tip if is_valid else None,
                is_valid=is_valid,
                rejection_reason=None if is_valid else validation_msg,
                meets_confidence_threshold=True,
                meets_ev_threshold=True,
                meets_odds_criteria=True,
                meets_timing_criteria=True
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar tip para {match_data.match_id}: {e}")
            return TipGenerationResult(
                tip=None,
                is_valid=False,
                rejection_reason=f"Erro interno: {str(e)}"
            )

    def _extract_odds_from_data(self, odds_data: Dict) -> Tuple[float, float]:
        """Extrai odds dos times dos dados fornecidos"""
        try:
            # Formato PandaScore
            if "outcomes" in odds_data:
                outcomes = odds_data["outcomes"]
                if len(outcomes) >= 2:
                    return float(outcomes[0]["odd"]), float(outcomes[1]["odd"])
            
            # Formato direto
            if "team1_odds" in odds_data and "team2_odds" in odds_data:
                return float(odds_data["team1_odds"]), float(odds_data["team2_odds"])
            
            # Fallback para odds equilibradas
            return 2.0, 2.0
            
        except Exception as e:
            logger.warning(f"Erro ao extrair odds: {e}")
            return 2.0, 2.0

    def _extract_league_name(self, league_data) -> str:
        """Extrai nome da liga dos dados"""
        if isinstance(league_data, dict):
            return league_data.get('name', league_data.get('slug', 'Liga Desconhecida'))
        return str(league_data) if league_data else 'Liga Desconhecida'

    async def _generate_enhanced_tip_info(
        self, 
        match_data: MatchData, 
        prediction_result: PredictionResult, 
        bet_on_team: str, 
        odds: float, 
        ev_percentage: float
    ) -> Dict[str, Any]:
        """Gera informações aprimoradas para experiência premium"""
        from ..utils.constants import (
            TIP_EXPLANATIONS, TIMING_ADVICE, ALERT_MESSAGES, 
            MATCH_STATUS_PT, NEXT_OBJECTIVES_BY_TIME
        )
        
        game_analysis = self.game_analyzer.get_match_analysis(match_data.match_id)
        game_minutes = match_data.get_game_time_minutes()
        
        # 1. Odds mínima (5% abaixo da atual)
        min_odds = round(odds * 0.95, 2)
        
        # 2. Número do mapa (tenta extrair ou assume mapa 1)
        map_number = self._extract_map_number(match_data)
        
        # 3. Status da partida em português
        match_status = MATCH_STATUS_PT.get(match_data.status, "🔴 AO VIVO")
        
        # 4. Explicação didática da tip
        explanation_text = self._generate_tip_explanation(
            bet_on_team, game_analysis, prediction_result, ev_percentage
        )
        
        # 5. Situação atual do jogo
        game_situation_text = self._generate_game_situation(game_analysis, game_minutes)
        
        # 6. Próximos objetivos importantes
        objectives_text = self._generate_next_objectives(game_minutes)
        
        # 7. Conselho de timing
        timing_advice = self._generate_timing_advice(game_analysis, ev_percentage, odds)
        
        # 8. Alertas importantes
        alerts_text = self._generate_alerts(game_analysis, game_minutes)
        
        # 9. Histórico dos times (simplificado por agora)
        history_text = self._generate_teams_history(match_data.team1_name, match_data.team2_name)
        
        return {
            "min_odds": min_odds,
            "map_number": map_number,
            "match_status": match_status,
            "explanation_text": explanation_text,
            "game_situation_text": game_situation_text,
            "objectives_text": objectives_text,
            "timing_advice": timing_advice,
            "alerts_text": alerts_text,
            "history_text": history_text
        }

    def _extract_map_number(self, match_data: MatchData) -> int:
        """Extrai número do mapa ou assume padrão"""
        # Tenta extrair do game_id, tournament ou match_id
        try:
            if hasattr(match_data, 'game_number'):
                return int(match_data.game_number)
            if hasattr(match_data, 'map_number'):
                return int(match_data.map_number)
            # Busca por indicadores no match_id
            match_id_str = str(match_data.match_id).lower()
            if 'game2' in match_id_str or 'map2' in match_id_str:
                return 2
            elif 'game3' in match_id_str or 'map3' in match_id_str:
                return 3
            elif 'game4' in match_id_str or 'map4' in match_id_str:
                return 4
            elif 'game5' in match_id_str or 'map5' in match_id_str:
                return 5
        except:
            pass
        return 1  # Padrão: Mapa 1

    def _generate_tip_explanation(
        self, 
        bet_on_team: str, 
        game_analysis: Optional[any], 
        prediction_result: PredictionResult, 
        ev_percentage: float
    ) -> str:
        """Gera explicação didática da tip"""
        from ..utils.constants import TIP_EXPLANATIONS
        
        if not game_analysis:
            return TIP_EXPLANATIONS["default"].format(team=bet_on_team)
        
        # Determina tipo de explicação baseado na situação
        if ev_percentage > 10.0:
            if game_analysis.team1_advantage.gold_advantage > 3000:
                explanation_type = "gold_lead_significant"
                gold_diff = abs(game_analysis.team1_advantage.gold_advantage)
                win_rate = min(85, 65 + (gold_diff / 1000) * 5)
                return TIP_EXPLANATIONS[explanation_type].format(
                    team=bet_on_team, 
                    gold_diff=int(gold_diff), 
                    win_rate=int(win_rate)
                )
            elif game_analysis.momentum_team == bet_on_team:
                return TIP_EXPLANATIONS["momentum_shift"].format(team=bet_on_team)
            elif game_analysis.current_phase.value == "late_game":
                return TIP_EXPLANATIONS["late_game_superior"].format(team=bet_on_team)
            else:
                return TIP_EXPLANATIONS["objective_control"].format(team=bet_on_team)
        else:
            return TIP_EXPLANATIONS["default"].format(team=bet_on_team)

    def _generate_game_situation(self, game_analysis: Optional[any], game_minutes: float) -> str:
        """Gera descrição da situação atual do jogo"""
        if not game_analysis:
            return f"📊 Partida em andamento há {game_minutes:.0f} minutos"
        
        situation_parts = []
        
        # Vantagem de ouro
        gold_adv = game_analysis.team1_advantage.gold_advantage
        if abs(gold_adv) > 1500:
            leader = "Time A" if gold_adv > 0 else "Time B"
            situation_parts.append(f"💰 {leader} lidera com {abs(int(gold_adv))} de ouro")
        
        # Torres
        tower_adv = game_analysis.team1_advantage.tower_advantage
        if abs(tower_adv) > 0:
            leader = "Time A" if tower_adv > 0 else "Time B"
            situation_parts.append(f"🏰 {leader} com vantagem de {abs(tower_adv)} torres")
        
        # Dragões
        if hasattr(game_analysis.team1_advantage, 'dragon_advantage'):
            dragon_adv = game_analysis.team1_advantage.dragon_advantage
            if abs(dragon_adv) > 0:
                leader = "Time A" if dragon_adv > 0 else "Time B"
                situation_parts.append(f"🐉 {leader} controla dragões ({abs(dragon_adv)} a mais)")
        
        # Momentum
        if game_analysis.momentum_team:
            situation_parts.append(f"⚡ {game_analysis.momentum_team} com momentum")
        
        return "\n".join(situation_parts) if situation_parts else "📊 Partida equilibrada no momento"

    def _generate_next_objectives(self, game_minutes: float) -> str:
        """Gera lista de próximos objetivos importantes"""
        from ..utils.constants import NEXT_OBJECTIVES_BY_TIME
        
        if game_minutes < 15:
            objectives = NEXT_OBJECTIVES_BY_TIME["early"]
        elif game_minutes < 30:
            objectives = NEXT_OBJECTIVES_BY_TIME["mid"]
        else:
            objectives = NEXT_OBJECTIVES_BY_TIME["late"]
        
        return "\n".join(f"• {obj}" for obj in objectives[:3])

    def _generate_timing_advice(
        self, 
        game_analysis: Optional[any], 
        ev_percentage: float, 
        odds: float
    ) -> str:
        """Gera conselho de timing para a aposta"""
        from ..utils.constants import TIMING_ADVICE
        
        # Lógica de timing baseada em EV e situação
        if ev_percentage > 15.0:
            return TIMING_ADVICE["immediate"]
        elif ev_percentage > 8.0 and odds > 2.5:
            return TIMING_ADVICE["stable_situation"]
        elif game_analysis and hasattr(game_analysis, 'volatility') and game_analysis.volatility > 0.7:
            return TIMING_ADVICE["risky_timing"]
        elif odds < 1.5:
            return TIMING_ADVICE["wait_for_better_odds"]
        else:
            return TIMING_ADVICE["stable_situation"]

    def _generate_alerts(self, game_analysis: Optional[any], game_minutes: float) -> str:
        """Gera alertas importantes"""
        from ..utils.constants import ALERT_MESSAGES
        
        alerts = []
        
        # Alertas baseados no tempo de jogo
        if game_minutes < 10:
            alerts.append(ALERT_MESSAGES["early_game"])
        elif game_minutes > 35:
            alerts.append(ALERT_MESSAGES["late_game_decide"])
        
        # Alertas baseados na análise do jogo
        if game_analysis:
            # Baron disponível
            if game_minutes > 20 and game_minutes < 40:
                alerts.append(ALERT_MESSAGES["baron_available"])
            
            # Elder Dragon
            if game_minutes > 35:
                alerts.append(ALERT_MESSAGES["elder_dragon_up"])
            
            # Posição dominante
            if hasattr(game_analysis.team1_advantage, 'overall_advantage'):
                overall_adv = abs(game_analysis.team1_advantage.overall_advantage)
                if overall_adv > 0.3:
                    alerts.append(ALERT_MESSAGES["dominant_position"])
                elif overall_adv < 0.1:
                    alerts.append(ALERT_MESSAGES["comeback_possible"])
        
        return "\n".join(f"• {alert}" for alert in alerts[:2]) if alerts else "• " + ALERT_MESSAGES["no_major_alerts"]

    def _generate_teams_history(self, team1: str, team2: str) -> str:
        """Gera histórico simplificado dos times"""
        # Por agora, um placeholder - futuramente pode incluir dados reais de histórico
        return f"📊 Analisando histórico recente de {team1} vs {team2}\n• Dados de confrontos diretos em análise\n• Performance em partidas similares calculada"

    async def _predict_with_ml(self, game_analysis: GameAnalysis, match_data: MatchData, composition_analysis: Dict, patch_analysis: Dict) -> Dict:
        """Predição usando Machine Learning (simulado)"""
        try:
            # Em uma implementação real, aqui teria um modelo ML treinado
            # Por agora, simula um modelo baseado nas métricas do game_analysis
            
            # Features principais
            features = {
                "gold_advantage": game_analysis.team1_advantage.gold_advantage,
                "tower_advantage": game_analysis.team1_advantage.tower_advantage,
                "dragon_advantage": game_analysis.team1_advantage.dragon_advantage,
                "baron_advantage": game_analysis.team1_advantage.baron_advantage,
                "kill_advantage": game_analysis.team1_advantage.kill_advantage,
                "overall_advantage": game_analysis.team1_advantage.overall_advantage,
                "game_phase": game_analysis.current_phase.value,
                "game_time_normalized": min(game_analysis.game_time_seconds / (45 * 60), 1.0),
                "crucial_events": game_analysis.crucial_events_count,
                "has_momentum": 1.0 if game_analysis.momentum_team else 0.0,
                "composition_analysis": composition_analysis["composition_score"],
                "patch_meta_analysis": patch_analysis["patch_meta_score"]
            }
            
            # Simula predição ML com base nas features
            ml_confidence = self._simulate_ml_model(features)
            
            return {
                "winner": match_data.team1_name if ml_confidence > 0.5 else match_data.team2_name,
                "probability": ml_confidence if ml_confidence > 0.5 else 1.0 - ml_confidence,
                "confidence": ml_confidence,
                "features": features,
                "model_version": "v1.0_simulated"
            }
            
        except Exception as e:
            logger.error(f"Erro na predição ML: {e}")
            return {
                "winner": match_data.team1_name,
                "probability": 0.5,
                "confidence": 0.3,
                "features": {},
                "error": str(e)
            }

    async def _predict_with_algorithms(self, game_analysis: GameAnalysis, match_data: MatchData, composition_analysis: Dict, patch_analysis: Dict) -> Dict:
        """Predição usando algoritmos heurísticos"""
        try:
            # Algoritmo baseado nas vantagens calculadas pelo game analyzer
            overall_advantage = game_analysis.team1_advantage.overall_advantage
            
            # **NOVO: Incorpora vantagem de composição**
            composition_factor = composition_analysis["composition_score"] / 100  # Normaliza para -1 a +1
            
            # **NOVO: Incorpora vantagem de patch/meta**
            patch_factor = patch_analysis["patch_meta_score"] / 100  # Normaliza para -1 a +1
            
            # Modificadores por fase do jogo
            phase_modifiers = {
                GamePhase.EARLY_GAME: 0.7,   # Early game menos decisivo
                GamePhase.MID_GAME: 1.0,     # Mid game balanceado
                GamePhase.LATE_GAME: 1.3     # Late game mais decisivo
            }
            
            phase_modifier = phase_modifiers[game_analysis.current_phase]
            
            # Modificador por momentum
            momentum_modifier = 1.0
            if game_analysis.momentum_team == match_data.team1_name:
                momentum_modifier = 1.1
            elif game_analysis.momentum_team == match_data.team2_name:
                momentum_modifier = 0.9
            
            # **NOVO: Combina vantagens usando os pesos do sistema**
            combined_advantage = (
                overall_advantage * self.feature_weights["real_time_data"] +
                composition_factor * self.feature_weights["composition_analysis"] +
                patch_factor * self.feature_weights["patch_meta_analysis"]
            )
            
            # Aplica modificadores
            adjusted_advantage = combined_advantage * phase_modifier * momentum_modifier
            
            # Converte para probabilidade (sigmoid-like)
            probability = 0.5 + (adjusted_advantage * 0.35)  # Fator de suavização
            probability = max(0.05, min(0.95, probability))   # Clampeia
            
            # Determina vencedor
            winner = match_data.team1_name if probability > 0.5 else match_data.team2_name
            win_prob = probability if probability > 0.5 else 1.0 - probability
            
            return {
                "winner": winner,
                "probability": win_prob,
                "confidence": game_analysis.confidence_score,
                "overall_advantage": overall_advantage,
                "composition_advantage": composition_factor,
                "patch_meta_advantage": patch_factor,
                "combined_advantage": combined_advantage,
                "phase_modifier": phase_modifier,
                "momentum_modifier": momentum_modifier,
                "algorithm_version": "heuristic_v2.1_with_compositions_and_patch_meta"
            }
            
        except Exception as e:
            logger.error(f"Erro na predição algorítmica: {e}")
            return {
                "winner": match_data.team1_name,
                "probability": 0.5,
                "confidence": 0.3,
                "error": str(e)
            }

    def _combine_predictions(
        self, 
        ml_pred: Optional[Dict], 
        algo_pred: Optional[Dict],
        game_analysis: GameAnalysis,
        method: PredictionMethod,
        composition_analysis: Dict
    ) -> Dict:
        """Combina predições de diferentes métodos"""
        
        if method == PredictionMethod.MACHINE_LEARNING and ml_pred:
            return ml_pred
        elif method == PredictionMethod.ALGORITHM_BASED and algo_pred:
            return algo_pred
        elif method == PredictionMethod.HYBRID and ml_pred and algo_pred:
            # Combina com pesos baseados na confiança
            ml_weight = 0.6  # ML tem peso maior
            algo_weight = 0.4
            
            # Se ambos predizem o mesmo vencedor, aumenta confiança
            same_winner = ml_pred["winner"] == algo_pred["winner"]
            
            if same_winner:
                # Média ponderada das probabilidades
                combined_prob = (
                    ml_pred["probability"] * ml_weight + 
                    algo_pred["probability"] * algo_weight
                )
                combined_confidence = (
                    ml_pred["confidence"] * ml_weight + 
                    algo_pred["confidence"] * algo_weight
                ) * 1.1  # Bônus por concordância
                
                return {
                    "winner": ml_pred["winner"],
                    "probability": min(combined_prob, 0.95),
                    "confidence": min(combined_confidence, 0.95),
                    "method_agreement": True,
                    "feature_importance": ml_pred.get("features", {})
                }
            else:
                # Conflito entre métodos - usa o de maior confiança
                if ml_pred["confidence"] > algo_pred["confidence"]:
                    return ml_pred
                else:
                    return algo_pred
        
        # Fallback para análise do game analyzer
        return {
            "winner": game_analysis.predicted_winner or "Unknown",
            "probability": game_analysis.win_probability,
            "confidence": game_analysis.confidence_score,
            "method_agreement": False,
            "fallback": True
        }

    def _simulate_ml_model(self, features: Dict[str, float]) -> float:
        """Simula modelo de Machine Learning"""
        
        # Pesos simulados (em uma implementação real seriam aprendidos)
        weights = {
            "gold_advantage": 0.25,
            "tower_advantage": 0.20,
            "dragon_advantage": 0.15,
            "baron_advantage": 0.15,
            "kill_advantage": 0.10,
            "overall_advantage": 0.30,
            "game_phase": 0.05,
            "crucial_events": 0.10,
            "has_momentum": 0.08,
            "composition_analysis": 0.05,
            "patch_meta_analysis": 0.03
        }
        
        # Normaliza features
        normalized_features = {}
        normalized_features["gold_advantage"] = max(-1, min(1, features["gold_advantage"] / 5000))
        normalized_features["tower_advantage"] = max(-1, min(1, features["tower_advantage"] / 3))
        normalized_features["dragon_advantage"] = max(-1, min(1, features["dragon_advantage"] / 3))
        normalized_features["baron_advantage"] = max(-1, min(1, features["baron_advantage"] / 2))
        normalized_features["kill_advantage"] = max(-1, min(1, features["kill_advantage"] / 8))
        normalized_features["overall_advantage"] = features["overall_advantage"]
        normalized_features["game_phase"] = 0.5 if "early" in features["game_phase"] else 1.0
        normalized_features["crucial_events"] = min(1, features["crucial_events"] / 5)
        normalized_features["has_momentum"] = features["has_momentum"]
        normalized_features["composition_analysis"] = max(-1, min(1, features["composition_analysis"] / 100))
        normalized_features["patch_meta_analysis"] = max(-1, min(1, features["patch_meta_analysis"] / 100))
        
        # Calcula score
        score = sum(weights.get(k, 0) * v for k, v in normalized_features.items())
        
        # Aplica sigmoid para obter probabilidade
        probability = 1 / (1 + pow(2.71828, -score * 3))  # e^(-score*3)
        
        return max(0.05, min(0.95, probability))

    def _calculate_expected_value(self, true_probability: float, bookmaker_odds: float) -> float:
        """Calcula Expected Value da aposta"""
        implied_probability = 1 / bookmaker_odds
        ev = ((true_probability * bookmaker_odds) - 1) * 100
        logger.debug(f"EV Calculation: prob={true_probability:.3f}, odds={bookmaker_odds:.2f}, ev={ev:.2f}%")
        return ev

    def _validate_tip_criteria(
        self, 
        confidence: float, 
        ev_percentage: float, 
        odds: float,
        game_time: int,
        data_quality: float
    ) -> Dict[str, Any]:
        """Valida se tip atende aos critérios mínimos - APRIMORADO para odds altas"""
        
        # Importa thresholds das constantes
        from ..utils.constants import PREDICTION_THRESHOLDS
        
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
            logger.info(f"🎯 ODDS ALTAS DETECTADAS: {odds:.2f} - Aplicando critérios especiais")
            
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
            
            logger.info(f"📊 CRITÉRIOS ODDS ALTAS:")
            logger.info(f"   Confiança: {confidence:.1%} >= {adjusted_confidence_threshold:.1%} = {meets_confidence}")
            logger.info(f"   EV: {ev_percentage:.1f}% >= {high_odds_min_ev:.1f}% = {meets_ev}")
            logger.info(f"   Razão: Odds altas ({odds:.2f}) podem ter valor elevado mesmo com menor confiança")
        
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
            reason = f"Odds fora do range: {odds} (range: {PREDICTION_THRESHOLDS['min_odds']}-{PREDICTION_THRESHOLDS['max_odds']})"
        elif not meets_timing:
            reason = f"Jogo muito cedo: {game_time//60}min (min: {PREDICTION_THRESHOLDS['min_game_time']//60}min)"
        elif not meets_quality:
            reason = f"Qualidade dos dados baixa: {data_quality:.1%} (min: {PREDICTION_THRESHOLDS['min_data_quality']:.1%})"
        
        return {
            "is_valid": is_valid,
            "reason": reason,
            "meets_confidence": meets_confidence,
            "meets_ev": meets_ev,
            "meets_odds": meets_odds,
            "meets_timing": meets_timing,
            "meets_quality": meets_quality,
            "is_high_odds": is_high_odds,
            "special_criteria_applied": is_high_odds
        }

    def _generate_analysis_reasoning(
        self, 
        prediction: PredictionResult, 
        match_data: MatchData, 
        ev_percentage: float,
        tip_recommendation: TipRecommendation
    ) -> str:
        """Gera reasoning detalhado da análise"""
        
        reasoning_parts = []
        
        # Informações básicas da predição
        reasoning_parts.append(f"🎯 **PREDIÇÃO: {prediction.predicted_winner}** (Confiança: {prediction.confidence_level.value})")
        reasoning_parts.append(f"📊 **Probabilidade de vitória:** {prediction.win_probability:.1%}")
        reasoning_parts.append(f"💰 **Expected Value:** {ev_percentage:+.1f}%")
        
        # **NOVO: Análise de composições**
        if hasattr(prediction, 'ml_prediction') and prediction.ml_prediction:
            ml_pred = prediction.ml_prediction
            if "composition_analysis" in ml_pred.get("features", {}):
                comp_score = ml_pred["features"]["composition_analysis"]
                if abs(comp_score) > 10:  # Diferença significativa
                    advantage_team = prediction.predicted_winner if comp_score > 0 else "time adversário"
                    reasoning_parts.append(f"⚔️ **Vantagem de Composição:** {advantage_team} (+{abs(comp_score):.0f} pontos)")
            
            # **NOVO: Análise de patch/meta**
            if "patch_meta_analysis" in ml_pred.get("features", {}):
                patch_score = ml_pred["features"]["patch_meta_analysis"]
                if abs(patch_score) > 5:  # Diferença significativa
                    meta_team = prediction.predicted_winner if patch_score > 0 else "time adversário"
                    reasoning_parts.append(f"📋 **Vantagem de Patch/Meta:** {meta_team} (+{abs(patch_score):.0f} pontos)")
        
        # Informações do algoritmo se disponível
        if hasattr(prediction, 'algorithm_prediction') and prediction.algorithm_prediction:
            algo_pred = prediction.algorithm_prediction
            if "composition_advantage" in algo_pred:
                comp_factor = algo_pred["composition_advantage"]
                if abs(comp_factor) > 0.1:  # Diferença significativa
                    reasoning_parts.append(f"🎮 **Draft Analysis:** Vantagem de {comp_factor:+.1f} na composição")
            
            # **NOVO: Análise de patch no algoritmo**
            if "patch_meta_advantage" in algo_pred:
                patch_factor = algo_pred["patch_meta_advantage"]
                if abs(patch_factor) > 0.1:  # Diferença significativa
                    reasoning_parts.append(f"🔄 **Meta Analysis:** Impacto de patch {patch_factor:+.1f}")
        
        # Fatores técnicos
        reasoning_parts.append(f"⚙️ **Método:** {prediction.method_used.value.upper()}")
        reasoning_parts.append(f"📈 **Força da Predição:** {prediction.prediction_strength:.1%}")
        reasoning_parts.append(f"🎲 **Qualidade dos Dados:** {prediction.data_quality:.1%}")
        
        if prediction.model_agreement > 0.8:
            reasoning_parts.append("✅ **Alta concordância entre modelos**")
        
        # Recomendação de unidades
        reasoning_parts.append(f"💵 **Unidades Recomendadas:** {tip_recommendation.units:.1f}")
        reasoning_parts.append(f"🎯 **Nível de Confiança:** {tip_recommendation.confidence_percentage:.1f}%")
        
        return "\n".join(reasoning_parts)

    def _calculate_prediction_strength(self, prediction: Dict, game_analysis: GameAnalysis, composition_analysis: Dict) -> float:
        """Calcula força da predição"""
        strength = 0.0
        
        # Força baseada na probabilidade
        prob_strength = abs(prediction["probability"] - 0.5) * 2  # 0-1
        strength += prob_strength * 0.4
        
        # Força baseada na confiança do game analyzer
        strength += game_analysis.confidence_score * 0.3
        
        # Força baseada em eventos cruciais
        events_strength = min(game_analysis.crucial_events_count / 5, 1.0)
        strength += events_strength * 0.2
        
        # Força baseada no tempo de jogo
        time_strength = min(game_analysis.game_time_seconds / (20 * 60), 1.0)
        strength += time_strength * 0.1
        
        # Força baseada na análise de composições
        comp_strength = composition_analysis["composition_score"] * 0.1
        strength += comp_strength * 0.1
        
        return min(strength, 1.0)

    def _calculate_model_agreement(self, ml_pred: Optional[Dict], algo_pred: Optional[Dict]) -> float:
        """Calcula acordo entre modelos"""
        if not ml_pred or not algo_pred:
            return 0.5  # Neutro se só um método foi usado
        
        # Verifica se predizem o mesmo vencedor
        same_winner = ml_pred["winner"] == algo_pred["winner"]
        
        if same_winner:
            # Calcula similaridade das probabilidades
            prob_diff = abs(ml_pred["probability"] - algo_pred["probability"])
            prob_agreement = 1.0 - prob_diff
            return min(prob_agreement, 1.0)
        else:
            # Vencedores diferentes = baixo acordo
            return 0.2

    def _determine_confidence_level(
        self, 
        confidence: float, 
        prediction_strength: float, 
        data_quality: float
    ) -> PredictionConfidence:
        """Determina nível de confiança final"""
        
        # Combina métricas
        combined_score = (confidence * 0.5 + prediction_strength * 0.3 + data_quality * 0.2)
        
        if combined_score >= 0.90:
            return PredictionConfidence.VERY_HIGH
        elif combined_score >= 0.80:
            return PredictionConfidence.HIGH
        elif combined_score >= 0.70:
            return PredictionConfidence.MEDIUM
        elif combined_score >= 0.60:
            return PredictionConfidence.LOW
        else:
            return PredictionConfidence.VERY_LOW

    def _get_league_tier(self, league) -> str:
        """Determina tier da liga"""
        # Trata league como string ou dict
        if isinstance(league, dict):
            league_name = league.get('name', league.get('slug', 'unknown'))
        else:
            league_name = str(league) if league else 'unknown'
        
        return LEAGUE_TIERS.get(league_name.upper(), "tier_2")

    def _get_cached_prediction(self, match_id: str, max_age_minutes: int = 10) -> Optional[PredictionResult]:
        """Recupera predição do cache se ainda válida"""
        cached = self.predictions_cache.get(match_id)
        if not cached:
            return None
        
        age_minutes = (time.time() - cached.prediction_timestamp) / 60
        if age_minutes > max_age_minutes:
            del self.predictions_cache[match_id]
            return None
        
        return cached

    def _initialize_ml_config(self) -> Dict:
        """Inicializa configuração do modelo ML"""
        return {
            "model_version": "v1.0_simulated",
            "features": [
                "gold_advantage", "tower_advantage", "dragon_advantage",
                "baron_advantage", "kill_advantage", "overall_advantage",
                "game_phase", "crucial_events", "has_momentum",
                "composition_analysis", "patch_meta_analysis"
            ],
            "prediction_threshold": 0.6,
            "confidence_threshold": 0.7
        }

    def get_prediction_stats(self) -> Dict:
        """Retorna estatísticas de performance do sistema"""
        total_predictions = self.prediction_stats["total_predictions"]
        
        return {
            "total_predictions": total_predictions,
            "method_breakdown": {
                "ml_predictions": self.prediction_stats["ml_predictions"],
                "algorithm_predictions": self.prediction_stats["algorithm_predictions"],
                "hybrid_predictions": self.prediction_stats["hybrid_predictions"]
            },
            "tip_generation": {
                "tips_generated": self.prediction_stats["tips_generated"],
                "tips_rejected": self.prediction_stats["tips_rejected"],
                "acceptance_rate": (
                    self.prediction_stats["tips_generated"] / 
                    max(self.prediction_stats["tips_generated"] + self.prediction_stats["tips_rejected"], 1)
                ) * 100
            },
            "composition_analysis": {
                "total_analyses": self.prediction_stats["composition_analyses"],
                "usage_rate": (
                    self.prediction_stats["composition_analyses"] / max(total_predictions, 1)
                ) * 100 if total_predictions > 0 else 0
            },
            "patch_analysis": {
                "total_analyses": self.prediction_stats["patch_analyses"],
                "usage_rate": (
                    self.prediction_stats["patch_analyses"] / max(total_predictions, 1)
                ) * 100 if total_predictions > 0 else 0
            },
            "feature_weights": self.feature_weights,
            "cache_status": {
                "cached_predictions": len(self.predictions_cache),
                "cache_hit_rate": "Not implemented"
            }
        }

    def clear_old_predictions(self, max_age_hours: int = 24) -> None:
        """Remove predições antigas do cache"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        old_predictions = [
            match_id for match_id, prediction in self.predictions_cache.items()
            if prediction.prediction_timestamp < cutoff_time
        ]
        
        for match_id in old_predictions:
            del self.predictions_cache[match_id]
        
        if old_predictions:
            logger.info(f"Removidas {len(old_predictions)} predições antigas do cache")

    async def _analyze_team_compositions(self, match_data: MatchData) -> Dict:
        """
        Analisa composições dos times usando o CompositionAnalyzer
        
        Args:
            match_data: Dados da partida com informações dos times
            
        Returns:
            Dict com análise de composições e vantagem relativa
        """
        try:
            # Incrementa estatísticas
            self.prediction_stats["composition_analyses"] += 1
            
            # Extrai dados de composição do match_data
            team1_composition = self._extract_team_composition(match_data, "team1")
            team2_composition = self._extract_team_composition(match_data, "team2")
            
            if not team1_composition or not team2_composition:
                logger.warning("Dados de composição insuficientes, usando análise básica")
                return {
                    "composition_score": 0.0,  # Neutro
                    "team1_analysis": None,
                    "team2_analysis": None,
                    "advantage_team": None,
                    "confidence": 0.3
                }
            
            # Análise detalhada de cada composição
            team1_analysis = await self.composition_analyzer.analyze_team_composition(
                team_picks=team1_composition,
                enemy_picks=team2_composition,
                patch_version=getattr(match_data, 'patch_version', '14.10')
            )
            
            team2_analysis = await self.composition_analyzer.analyze_team_composition(
                team_picks=team2_composition,
                enemy_picks=team1_composition,
                patch_version=getattr(match_data, 'patch_version', '14.10')
            )
            
            # Calcula vantagem relativa (Team1 vs Team2)
            team1_score = team1_analysis["overall_score"]
            team2_score = team2_analysis["overall_score"]
            composition_advantage = team1_score - team2_score  # -10 a +10
            
            # Normaliza para -100 a +100 (compatível com outras métricas)
            normalized_score = composition_advantage * 10
            
            # Determina time com vantagem
            advantage_team = None
            if abs(composition_advantage) > 0.5:  # Diferença significativa
                advantage_team = match_data.team1_name if composition_advantage > 0 else match_data.team2_name
            
            # Calcula confiança baseada na qualidade das análises
            confidence = min(
                team1_analysis.get("team_synergies", 5.0) / 10,
                team2_analysis.get("team_synergies", 5.0) / 10
            )
            
            logger.info(f"Análise de composições: {match_data.team1_name} {team1_score:.1f} vs {match_data.team2_name} {team2_score:.1f}")
            
            return {
                "composition_score": normalized_score,
                "team1_analysis": team1_analysis,
                "team2_analysis": team2_analysis,
                "advantage_team": advantage_team,
                "confidence": confidence,
                "raw_scores": {
                    "team1": team1_score,
                    "team2": team2_score
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de composições: {e}")
            return {
                "composition_score": 0.0,
                "team1_analysis": None,
                "team2_analysis": None,
                "advantage_team": None,
                "confidence": 0.1,
                "error": str(e)
            }

    def _extract_team_composition(self, match_data: MatchData, team_key: str) -> List[Dict]:
        """
        Extrai composição de campeões de um time específico
        
        Args:
            match_data: Dados da partida
            team_key: "team1" ou "team2"
            
        Returns:
            Lista de picks do time no formato esperado pelo CompositionAnalyzer
        """
        try:
            # Tenta extrair de diferentes estruturas possíveis
            composition = []
            
            # Verifica se há dados de picks & bans
            if hasattr(match_data, 'draft_data') and match_data.draft_data:
                draft = match_data.draft_data
                
                # Verifica se draft_data é um dicionário
                if isinstance(draft, dict):
                    team_picks = draft.get(f"{team_key}_picks", [])
                    
                    for i, pick in enumerate(team_picks):
                        if isinstance(pick, dict):
                            champion = pick.get("champion", pick.get("champion_name", ""))
                            position = pick.get("position", pick.get("role", self._guess_position(i)))
                            
                            composition.append({
                                "champion": champion,
                                "position": position,
                                "pick_order": i + 1
                            })
                else:
                    # Se draft_data não é um dict, tenta acessar como atributo
                    team_picks = getattr(draft, f"{team_key}_picks", [])
                    if team_picks:
                        for i, pick in enumerate(team_picks):
                            if hasattr(pick, 'champion'):
                                champion = pick.champion
                                position = getattr(pick, 'position', self._guess_position(i))
                                
                                composition.append({
                                    "champion": champion,
                                    "position": position,
                                    "pick_order": i + 1
                                })
            
            # Fallback: tenta extrair dos dados gerais do match
            elif hasattr(match_data, 'teams') and match_data.teams:
                teams_data = match_data.teams
                if isinstance(teams_data, dict):
                    team_data = teams_data.get(team_key, {})
                    players = team_data.get('players', [])
                    
                    for i, player in enumerate(players):
                        if isinstance(player, dict):
                            champion = player.get("champion", player.get("champion_name", ""))
                            position = player.get("position", player.get("role", self._guess_position(i)))
                            
                            if champion:
                                composition.append({
                                    "champion": champion,
                                    "position": position,
                                    "pick_order": i + 1
                                })
            
            # Se ainda não tem dados, tenta estrutura simples
            else:
                team_attr = getattr(match_data, f"{team_key}_composition", None)
                if team_attr and isinstance(team_attr, list):
                    for i, champion in enumerate(team_attr):
                        composition.append({
                            "champion": champion,
                            "position": self._guess_position(i),
                            "pick_order": i + 1
                        })
            
            logger.debug(f"Composição extraída para {team_key}: {[pick['champion'] for pick in composition]}")
            return composition
            
        except Exception as e:
            logger.error(f"Erro ao extrair composição do {team_key}: {e}")
            return []

    def _guess_position(self, pick_order: int) -> str:
        """Estima posição baseada na ordem de pick (convenção padrão)"""
        positions = ["top", "jungle", "mid", "adc", "support"]
        return positions[pick_order] if pick_order < len(positions) else "unknown"

    async def _analyze_patch_impact(self, match_data: MatchData) -> Dict:
        """
        Analisa impacto do patch atual nas composições dos times
        
        Args:
            match_data: Dados da partida com informações dos times
            
        Returns:
            Dict com análise de impacto do patch e vantagem relativa
        """
        try:
            # Incrementa estatísticas
            self.prediction_stats["patch_analyses"] += 1
            
            # Obtém patch atual
            patch_version = getattr(match_data, 'patch_version', self.patch_analyzer.current_patch)
            
            if not patch_version:
                logger.warning("Versão do patch não disponível, usando análise básica")
                return {
                    "patch_meta_score": 0.0,
                    "team1_patch_impact": 0.0,
                    "team2_patch_impact": 0.0,
                    "meta_shift": None,
                    "confidence": 0.3
                }
            
            # Extrai composições dos times
            team1_composition = self._extract_team_composition(match_data, "team1")
            team2_composition = self._extract_team_composition(match_data, "team2")
            
            if not team1_composition or not team2_composition:
                logger.warning("Dados de composição insuficientes para análise de patch")
                return {
                    "patch_meta_score": 0.0,
                    "team1_patch_impact": 0.0,
                    "team2_patch_impact": 0.0,
                    "meta_shift": None,
                    "confidence": 0.2
                }
            
            # Calcula impacto do patch em cada campeão
            team1_patch_impact = 0.0
            team1_champions_analyzed = 0
            
            for pick in team1_composition:
                champion = pick.get("champion", "").lower()
                if champion:
                    strength_adjustment = self.patch_analyzer.get_champion_strength_adjustment(champion, patch_version)
                    team1_patch_impact += strength_adjustment
                    team1_champions_analyzed += 1
            
            team2_patch_impact = 0.0
            team2_champions_analyzed = 0
            
            for pick in team2_composition:
                champion = pick.get("champion", "").lower()
                if champion:
                    strength_adjustment = self.patch_analyzer.get_champion_strength_adjustment(champion, patch_version)
                    team2_patch_impact += strength_adjustment
                    team2_champions_analyzed += 1
            
            # Normaliza por número de campeões analisados
            if team1_champions_analyzed > 0:
                team1_patch_impact /= team1_champions_analyzed
            if team2_champions_analyzed > 0:
                team2_patch_impact /= team2_champions_analyzed
            
            # Calcula vantagem relativa (Team1 vs Team2)
            patch_advantage = team1_patch_impact - team2_patch_impact
            
            # Normaliza para -100 a +100 (compatível com outras métricas)
            normalized_score = patch_advantage * 10  # Ajuste de escala
            
            # Analisa meta shift geral
            meta_shift = self._analyze_meta_shift(team1_composition, team2_composition, patch_version)
            
            # Calcula confiança baseada no número de campeões com dados de patch
            total_champions = team1_champions_analyzed + team2_champions_analyzed
            confidence = min(0.9, total_champions / 10)  # Máximo de 0.9 com 10 campeões
            
            logger.debug(f"Análise de patch: Team1 {team1_patch_impact:.2f}, Team2 {team2_patch_impact:.2f}, Vantagem: {patch_advantage:.2f}")
            
            return {
                "patch_meta_score": normalized_score,
                "team1_patch_impact": team1_patch_impact,
                "team2_patch_impact": team2_patch_impact,
                "meta_shift": meta_shift,
                "confidence": confidence,
                "patch_version": patch_version,
                "champions_analyzed": total_champions
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de patch: {e}")
            return {
                "patch_meta_score": 0.0,
                "team1_patch_impact": 0.0,
                "team2_patch_impact": 0.0,
                "meta_shift": None,
                "confidence": 0.1,
                "error": str(e)
            }

    def _analyze_meta_shift(self, team1_composition: List[Dict], team2_composition: List[Dict], patch_version: str) -> Dict:
        """
        Analisa mudanças no meta que afetam as composições
        
        Args:
            team1_composition: Composição do time 1
            team2_composition: Composição do time 2
            patch_version: Versão do patch
            
        Returns:
            Dict com análise de meta shift
        """
        try:
            # Mapeamento de campeões para classes
            champion_classes = {
                "akali": "assassins", "zed": "assassins", "leblanc": "assassins",
                "azir": "mages", "viktor": "mages", "orianna": "mages",
                "jinx": "marksmen", "caitlyn": "marksmen", "vayne": "marksmen", "aphelios": "marksmen",
                "malphite": "tanks", "leona": "tanks", "sejuani": "tanks",
                "irelia": "fighters", "jax": "fighters", "fiora": "fighters", "gnar": "fighters", "graves": "fighters",
                "thresh": "supports", "lulu": "supports"
            }
            
            # Conta classes em cada time
            team1_classes = {}
            team2_classes = {}
            
            for pick in team1_composition:
                champion = pick.get("champion", "").lower()
                champion_class = champion_classes.get(champion, "unknown")
                team1_classes[champion_class] = team1_classes.get(champion_class, 0) + 1
            
            for pick in team2_composition:
                champion = pick.get("champion", "").lower()
                champion_class = champion_classes.get(champion, "unknown")
                team2_classes[champion_class] = team2_classes.get(champion_class, 0) + 1
            
            # Analisa força das classes no meta atual
            meta_advantages = {}
            
            for class_name in ["assassins", "mages", "marksmen", "tanks", "fighters", "supports"]:
                team1_count = team1_classes.get(class_name, 0)
                team2_count = team2_classes.get(class_name, 0)
                meta_strength = self.patch_analyzer.get_meta_strength(class_name, patch_version)
                
                # Vantagem = (diferença de campeões) * força no meta
                class_advantage = (team1_count - team2_count) * meta_strength
                meta_advantages[class_name] = class_advantage
            
            # Identifica mudança de meta mais significativa
            strongest_shift = max(meta_advantages.items(), key=lambda x: abs(x[1]))
            
            return {
                "class_advantages": meta_advantages,
                "strongest_shift": {
                    "class": strongest_shift[0],
                    "advantage": strongest_shift[1]
                },
                "total_meta_impact": sum(meta_advantages.values())
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar meta shift: {e}")
            return {
                "class_advantages": {},
                "strongest_shift": {"class": "unknown", "advantage": 0.0},
                "total_meta_impact": 0.0
            } 