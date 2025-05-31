"""
Modelo de dados para tips profissionais
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

from ..utils.helpers import format_odds, calculate_percentage, get_current_timestamp


@dataclass
class ProfessionalTip:
    """Tip profissional de League of Legends"""
    
    # Identificação da partida (OBRIGATÓRIOS)
    match_id: str
    team_a: str
    team_b: str
    league: str
    tip_on_team: str  # Nome do time apostado (ex: "Team A ML")
    odds: float
    units: float
    risk_level: str  # "Risco Baixo", "Risco Médio", etc.
    confidence_percentage: float  # 0-100
    ev_percentage: float  # Expected Value em %
    analysis_reasoning: str
    game_time_at_tip: str  # ex: "25min"
    
    # Campos opcionais com valores padrão
    tournament: str = ""
    tip_type: str = "ML"  # Moneyline (ML), outros tipos no futuro
    game_time_seconds: int = 0
    timestamp: int = field(default_factory=get_current_timestamp)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Metadados da análise
    prediction_source: str = "ML"  # "ML", "Algorithm", "Hybrid"
    data_quality_score: float = 0.0  # 0-1
    
    # Dados brutos para referência
    match_data_snapshot: Dict = field(default_factory=dict)
    analysis_data: Dict = field(default_factory=dict)
    
    # Status da tip
    status: str = "active"  # "active", "won", "lost", "void"
    result: Optional[str] = None  # "win", "loss", "void"
    settled_at: Optional[datetime] = None
    
    # Performance tracking
    profit_loss: float = 0.0  # Em unidades
    actual_odds: Optional[float] = None  # Odds reais quando apostado
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        # Garante que tip_on_team tem formato correto
        if not self.tip_on_team.endswith(" ML"):
            self.tip_on_team = f"{self.tip_on_team} ML"
    
    def get_formatted_odds(self) -> str:
        """Retorna odds formatada para exibição"""
        return format_odds(self.odds)
    
    def get_formatted_confidence(self) -> str:
        """Retorna confiança formatada"""
        return f"{self.confidence_percentage:.1f}%"
    
    def get_formatted_ev(self) -> str:
        """Retorna EV formatado"""
        return f"+{self.ev_percentage:.1f}%"
    
    def get_risk_emoji(self) -> str:
        """Retorna emoji baseado no nível de risco"""
        risk_emojis = {
            "Risco Muito Alto": "🔥",
            "Risco Alto": "⚡",
            "Risco Médio-Alto": "📈",
            "Risco Médio": "📊",
            "Risco Baixo": "🎯",
            "Risco Mínimo": "💡"
        }
        return risk_emojis.get(self.risk_level, "📊")
    
    def format_telegram_message(self) -> str:
        """Formata tip para mensagem do Telegram"""
        risk_emoji = self.get_risk_emoji()
        
        message = f"""🔥 **TIP PROFISSIONAL LoL** 🔥

🎮 **{self.team_a} vs {self.team_b}**
🏆 **Liga:** {self.league}
⚡ **Tip:** {self.tip_on_team}
💰 **Odds:** {self.get_formatted_odds()}
📊 **Unidades:** {self.units} ({self.risk_level}) {risk_emoji}
⏰ **Tempo:** {self.game_time_at_tip}

📈 **Análise:**
{self.analysis_reasoning}

🎯 **EV:** {self.get_formatted_ev()} | **Confiança:** {self.get_formatted_confidence()}

