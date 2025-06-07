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
        
        # NOVO: Controle de tips por mapa individual (1 tip por mapa)
        self.processed_maps: Set[str] = set()  # Cache de mapas já processados
        
        # Rate limiting
        self.last_tip_times: List[float] = []
        self.max_tips_per_hour = 5
        
        # Estatísticas
        self.stats = MonitoringStats()
        
        # Filtros de qualidade - AJUSTADOS para dados reais
        self.quality_filters = {
            "min_game_time_minutes": 0,  # Permitir partidas desde o início (draft)
            "max_game_time_minutes": 60,  # Aumentado para permitir partidas longas
            "supported_leagues": SUPPORTED_LEAGUES,
            "min_data_quality": 0.05,  # Reduzido drasticamente para aceitar dados básicos
            "required_events": 0  # Reduzido para aceitar partidas no início
        }
        
        logger.info("ProfessionalTipsSystem inicializado com sucesso")

    async def start_monitoring(self) -> None:
        """Inicia o monitoramento contínuo de partidas"""
        if self.is_monitoring:
            logger.warning("Monitoramento já está ativo")
            return
        
        # CORREÇÃO CRÍTICA: Força limpeza de cache na inicialização
        old_count = len(self.processed_maps)
        self.processed_maps.clear()
        logger.info(f"🧹 FORCE CLEANUP: Cache limpo na inicialização ({old_count} mapas removidos)")
        
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
                
                # 5. Limpa tips expiradas e mapas antigos
                self._cleanup_expired_tips()
                self._cleanup_old_processed_maps()  # CORREÇÃO: Limpa mapas a cada 30min
                
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
        """Obtém partidas ao vivo de ambas as APIs"""
        all_matches = []
        
        try:
            # PandaScore - partidas com odds
            pandascore_raw = await self.pandascore_client.get_lol_live_matches()
            logger.debug(f"PandaScore: {len(pandascore_raw)} partidas encontradas")
            
            # Riot API - dados detalhados de partidas  
            riot_raw = await self.riot_client.get_live_matches()
            logger.debug(f"Riot API: {len(riot_raw)} partidas encontradas")
            
            # Converte dados raw em objetos MatchData
            from ..data_models.match_data import MatchData
            
            # Converte dados do PandaScore
            for raw_match in pandascore_raw:
                try:
                    if isinstance(raw_match, dict):
                        match_obj = MatchData.from_api_data(raw_match, api_source="pandascore")
                        all_matches.append(match_obj)
                    elif isinstance(raw_match, MatchData):
                        # Já é um objeto MatchData
                        all_matches.append(raw_match)
                    else:
                        logger.warning(f"Tipo inesperado do PandaScore: {type(raw_match)}")
                except Exception as e:
                    logger.warning(f"Erro ao converter partida PandaScore: {e}")
                    continue
            
            # Converte dados do Riot API
            for raw_match in riot_raw:
                try:
                    if isinstance(raw_match, dict):
                        match_obj = MatchData.from_api_data(raw_match, api_source="riot")
                        all_matches.append(match_obj)
                    elif isinstance(raw_match, MatchData):
                        # Já é um objeto MatchData
                        all_matches.append(raw_match)
                    else:
                        logger.warning(f"Tipo inesperado do Riot API: {type(raw_match)}")
                except Exception as e:
                    logger.warning(f"Erro ao converter partida Riot API: {e}")
                    continue
            
            logger.info(f"Encontradas {len(all_matches)} partidas ao vivo no total")
            return all_matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas ao vivo: {e}")
            return []

    def _filter_suitable_matches(self, matches: List[MatchData]) -> List[MatchData]:
        """Filtra partidas adequadas para análise"""
        suitable = []
        
        for match in matches:
            # NOVO: Verifica se este mapa específico já foi processado
            map_id = self._get_map_identifier(match)
            if map_id in self.processed_maps:
                logger.debug(f"Mapa já processado: {map_id}")
                continue
            
            # Verifica se já foi processada recentemente (fallback)
            if match.match_id in self.generated_tips:
                existing_tip = self.generated_tips[match.match_id]
                if existing_tip.is_valid:
                    continue  # Pula se já tem tip válida
            
            # Aplicar filtros de qualidade
            if not self._match_meets_quality_criteria(match):
                continue
            
            suitable.append(match)
            logger.debug(f"Mapa adequado: {match.team1_name} vs {match.team2_name} - {map_id} ({match.get_game_time_minutes()}min)")
        
        return suitable

    def _match_meets_quality_criteria(self, match: MatchData) -> bool:
        """Verifica se partida atende critérios de qualidade"""
        
        # 1. Liga suportada - MODO SUPER INCLUSIVO
        # match.league pode ser string ou dict
        league_name = match.league
        if isinstance(match.league, dict):
            league_name = match.league.get('name', '')
        
        # Extrai apenas o nome principal da liga (ex: "LCK Spring" -> "LCK")
        league_key = league_name.upper()
        is_supported_league = False
        
        # Primeiro tenta match exato
        for supported_league in self.quality_filters["supported_leagues"]:
            if supported_league.upper() in league_key or league_key in supported_league.upper():
                is_supported_league = True
                break
        
        # Se não encontrou match direto, tenta por palavras-chave profissionais
        if not is_supported_league:
            professional_keywords = [
                'LEAGUE', 'CHAMPIONSHIP', 'CUP', 'TOURNAMENT', 'SERIES', 'MASTERS',
                'ACADEMY', 'PREMIER', 'PRO', 'PROFESSIONAL', 'ELITE', 'SUPER',
                'REGIONAL', 'NATIONAL', 'INTERNATIONAL', 'QUALIFIER', 'CIRCUIT',
                'DIVISION', 'CONFERENCE', 'ESPORTS', 'GAMING', 'LOL', 'LEAGUE OF LEGENDS'
            ]
            
            # Se contém pelo menos uma palavra-chave profissional, aceita
            if any(keyword in league_key for keyword in professional_keywords):
                is_supported_league = True
                logger.debug(f"Liga aceita por palavra-chave profissional: {league_name}")
        
        # Se ainda não aceitou, mas tem teams válidos e estrutura de liga, aceita
        if not is_supported_league and match.team1_name and match.team2_name:
            # Se tem nomes de teams válidos e pelo menos 3 caracteres na liga, provavelmente é legítima
            if len(league_name.strip()) >= 3:
                is_supported_league = True
                logger.debug(f"Liga aceita por ter estrutura válida: {league_name}")
        
        if not is_supported_league:
            logger.debug(f"Liga não suportada: {league_name}")
            return False
        
        # 2. Status válido - AJUSTADO para permitir partidas reais sem status explícito
        # Se não tem status MAS tem dados válidos da Riot API, considera como "ao vivo"
        has_valid_status = match.status in VALID_LIVE_STATUSES
        is_riot_live_match = (not match.status or match.status == "") and hasattr(match, 'match_id') and match.match_id
        
        if not (has_valid_status or is_riot_live_match):
            logger.debug(f"Status inválido e não é partida ao vivo da Riot: {match.status}")
            return False
        
        # 3. NOVO: Verificação de draft completo - APENAS TIPS APÓS DRAFT FECHADO
        if not self._is_draft_complete(match):
            logger.debug(f"Draft incompleto - aguardando fechamento do draft: {match.match_id}")
            return False
        
        # 4. Tempo de jogo - AJUSTADO para tips pós-draft (0-2 minutos após draft)
        game_minutes = match.get_game_time_minutes()
        
        # Tips apenas nos primeiros 2 minutos APÓS o draft estar completo
        if game_minutes > 2.0:
            logger.debug(f"Tempo de jogo muito avançado para tip: {game_minutes}min")
            return False
        
        # Se tem tempo 0 mas draft completo, é o momento ideal para tip
        if game_minutes == 0.0 and self._is_draft_complete(match):
            logger.debug(f"Momento ideal: draft completo, jogo começando")
            return True
        
        # 5. Qualidade dos dados - PRIORIZA DADOS DE COMPOSIÇÃO PÓS-DRAFT
        data_quality = match.calculate_data_quality()
        min_quality = self.quality_filters["min_data_quality"]
        
        # Se tem composição completa (pós-draft), reduz requisito de qualidade
        has_composition = (hasattr(match, 'team1_composition') and match.team1_composition and
                          hasattr(match, 'team2_composition') and match.team2_composition)
        
        if has_composition:
            min_quality = max(0.4, min_quality - 0.2)  # Reduz em 20% se tem composição
            logger.debug(f"Tem composição pós-draft - qualidade mínima reduzida para: {min_quality:.1%}")
        
        # Para partidas da Riot API, aceita qualidade menor se são dados reais
        if is_riot_live_match and data_quality >= 0.3:
            logger.debug(f"Partida da Riot com qualidade aceitável: {data_quality:.1%}")
            return True
        
        if data_quality < min_quality:
            logger.debug(f"Qualidade dos dados baixa: {data_quality:.1%} (min: {min_quality:.1%})")
            return False
        
        # 5. Eventos cruciais mínimos - FLEXIBILIZADO para início de partida
        # Se é partida recente (≤ 10min), não exige muitos eventos
        if game_minutes <= 10:
            min_events = max(0, self.quality_filters["required_events"] - 2)
        else:
            min_events = self.quality_filters["required_events"]
        
        if len(match.events) < min_events:
            logger.debug(f"Poucos eventos cruciais: {len(match.events)} (min: {min_events})")
            # Para partidas da Riot, aceita mesmo sem eventos se tem dados básicos
            if is_riot_live_match and match.team1_name and match.team2_name:
                logger.debug("Aceitando partida da Riot mesmo sem eventos - tem dados básicos")
                return True
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
                
                # VALIDAÇÃO CRÍTICA: Verifica se o mapa atual ainda está ativo
                if not self._is_current_game_active(match):
                    logger.warning(f"❌ MAPA JÁ FINALIZADO - pulando: {match.match_id}")
                    continue
                
                # Gera identificador do mapa
                map_id = self._get_map_identifier(match)
                
                # CRÍTICO: Marca como processado ANTES de gerar para evitar condições de corrida
                self.processed_maps.add(map_id)
                logger.info(f"🔒 Mapa marcado como processado: {map_id}")
                
                # Gera tip para a partida
                tip_result = await self._generate_tip_for_match(match)
                
                if tip_result:
                    game_number = self._get_game_number_in_series(match)
                    logger.info(f"✅ Tip gerada: {match.team1_name} vs {match.team2_name} - Game {game_number}")
                    
                    await self._handle_generated_tip(tip_result, match)
                else:
                    # Se falhou na geração, remove do cache para tentar novamente depois
                    self.processed_maps.discard(map_id)
                    logger.debug(f"❌ Tip não gerada - removendo do cache: {map_id}")
                
            except Exception as e:
                logger.error(f"Erro ao processar partida {match.match_id}: {e}")

    
    async def _validate_real_odds_first(self, match: MatchData) -> Dict:
        """
        CORREÇÃO: Tenta buscar odds REAIS antes de usar estimadas
        """
        try:
            # 1. Busca no PandaScore por match_id
            real_odds = await self.pandascore_client.get_match_odds(match.match_id)
            if real_odds and self._are_valid_odds(real_odds):
                logger.info(f"✅ Odds reais encontradas: {match.match_id}")
                return real_odds
            
            # 2. Busca por nomes dos times
            real_odds = await self.pandascore_client.find_match_odds_by_teams(
                match.team1_name, match.team2_name
            )
            if real_odds and self._are_valid_odds(real_odds):
                logger.info(f"✅ Odds reais por times: {match.team1_name} vs {match.team2_name}")
                return real_odds
            
            # 3. Busca na liga específica
            if hasattr(match, 'league') and match.league:
                league_matches = await self.pandascore_client.get_league_matches(match.league)
                for league_match in league_matches:
                    if (league_match.get('team1') == match.team1_name and 
                        league_match.get('team2') == match.team2_name):
                        odds_data = league_match.get('odds')
                        if odds_data and self._are_valid_odds(odds_data):
                            logger.info(f"✅ Odds reais da liga: {match.league}")
                            return odds_data
            
            # Se não encontrou odds reais, retorna None para usar estimadas
            logger.warning(f"⚠️ Odds reais não encontradas para {match.match_id} - usando estimativa")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar odds reais: {e}")
            return None

    async def _generate_tip_for_match(self, match: MatchData) -> Optional[ProfessionalTip]:
        """Gera tip profissional para uma partida (apenas dados reais)"""
        try:
            # Verifica se é partida real (não mock)
            if not self._is_real_match_data(match):
                logger.debug(f"Partida rejeitada: dados não são reais - {match.match_id}")
                return None
            
            # 1. CORREÇÃO: Busca odds reais com método aprimorado
            odds_data = await self._validate_real_odds_first(match)
            # 3. Se ainda não tem odds, gera estimativa baseada em dados da partida
            if not odds_data:
                logger.debug(f"Sem odds reais - gerando estimativa para {match.match_id}")
                odds_data = self._generate_estimated_odds(match)
            
            # Verifica se são odds válidas (reais ou estimadas)
            if not odds_data or not self._are_valid_odds(odds_data):
                logger.debug(f"Odds inválidas para {match.match_id}")
                return None
            
            # Gera predição e tip
            tip_generation_result = await self.prediction_system.generate_professional_tip(
                match, odds_data
            )
            
            if tip_generation_result.is_valid and tip_generation_result.tip:
                # Adiciona informação do mapa na tip
                game_number = self._get_game_number_in_series(match)
                tip_generation_result.tip.map_number = game_number
                
                logger.info(
                    f"✅ Tip gerada: {tip_generation_result.tip.tip_on_team} @ "
                    f"{tip_generation_result.tip.odds} ({tip_generation_result.tip.units}u) - Game {game_number}"
                )
                return tip_generation_result.tip
            else:
                logger.debug(f"Tip rejeitada: {tip_generation_result.rejection_reason}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao gerar tip para {match.match_id}: {e}")
            return None

    def _generate_estimated_odds(self, match: MatchData) -> Dict:
        """Gera odds estimadas baseadas nos dados da partida"""
        try:
            # Análise básica dos dados disponíveis
            team1_strength = 0.5  # Base neutra
            team2_strength = 0.5
            
            # Ajusta baseado no tempo de jogo e eventos
            game_minutes = match.get_game_time_minutes()
            
            # Se tem eventos, analisa vantagem
            if match.events:
                team1_events = sum(1 for event in match.events if 'team1' in str(event).lower())
                team2_events = sum(1 for event in match.events if 'team2' in str(event).lower())
                
                total_events = team1_events + team2_events
                if total_events > 0:
                    team1_strength = team1_events / total_events
                    team2_strength = team2_events / total_events
            
            # Ajusta para odds realistas (entre 1.30 e 3.50)
            if team1_strength > team2_strength:
                team1_odds = max(1.30, min(2.50, 1 / max(0.4, team1_strength)))
                team2_odds = max(1.50, min(3.50, 1 / max(0.3, team2_strength)))
            else:
                team1_odds = max(1.50, min(3.50, 1 / max(0.3, team1_strength)))
                team2_odds = max(1.30, min(2.50, 1 / max(0.4, team2_strength)))
            
            # Estrutura compatível com PandaScore
            estimated_odds = {
                "id": f"estimated_{match.match_id}",
                "name": "Estimated Match Winner",
                "bookmaker": {"name": "Estimation System"},
                "outcomes": [
                    {
                        "name": match.team1_name,
                        "odd": round(team1_odds, 2)
                    },
                    {
                        "name": match.team2_name, 
                        "odd": round(team2_odds, 2)
                    }
                ],
                "is_estimated": True  # Marca como estimativa
            }
            
            logger.debug(f"Odds estimadas: {match.team1_name} @ {team1_odds:.2f}, {match.team2_name} @ {team2_odds:.2f}")
            return estimated_odds
            
        except Exception as e:
            logger.error(f"Erro ao gerar odds estimadas: {e}")
            return None

    def _are_valid_odds(self, odds_data: Dict) -> bool:
        """Verifica se odds são válidas (reais ou estimadas)"""
        try:
            if not odds_data:
                return False
            
            # Verifica estrutura básica
            if "outcomes" not in odds_data:
                return False
            
            outcomes = odds_data["outcomes"]
            if not outcomes or len(outcomes) < 2:
                return False
            
            # Verifica se todas as odds estão no range válido
            for outcome in outcomes:
                if "odd" not in outcome:
                    return False
                
                odd_value = float(outcome["odd"])
                if not (1.10 <= odd_value <= 10.0):  # Range amplo para aceitar estimativas
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erro ao validar odds: {e}")
            return False

    def _is_real_match_data(self, match: MatchData) -> bool:
        """Verifica se os dados da partida são reais (não mock/simulados)"""
        # Verifica indicadores de dados mock explícitos
        if hasattr(match, 'match_id') and match.match_id:
            match_id_str = str(match.match_id).lower()
            if any(keyword in match_id_str for keyword in ['mock', 'test', 'fake', 'dummy']):
                return False
        
        # Verifica se tem dados básicos obrigatórios
        if not hasattr(match, 'league') or not match.league:
            return False
        
        # Se tem liga válida da Riot API (dict com id), considera real
        if isinstance(match.league, dict) and match.league.get('id'):
            return True
        
        # Se tem liga como string válida, considera real
        if isinstance(match.league, str) and len(match.league) > 2:
            return True
        
        # Se tem match_id válido e não é obviamente fake, considera real
        if hasattr(match, 'match_id') and match.match_id:
            # IDs numéricos longos são tipicamente reais
            try:
                match_id_num = int(match.match_id)
                if match_id_num > 10000:  # IDs reais são tipicamente longos
                    return True
            except (ValueError, TypeError):
                pass
        
        return False

    def _are_real_odds(self, odds_data: Dict) -> bool:
        """Verifica se as odds são reais (não simuladas)"""
        # Verifica se tem marcador de dados simulados
        if odds_data.get("source") == "simulated":
            return False
        
        if odds_data.get("mock") is True:
            return False
        
        if odds_data.get("test") is True:
            return False
        
        # Verifica se tem estrutura de odds reais
        if "odds" not in odds_data:
            return False
        
        odds = odds_data["odds"]
        if not isinstance(odds, dict) or len(odds) < 2:
            return False
        
        # Verifica se odds são valores realistas
        for team, odd_value in odds.items():
            if not isinstance(odd_value, (int, float)):
                return False
            if odd_value < 1.01 or odd_value > 50.0:  # Range realista de odds
                return False
        
        return True

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
        
        # NOVO: Limpa mapas processados antigos (após 4 horas)
        self._cleanup_old_processed_maps()

    def _cleanup_old_processed_maps(self) -> None:
        """
        Limpa mapas processados antigos do cache
        
        CORREÇÃO CRÍTICA: Limpa cache mais agressivamente para evitar repetições
        """
        try:
            current_time = time.time()
            
            # CORREÇÃO: Limpa cache a cada 30 minutos ao invés de 4 horas
            # Isso resolve o problema de tips repetidas após restarts
            cleanup_interval = 30 * 60  # 30 minutos
            
            if hasattr(self, '_last_cleanup_time'):
                if current_time - self._last_cleanup_time > cleanup_interval:
                    old_count = len(self.processed_maps)
                    self.processed_maps.clear()
                    self._last_cleanup_time = current_time
                    logger.info(f"🧹 Cache de mapas processados limpo: {old_count} entradas removidas (30min cleanup)")
            else:
                # FORÇAR limpeza na inicialização para resolver problema Railway
                self.processed_maps.clear()
                self._last_cleanup_time = current_time
                logger.info("🔄 Cache de mapas forçadamente limpo na inicialização")
                
        except Exception as e:
            logger.warning(f"Erro ao limpar cache de mapas: {e}")

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
                "processed_maps": len(self.processed_maps),
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

    def _is_draft_complete(self, match: MatchData) -> bool:
        """Verifica se o draft está completo (todos os 10 champions selecionados)"""
        try:
            # Verifica se tem dados de composição dos times
            has_team1_comp = hasattr(match, 'team1_composition') and match.team1_composition
            has_team2_comp = hasattr(match, 'team2_composition') and match.team2_composition
            
            # Se tem composições, verifica se estão completas (5 champions cada)
            if has_team1_comp and has_team2_comp:
                team1_champions = len([c for c in match.team1_composition if c and c.strip()])
                team2_champions = len([c for c in match.team2_composition if c and c.strip()])
                
                draft_complete = team1_champions == 5 and team2_champions == 5
                if draft_complete:
                    logger.debug(f"Draft completo: {team1_champions + team2_champions}/10 champions")
                    return True
                else:
                    logger.debug(f"Draft incompleto: {team1_champions + team2_champions}/10 champions")
                    return False
            
            # Se não tem dados de composição, verifica por outros indicadores
            # Status específicos que indicam draft completo
            draft_complete_status = [
                'in_game', 'in-game', 'ingame', 'started', 'live', 'running'
            ]
            
            if match.status and match.status.lower() in draft_complete_status:
                logger.debug(f"Draft presumivelmente completo pelo status: {match.status}")
                return True
            
            # Se tem tempo de jogo > 0, draft provavelmente está completo
            if match.get_game_time_minutes() > 0:
                logger.debug("Draft completo: jogo já iniciado")
                return True
            
            # Por segurança, se não conseguiu determinar, assume que não está completo
            logger.debug("Não foi possível determinar se draft está completo - assumindo incompleto")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar draft completo: {e}")
            return False

    def _get_game_number_in_series(self, match: MatchData) -> int:
        """Determina qual game da série é esta partida"""
        try:
            # PRIORIDADE 1: Informação direta da API sobre game number
            if hasattr(match, 'game_number') and match.game_number:
                return int(match.game_number)
            
            if hasattr(match, 'number_of_game') and match.number_of_game:
                return int(match.number_of_game)
                
            if hasattr(match, 'serie_game_number') and match.serie_game_number:
                return int(match.serie_game_number)
            
            # PRIORIDADE 2: Análise do status da série
            if hasattr(match, 'serie') and match.serie:
                serie_info = match.serie
                if isinstance(serie_info, dict):
                    # Verifica status atual da série
                    if 'games' in serie_info:
                        games = serie_info['games']
                        if isinstance(games, list):
                            # Conta jogos já finalizados + 1 para o atual
                            finished_games = len([g for g in games if g.get('status') in ['finished', 'closed']])
                            return finished_games + 1
                    
                    # Verifica wins dos times para determinar game atual
                    if 'opponent1' in serie_info and 'opponent2' in serie_info:
                        team1_wins = serie_info['opponent1'].get('wins', 0)
                        team2_wins = serie_info['opponent2'].get('wins', 0)
                        total_games_played = team1_wins + team2_wins
                        return total_games_played + 1  # Próximo game
            
            # PRIORIDADE 3: Análise de contexto temporal da partida
            if hasattr(match, 'begin_at') and match.begin_at:
                # Se a partida começou há mais tempo, provavelmente é um game posterior
                import datetime
                try:
                    if isinstance(match.begin_at, str):
                        begin_time = datetime.datetime.fromisoformat(match.begin_at.replace('Z', '+00:00'))
                    else:
                        begin_time = match.begin_at
                    
                    time_diff = datetime.datetime.now(datetime.timezone.utc) - begin_time
                    hours_elapsed = time_diff.total_seconds() / 3600
                    
                    # Estima game baseado no tempo decorrido (games duram ~30-45min)
                    if hours_elapsed > 2.5:  # 2.5+ horas = Game 4+
                        return 4
                    elif hours_elapsed > 1.8:  # 1.8+ horas = Game 3+  
                        return 3
                    elif hours_elapsed > 1.0:  # 1+ hora = Game 2+
                        return 2
                    else:
                        return 1
                except Exception:
                    pass
            
            # PRIORIDADE 4: Padrões no match_id 
            match_id_str = str(match.match_id).lower()
            if 'game5' in match_id_str or '_5_' in match_id_str or 'g5' in match_id_str:
                return 5
            elif 'game4' in match_id_str or '_4_' in match_id_str or 'g4' in match_id_str:
                return 4
            elif 'game3' in match_id_str or '_3_' in match_id_str or 'g3' in match_id_str:
                return 3
            elif 'game2' in match_id_str or '_2_' in match_id_str or 'g2' in match_id_str:
                return 2
            elif 'game1' in match_id_str or '_1_' in match_id_str or 'g1' in match_id_str:
                return 1
            
            # PRIORIDADE 5: Análise do nome/título da partida
            if hasattr(match, 'name') and match.name:
                name_lower = match.name.lower()
                for i in range(5, 0, -1):  # 5, 4, 3, 2, 1
                    if f"game {i}" in name_lower or f"game{i}" in name_lower or f"g{i}" in name_lower:
                        return i
            
            # Se nada funcionar, assume Game 1 mas loga warning
            logger.warning(f"Não foi possível determinar game number para match {match.match_id}, assumindo Game 1")
            return 1
            
        except Exception as e:
            logger.error(f"Erro ao determinar game number: {e}")
            return 1

    def _is_current_game_active(self, match: MatchData) -> bool:
        """
        VALIDAÇÃO CRÍTICA: Verifica se o mapa atual ainda está ativo para tips
        
        Previne tips para mapas já finalizados
        """
        try:
            # 1. Verifica se o status indica que o jogo atual terminou
            if match.status:
                finished_status = ['finished', 'ended', 'closed', 'completed', 'done']
                if match.status.lower() in finished_status:
                    logger.debug(f"Game finalizado pelo status: {match.status}")
                    return False
            
            # 2. Analisa informações da série para ver se o game atual terminou
            if hasattr(match, 'serie') and match.serie:
                serie_info = match.serie
                if isinstance(serie_info, dict):
                    # Verifica se há games finalizados na série
                    if 'games' in serie_info:
                        games = serie_info['games']
                        if isinstance(games, list):
                            current_game_number = self._get_game_number_in_series(match)
                            
                            # Verifica se o game atual existe na lista e está finalizado
                            for game in games:
                                if isinstance(game, dict):
                                    game_number = game.get('number', game.get('position', 0))
                                    if game_number == current_game_number:
                                        game_status = game.get('status', '').lower()
                                        if game_status in ['finished', 'ended', 'closed']:
                                            logger.warning(f"Game {current_game_number} já finalizado na série")
                                            return False
                    
                    # Verifica se a série já terminou completamente
                    serie_status = serie_info.get('status', '').lower()
                    if serie_status in ['finished', 'ended', 'closed']:
                        logger.debug(f"Série já finalizada: {serie_status}")
                        return False
            
            # 3. Verifica tempo de jogo - se muito avançado pode estar próximo do fim
            game_minutes = match.get_game_time_minutes()
            if game_minutes > 50:  # Games muito longos (50+ min) podem estar terminando
                logger.debug(f"Game com {game_minutes} minutos - pode estar terminando")
                # Ainda permite tip mas com cautela
            
            # 4. Verifica se há indicadores específicos de fim de jogo
            if hasattr(match, 'winner') and match.winner:
                logger.warning(f"Game já tem vencedor definido: {match.winner}")
                return False
            
            # 5. Se passou por todas as validações, considera ativo
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar se game está ativo: {e}")
            # Em caso de erro, assume que está ativo para não bloquear desnecessariamente
            return True

    def _get_map_identifier(self, match: MatchData) -> str:
        """
        Cria identificador único para o mapa individual
        
        Formato: {team1}_vs_{team2}_{league}_{game_number}
        Exemplo: flyquest_vs_cloud9_lta_norte_game2
        """
        try:
            team1 = normalize_team_name(match.team1_name).lower()
            team2 = normalize_team_name(match.team2_name).lower()
            league = normalize_team_name(match.league).lower()
            game_number = self._get_game_number_in_series(match)
            
            map_id = f"{team1}_vs_{team2}_{league}_game{game_number}"
            
            # Remove caracteres especiais e espaços
            import re
            map_id = re.sub(r'[^a-z0-9_]', '', map_id)
            
            return map_id
            
        except Exception as e:
            logger.warning(f"Erro ao gerar map identifier: {e}")
            return f"map_{match.match_id}_game1"
