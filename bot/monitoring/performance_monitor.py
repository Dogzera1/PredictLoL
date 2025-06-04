"""
Sistema de Monitoramento de Performance - Semana 4
Monitora métricas em tempo real do Bot LoL V3 Ultra Avançado

Funcionalidades:
- Tracking de ROI e win rate em tempo real
- Monitoramento de performance das predições
- Análise de composições e patches
- Alertas automáticos
- Métricas para dashboard
"""

from __future__ import annotations

import time
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from ..utils.logger_config import get_logger
from ..utils.helpers import get_current_timestamp

logger = get_logger(__name__)


class AlertLevel(Enum):
    """Níveis de alerta do sistema"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PredictionMetrics:
    """Métricas de uma predição individual"""
    prediction_id: str
    match_id: str
    timestamp: float
    predicted_winner: str
    actual_winner: Optional[str] = None
    win_probability: float = 0.0
    confidence_level: str = "medium"
    method_used: str = "hybrid"
    
    # Dados financeiros
    odds_used: float = 0.0
    stake_amount: float = 0.0
    potential_return: float = 0.0
    actual_return: float = 0.0
    
    # Análises específicas
    composition_score: float = 0.0
    patch_score: float = 0.0
    real_time_score: float = 0.0
    
    # Status
    is_resolved: bool = False
    processing_time_ms: float = 0.0
    
    def calculate_profit_loss(self) -> float:
        """Calcula lucro/prejuízo da predição"""
        if not self.is_resolved:
            return 0.0
        return self.actual_return - self.stake_amount


@dataclass
class SystemMetrics:
    """Métricas gerais do sistema"""
    timestamp: float
    
    # Performance geral
    total_predictions: int = 0
    correct_predictions: int = 0
    win_rate_percentage: float = 0.0
    
    # Performance financeira
    total_staked: float = 0.0
    total_returned: float = 0.0
    net_profit: float = 0.0
    roi_percentage: float = 0.0
    
    # Performance por método
    ml_predictions: int = 0
    ml_correct: int = 0
    algorithm_predictions: int = 0
    algorithm_correct: int = 0
    hybrid_predictions: int = 0
    hybrid_correct: int = 0
    
    # Performance por análise
    composition_analyses: int = 0
    patch_analyses: int = 0
    
    # Tempos de processamento
    avg_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    
    # Sistema
    uptime_hours: float = 0.0
    alerts_generated: int = 0


@dataclass
class Alert:
    """Alerta do sistema"""
    alert_id: str
    timestamp: float
    level: AlertLevel
    category: str
    message: str
    details: Dict[str, Any]
    is_resolved: bool = False


class PerformanceMonitor:
    """
    Monitor de Performance do Bot LoL V3 Ultra Avançado
    
    Funcionalidades:
    - Tracking de todas as predições e resultados
    - Cálculo de ROI e win rate em tempo real
    - Monitoramento de performance por método
    - Sistema de alertas automáticos
    - Métricas para dashboard
    """

    def __init__(self):
        """Inicializa o monitor de performance"""
        self.start_time = time.time()
        
        # Storage de dados
        self.predictions: Dict[str, PredictionMetrics] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        
        # Configurações de alertas
        self.alert_thresholds = {
            "min_win_rate": 70.0,      # Win rate mínima: 70%
            "min_roi": 15.0,           # ROI mínimo: 15%
            "max_processing_time": 5000,  # Tempo máximo: 5s
            "min_predictions_day": 10,  # Predições mínimas por dia
            "max_consecutive_losses": 5  # Perdas consecutivas máximas
        }
        
        # Contadores de performance
        self.consecutive_losses = 0
        self.last_metrics_calculation = time.time()
        
        # Task de monitoramento contínuo
        self.monitoring_task = None
        
        logger.info("PerformanceMonitor inicializado para Semana 4")

    async def start_monitoring(self, interval_seconds: int = 60):
        """Inicia monitoramento contínuo"""
        try:
            logger.info(f"Iniciando monitoramento contínuo (intervalo: {interval_seconds}s)")
            
            self.monitoring_task = asyncio.create_task(
                self._continuous_monitoring(interval_seconds)
            )
            
            # Carrega dados históricos se existirem
            await self._load_historical_data()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar monitoramento: {e}")
            return False

    async def stop_monitoring(self):
        """Para monitoramento contínuo"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            logger.info("Monitoramento contínuo parado")

    async def track_prediction(
        self, 
        prediction_result: Any,
        odds_data: Dict,
        stake_amount: float = 10.0
    ) -> str:
        """
        Registra uma nova predição para tracking
        
        Args:
            prediction_result: Resultado da predição do sistema
            odds_data: Dados de odds utilizadas
            stake_amount: Valor apostado (unidades)
            
        Returns:
            ID único da predição
        """
        try:
            prediction_id = f"pred_{int(time.time() * 1000)}"
            
            # Extrai odds utilizadas
            odds_used = self._extract_odds_for_winner(
                prediction_result.predicted_winner,
                odds_data
            )
            
            # Calcula retorno potencial
            potential_return = stake_amount * odds_used if odds_used > 0 else 0.0
            
            # Extrai scores das análises
            composition_score = 0.0
            patch_score = 0.0
            real_time_score = 0.0
            
            if hasattr(prediction_result, 'ml_prediction') and prediction_result.ml_prediction:
                features = prediction_result.ml_prediction.get('features', {})
                composition_score = features.get('composition_analysis', 0.0)
                patch_score = features.get('patch_meta_analysis', 0.0)
                real_time_score = features.get('overall_advantage', 0.0)
            
            # Cria métricas da predição
            metrics = PredictionMetrics(
                prediction_id=prediction_id,
                match_id=prediction_result.match_id,
                timestamp=time.time(),
                predicted_winner=prediction_result.predicted_winner,
                win_probability=prediction_result.win_probability,
                confidence_level=prediction_result.confidence_level.value,
                method_used=prediction_result.method_used.value,
                odds_used=odds_used,
                stake_amount=stake_amount,
                potential_return=potential_return,
                composition_score=composition_score,
                patch_score=patch_score,
                real_time_score=real_time_score,
                processing_time_ms=prediction_result.processing_time_ms
            )
            
            # Armazena predição
            self.predictions[prediction_id] = metrics
            
            logger.info(f"Predição trackada: {prediction_id} - {prediction_result.predicted_winner} @ {odds_used}")
            
            # Verifica alertas imediatos
            await self._check_prediction_alerts(metrics)
            
            return prediction_id
            
        except Exception as e:
            logger.error(f"Erro ao trackear predição: {e}")
            return ""

    async def resolve_prediction(
        self, 
        prediction_id: str, 
        actual_winner: str,
        match_result_data: Optional[Dict] = None
    ) -> bool:
        """
        Resolve uma predição com o resultado real
        
        Args:
            prediction_id: ID da predição
            actual_winner: Vencedor real da partida
            match_result_data: Dados adicionais do resultado
            
        Returns:
            True se resolvido com sucesso
        """
        try:
            if prediction_id not in self.predictions:
                logger.warning(f"Predição {prediction_id} não encontrada")
                return False
            
            prediction = self.predictions[prediction_id]
            
            # Atualiza dados da predição
            prediction.actual_winner = actual_winner
            prediction.is_resolved = True
            
            # Calcula retorno real
            is_correct = prediction.predicted_winner.lower() == actual_winner.lower()
            if is_correct:
                prediction.actual_return = prediction.potential_return
                self.consecutive_losses = 0
            else:
                prediction.actual_return = 0.0
                self.consecutive_losses += 1
            
            logger.info(
                f"Predição resolvida: {prediction_id} - {'✅ CORRECT' if is_correct else '❌ WRONG'} "
                f"(P&L: {prediction.calculate_profit_loss():+.2f})"
            )
            
            # Atualiza métricas do sistema
            await self._update_system_metrics()
            
            # Verifica alertas pós-resolução
            await self._check_resolution_alerts(prediction, is_correct)
            
            # Salva dados
            await self._save_performance_data()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao resolver predição {prediction_id}: {e}")
            return False

    async def get_current_metrics(self) -> SystemMetrics:
        """Retorna métricas atuais do sistema"""
        try:
            await self._update_system_metrics()
            
            if self.system_metrics:
                return self.system_metrics[-1]
            else:
                # Retorna métricas vazias se não há dados
                return SystemMetrics(timestamp=time.time())
                
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {e}")
            return SystemMetrics(timestamp=time.time())

    async def get_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Gera relatório de performance detalhado
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Relatório completo de performance
        """
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            recent_predictions = [
                pred for pred in self.predictions.values()
                if pred.timestamp > cutoff_time and pred.is_resolved
            ]
            
            if not recent_predictions:
                return {
                    "period_days": days,
                    "total_predictions": 0,
                    "message": "Nenhuma predição resolvida no período"
                }
            
            # Métricas básicas
            total_predictions = len(recent_predictions)
            correct_predictions = sum(1 for p in recent_predictions if p.predicted_winner == p.actual_winner)
            win_rate = (correct_predictions / total_predictions) * 100
            
            # Métricas financeiras
            total_staked = sum(p.stake_amount for p in recent_predictions)
            total_returned = sum(p.actual_return for p in recent_predictions)
            net_profit = total_returned - total_staked
            roi = (net_profit / total_staked) * 100 if total_staked > 0 else 0
            
            # Performance por método
            method_stats = {}
            for method in ["ml", "algorithm", "hybrid"]:
                method_preds = [p for p in recent_predictions if p.method_used == method]
                if method_preds:
                    method_correct = sum(1 for p in method_preds if p.predicted_winner == p.actual_winner)
                    method_stats[method] = {
                        "predictions": len(method_preds),
                        "correct": method_correct,
                        "win_rate": (method_correct / len(method_preds)) * 100,
                        "profit": sum(p.calculate_profit_loss() for p in method_preds)
                    }
            
            # Performance por confiança
            confidence_stats = {}
            for conf_level in ["very_low", "low", "medium", "high", "very_high"]:
                conf_preds = [p for p in recent_predictions if p.confidence_level == conf_level]
                if conf_preds:
                    conf_correct = sum(1 for p in conf_preds if p.predicted_winner == p.actual_winner)
                    confidence_stats[conf_level] = {
                        "predictions": len(conf_preds),
                        "correct": conf_correct,
                        "win_rate": (conf_correct / len(conf_preds)) * 100,
                        "avg_odds": sum(p.odds_used for p in conf_preds) / len(conf_preds)
                    }
            
            # Análise temporal
            daily_stats = self._calculate_daily_stats(recent_predictions, days)
            
            # Best/Worst predictions
            best_prediction = max(recent_predictions, key=lambda p: p.calculate_profit_loss())
            worst_prediction = min(recent_predictions, key=lambda p: p.calculate_profit_loss())
            
            return {
                "period_days": days,
                "period_start": datetime.fromtimestamp(cutoff_time).isoformat(),
                "period_end": datetime.now().isoformat(),
                
                # Métricas principais
                "overall": {
                    "total_predictions": total_predictions,
                    "correct_predictions": correct_predictions,
                    "win_rate_percentage": win_rate,
                    "total_staked": total_staked,
                    "total_returned": total_returned,
                    "net_profit": net_profit,
                    "roi_percentage": roi
                },
                
                # Performance por método
                "by_method": method_stats,
                
                # Performance por confiança
                "by_confidence": confidence_stats,
                
                # Análise temporal
                "daily_breakdown": daily_stats,
                
                # Extremos
                "best_prediction": {
                    "match_id": best_prediction.match_id,
                    "profit": best_prediction.calculate_profit_loss(),
                    "odds": best_prediction.odds_used,
                    "method": best_prediction.method_used
                },
                "worst_prediction": {
                    "match_id": worst_prediction.match_id,
                    "loss": worst_prediction.calculate_profit_loss(),
                    "odds": worst_prediction.odds_used,
                    "method": worst_prediction.method_used
                },
                
                # Alertas recentes
                "recent_alerts": [
                    {
                        "level": alert.level.value,
                        "message": alert.message,
                        "timestamp": datetime.fromtimestamp(alert.timestamp).isoformat()
                    }
                    for alert in self.alerts[-5:]  # Últimos 5 alertas
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return {"error": str(e)}

    def _extract_odds_for_winner(self, predicted_winner: str, odds_data: Dict) -> float:
        """Extrai odds para o time previsto como vencedor"""
        try:
            # Formato PandaScore
            if "outcomes" in odds_data:
                for outcome in odds_data["outcomes"]:
                    if outcome.get("name", "").lower() == predicted_winner.lower():
                        return float(outcome.get("odd", 2.0))
            
            # Formato direto com mapeamento de times
            if "team1_odds" in odds_data and "team2_odds" in odds_data:
                # Assume que precisamos do nome dos times para mapear corretamente
                # Por agora retorna odds médias
                return (float(odds_data["team1_odds"]) + float(odds_data["team2_odds"])) / 2
            
            # Fallback
            return 2.0
            
        except Exception as e:
            logger.warning(f"Erro ao extrair odds: {e}")
            return 2.0

    async def _update_system_metrics(self):
        """Atualiza métricas gerais do sistema"""
        try:
            current_time = time.time()
            resolved_predictions = [p for p in self.predictions.values() if p.is_resolved]
            
            if not resolved_predictions:
                metrics = SystemMetrics(timestamp=current_time)
            else:
                # Calcula métricas básicas
                total_predictions = len(resolved_predictions)
                correct_predictions = sum(
                    1 for p in resolved_predictions 
                    if p.predicted_winner == p.actual_winner
                )
                win_rate = (correct_predictions / total_predictions) * 100
                
                # Métricas financeiras
                total_staked = sum(p.stake_amount for p in resolved_predictions)
                total_returned = sum(p.actual_return for p in resolved_predictions)
                net_profit = total_returned - total_staked
                roi = (net_profit / total_staked) * 100 if total_staked > 0 else 0
                
                # Performance por método
                ml_preds = [p for p in resolved_predictions if p.method_used == "ml"]
                algo_preds = [p for p in resolved_predictions if p.method_used == "algorithm"]
                hybrid_preds = [p for p in resolved_predictions if p.method_used == "hybrid"]
                
                ml_correct = sum(1 for p in ml_preds if p.predicted_winner == p.actual_winner)
                algo_correct = sum(1 for p in algo_preds if p.predicted_winner == p.actual_winner)
                hybrid_correct = sum(1 for p in hybrid_preds if p.predicted_winner == p.actual_winner)
                
                # Análises
                composition_analyses = sum(1 for p in self.predictions.values() if p.composition_score != 0)
                patch_analyses = sum(1 for p in self.predictions.values() if p.patch_score != 0)
                
                # Tempos de processamento
                processing_times = [p.processing_time_ms for p in self.predictions.values() if p.processing_time_ms > 0]
                avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0
                max_processing = max(processing_times) if processing_times else 0
                
                # Uptime
                uptime_hours = (current_time - self.start_time) / 3600
                
                metrics = SystemMetrics(
                    timestamp=current_time,
                    total_predictions=total_predictions,
                    correct_predictions=correct_predictions,
                    win_rate_percentage=win_rate,
                    total_staked=total_staked,
                    total_returned=total_returned,
                    net_profit=net_profit,
                    roi_percentage=roi,
                    ml_predictions=len(ml_preds),
                    ml_correct=ml_correct,
                    algorithm_predictions=len(algo_preds),
                    algorithm_correct=algo_correct,
                    hybrid_predictions=len(hybrid_preds),
                    hybrid_correct=hybrid_correct,
                    composition_analyses=composition_analyses,
                    patch_analyses=patch_analyses,
                    avg_processing_time_ms=avg_processing,
                    max_processing_time_ms=max_processing,
                    uptime_hours=uptime_hours,
                    alerts_generated=len(self.alerts)
                )
            
            # Adiciona às métricas históricas
            self.system_metrics.append(metrics)
            
            # Mantém apenas últimas 24h de métricas (1 por minuto)
            cutoff_time = current_time - (24 * 3600)
            self.system_metrics = [
                m for m in self.system_metrics 
                if m.timestamp > cutoff_time
            ]
            
            self.last_metrics_calculation = current_time
            
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")

    async def _check_prediction_alerts(self, prediction: PredictionMetrics):
        """Verifica alertas relacionados à nova predição"""
        try:
            alerts = []
            
            # Alerta por tempo de processamento alto
            if prediction.processing_time_ms > self.alert_thresholds["max_processing_time"]:
                alerts.append(Alert(
                    alert_id=f"slow_processing_{prediction.prediction_id}",
                    timestamp=time.time(),
                    level=AlertLevel.WARNING,
                    category="performance",
                    message=f"Processamento lento detectado: {prediction.processing_time_ms:.0f}ms",
                    details={
                        "prediction_id": prediction.prediction_id,
                        "processing_time": prediction.processing_time_ms,
                        "threshold": self.alert_thresholds["max_processing_time"]
                    }
                ))
            
            # Alerta por odds muito baixas
            if prediction.odds_used < 1.2:
                alerts.append(Alert(
                    alert_id=f"low_odds_{prediction.prediction_id}",
                    timestamp=time.time(),
                    level=AlertLevel.INFO,
                    category="betting",
                    message=f"Odds muito baixas: {prediction.odds_used}",
                    details={
                        "prediction_id": prediction.prediction_id,
                        "odds": prediction.odds_used
                    }
                ))
            
            # Adiciona alertas à lista
            for alert in alerts:
                self.alerts.append(alert)
                logger.warning(f"Alerta gerado: {alert.message}")
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de predição: {e}")

    async def _check_resolution_alerts(self, prediction: PredictionMetrics, is_correct: bool):
        """Verifica alertas após resolução de predição"""
        try:
            alerts = []
            
            # Alerta por perdas consecutivas
            if not is_correct and self.consecutive_losses >= self.alert_thresholds["max_consecutive_losses"]:
                alerts.append(Alert(
                    alert_id=f"consecutive_losses_{int(time.time())}",
                    timestamp=time.time(),
                    level=AlertLevel.ERROR,
                    category="performance",
                    message=f"Perdas consecutivas detectadas: {self.consecutive_losses}",
                    details={
                        "consecutive_losses": self.consecutive_losses,
                        "threshold": self.alert_thresholds["max_consecutive_losses"],
                        "last_prediction": prediction.prediction_id
                    }
                ))
            
            # Adiciona alertas à lista
            for alert in alerts:
                self.alerts.append(alert)
                logger.error(f"Alerta crítico: {alert.message}")
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de resolução: {e}")

    async def _continuous_monitoring(self, interval_seconds: int):
        """Loop de monitoramento contínuo"""
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                
                # Atualiza métricas
                await self._update_system_metrics()
                
                # Verifica alertas de sistema
                await self._check_system_alerts()
                
                # Salva dados periodicamente
                await self._save_performance_data()
                
                logger.debug("Ciclo de monitoramento completado")
                
        except asyncio.CancelledError:
            logger.info("Monitoramento contínuo cancelado")
        except Exception as e:
            logger.error(f"Erro no monitoramento contínuo: {e}")

    async def _check_system_alerts(self):
        """Verifica alertas de sistema"""
        try:
            if not self.system_metrics:
                return
            
            current_metrics = self.system_metrics[-1]
            alerts = []
            
            # Alerta por win rate baixa
            if (current_metrics.total_predictions >= 20 and 
                current_metrics.win_rate_percentage < self.alert_thresholds["min_win_rate"]):
                alerts.append(Alert(
                    alert_id=f"low_winrate_{int(time.time())}",
                    timestamp=time.time(),
                    level=AlertLevel.WARNING,
                    category="performance",
                    message=f"Win rate baixa: {current_metrics.win_rate_percentage:.1f}%",
                    details={
                        "win_rate": current_metrics.win_rate_percentage,
                        "threshold": self.alert_thresholds["min_win_rate"],
                        "total_predictions": current_metrics.total_predictions
                    }
                ))
            
            # Alerta por ROI baixo
            if (current_metrics.total_predictions >= 10 and 
                current_metrics.roi_percentage < self.alert_thresholds["min_roi"]):
                alerts.append(Alert(
                    alert_id=f"low_roi_{int(time.time())}",
                    timestamp=time.time(),
                    level=AlertLevel.WARNING,
                    category="financial",
                    message=f"ROI baixo: {current_metrics.roi_percentage:.1f}%",
                    details={
                        "roi": current_metrics.roi_percentage,
                        "threshold": self.alert_thresholds["min_roi"],
                        "net_profit": current_metrics.net_profit
                    }
                ))
            
            # Adiciona alertas
            for alert in alerts:
                self.alerts.append(alert)
                logger.warning(f"Alerta de sistema: {alert.message}")
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de sistema: {e}")

    def _calculate_daily_stats(self, predictions: List[PredictionMetrics], days: int) -> List[Dict]:
        """Calcula estatísticas diárias"""
        daily_stats = []
        
        try:
            current_time = time.time()
            
            for day in range(days):
                day_start = current_time - ((day + 1) * 24 * 3600)
                day_end = current_time - (day * 24 * 3600)
                
                day_predictions = [
                    p for p in predictions 
                    if day_start <= p.timestamp < day_end
                ]
                
                if day_predictions:
                    correct = sum(1 for p in day_predictions if p.predicted_winner == p.actual_winner)
                    profit = sum(p.calculate_profit_loss() for p in day_predictions)
                    
                    daily_stats.append({
                        "date": datetime.fromtimestamp(day_start).strftime("%Y-%m-%d"),
                        "predictions": len(day_predictions),
                        "correct": correct,
                        "win_rate": (correct / len(day_predictions)) * 100,
                        "profit": profit
                    })
                else:
                    daily_stats.append({
                        "date": datetime.fromtimestamp(day_start).strftime("%Y-%m-%d"),
                        "predictions": 0,
                        "correct": 0,
                        "win_rate": 0,
                        "profit": 0
                    })
            
            return list(reversed(daily_stats))  # Mais recente primeiro
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas diárias: {e}")
            return []

    async def _save_performance_data(self):
        """Salva dados de performance em arquivo"""
        try:
            import os
            os.makedirs("bot/data/monitoring", exist_ok=True)
            
            # Salva predições
            predictions_data = {
                pred_id: asdict(pred) for pred_id, pred in self.predictions.items()
            }
            
            with open("bot/data/monitoring/predictions.json", "w", encoding="utf-8") as f:
                json.dump(predictions_data, f, indent=2, ensure_ascii=False)
            
            # Salva métricas do sistema
            metrics_data = [asdict(metric) for metric in self.system_metrics[-100:]]  # Últimas 100
            
            with open("bot/data/monitoring/system_metrics.json", "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
            # Salva alertas
            alerts_data = [asdict(alert) for alert in self.alerts[-50:]]  # Últimos 50
            
            with open("bot/data/monitoring/alerts.json", "w", encoding="utf-8") as f:
                json.dump(alerts_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Dados de performance salvos")
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados de performance: {e}")

    async def _load_historical_data(self):
        """Carrega dados históricos se existirem"""
        try:
            # Carrega predições
            try:
                with open("bot/data/monitoring/predictions.json", "r", encoding="utf-8") as f:
                    predictions_data = json.load(f)
                
                for pred_id, pred_dict in predictions_data.items():
                    self.predictions[pred_id] = PredictionMetrics(**pred_dict)
                
                logger.info(f"Carregadas {len(self.predictions)} predições históricas")
            except FileNotFoundError:
                logger.info("Nenhum histórico de predições encontrado")
            
            # Carrega alertas
            try:
                with open("bot/data/monitoring/alerts.json", "r", encoding="utf-8") as f:
                    alerts_data = json.load(f)
                
                for alert_dict in alerts_data:
                    alert = Alert(**alert_dict)
                    alert.level = AlertLevel(alert_dict["level"])  # Converte enum
                    self.alerts.append(alert)
                
                logger.info(f"Carregados {len(self.alerts)} alertas históricos")
            except FileNotFoundError:
                logger.info("Nenhum histórico de alertas encontrado")
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados históricos: {e}")

    def get_live_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados para dashboard em tempo real"""
        try:
            current_metrics = self.system_metrics[-1] if self.system_metrics else SystemMetrics(timestamp=time.time())
            
            # Últimas 24h
            last_24h = time.time() - (24 * 3600)
            recent_predictions = [
                p for p in self.predictions.values() 
                if p.timestamp > last_24h
            ]
            
            recent_resolved = [p for p in recent_predictions if p.is_resolved]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "online",
                "uptime_hours": current_metrics.uptime_hours,
                
                # Métricas principais
                "current_metrics": {
                    "total_predictions": current_metrics.total_predictions,
                    "win_rate": current_metrics.win_rate_percentage,
                    "roi": current_metrics.roi_percentage,
                    "net_profit": current_metrics.net_profit
                },
                
                # Últimas 24h
                "last_24h": {
                    "predictions": len(recent_predictions),
                    "resolved": len(recent_resolved),
                    "pending": len(recent_predictions) - len(recent_resolved),
                    "profit": sum(p.calculate_profit_loss() for p in recent_resolved)
                },
                
                # Performance por método
                "method_performance": {
                    "ml": {
                        "predictions": current_metrics.ml_predictions,
                        "win_rate": (current_metrics.ml_correct / max(current_metrics.ml_predictions, 1)) * 100
                    },
                    "algorithm": {
                        "predictions": current_metrics.algorithm_predictions,
                        "win_rate": (current_metrics.algorithm_correct / max(current_metrics.algorithm_predictions, 1)) * 100
                    },
                    "hybrid": {
                        "predictions": current_metrics.hybrid_predictions,
                        "win_rate": (current_metrics.hybrid_correct / max(current_metrics.hybrid_predictions, 1)) * 100
                    }
                },
                
                # Alertas ativos
                "active_alerts": [
                    {
                        "level": alert.level.value,
                        "message": alert.message,
                        "category": alert.category,
                        "timestamp": datetime.fromtimestamp(alert.timestamp).isoformat()
                    }
                    for alert in self.alerts[-5:] if not alert.is_resolved
                ],
                
                # Performance de análises
                "analysis_usage": {
                    "composition_analyses": current_metrics.composition_analyses,
                    "patch_analyses": current_metrics.patch_analyses,
                    "avg_processing_time": current_metrics.avg_processing_time_ms
                },
                
                # Trend (últimas métricas)
                "trend": {
                    "win_rate_trend": [m.win_rate_percentage for m in self.system_metrics[-10:]],
                    "roi_trend": [m.roi_percentage for m in self.system_metrics[-10:]],
                    "prediction_count_trend": [m.total_predictions for m in self.system_metrics[-10:]]
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados do dashboard: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()} 
