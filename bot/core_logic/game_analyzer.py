from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.constants import (
    CRUCIAL_EVENTS,
    TIMING_SCORES,
    LEAGUE_TIERS,
    VALID_LIVE_STATUSES,
)
from ..utils.helpers import normalize_team_name
from ..utils.logger_config import get_logger
from ..data_models.match_data import MatchData, TeamStats, GameEvent, DraftData

logger = get_logger(__name__)


class GamePhase(Enum):
    """Fases do jogo LoL"""
    EARLY_GAME = "early_game"      # 0-15 min
    MID_GAME = "mid_game"          # 15-30 min
    LATE_GAME = "late_game"        # 30+ min


class EventImportance(Enum):
    """Importância de eventos do jogo"""
    CRITICAL = "critical"     # Dragon Soul, Elder, Baron, Ace
    HIGH = "high"            # Dragão, Torre, Herald
    MEDIUM = "medium"        # Kills, Assists
    LOW = "low"              # CS, Vision


@dataclass
class TeamAdvantage:
    """Vantagem de um time em diferentes aspectos"""
    gold_advantage: float = 0.0          # Vantagem em ouro
    tower_advantage: int = 0             # Vantagem em torres
    dragon_advantage: int = 0            # Vantagem em dragões
    baron_advantage: int = 0             # Vantagem em barons
    kill_advantage: int = 0              # Vantagem em kills
    cs_advantage: float = 0.0            # Vantagem em CS
    vision_advantage: float = 0.0        # Vantagem em visão
    objective_control: float = 0.0       # Controle de objetivos (0-1)
    draft_advantage: float = 0.0         # Vantagem no draft (0-1)
    
    @property
    def overall_advantage(self) -> float:
        """Calcula vantagem geral ponderada"""
        weights = {
            'gold': 0.25,
            'towers': 0.20,
            'dragons': 0.15,
            'baron': 0.15,
            'kills': 0.10,
            'cs': 0.05,
            'vision': 0.05,
            'objectives': 0.05
        }
        
        # Normaliza valores para escala 0-1
        normalized_gold = min(max(self.gold_advantage / 5000, -1), 1)  # ±5k gold = ±100%
        normalized_towers = min(max(self.tower_advantage / 5, -1), 1)  # ±5 torres = ±100%
        normalized_dragons = min(max(self.dragon_advantage / 4, -1), 1)  # ±4 dragões = ±100%
        normalized_baron = min(max(self.baron_advantage / 2, -1), 1)   # ±2 barons = ±100%
        normalized_kills = min(max(self.kill_advantage / 10, -1), 1)   # ±10 kills = ±100%
        normalized_cs = min(max(self.cs_advantage / 50, -1), 1)        # ±50 CS = ±100%
        normalized_vision = min(max(self.vision_advantage, -1), 1)      # Já normalizada
        
        overall = (
            weights['gold'] * normalized_gold +
            weights['towers'] * normalized_towers +
            weights['dragons'] * normalized_dragons +
            weights['baron'] * normalized_baron +
            weights['kills'] * normalized_kills +
            weights['cs'] * normalized_cs +
            weights['vision'] * normalized_vision +
            weights['objectives'] * self.objective_control
        )
        
        return max(min(overall, 1.0), -1.0)  # Clampeia entre -1 e 1


@dataclass
class GameAnalysis:
    """Resultado completo da análise de uma partida"""
    match_id: str
    game_time_seconds: int
    current_phase: GamePhase
    team1_advantage: TeamAdvantage
    team2_advantage: TeamAdvantage
    crucial_events_count: int
    momentum_team: Optional[str] = None     # Time com momentum atual
    confidence_score: float = 0.0          # Confiança na análise (0-1)
    predicted_winner: Optional[str] = None  # Time previsto para ganhar
    win_probability: float = 0.5           # Probabilidade de vitória do team1
    analysis_timestamp: float = 0.0
    
    def __post_init__(self):
        if self.analysis_timestamp == 0.0:
            self.analysis_timestamp = time.time()