🤖 **Fonte:** {self.prediction_source} | **Qualidade:** {self.data_quality_score:.1%}"""
        
        return message
    
    def calculate_potential_profit(self, bet_amount: float) -> float:
        """
        Calcula lucro potencial baseado no valor apostado
        
        Args:
            bet_amount: Valor apostado
            
        Returns:
            Lucro potencial se ganhar
        """
        return bet_amount * (self.odds - 1)
    
    def calculate_expected_value_absolute(self, bet_amount: float) -> float:
        """
        Calcula Expected Value absoluto
        
        Args:
            bet_amount: Valor apostado
            
        Returns:
            EV em valor absoluto
        """
        win_probability = self.confidence_percentage / 100
        return (win_probability * self.calculate_potential_profit(bet_amount)) - ((1 - win_probability) * bet_amount)
    
    def settle_tip(self, result: str, actual_odds: Optional[float] = None) -> None:
        """
        Resolve a tip com o resultado final
        
        Args:
            result: "win", "loss", ou "void"
            actual_odds: Odds reais se diferentes da prevista
        """
        self.result = result
        self.status = "won" if result == "win" else "lost" if result == "loss" else "void"
        self.settled_at = datetime.now()
        
        if actual_odds:
            self.actual_odds = actual_odds
        else:
            self.actual_odds = self.odds
        
        # Calcula profit/loss em unidades
        if result == "win":
            self.profit_loss = self.units * (self.actual_odds - 1)
        elif result == "loss":
            self.profit_loss = -self.units
        else:  # void
            self.profit_loss = 0.0
    
    def get_age_minutes(self) -> int:
        """Retorna idade da tip em minutos"""
        now = datetime.now()
        diff = now - self.created_at
        return int(diff.total_seconds() / 60)
    
    def is_recent(self, max_age_minutes: int = 30) -> bool:
        """Verifica se a tip é recente"""
        return self.get_age_minutes() <= max_age_minutes
    
    def to_dict(self) -> Dict:
        """Converte tip para dicionário"""
        return {
            "match_id": self.match_id,
            "team_a": self.team_a,
            "team_b": self.team_b,
            "league": self.league,
            "tournament": self.tournament,
            "tip_on_team": self.tip_on_team,
            "tip_type": self.tip_type,
            "odds": self.odds,
            "units": self.units,
            "risk_level": self.risk_level,
            "confidence_percentage": self.confidence_percentage,
            "ev_percentage": self.ev_percentage,
            "analysis_reasoning": self.analysis_reasoning,
            "game_time_at_tip": self.game_time_at_tip,
            "game_time_seconds": self.game_time_seconds,
            "timestamp": self.timestamp,
            "created_at": self.created_at.isoformat(),
            "prediction_source": self.prediction_source,
            "data_quality_score": self.data_quality_score,
            "status": self.status,
            "result": self.result,
            "settled_at": self.settled_at.isoformat() if self.settled_at else None,
            "profit_loss": self.profit_loss,
            "actual_odds": self.actual_odds
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> ProfessionalTip:
        """Cria tip a partir de dicionário"""
        # Converte strings datetime de volta para objetos
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        settled_at = datetime.fromisoformat(data["settled_at"]) if data.get("settled_at") else None
        
        tip = cls(
            match_id=data["match_id"],
            team_a=data["team_a"],
            team_b=data["team_b"],
            league=data["league"],
            tip_on_team=data["tip_on_team"],
            odds=data["odds"],
            units=data["units"],
            risk_level=data["risk_level"],
            confidence_percentage=data["confidence_percentage"],
            ev_percentage=data["ev_percentage"],
            analysis_reasoning=data["analysis_reasoning"],
            game_time_at_tip=data["game_time_at_tip"],
            tournament=data.get("tournament", ""),
            tip_type=data.get("tip_type", "ML"),
            game_time_seconds=data.get("game_time_seconds", 0),
            timestamp=data.get("timestamp", get_current_timestamp()),
            created_at=created_at,
            prediction_source=data.get("prediction_source", "ML"),
            data_quality_score=data.get("data_quality_score", 0.0),
            status=data.get("status", "active"),
            result=data.get("result"),
            settled_at=settled_at,
            profit_loss=data.get("profit_loss", 0.0),
            actual_odds=data.get("actual_odds")
        )
        
        return tip
    
    def get_summary(self) -> str:
        """Retorna resumo curto da tip"""
        status_emoji = "✅" if self.status == "won" else "❌" if self.status == "lost" else "⏳"
        return f"{status_emoji} {self.team_a} vs {self.team_b} ({self.league}) - {self.tip_on_team} @ {self.get_formatted_odds()} - {self.units}u"
    
    def validate(self) -> tuple[bool, str]:
        """
        Valida se a tip atende critérios profissionais
        
        Returns:
            Tupla (é_válida, mensagem_erro)
        """
        # Verifica campos obrigatórios
        required_fields = [
            "match_id", "team_a", "team_b", "league", "tip_on_team",
            "odds", "units", "confidence_percentage", "ev_percentage"
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                return False, f"Campo obrigatório ausente: {field}"
        
        # Verifica valores mínimos
        if self.confidence_percentage < 60:
            return False, f"Confiança muito baixa: {self.confidence_percentage}%"
        
        if self.ev_percentage < 3:
            return False, f"EV muito baixo: {self.ev_percentage}%"
        
        if self.odds < 1.20 or self.odds > 4.0:
            return False, f"Odds fora do range aceitável: {self.odds}"
        
        if self.units < 0.5 or self.units > 5.0:
            return False, f"Unidades fora do range: {self.units}"
        
        # Verifica se análise tem conteúdo suficiente
        if len(self.analysis_reasoning) < 50:
            return False, "Análise muito curta"
        
        return True, "Tip válida" 