"""
Modelos de dados para partidas de League of Legends
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class TeamStats:
    """Estatísticas de um time durante a partida"""
    
    # Campos obrigatórios
    team_name: str = ""
    
    # Estatísticas principais (com aliases para compatibilidade)
    total_gold: int = 0  # Alias para 'gold'
    total_kills: int = 0  # Alias para 'kills'
    total_cs: int = 0  # Alias para 'cs'
    
    # Outros stats básicos
    deaths: int = 0
    assists: int = 0
    
    # Objetivos
    towers_destroyed: int = 0  # Alias para 'towers'
    dragons_taken: int = 0  # Alias para 'dragons'
    barons_taken: int = 0  # Alias para 'barons'
    heralds_taken: int = 0  # Herald Rift
    inhibitors: int = 0
    
    # Visão
    wards_placed: int = 0
    wards_destroyed: int = 0
    vision_score: int = 0
    
    # Objetivos específicos
    dragon_soul: bool = False
    elder_dragon: bool = False
    baron_buff: bool = False
    
    # Métricas calculadas
    gold_per_minute: float = 0.0
    cs_per_minute: float = 0.0
    kill_participation: float = 0.0
    
    # Properties para compatibilidade com código antigo
    @property
    def gold(self) -> int:
        return self.total_gold
    
    @gold.setter
    def gold(self, value: int):
        self.total_gold = value
    
    @property
    def kills(self) -> int:
        return self.total_kills
    
    @kills.setter
    def kills(self, value: int):
        self.total_kills = value
    
    @property
    def cs(self) -> int:
        return self.total_cs
    
    @cs.setter
    def cs(self, value: int):
        self.total_cs = value
    
    @property
    def towers(self) -> int:
        return self.towers_destroyed
    
    @towers.setter
    def towers(self, value: int):
        self.towers_destroyed = value
    
    @property
    def dragons(self) -> int:
        return self.dragons_taken
    
    @dragons.setter
    def dragons(self, value: int):
        self.dragons_taken = value
    
    @property
    def barons(self) -> int:
        return self.barons_taken
    
    @barons.setter
    def barons(self, value: int):
        self.barons_taken = value
    
    def calculate_derived_stats(self, game_time_minutes: int) -> None:
        """Calcula estatísticas derivadas baseadas no tempo de jogo"""
        if game_time_minutes > 0:
            self.gold_per_minute = self.total_gold / game_time_minutes
            self.cs_per_minute = self.total_cs / game_time_minutes
        
        total_team_kills = max(self.total_kills, 1)  # Evita divisão por zero
        self.kill_participation = (self.total_kills + self.assists) / total_team_kills


@dataclass
class Champion:
    """Informações de um campeão"""
    
    champion_id: str
    champion_name: str
    role: str = ""  # TOP, JUNGLE, MID, ADC, SUPPORT
    player_name: str = ""
    
    # Estatísticas do campeão
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    cs: int = 0
    gold: int = 0
    items: List[str] = field(default_factory=list)


@dataclass
class DraftData:
    """Dados de draft (pick/ban) de uma partida"""
    
    # Picks dos times (podem ser strings ou objetos Champion)
    team1_picks: List[Union[str, Champion]] = field(default_factory=list)
    team2_picks: List[Union[str, Champion]] = field(default_factory=list)
    
    # Bans dos times
    team1_bans: List[str] = field(default_factory=list)
    team2_bans: List[str] = field(default_factory=list)
    
    # Side (qual time joga de azul/vermelho)
    team1_side: str = "blue"  # "blue" ou "red"
    team2_side: str = "red"
    
    # Composições identificadas
    team1_composition_type: str = ""  # ex: "teamfight", "poke", "engage"
    team2_composition_type: str = ""
    
    def get_team_champions(self, team_number: int) -> List[Union[str, Champion]]:
        """Retorna lista de campeões de um time"""
        if team_number == 1:
            return self.team1_picks
        return self.team2_picks
    
    def get_team_champion_names(self, team_number: int) -> List[str]:
        """Retorna lista de nomes dos campeões de um time"""
        picks = self.get_team_champions(team_number)
        names = []
        for pick in picks:
            if isinstance(pick, str):
                names.append(pick)
            elif isinstance(pick, Champion):
                names.append(pick.champion_name)
        return names
    
    def get_team_bans(self, team_number: int) -> List[str]:
        """Retorna lista de bans de um time"""
        if team_number == 1:
            return self.team1_bans
        return self.team2_bans


@dataclass
class GameEvent:
    """Evento ocorrido durante a partida"""
    
    event_type: str  # Tipo do evento
    team: Optional[str] = None  # Time envolvido
    timestamp: int = 0  # Timestamp do evento em segundos
    description: str = ""
    impact_score: float = 0.0  # Impacto do evento (0-10)
    
    # Dados específicos do evento
    event_data: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Gera descrição automática se não fornecida"""
        if not self.description:
            if self.team:
                self.description = f"{self.event_type} por {self.team}"
            else:
                self.description = self.event_type


