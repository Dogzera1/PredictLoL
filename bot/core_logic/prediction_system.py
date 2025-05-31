from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .game_analyzer import LoLGameAnalyzer, GameAnalysis, GamePhase
from .units_system import ProfessionalUnitsSystem, TipRecommendation
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
        
        # Cache de predições
        self.predictions_cache: Dict[str, PredictionResult] = {}
        
        # Métricas de performance
        self.prediction_stats = {
            "total_predictions": 0,
            "ml_predictions": 0,
            "algorithm_predictions": 0,
            "hybrid_predictions": 0,
            "tips_generated": 0,
            "tips_rejected": 0
        }
        
        # Configurações do modelo ML (simplificado)
        self.ml_config = self._initialize_ml_config()
        
        logger.info("DynamicPredictionSystem inicializado com sucesso")

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
            
            # Executa predições baseadas no método escolhido
            ml_prediction = None
            algorithm_prediction = None
            
            if method in [PredictionMethod.MACHINE_LEARNING, PredictionMethod.HYBRID]:
                ml_prediction = await self._predict_with_ml(game_analysis, match_data)
            
            if method in [PredictionMethod.ALGORITHM_BASED, PredictionMethod.HYBRID]:
                algorithm_prediction = await self._predict_with_algorithms(game_analysis, match_data)
            
            # Combina predições se usando método híbrido
            final_prediction = self._combine_predictions(
                ml_prediction, 
                algorithm_prediction, 
                game_analysis,
                method
            )
            
            # Calcula métricas de qualidade
            prediction_strength = self._calculate_prediction_strength(final_prediction, game_analysis)
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
        Gera tip profissional baseado na predição
        
        Args:
            match_data: Dados da partida
            odds_data: Dados de odds das casas
            prediction_result: Resultado da predição (se já calculado)
            
        Returns:
            Resultado da geração de tip
        """
        try:
            logger.info(f"Gerando tip para {match_data.match_id}")
            
            # Faz predição se não fornecida
            if not prediction_result:
                prediction_result = await self.predict_live_match(match_data, odds_data)
            
            # Extrai odds das casas
            team1_odds = odds_data.get("team1_odds", 2.0)
            team2_odds = odds_data.get("team2_odds", 2.0)
            
            # Determina qual team apostar baseado na predição
            if prediction_result.predicted_winner == match_data.team1_name:
                bet_on_team = match_data.team1_name
                predicted_odds = team1_odds
                predicted_probability = prediction_result.win_probability
            else:
                bet_on_team = match_data.team2_name
                predicted_odds = team2_odds
                predicted_probability = 1.0 - prediction_result.win_probability
            
            # Calcula expected value
            ev_percentage = self._calculate_expected_value(predicted_probability, predicted_odds)
            
            # Validação inicial de critérios
            validation_result = self._validate_tip_criteria(
                confidence=prediction_result.win_probability,
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
            
            # Gera análise textual
            analysis_reasoning = self._generate_analysis_reasoning(
                prediction_result, 
                match_data, 
                ev_percentage,
                tip_recommendation
            )
            
            # Cria tip profissional
            professional_tip = ProfessionalTip(
                match_id=match_data.match_id,
                team_a=match_data.team1_name,
                team_b=match_data.team2_name,
                league=match_data.league,
                tournament=match_data.tournament,
                tip_on_team=bet_on_team,
                odds=predicted_odds,
                units=tip_recommendation.units,
                risk_level=tip_recommendation.risk_level,
                confidence_percentage=predicted_probability * 100,
                ev_percentage=ev_percentage,
                analysis_reasoning=analysis_reasoning,
                game_time_at_tip=f"{match_data.get_game_time_minutes()}min",
                game_time_seconds=match_data.game_time_seconds,
                prediction_source=prediction_result.method_used.value.upper(),
                data_quality_score=prediction_result.data_quality
            )
            
            # Validação final da tip
            is_valid, validation_msg = professional_tip.validate()
            
            if is_valid:
                self.prediction_stats["tips_generated"] += 1
                logger.info(f"Tip gerada com sucesso: {bet_on_team} @ {predicted_odds} ({tip_recommendation.units}u)")
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

    async def _predict_with_ml(self, game_analysis: GameAnalysis, match_data: MatchData) -> Dict:
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
                "has_momentum": 1.0 if game_analysis.momentum_team else 0.0
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

    async def _predict_with_algorithms(self, game_analysis: GameAnalysis, match_data: MatchData) -> Dict:
        """Predição usando algoritmos heurísticos"""
        try:
            # Algoritmo baseado nas vantagens calculadas pelo game analyzer
            overall_advantage = game_analysis.team1_advantage.overall_advantage
            
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
            
            # Calcula probabilidade final
            adjusted_advantage = overall_advantage * phase_modifier * momentum_modifier
            
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
                "phase_modifier": phase_modifier,
                "momentum_modifier": momentum_modifier,
                "algorithm_version": "heuristic_v2.0"
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
        method: PredictionMethod
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
            "has_momentum": 0.08
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
        
        # Calcula score
        score = sum(weights.get(k, 0) * v for k, v in normalized_features.items())
        
        # Aplica sigmoid para obter probabilidade
        probability = 1 / (1 + pow(2.71828, -score * 3))  # e^(-score*3)
        
        return max(0.05, min(0.95, probability))

    def _calculate_expected_value(self, true_probability: float, bookmaker_odds: float) -> float:
        """Calcula Expected Value da aposta"""
        implied_probability = 1 / bookmaker_odds
        return ((true_probability * bookmaker_odds) - 1) * 100

    def _validate_tip_criteria(
        self, 
        confidence: float, 
        ev_percentage: float, 
        odds: float,
        game_time: int,
        data_quality: float
    ) -> Dict[str, Any]:
        """Valida se tip atende critérios profissionais"""
        
        # Critérios mínimos
        meets_confidence = confidence >= 0.65  # 65% mínimo
        meets_ev = ev_percentage >= 3.0        # 3% EV mínimo
        meets_odds = 1.3 <= odds <= 3.5        # Odds entre 1.30 e 3.50
        meets_timing = game_time >= 300        # Pelo menos 5 minutos
        meets_quality = data_quality >= 0.6    # 60% qualidade mínima
        
        is_valid = all([meets_confidence, meets_ev, meets_odds, meets_timing, meets_quality])
        
        # Determina motivo de rejeição
        reason = None
        if not meets_confidence:
            reason = f"Confiança muito baixa: {confidence:.1%}"
        elif not meets_ev:
            reason = f"EV insuficiente: {ev_percentage:.1f}%"
        elif not meets_odds:
            reason = f"Odds fora do range: {odds}"
        elif not meets_timing:
            reason = f"Jogo muito cedo: {game_time//60}min"
        elif not meets_quality:
            reason = f"Qualidade dos dados baixa: {data_quality:.1%}"
        
        return {
            "is_valid": is_valid,
            "reason": reason,
            "meets_confidence": meets_confidence,
            "meets_ev": meets_ev,
            "meets_odds": meets_odds,
            "meets_timing": meets_timing,
            "meets_quality": meets_quality
        }

    def _generate_analysis_reasoning(
        self, 
        prediction: PredictionResult, 
        match_data: MatchData, 
        ev_percentage: float,
        tip_recommendation: TipRecommendation
    ) -> str:
        """Gera análise textual da tip"""
        
        game_analysis = self.game_analyzer.get_match_analysis(match_data.match_id)
        if not game_analysis:
            return "Análise baseada em predição do sistema."
        
        minutes = match_data.get_game_time_minutes()
        phase_names = {
            GamePhase.EARLY_GAME: "Early Game",
            GamePhase.MID_GAME: "Mid Game", 
            GamePhase.LATE_GAME: "Late Game"
        }
        
        reasoning = f"""🎯 **Análise Profissional ({minutes}min - {phase_names[game_analysis.current_phase]})**

