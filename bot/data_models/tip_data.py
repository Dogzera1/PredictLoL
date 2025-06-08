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
    """
    Tip profissional melhorada com experiência premium para usuários
    
    Inclui informações detalhadas, explicações didáticas e alertas importantes
    para proporcionar a melhor experiência possível ao apostador.
    """
    # Dados básicos da partida (OBRIGATÓRIOS)
    match_id: str
    team_a: str
    team_b: str
    league: str
    tournament: str
    
    # Dados da tip principal (OBRIGATÓRIOS)
    tip_on_team: str
    odds: float
    units: float
    risk_level: str
    
    # Análise e métricas (OBRIGATÓRIAS)
    confidence_percentage: float
    ev_percentage: float
    analysis_reasoning: str
    
    # Informações de contexto de jogo (OBRIGATÓRIAS)
    game_time_at_tip: str
    game_time_seconds: int
    
    # Metadados técnicos (OBRIGATÓRIOS)
    prediction_source: str
    data_quality_score: float
    
    # Campos com valores padrão
    min_odds: float = 0.0  # Odds mínima recomendada
    map_number: int = 1  # Número do mapa
    match_status: str = "live"  # Status da partida
    
    # Experiência melhorada para usuário
    explanation_text: str = ""  # Explicação didática da tip
    game_situation_text: str = ""  # Situação atual do jogo
    objectives_text: str = ""  # Próximos objetivos importantes
    timing_advice: str = ""  # Conselho de timing
    alerts_text: str = ""  # Alertas importantes
    history_text: str = ""  # Histórico dos times
    
    # Gestão de risco melhorada
    unit_value: float = 10.0  # Valor de uma unidade em R$
    bet_amount: float = 0.0  # Valor recomendado da aposta
    
    # Metadados adicionais
    tip_id: str = ""  # ID único da tip
    generated_time: str = ""  # Hora de geração
    
    # Campos legados mantidos para compatibilidade
    tip_type: str = "ML"  # Moneyline (ML), outros tipos no futuro
    timestamp: int = field(default_factory=get_current_timestamp)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Status da tip
    status: str = "active"  # active, settled, cancelled
    result: Optional[str] = None  # win, loss, push
    settled_at: Optional[datetime] = None
    profit_loss: float = 0.0
    actual_odds: Optional[float] = None
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.bet_amount == 0.0:
            self.bet_amount = self.units * self.unit_value
        
        if not self.tip_id:
            import time
            self.tip_id = f"TIP{int(time.time())}"
        
        if not self.generated_time:
            from datetime import datetime
            self.generated_time = datetime.now().strftime("%H:%M")
        
        # Calcula odds mínima se não fornecida (5% abaixo da atual)
        if self.min_odds == 0.0:
            self.min_odds = round(self.odds * 0.95, 2)
        
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
        
        # Formata número do mapa
        game_info = f"Game {self.map_number}" if self.map_number > 1 else "Game 1"
        
        message = f"""🔥 **TIP PROFISSIONAL LoL** 🔥

🎮 **{self.team_a} vs {self.team_b}** 
🏆 **Liga:** {self.league}
🗺️ **Mapa:** {game_info}
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
            "actual_odds": self.actual_odds,
            "min_odds": self.min_odds,
            "explanation_text": self.explanation_text,
            "game_situation_text": self.game_situation_text,
            "objectives_text": self.objectives_text,
            "timing_advice": self.timing_advice,
            "alerts_text": self.alerts_text,
            "history_text": self.history_text,
            "unit_value": self.unit_value,
            "bet_amount": self.bet_amount,
            "tip_id": self.tip_id,
            "generated_time": self.generated_time
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
            tournament=data["tournament"],
            tip_type=data.get("tip_type", "ML"),
            game_time_seconds=data["game_time_seconds"],
            timestamp=data.get("timestamp", get_current_timestamp()),
            created_at=created_at,
            prediction_source=data["prediction_source"],
            data_quality_score=data["data_quality_score"],
            status=data["status"],
            result=data["result"],
            settled_at=settled_at,
            profit_loss=data["profit_loss"],
            actual_odds=data["actual_odds"],
            min_odds=data.get("min_odds", 0.0),
            explanation_text=data.get("explanation_text", ""),
            game_situation_text=data.get("game_situation_text", ""),
            objectives_text=data.get("objectives_text", ""),
            timing_advice=data.get("timing_advice", ""),
            alerts_text=data.get("alerts_text", ""),
            history_text=data.get("history_text", ""),
            unit_value=data.get("unit_value", 10.0),
            bet_amount=data.get("bet_amount", 0.0),
            tip_id=data.get("tip_id", ""),
            generated_time=data.get("generated_time", "")
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
            value = getattr(self, field)
            # Para campos numéricos, verifica se não é None; para strings, verifica se não está vazio
            if field in ["odds", "units", "confidence_percentage", "ev_percentage"]:
                if value is None:
                    return False, f"Campo obrigatório ausente: {field}"
            else:
                if not value:
                    return False, f"Campo obrigatório ausente: {field}"
        
        # CORREÇÃO: Usa threshold configurável das constantes
        from ..utils.constants import PREDICTION_THRESHOLDS
        min_confidence = PREDICTION_THRESHOLDS["min_confidence"] * 100  # Converte para %
        if self.confidence_percentage < min_confidence:
            return False, f"Confiança muito baixa: {self.confidence_percentage}% (mín: {min_confidence}%)"
        
        min_ev = PREDICTION_THRESHOLDS["min_ev"] * 100  # Converte para %
        if self.ev_percentage < min_ev:
            return False, f"EV muito baixo: {self.ev_percentage}% (mín: {min_ev}%)"
        
        # NOVO: Validação de qualidade dos dados - ajustada para aceitar dados básicos
        min_quality = PREDICTION_THRESHOLDS.get("min_data_quality", 0.05)  # 5% como padrão
        if self.data_quality_score < min_quality:
            return False, f"Qualidade dos dados insuficiente: {self.data_quality_score:.1%} (mín: {min_quality:.1%})"
        
        if self.odds < 1.15 or self.odds > 6.0:  # Range expandido
            return False, f"Odds fora do range aceitável: {self.odds}"
        
        if self.units < 0.5 or self.units > 5.0:
            return False, f"Unidades fora do range: {self.units}"
        
        # Verifica se análise tem conteúdo suficiente
        if len(self.analysis_reasoning) < 20:  # Reduzido para permitir análises mais curtas
            return False, "Análise muito curta"
        
        return True, "Tip válida" 
