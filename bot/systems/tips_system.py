from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from ..api_clients.pandascore_api_client import PandaScoreAPIClient
from ..api_clients.riot_api_client import RiotAPIClient
from ..core_logic import (
    DynamicPredictionSystem,
    LoLGameAnalyzer,
    ProfessionalUnitsSystem,
    PredictionMethod
)
from ..data_models.match_data import MatchData
from ..data_models.tip_data import ProfessionalTip
from ..utils.constants import (
    SCAN_INTERVAL_MINUTES,
    SUPPORTED_LEAGUES,
    VALID_LIVE_STATUSES,
    PREDICTION_THRESHOLDS
)
from ..utils.helpers import get_current_timestamp, normalize_team_name
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class TipStatus(Enum):
    """Status de uma tip profissional"""
    PENDING = "pending"
    SENT = "sent"
    EXPIRED = "expired"
    INVALID = "invalid"


@dataclass
class GeneratedTip:
    """Tip gerada pelo sistema"""
    tip: ProfessionalTip
    match_data: MatchData
    status: TipStatus
    generated_at: float
    sent_at: Optional[float] = None
    expiry_time: float = 0.0
    
    def __post_init__(self):
        if self.expiry_time == 0.0:
            # Tips expiram após 15 minutos
            self.expiry_time = self.generated_at + (15 * 60)
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a tip expirou"""
        return time.time() > self.expiry_time
    
    @property
    def is_valid(self) -> bool:
        """Verifica se a tip ainda é válida"""
        return not self.is_expired and self.status in [TipStatus.PENDING, TipStatus.SENT]


@dataclass
class MonitoringStats:
    """Estatísticas de monitoramento"""
    matches_scanned: int = 0
    tips_generated: int = 0
    tips_sent: int = 0
    tips_expired: int = 0
    tips_invalid: int = 0
    last_scan_time: float = 0.0
    uptime_start: float = 0.0
    
    def __post_init__(self):
        if self.uptime_start == 0.0:
            self.uptime_start = time.time()
    
    @property
    def uptime_hours(self) -> float:
        """Tempo de atividade em horas"""
        return (time.time() - self.uptime_start) / 3600


class ProfessionalTipsSystem:
    """
    Sistema Profissional de Tips para League of Legends
    
    Motor principal que automatiza:
    - Monitoramento de partidas ao vivo
    - Análise e predição usando ML + algoritmos
    - Geração de tips profissionais
    - Validação rigorosa de critérios
    - Gestão de timing e rate limits
    - Integração com sistema de alertas
    
    Características:
    - Monitoramento contínuo a cada 3 minutos
    - Validação de 5 critérios profissionais
    - Sistema anti-spam (máx 5 tips/hora)
    - Expiração automática de tips antigas
    - Métricas detalhadas de performance
    """

    def __init__(
        self,
        pandascore_client: PandaScoreAPIClient,
        riot_client: RiotAPIClient,
        prediction_system: DynamicPredictionSystem,
        telegram_alerts=None  # TelegramAlertsSystem será implementado depois
    ):
        """
        Inicializa o sistema profissional de tips
        
        Args:
            pandascore_client: Cliente do PandaScore API
            riot_client: Cliente da Riot API
            prediction_system: Sistema de predição dinâmico
            telegram_alerts: Sistema de alertas Telegram (opcional)
        """
        self.pandascore_client = pandascore_client
        self.riot_client = riot_client
        self.prediction_system = prediction_system
        self.telegram_alerts = telegram_alerts
        
        # Estado do sistema
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Cache de partidas monitoradas
        self.monitored_matches: Dict[str, MatchData] = {}
        self.generated_tips: Dict[str, GeneratedTip] = {}
        
        # Rate limiting
        self.last_tip_times: List[float] = []
        self.max_tips_per_hour = 5
        
        # Estatísticas
        self.stats = MonitoringStats()
        
        # Filtros de qualidade
        self.quality_filters = {
            "min_game_time_minutes": 5,
            "max_game_time_minutes": 45,
            "supported_leagues": SUPPORTED_LEAGUES,
            "min_data_quality": 0.60,
            "required_events": 3  # Mínimo de eventos cruciais
        }
        
        logger.info("ProfessionalTipsSystem inicializado com sucesso")

    async def start_monitoring(self) -> None:
        """Inicia o monitoramento contínuo de partidas"""
        if self.is_monitoring:
            logger.warning("Monitoramento já está ativo")
            return
        
        self.is_monitoring = True
        logger.info("🚀 Iniciando monitoramento profissional de tips")
        
        try:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            await self.monitoring_task
        except asyncio.CancelledError:
            logger.info("Monitoramento cancelado")
        except Exception as e:
            logger.error(f"Erro no monitoramento: {e}")
            self.is_monitoring = False
            raise

    async def stop_monitoring(self) -> None:
        """Para o monitoramento"""
        if not self.is_monitoring:
            return
        
        logger.info("🛑 Parando monitoramento de tips")
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self) -> None:
        """Loop principal de monitoramento"""
        logger.info(f"Loop de monitoramento iniciado (intervalo: {SCAN_INTERVAL_MINUTES}min)")
        
        while self.is_monitoring:
            try:
                scan_start = time.time()
                
                # 1. Busca partidas ao vivo
                live_matches = await self._get_live_matches()
                logger.debug(f"Encontradas {len(live_matches)} partidas ao vivo")
                
                # 2. Filtra partidas adequadas
                suitable_matches = self._filter_suitable_matches(live_matches)
                logger.debug(f"Filtradas {len(suitable_matches)} partidas adequadas")
                
                # 3. Atualiza cache de partidas monitoradas
                self._update_monitored_matches(suitable_matches)
                
                # 4. Gera e processa tips
                if suitable_matches:
                    await self._process_matches_for_tips(suitable_matches)
                
                # 5. Limpa tips expiradas
                self._cleanup_expired_tips()
                
                # 6. Atualiza estatísticas
                self.stats.matches_scanned += len(live_matches)
                self.stats.last_scan_time = time.time()
                
                scan_duration = time.time() - scan_start
                logger.debug(f"Scan completo em {scan_duration:.2f}s")
                
                # 7. Aguarda próximo ciclo
                await asyncio.sleep(SCAN_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                await asyncio.sleep(30)  # Espera 30s em caso de erro

    async def _get_live_matches(self) -> List[MatchData]:
        """Busca partidas ao vivo das principais ligas"""
        live_matches = []
        
        try:
            # Busca via PandaScore (principal fonte)
            pandascore_matches = await self.pandascore_client.get_live_matches()
            live_matches.extend(pandascore_matches)
            
            # Busca via Riot API (backup)
            try:
                riot_matches = await self.riot_client.get_live_matches()
                # Evita duplicatas
                existing_ids = {match.match_id for match in live_matches}
                for match in riot_matches:
                    if match.match_id not in existing_ids:
                        live_matches.append(match)
            except Exception as e:
                logger.warning(f"Erro ao buscar partidas da Riot API: {e}")
            
            logger.info(f"Encontradas {len(live_matches)} partidas ao vivo no total")
            return live_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return []

    def _filter_suitable_matches(self, matches: List[MatchData]) -> List[MatchData]:
        """Filtra partidas adequadas para análise"""
        suitable = []
        
        for match in matches:
            # Verifica se já foi processada recentemente
            if match.match_id in self.generated_tips:
                existing_tip = self.generated_tips[match.match_id]
                if existing_tip.is_valid:
                    continue  # Pula se já tem tip válida
            
            # Aplicar filtros de qualidade
            if not self._match_meets_quality_criteria(match):
                continue
            
            suitable.append(match)
            logger.debug(f"Partida adequada: {match.team1_name} vs {match.team2_name} ({match.get_game_time_minutes()}min)")
        
        return suitable

    def _match_meets_quality_criteria(self, match: MatchData) -> bool:
        """Verifica se partida atende critérios de qualidade"""
        
        # 1. Liga suportada
        if match.league not in self.quality_filters["supported_leagues"]:
            logger.debug(f"Liga não suportada: {match.league}")
            return False
        
        # 2. Status válido
        if match.status not in VALID_LIVE_STATUSES:
            logger.debug(f"Status inválido: {match.status}")
            return False
        
        # 3. Tempo de jogo
        game_minutes = match.get_game_time_minutes()
        if not (self.quality_filters["min_game_time_minutes"] <= 
                game_minutes <= 
                self.quality_filters["max_game_time_minutes"]):
            logger.debug(f"Tempo de jogo fora do range: {game_minutes}min")
            return False
        
        # 4. Qualidade dos dados
        data_quality = match.calculate_data_quality()
        if data_quality < self.quality_filters["min_data_quality"]:
            logger.debug(f"Qualidade dos dados baixa: {data_quality:.1%}")
            return False
        
        # 5. Eventos cruciais mínimos
        if len(match.events) < self.quality_filters["required_events"]:
            logger.debug(f"Poucos eventos cruciais: {len(match.events)}")
            return False
        
        return True

    def _update_monitored_matches(self, matches: List[MatchData]) -> None:
        """Atualiza cache de partidas monitoradas"""
        current_ids = {match.match_id for match in matches}
        
        # Remove partidas que não estão mais ao vivo
        to_remove = [
            match_id for match_id in self.monitored_matches.keys()
            if match_id not in current_ids
        ]
        
        for match_id in to_remove:
            logger.debug(f"Removendo partida do monitoramento: {match_id}")
            del self.monitored_matches[match_id]
        
        # Adiciona/atualiza partidas atuais
        for match in matches:
            self.monitored_matches[match.match_id] = match

    async def _process_matches_for_tips(self, matches: List[MatchData]) -> None:
        """Processa partidas para geração de tips"""
        
        for match in matches:
            try:
                # Verifica rate limiting
                if not self._can_generate_tip():
                    logger.debug("Rate limit atingido, pulando geração de tips")
                    break
                
                # Gera tip para a partida
                tip_result = await self._generate_tip_for_match(match)
                
                if tip_result:
                    logger.info(f"✅ Tip gerada: {match.team1_name} vs {match.team2_name}")
                    await self._handle_generated_tip(tip_result, match)
                else:
                    logger.debug(f"Nenhuma tip gerada para: {match.team1_name} vs {match.team2_name}")
                
            except Exception as e:
                logger.error(f"Erro ao processar partida {match.match_id}: {e}")

    async def _generate_tip_for_match(self, match: MatchData) -> Optional[ProfessionalTip]:
        """Gera tip profissional para uma partida"""
        try:
            # Busca odds da partida
            odds_data = await self.pandascore_client.get_match_odds(match.match_id)
            
            if not odds_data:
                logger.debug(f"Sem odds disponíveis para {match.match_id}")
                return None
            
            # Gera predição e tip
            tip_generation_result = await self.prediction_system.generate_professional_tip(
                match, odds_data
            )
            
            if tip_generation_result.is_valid and tip_generation_result.tip:
                logger.info(
                    f"Tip válida gerada: {tip_generation_result.tip.tip_on_team} @ "
                    f"{tip_generation_result.tip.odds} ({tip_generation_result.tip.units}u)"
                )
                return tip_generation_result.tip
            else:
                logger.debug(f"Tip rejeitada: {tip_generation_result.rejection_reason}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao gerar tip para {match.match_id}: {e}")
            return None

    async def _handle_generated_tip(self, tip: ProfessionalTip, match: MatchData) -> None:
        """Processa tip gerada"""
        
        # Cria registro da tip
        generated_tip = GeneratedTip(
            tip=tip,
            match_data=match,
            status=TipStatus.PENDING,
            generated_at=time.time()
        )
        
        # Armazena no cache
        self.generated_tips[match.match_id] = generated_tip
        
        # Atualiza rate limiting
        self.last_tip_times.append(time.time())
        
        # Envia via Telegram (se disponível)
        if self.telegram_alerts:
            try:
                await self.telegram_alerts.send_professional_tip(tip)
                generated_tip.status = TipStatus.SENT
                generated_tip.sent_at = time.time()
                self.stats.tips_sent += 1
                logger.info(f"✅ Tip enviada via Telegram")
            except Exception as e:
                logger.error(f"Erro ao enviar tip via Telegram: {e}")
                generated_tip.status = TipStatus.INVALID
                self.stats.tips_invalid += 1
        else:
            # Simula envio bem-sucedido para testes
            generated_tip.status = TipStatus.SENT
            generated_tip.sent_at = time.time()
            self.stats.tips_sent += 1
            logger.info(f"✅ Tip processada (Telegram não configurado)")
        
        self.stats.tips_generated += 1

    def _can_generate_tip(self) -> bool:
        """Verifica se pode gerar nova tip (rate limiting)"""
        current_time = time.time()
        one_hour_ago = current_time - 3600
        
        # Remove registros antigos
        self.last_tip_times = [
            tip_time for tip_time in self.last_tip_times
            if tip_time > one_hour_ago
        ]
        
        # Verifica limite
        can_generate = len(self.last_tip_times) < self.max_tips_per_hour
        
        if not can_generate:
            logger.debug(f"Rate limit: {len(self.last_tip_times)}/{self.max_tips_per_hour} tips na última hora")
        
        return can_generate

    def _cleanup_expired_tips(self) -> None:
        """Remove tips expiradas"""
        current_time = time.time()
        expired_tips = []
        
        for match_id, generated_tip in self.generated_tips.items():
            if generated_tip.is_expired:
                expired_tips.append(match_id)
        
        for match_id in expired_tips:
            logger.debug(f"Removendo tip expirada: {match_id}")
            self.generated_tips[match_id].status = TipStatus.EXPIRED
            self.stats.tips_expired += 1
            del self.generated_tips[match_id]

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do monitoramento"""
        current_time = time.time()
        
        # Tips por status
        tips_by_status = {}
        for status in TipStatus:
            tips_by_status[status.value] = sum(
                1 for tip in self.generated_tips.values()
                if tip.status == status
            )
        
        # Rate limiting status
        one_hour_ago = current_time - 3600
        recent_tips = len([
            tip_time for tip_time in self.last_tip_times
            if tip_time > one_hour_ago
        ])
        
        return {
            "is_monitoring": self.is_monitoring,
            "uptime_hours": self.stats.uptime_hours,
            "last_scan": {
                "time": self.stats.last_scan_time,
                "minutes_ago": (current_time - self.stats.last_scan_time) / 60
            },
            "statistics": {
                "matches_scanned": self.stats.matches_scanned,
                "tips_generated": self.stats.tips_generated,
                "tips_sent": self.stats.tips_sent,
                "tips_expired": self.stats.tips_expired,
                "tips_invalid": self.stats.tips_invalid,
                "success_rate": (
                    self.stats.tips_sent / max(self.stats.tips_generated, 1)
                ) * 100
            },
            "current_state": {
                "monitored_matches": len(self.monitored_matches),
                "active_tips": len(self.generated_tips),
                "tips_by_status": tips_by_status
            },
            "rate_limiting": {
                "recent_tips": recent_tips,
                "max_per_hour": self.max_tips_per_hour,
                "can_generate": self._can_generate_tip()
            },
            "quality_filters": self.quality_filters
        }

    def get_recent_tips(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna tips recentes"""
        recent_tips = sorted(
            self.generated_tips.values(),
            key=lambda x: x.generated_at,
            reverse=True
        )[:limit]
        
        return [
            {
                "match": f"{tip.match_data.team1_name} vs {tip.match_data.team2_name}",
                "league": tip.match_data.league,
                "tip_on": tip.tip.tip_on_team,
                "odds": tip.tip.odds,
                "units": tip.tip.units,
                "confidence": tip.tip.confidence_percentage,
                "ev": tip.tip.ev_percentage,
                "status": tip.status.value,
                "generated_at": tip.generated_at,
                "game_time": tip.tip.game_time_at_tip
            }
            for tip in recent_tips
        ]

    async def force_scan(self) -> Dict[str, Any]:
        """Força um scan manual para testes"""
        logger.info("🔍 Executando scan manual...")
        
        scan_start = time.time()
        
        # Busca partidas
        live_matches = await self._get_live_matches()
        suitable_matches = self._filter_suitable_matches(live_matches)
        
        # Processa uma partida se disponível
        tip_generated = False
        if suitable_matches and self._can_generate_tip():
            tip = await self._generate_tip_for_match(suitable_matches[0])
            if tip:
                await self._handle_generated_tip(tip, suitable_matches[0])
                tip_generated = True
        
        scan_duration = time.time() - scan_start
        
        return {
            "scan_duration_seconds": round(scan_duration, 2),
            "live_matches_found": len(live_matches),
            "suitable_matches": len(suitable_matches),
            "tip_generated": tip_generated,
            "can_generate_more": self._can_generate_tip(),
            "timestamp": get_current_timestamp()
        }

    def update_quality_filters(self, new_filters: Dict[str, Any]) -> None:
        """Atualiza filtros de qualidade"""
        old_filters = self.quality_filters.copy()
        self.quality_filters.update(new_filters)
        
        logger.info(f"Filtros de qualidade atualizados: {old_filters} -> {self.quality_filters}")

    def set_max_tips_per_hour(self, max_tips: int) -> None:
        """Atualiza limite de tips por hora"""
        if max_tips < 1 or max_tips > 10:
            raise ValueError("Limite deve estar entre 1 e 10 tips por hora")
        
        old_limit = self.max_tips_per_hour
        self.max_tips_per_hour = max_tips
        
        logger.info(f"Limite de tips atualizado: {old_limit} -> {max_tips} por hora") 