class LoLGameAnalyzer:
    """
    Analisador profissional de jogos League of Legends
    
    Características:
    - Análise de draft e composições
    - Tracking de vantagens em tempo real
    - Detecção de eventos cruciais
    - Cálculo de momentum e timing
    - Predição de vencedor baseada em múltiplos fatores
    """

    def __init__(self):
        """Inicializa o analisador"""
        self.champion_win_rates = self._load_champion_data()
        self.match_analyses_cache: Dict[str, GameAnalysis] = {}
        
        logger.info("LoLGameAnalyzer inicializado com sucesso")

    async def analyze_live_match(self, match_data: MatchData) -> GameAnalysis:
        """
        Análise principal de uma partida ao vivo
        
        Args:
            match_data: Dados da partida
            
        Returns:
            Análise completa da partida
        """
        try:
            logger.debug(f"Analisando partida {match_data.match_id}")
            
            # Determina fase do jogo
            game_phase = self._determine_game_phase(match_data.game_time_seconds)
            
            # Analisa vantagens dos times
            team1_advantage = self._calculate_team_advantage(
                match_data.team1_stats, 
                match_data.team2_stats, 
                match_data.draft_data
            )
            
            team2_advantage = self._calculate_team_advantage(
                match_data.team2_stats, 
                match_data.team1_stats, 
                match_data.draft_data,
                perspective_team2=True
            )
            
            # Analisa eventos cruciais
            crucial_events = self._analyze_crucial_events(match_data.events, game_phase)
            
            # Calcula momentum
            momentum_team = self._calculate_momentum(match_data.events, match_data.team1_name, match_data.team2_name)
            
            # Calcula timing score
            timing_score = self._calculate_timing_score(match_data.game_time_seconds, match_data.events)
            
            # Predição de vencedor
            win_probability = self._predict_winner(
                team1_advantage, 
                team2_advantage, 
                game_phase, 
                timing_score
            )
            
            predicted_winner = match_data.team1_name if win_probability > 0.5 else match_data.team2_name
            
            # Confiança na análise
            confidence = self._calculate_confidence(
                match_data.game_time_seconds, 
                crucial_events,
                abs(win_probability - 0.5) * 2  # Converte para 0-1
            )
            
            # Cria análise
            analysis = GameAnalysis(
                match_id=match_data.match_id,
                game_time_seconds=match_data.game_time_seconds,
                current_phase=game_phase,
                team1_advantage=team1_advantage,
                team2_advantage=team2_advantage,
                crucial_events_count=crucial_events,
                momentum_team=momentum_team,
                confidence_score=confidence,
                predicted_winner=predicted_winner,
                win_probability=win_probability
            )
            
            # Cache da análise
            self.match_analyses_cache[match_data.match_id] = analysis
            
            logger.info(f"Análise concluída para {match_data.match_id}: {predicted_winner} ({win_probability:.1%})")
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar partida {match_data.match_id}: {e}")
            # Retorna análise básica em caso de erro
            return GameAnalysis(
                match_id=match_data.match_id,
                game_time_seconds=match_data.game_time_seconds or 0,
                current_phase=GamePhase.EARLY_GAME,
                team1_advantage=TeamAdvantage(),
                team2_advantage=TeamAdvantage(),
                crucial_events_count=0
            )

    def _determine_game_phase(self, game_time_seconds: int) -> GamePhase:
        """Determina a fase atual do jogo"""
        if game_time_seconds < 15 * 60:  # 15 minutos
            return GamePhase.EARLY_GAME
        elif game_time_seconds < 30 * 60:  # 30 minutos
            return GamePhase.MID_GAME
        else:
            return GamePhase.LATE_GAME

    def _calculate_team_advantage(
        self, 
        team_stats: TeamStats, 
        enemy_stats: TeamStats, 
        draft_data: Optional[DraftData],
        perspective_team2: bool = False
    ) -> TeamAdvantage:
        """Calcula vantagens de um time"""
        advantage = TeamAdvantage()
        
        # Vantagem em ouro
        advantage.gold_advantage = team_stats.total_gold - enemy_stats.total_gold
        
        # Vantagem em torres
        advantage.tower_advantage = team_stats.towers_destroyed - enemy_stats.towers_destroyed
        
        # Vantagem em dragões
        advantage.dragon_advantage = team_stats.dragons_taken - enemy_stats.dragons_taken
        
        # Vantagem em barons
        advantage.baron_advantage = team_stats.barons_taken - enemy_stats.barons_taken
        
        # Vantagem em kills
        advantage.kill_advantage = team_stats.total_kills - enemy_stats.total_kills
        
        # Vantagem em CS
        advantage.cs_advantage = team_stats.total_cs - enemy_stats.total_cs
        
        # Vantagem em visão
        advantage.vision_advantage = self._calculate_vision_advantage(team_stats, enemy_stats)
        
        # Controle de objetivos
        advantage.objective_control = self._calculate_objective_control(team_stats, enemy_stats)
        
        # Vantagem no draft
        if draft_data:
            advantage.draft_advantage = self._analyze_draft_advantage(draft_data, perspective_team2)
        
        return advantage

    def _calculate_vision_advantage(self, team_stats: TeamStats, enemy_stats: TeamStats) -> float:
        """Calcula vantagem em visão (normalizada -1 a 1)"""
        team_vision = team_stats.wards_placed + team_stats.wards_destroyed * 0.5
        enemy_vision = enemy_stats.wards_placed + enemy_stats.wards_destroyed * 0.5
        
        if team_vision + enemy_vision == 0:
            return 0.0
        
        return (team_vision - enemy_vision) / (team_vision + enemy_vision)

    def _calculate_objective_control(self, team_stats: TeamStats, enemy_stats: TeamStats) -> float:
        """Calcula controle de objetivos (0 a 1)"""
        team_objectives = (
            team_stats.dragons_taken * 2 +      # Dragões valem 2
            team_stats.barons_taken * 3 +       # Barons valem 3
            team_stats.towers_destroyed +       # Torres valem 1
            team_stats.heralds_taken * 1.5      # Heralds valem 1.5
        )
        
        enemy_objectives = (
            enemy_stats.dragons_taken * 2 +
            enemy_stats.barons_taken * 3 +
            enemy_stats.towers_destroyed +
            enemy_stats.heralds_taken * 1.5
        )
        
        total_objectives = team_objectives + enemy_objectives
        
        if total_objectives == 0:
            return 0.5  # Neutro se nenhum objetivo foi tomado
        
        return team_objectives / total_objectives

    def _analyze_draft_advantage(self, draft_data: DraftData, perspective_team2: bool = False) -> float:
        """Analisa vantagem no draft baseada em win rates e sinergia"""
        if not draft_data or not draft_data.team1_picks or not draft_data.team2_picks:
            return 0.0
        
        team1_score = self._calculate_draft_score(draft_data.team1_picks)
        team2_score = self._calculate_draft_score(draft_data.team2_picks)
        
        # Bônus por sinergia de composição
        team1_synergy = self._calculate_team_synergy(draft_data.team1_picks)
        team2_synergy = self._calculate_team_synergy(draft_data.team2_picks)
        
        team1_total = team1_score + team1_synergy
        team2_total = team2_score + team2_synergy
        
        # Normaliza para -1 a 1
        if team1_total + team2_total == 0:
            advantage = 0.0
        else:
            advantage = (team1_total - team2_total) / (team1_total + team2_total)
        
        # Inverte se é perspectiva do time 2
        return -advantage if perspective_team2 else advantage

    def _calculate_draft_score(self, champions: List[str]) -> float:
        """Calcula score do draft baseado em win rates"""
        if not champions:
            return 0.0
        
        total_score = 0.0
        for champion in champions:
            win_rate = self.champion_win_rates.get(champion.lower(), 0.50)
            total_score += win_rate
        
        return total_score / len(champions)

    def _calculate_team_synergy(self, champions: List[str]) -> float:
        """Calcula sinergia da composição (simplificado)"""
        if len(champions) < 5:
            return 0.0
        
        # Análise simplificada de sinergia baseada em tipos de campeões
        synergy_score = 0.0
        
        # Identifica tipos de composição
        assassins = self._count_champion_type(champions, 'assassin')
        tanks = self._count_champion_type(champions, 'tank')
        adcs = self._count_champion_type(champions, 'adc')
        mages = self._count_champion_type(champions, 'mage')
        supports = self._count_champion_type(champions, 'support')
        
        # Bônus por composição balanceada
        if tanks >= 1 and adcs >= 1 and supports >= 1:
            synergy_score += 0.05  # Comp balanceada
        
        # Bônus por dive comp
        if assassins >= 2 and tanks >= 1:
            synergy_score += 0.03  # Dive comp
        
        # Bônus por protect the carry
        if adcs >= 1 and supports >= 1 and tanks >= 1:
            synergy_score += 0.02  # Protect comp
        
        return synergy_score

    def _count_champion_type(self, champions: List[str], champion_type: str) -> int:
        """Conta campeões de um tipo específico (implementação simplificada)"""
        # Esta seria uma implementação real baseada em dados de campeões
        type_mapping = {
            'assassin': ['zed', 'yasuo', 'katarina', 'akali', 'talon'],
            'tank': ['malphite', 'amumu', 'leona', 'braum', 'alistar'],
            'adc': ['jinx', 'caitlyn', 'vayne', 'ezreal', 'ashe'],
            'mage': ['azir', 'orianna', 'viktor', 'syndra', 'lux'],
            'support': ['thresh', 'nautilus', 'lulu', 'janna', 'soraka']
        }
        
        type_champions = type_mapping.get(champion_type, [])
        count = 0
        
        for champion in champions:
            if champion.lower() in type_champions:
                count += 1
        
        return count

    def _analyze_crucial_events(self, events: List[GameEvent], game_phase: GamePhase) -> int:
        """Analiza eventos cruciais e retorna a contagem"""
        crucial_count = 0
        
        for event in events:
            event_type = event.event_type.upper()
            
            # Eventos sempre cruciais
            if event_type in [CRUCIAL_EVENTS['dragon_soul'], CRUCIAL_EVENTS['elder_dragon'], 
                             CRUCIAL_EVENTS['baron'], CRUCIAL_EVENTS['ace']]:
                crucial_count += 2  # Eventos críticos valem 2
            
            # Eventos importantes por fase
            elif event_type == CRUCIAL_EVENTS['inhibitor']:
                crucial_count += 1
            
            elif event_type == CRUCIAL_EVENTS['nexus_tower']:
                crucial_count += 1
            
            # Teamfights são mais importantes no mid/late game
            elif event_type == CRUCIAL_EVENTS['teamfight'] and game_phase != GamePhase.EARLY_GAME:
                crucial_count += 1
        
        return crucial_count

    def _calculate_momentum(self, events: List[GameEvent], team1_name: str, team2_name: str) -> Optional[str]:
        """Calcula qual time tem momentum baseado em eventos recentes"""
        if not events:
            return None
        
        # Analisa últimos 5 minutos de eventos
        current_time = max(event.timestamp for event in events) if events else 0
        recent_threshold = current_time - 300  # 5 minutos
        
        recent_events = [e for e in events if e.timestamp >= recent_threshold]
        
        if not recent_events:
            return None
        
        team1_score = 0
        team2_score = 0
        
        for event in recent_events:
            if event.team == team1_name:
                weight = self._get_event_weight(event.event_type)
                team1_score += weight
            elif event.team == team2_name:
                weight = self._get_event_weight(event.event_type)
                team2_score += weight
        
        if team1_score > team2_score * 1.5:  # Margem de 50% para considerar momentum
            return team1_name
        elif team2_score > team1_score * 1.5:
            return team2_name
        
        return None

    def _get_event_weight(self, event_type: str) -> float:
        """Retorna peso de um evento para cálculo de momentum"""
        event_weights = {
            'BARON_NASHOR': 5.0,
            'DRAGON_SOUL': 4.0,
            'ELDER_DRAGON': 4.0,
            'ACE': 3.0,
            'DRAGON': 2.0,
            'TOWER_DESTROYED': 1.5,
            'INHIBITOR_DESTROYED': 2.5,
            'HERALD': 1.5,
            'TEAMFIGHT_WIN': 2.0,
            'KILL': 1.0
        }
        
        return event_weights.get(event_type.upper(), 0.5)

    def _calculate_timing_score(self, game_time_seconds: int, events: List[GameEvent]) -> float:
        """Calcula score de timing baseado na fase do jogo e eventos"""
        game_phase = self._determine_game_phase(game_time_seconds)
        
        base_score = TIMING_SCORES[game_phase.value]["weight"]
        
        # Ajusta baseado em eventos importantes
        event_modifier = min(len(events) * 0.01, 0.2)  # Máximo +20%
        
        return min(base_score + event_modifier, 1.0)

    def _predict_winner(
        self, 
        team1_advantage: TeamAdvantage, 
        team2_advantage: TeamAdvantage, 
        game_phase: GamePhase,
        timing_score: float
    ) -> float:
        """Prediz probabilidade de vitória do team1 (0.0 a 1.0)"""
        
        # Vantagem geral dos times
        team1_overall = team1_advantage.overall_advantage
        team2_overall = team2_advantage.overall_advantage
        
        # Diferença de vantagem
        advantage_diff = team1_overall - team2_overall
        
        # Modificadores por fase do jogo
        phase_modifiers = {
            GamePhase.EARLY_GAME: 0.8,   # Early game é menos decisivo
            GamePhase.MID_GAME: 1.0,     # Mid game balanceado
            GamePhase.LATE_GAME: 1.2     # Late game é mais decisivo
        }
        
        phase_modifier = phase_modifiers[game_phase]
        
        # Aplicação de modificadores
        weighted_advantage = advantage_diff * phase_modifier * timing_score
        
        # Converte para probabilidade usando sigmoid
        probability = 0.5 + (weighted_advantage * 0.3)  # Fator de 0.3 para suavizar
        
        return max(0.05, min(0.95, probability))  # Clampeia entre 5% e 95%

    def _calculate_confidence(self, game_time_seconds: int, crucial_events: int, prediction_strength: float) -> float:
        """Calcula confiança na análise"""
        
        # Confiança base por tempo de jogo
        time_confidence = min(game_time_seconds / (20 * 60), 1.0)  # Máximo aos 20 min
        
        # Confiança por eventos cruciais
        events_confidence = min(crucial_events * 0.1, 0.4)  # Máximo 40% por eventos
        
        # Confiança por força da predição
        prediction_confidence = prediction_strength * 0.3  # Máximo 30%
        
        total_confidence = time_confidence * 0.4 + events_confidence + prediction_confidence
        
        return min(max(total_confidence, 0.1), 0.95)  # Entre 10% e 95%

    def _load_champion_data(self) -> Dict[str, float]:
        """Carrega dados de win rate dos campeões (implementação simplificada)"""
        # Em uma implementação real, isso viria de uma API ou database
        return {
            # ADCs
            'jinx': 0.52, 'caitlyn': 0.51, 'vayne': 0.53, 'ezreal': 0.49, 'ashe': 0.50,
            'kaisa': 0.52, 'jhin': 0.51, 'lucian': 0.48, 'sivir': 0.50, 'tristana': 0.51,
            
            # Supports
            'thresh': 0.50, 'nautilus': 0.52, 'leona': 0.51, 'braum': 0.50, 'alistar': 0.49,
            'lulu': 0.51, 'janna': 0.52, 'soraka': 0.50, 'yuumi': 0.48, 'pyke': 0.49,
            
            # Mids
            'azir': 0.48, 'orianna': 0.50, 'viktor': 0.51, 'syndra': 0.49, 'lux': 0.52,
            'yasuo': 0.50, 'zed': 0.49, 'katarina': 0.51, 'akali': 0.48, 'leblanc': 0.49,
            
            # Junglers
            'graves': 0.51, 'kha6': 0.50, 'lee': 0.49, 'elise': 0.48, 'nidalee': 0.47,
            'sejuani': 0.51, 'zac': 0.52, 'amumu': 0.53, 'warwick': 0.52, 'master_yi': 0.50,
            
            # Tops
            'gnar': 0.50, 'camille': 0.51, 'jax': 0.52, 'fiora': 0.49, 'riven': 0.48,
            'malphite': 0.53, 'maokai': 0.52, 'shen': 0.51, 'ornn': 0.50, 'gangplank': 0.47
        }

    def get_match_analysis(self, match_id: str) -> Optional[GameAnalysis]:
        """Recupera análise de uma partida do cache"""
        return self.match_analyses_cache.get(match_id)

    def clear_old_analyses(self, max_age_hours: int = 24) -> None:
        """Remove análises antigas do cache"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        old_analyses = [
            match_id for match_id, analysis in self.match_analyses_cache.items()
            if current_time - analysis.analysis_timestamp > max_age_seconds
        ]
        
        for match_id in old_analyses:
            del self.match_analyses_cache[match_id]
        
        if old_analyses:
            logger.info(f"Removidas {len(old_analyses)} análises antigas do cache")

    def get_analysis_summary(self, analysis: GameAnalysis) -> str:
        """Gera resumo textual da análise"""
        phase_names = {
            GamePhase.EARLY_GAME: "Early Game",
            GamePhase.MID_GAME: "Mid Game",
            GamePhase.LATE_GAME: "Late Game"
        }
        
        minutes = analysis.game_time_seconds // 60
        
        winner_prob = analysis.win_probability if analysis.predicted_winner else 0.5
        
        summary = f"""🎮 **Análise da Partida** ({minutes}min - {phase_names[analysis.current_phase]})

🏆 **Predição:** {analysis.predicted_winner} ({winner_prob:.1%})
📊 **Confiança:** {analysis.confidence_score:.1%}
⚡ **Momentum:** {analysis.momentum_team or 'Neutro'}

📈 **Vantagens Principais:**
• Ouro: {analysis.team1_advantage.gold_advantage:+.0f}
• Torres: {analysis.team1_advantage.tower_advantage:+d}
• Dragões: {analysis.team1_advantage.dragon_advantage:+d}
• Kills: {analysis.team1_advantage.kill_advantage:+d}

🎯 **Score Geral:** {analysis.team1_advantage.overall_advantage:+.1%}
🔥 **Eventos Cruciais:** {analysis.crucial_events_count}"""
        
        return summary 