@dataclass
class MatchData:
    """Dados completos de uma partida"""
    
    # Identificação básica (OBRIGATÓRIOS)
    match_id: str
    team1_name: str
    team2_name: str
    league: str
    status: str  # "live", "inprogress", "ongoing", "finished", "scheduled"
    
    # Campos opcionais com valores padrão
    tournament: str = ""
    team1_code: str = ""
    team2_code: str = ""
    game_number: int = 1  # Número do jogo em uma série
    series_type: str = "BO1"  # BO1, BO3, BO5
    
    # Tempo
    start_time: Optional[datetime] = None
    game_time_seconds: int = 0
    last_update: Optional[datetime] = None
    
    # Estatísticas dos times
    team1_stats: Optional[TeamStats] = None
    team2_stats: Optional[TeamStats] = None
    
    # Draft
    draft_data: Optional[DraftData] = None
    
    # Eventos da partida
    events: List[GameEvent] = field(default_factory=list)
    
    # Dados da API original (para referência)
    raw_data: Dict = field(default_factory=dict)
    
    # Análise calculada
    gold_difference: int = 0
    kill_difference: int = 0
    tower_difference: int = 0
    favored_team: str = ""  # "team1" ou "team2"
    
    # Metadados
    data_quality_score: float = 0.0  # 0-1, qualidade dos dados
    has_complete_draft: bool = False
    has_live_stats: bool = False
    
    def __post_init__(self):
        """Inicializa dados calculados após criação"""
        if self.team1_stats and self.team2_stats:
            self.calculate_differences()
            self.determine_favored_team()
    
    def calculate_differences(self) -> None:
        """Calcula diferenças entre os times"""
        if not self.team1_stats or not self.team2_stats:
            return
        
        self.gold_difference = self.team1_stats.total_gold - self.team2_stats.total_gold
        self.kill_difference = self.team1_stats.total_kills - self.team2_stats.total_kills
        self.tower_difference = self.team1_stats.towers_destroyed - self.team2_stats.towers_destroyed
    
    def determine_favored_team(self) -> None:
        """Determina qual time está favorito baseado nas estatísticas"""
        if not self.team1_stats or not self.team2_stats:
            return
        
        # Score simples baseado em ouro, kills e torres
        team1_score = (
            self.team1_stats.total_gold * 0.5 +
            self.team1_stats.total_kills * 1000 +
            self.team1_stats.towers_destroyed * 2000 +
            self.team1_stats.dragons_taken * 1500 +
            self.team1_stats.barons_taken * 3000
        )
        
        team2_score = (
            self.team2_stats.total_gold * 0.5 +
            self.team2_stats.total_kills * 1000 +
            self.team2_stats.towers_destroyed * 2000 +
            self.team2_stats.dragons_taken * 1500 +
            self.team2_stats.barons_taken * 3000
        )
        
        if team1_score > team2_score:
            self.favored_team = "team1"
        elif team2_score > team1_score:
            self.favored_team = "team2"
        else:
            self.favored_team = ""
    
    def get_game_time_minutes(self) -> int:
        """Retorna tempo de jogo em minutos"""
        return self.game_time_seconds // 60
    
    def add_event(self, event: GameEvent) -> None:
        """Adiciona evento à partida"""
        self.events.append(event)
        # Ordena eventos por timestamp
        self.events.sort(key=lambda x: x.timestamp)
    
    def get_recent_events(self, last_minutes: int = 5) -> List[GameEvent]:
        """Retorna eventos recentes"""
        if not self.events:
            return []
        
        cutoff_time = self.game_time_seconds - (last_minutes * 60)
        return [event for event in self.events if event.timestamp >= cutoff_time]
    
    def calculate_data_quality(self) -> float:
        """Calcula score de qualidade dos dados (0-1)"""
        score = 0.0
        max_score = 10.0
        
        # Tem dados básicos dos times
        if self.team1_stats and self.team2_stats:
            score += 3.0
        
        # Tem dados de draft
        if self.draft_data and self.has_complete_draft:
            score += 2.0
        
        # Tem estatísticas live
        if self.has_live_stats:
            score += 2.0
        
        # Tem tempo de jogo válido
        if self.game_time_seconds > 0:
            score += 1.0
        
        # Tem eventos
        if self.events:
            score += 1.0
        
        # Tem identificação completa
        if self.match_id and self.league:
            score += 1.0
        
        self.data_quality_score = min(score / max_score, 1.0)
        return self.data_quality_score
    
    def is_suitable_for_analysis(self) -> bool:
        """Verifica se a partida tem dados suficientes para análise"""
        quality = self.calculate_data_quality()
        
        # Critérios mínimos
        return (
            quality >= 0.6 and
            self.status in ["live", "inprogress", "ongoing"] and
            self.game_time_seconds >= 300  # Pelo menos 5 minutos
        )
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            "match_id": self.match_id,
            "league": self.league,
            "tournament": self.tournament,
            "team1_name": self.team1_name,
            "team2_name": self.team2_name,
            "status": self.status,
            "game_time_seconds": self.game_time_seconds,
            "gold_difference": self.gold_difference,
            "kill_difference": self.kill_difference,
            "favored_team": self.favored_team,
            "data_quality_score": self.data_quality_score,
            "has_complete_draft": self.has_complete_draft,
            "has_live_stats": self.has_live_stats
        }
    
    @classmethod
    def from_api_data(cls, api_data: Dict, api_source: str = "riot") -> MatchData:
        """
        Cria MatchData a partir de dados da API
        
        Args:
            api_data: Dados brutos da API
            api_source: Fonte da API ("riot", "pandascore", "other")
            
        Returns:
            Instância de MatchData
        """
        try:
            if api_source == "riot":
                return cls._from_riot_api_data(api_data)
            elif api_source == "pandascore":
                return cls._from_pandascore_data(api_data)
            else:
                # Implementação genérica
                return cls._from_generic_data(api_data)
        except Exception as e:
            logger.warning(f"Erro ao processar dados da API {api_source}: {e}")
            # Retorna dados básicos com fallbacks
            return cls._create_fallback_match(api_data, api_source)
    
    @classmethod
    def _from_riot_api_data(cls, data: Dict) -> MatchData:
        """Processa dados específicos da Riot API"""
        # Extrai match_id
        match_id = str(data.get("id", data.get("eventId", "unknown")))
        
        # Extrai informações da liga
        league_data = data.get("league", {})
        league_name = "LEC"  # Default para eventos da Riot
        if isinstance(league_data, dict):
            league_name = league_data.get("name", league_data.get("slug", "Liga Desconhecida"))
        elif isinstance(league_data, str):
            league_name = league_data
        
        # Extrai times das matches dentro do evento
        team1_name = "Team A"
        team2_name = "Team B"
        
        # Tenta extrair times de diferentes estruturas possíveis
        if "match" in data:
            match_data = data["match"]
            teams = match_data.get("teams", [])
            if len(teams) >= 2:
                team1_name = teams[0].get("name", teams[0].get("code", "Team A"))
                team2_name = teams[1].get("name", teams[1].get("code", "Team B"))
        
        elif "teams" in data:
            teams = data["teams"]
            if len(teams) >= 2:
                team1_name = teams[0].get("name", teams[0].get("code", "Team A"))
                team2_name = teams[1].get("name", teams[1].get("code", "Team B"))
        
        # Se ainda não encontrou, tenta outras estruturas
        if team1_name == "Team A":
            # Busca em games se disponível
            if "games" in data and data["games"]:
                game = data["games"][0]
                teams = game.get("teams", [])
                if len(teams) >= 2:
                    team1_name = teams[0].get("name", teams[0].get("code", "Team A"))
                    team2_name = teams[1].get("name", teams[1].get("code", "Team B"))
        
        # Status da partida
        status = data.get("state", data.get("status", "live"))
        if status in ["inProgress", "unstarted", "unneeded"]:
            status = "live"
        
        # Tempo de jogo (se disponível)
        game_time = 0
        if "games" in data and data["games"]:
            game = data["games"][0]
            game_time = game.get("gameTime", 0)
        
        return cls(
            match_id=match_id,
            team1_name=team1_name,
            team2_name=team2_name,
            league=league_name,
            status=status,
            tournament=league_name,
            game_time_seconds=game_time,
            raw_data=data
        )
    
    @classmethod
    def _from_pandascore_data(cls, data: Dict) -> MatchData:
        """Processa dados específicos do PandaScore"""
        # Extrai informações básicas
        match_id = str(data.get("id", "unknown"))
        
        # Times
        opponents = data.get("opponents", [])
        team1_name = "Team A"
        team2_name = "Team B"
        
        if len(opponents) >= 2:
            team1_name = opponents[0].get("opponent", {}).get("name", "Team A")
            team2_name = opponents[1].get("opponent", {}).get("name", "Team B")
        
        # Liga
        league_data = data.get("league", {})
        league_name = league_data.get("name", "Liga Desconhecida")
        
        # Tournament
        tournament_data = data.get("tournament", {})
        tournament_name = tournament_data.get("name", league_name)
        
        # Status
        status = data.get("status", "live")
        
        return cls(
            match_id=match_id,
            team1_name=team1_name,
            team2_name=team2_name,
            league=league_name,
            status=status,
            tournament=tournament_name,
            raw_data=data
        )
    
    @classmethod
    def _from_generic_data(cls, data: Dict) -> MatchData:
        """Processa dados de formato genérico"""
        return cls(
            match_id=str(data.get("id", data.get("match_id", "unknown"))),
            team1_name=data.get("team1", {}).get("name", data.get("team1_name", "Team A")),
            team2_name=data.get("team2", {}).get("name", data.get("team2_name", "Team B")),
            league=data.get("league", "Liga Desconhecida"),
            status=data.get("status", "live"),
            raw_data=data
        )
    
    @classmethod
    def _create_fallback_match(cls, data: Dict, api_source: str) -> MatchData:
        """Cria match com dados mínimos quando há erro no processamento"""
        return cls(
            match_id=str(data.get("id", f"fallback_{hash(str(data))}")),
            team1_name="Team A (Dados Incompletos)",
            team2_name="Team B (Dados Incompletos)",
            league=f"Liga Desconhecida ({api_source})",
            status="live",
            raw_data=data
        ) 