📊 **Situação Atual:**
• {prediction.predicted_winner} está com {prediction.win_probability:.1%} de chance de vitória
• Vantagem geral: {game_analysis.team1_advantage.overall_advantage:+.1%}
• Confiança do modelo: {prediction.confidence_level.value.title()}

⚡ **Fatores Decisivos:**
• Ouro: {game_analysis.team1_advantage.gold_advantage:+.0f} gold
• Torres: {game_analysis.team1_advantage.tower_advantage:+d}
• Objetivos: {game_analysis.team1_advantage.objective_control:.1%} controle"""

        if game_analysis.momentum_team:
            reasoning += f"\n• Momentum: {game_analysis.momentum_team} tem vantagem recente"
        
        reasoning += f"""

💰 **Justificativa da Aposta:**
• Expected Value: +{ev_percentage:.1f}% (excelente)
• Método: {prediction.method_used.value.upper()}
• Qualidade dos dados: {prediction.data_quality:.1%}

🎲 **Gestão de Risco:**
• {tip_recommendation.units} unidades ({tip_recommendation.risk_level})
• Baseado em {tip_recommendation.confidence_percentage:.0f}% confiança
"""

        if prediction.model_agreement > 0.8:
            reasoning += "• Alto acordo entre modelos ML e algoritmos"
        
        return reasoning

    def _calculate_prediction_strength(self, prediction: Dict, game_analysis: GameAnalysis) -> float:
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

    def _get_league_tier(self, league: str) -> str:
        """Determina tier da liga"""
        return LEAGUE_TIERS.get(league.upper(), "tier_2")

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
                "game_phase", "crucial_events", "has_momentum"
            ],
            "prediction_threshold": 0.6,
            "confidence_threshold": 0.7
        }

    def get_prediction_stats(self) -> Dict:
        """Retorna estatísticas do sistema"""
        return {
            **self.prediction_stats,
            "cache_size": len(self.predictions_cache),
            "success_rate": (
                self.prediction_stats["tips_generated"] / 
                max(self.prediction_stats["total_predictions"], 1)
            ) * 100
        }

    def clear_old_predictions(self, max_age_hours: int = 24) -> None:
        """Remove predições antigas do cache"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        old_predictions = [
            match_id for match_id, prediction in self.predictions_cache.items()
            if current_time - prediction.prediction_timestamp > max_age_seconds
        ]
        
        for match_id in old_predictions:
            del self.predictions_cache[match_id]
        
        if old_predictions:
            logger.info(f"Removidas {len(old_predictions)} predições antigas do cache") 