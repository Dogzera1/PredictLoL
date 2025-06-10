#!/usr/bin/env python3
"""
Pre-Game Analyzer para Apostas LoL
Sistema de análise automatizada com dados históricos

Funcionalidades:
- Análise automática de performance histórica
- Cálculo de probabilidades baseado em dados
- Análise de meta e patches
- Head-to-head histórico automatizado
- Form analysis com tendências
- Integração com outros sistemas
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import math

# Logger local simples
class SimpleLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

logger = SimpleLogger()


class AnalysisConfidence(Enum):
    """Níveis de confiança da análise"""
    VERY_HIGH = "very_high"    # 90%+ dados disponíveis
    HIGH = "high"              # 70-89% dados
    MEDIUM = "medium"          # 50-69% dados
    LOW = "low"               # 30-49% dados
    VERY_LOW = "very_low"     # <30% dados


class PredictionQuality(Enum):
    """Qualidade da predição"""
    EXCELLENT = "excellent"    # Múltiplos indicadores convergem
    GOOD = "good"             # Maioria dos indicadores convergem
    MODERATE = "moderate"     # Indicadores mistos
    POOR = "poor"            # Indicadores conflitantes


@dataclass
class MatchResult:
    """Resultado de uma partida histórica"""
    date: str
    team1: str
    team2: str
    winner: str
    duration_minutes: int
    patch: str
    league: str
    importance: str  # "regular", "playoffs", "final"
    team1_kills: int = 0
    team2_kills: int = 0
    team1_towers: int = 0
    team2_towers: int = 0


@dataclass
class TeamStats:
    """Estatísticas de um time"""
    name: str
    league: str
    
    # Record básico
    wins: int = 0
    losses: int = 0
    
    # Estatísticas de jogo
    avg_game_duration: float = 0.0
    avg_kills_per_game: float = 0.0
    avg_deaths_per_game: float = 0.0
    kill_death_ratio: float = 0.0
    
    # Meta e estilo
    early_game_strength: float = 0.0  # 0-1
    late_game_strength: float = 0.0   # 0-1
    teamfight_rating: float = 0.0     # 0-1
    macro_rating: float = 0.0         # 0-1
    
    # Form recente
    last_5_games: List[str] = None    # ["W", "L", "W", "W", "L"]
    form_trend: str = "stable"        # "improving", "declining", "stable"
    
    # Contexto
    roster_stability: float = 1.0     # 0-1 (1 = sem mudanças)
    patch_adaptation: float = 0.5     # 0-1
    
    def __post_init__(self):
        if self.last_5_games is None:
            self.last_5_games = []
    
    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return (self.wins / total) if total > 0 else 0.0
    
    @property
    def recent_form_score(self) -> float:
        if not self.last_5_games:
            return 0.5
        wins = self.last_5_games.count("W")
        return wins / len(self.last_5_games)


@dataclass
class HeadToHeadStats:
    """Estatísticas head-to-head entre dois times"""
    team1: str
    team2: str
    team1_wins: int
    team2_wins: int
    total_games: int
    avg_game_duration: float
    last_meeting_date: str
    recent_trend: str  # "team1_favored", "team2_favored", "even"
    
    @property
    def team1_win_rate(self) -> float:
        return (self.team1_wins / self.total_games) if self.total_games > 0 else 0.5
    
    @property
    def team2_win_rate(self) -> float:
        return (self.team2_wins / self.total_games) if self.total_games > 0 else 0.5


@dataclass
class PreGameAnalysis:
    """Análise pré-jogo completa"""
    id: str
    date: datetime
    team1: str
    team2: str
    league: str
    
    # Estatísticas dos times
    team1_stats: TeamStats
    team2_stats: TeamStats
    head_to_head: HeadToHeadStats
    
    # Análise de contexto
    patch_impact: str
    match_importance: str
    
    # Predições calculadas
    team1_win_probability: float
    team2_win_probability: float
    confidence_level: float
    prediction_quality: str
    
    # Fatores de análise
    key_factors: List[str]
    risk_factors: List[str]
    value_opportunities: List[str]
    
    # Recomendação final
    recommended_bet: Optional[str] = None
    reasoning: str = ""


class PreGameAnalyzer:
    """
    Sistema de Análise Pré-Jogo Automatizada
    
    Funcionalidades principais:
    - Análise automática de dados históricos
    - Cálculo de probabilidades baseado em estatísticas
    - Análise de form e tendências
    - Head-to-head automatizado
    - Integração com outros sistemas
    """
    
    def __init__(self, 
                 data_file: str = "bot/data/personal_betting/pre_game_data.json",
                 bankroll_manager=None,
                 value_analyzer=None):
        """
        Inicializa o Pre-Game Analyzer
        
        Args:
            data_file: Arquivo para dados históricos
            bankroll_manager: Instance do bankroll manager
            value_analyzer: Instance do value analyzer
        """
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        self.bankroll_manager = bankroll_manager
        self.value_analyzer = value_analyzer
        
        # Cria diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Dados históricos
        self.historical_results: List[MatchResult] = []
        self.team_stats: Dict[str, TeamStats] = {}
        self.analyses: List[PreGameAnalysis] = []
        
        # Carrega dados existentes
        self._load_data()
        self._initialize_sample_data()
        
        logger.info(f"Pre-Game Analyzer inicializado - {len(self.historical_results)} partidas históricas")
    
    def analyze_upcoming_match(self,
                             team1: str,
                             team2: str,
                             league: str,
                             match_importance: str = "regular",
                             patch: str = "current") -> PreGameAnalysis:
        """
        Analisa uma partida futura baseado em dados históricos
        
        Args:
            team1: Nome do time 1
            team2: Nome do time 2
            league: Liga da partida
            match_importance: Importância ("regular", "playoffs", "final")
            patch: Patch atual
            
        Returns:
            Análise completa pré-jogo
        """
        try:
            # Cria ID único
            analysis_id = f"pregame_{int(datetime.now().timestamp())}"
            
            # Atualiza estatísticas dos times
            self._update_team_stats()
            
            # Obtém stats dos times
            team1_stats = self.team_stats.get(team1, self._create_default_team_stats(team1, league))
            team2_stats = self.team_stats.get(team2, self._create_default_team_stats(team2, league))
            
            # Calcula head-to-head
            h2h_stats = self._calculate_head_to_head(team1, team2)
            
            # Calcula probabilidades
            team1_prob, team2_prob = self._calculate_win_probabilities(
                team1_stats, team2_stats, h2h_stats, match_importance
            )
            
            # Determina confiança e qualidade
            confidence = self._calculate_confidence(team1_stats, team2_stats, h2h_stats)
            quality = self._determine_prediction_quality(confidence, team1_stats, team2_stats)
            
            # Análise de fatores
            key_factors = self._identify_key_factors(team1_stats, team2_stats, h2h_stats)
            risk_factors = self._identify_risk_factors(team1_stats, team2_stats, match_importance)
            value_opps = self._identify_value_opportunities(team1_prob, team2_prob, confidence)
            
            # Recomendação
            recommendation = self._generate_recommendation(
                team1, team2, team1_prob, team2_prob, confidence, key_factors
            )
            
            # Cria análise
            analysis = PreGameAnalysis(
                id=analysis_id,
                date=datetime.now(),
                team1=team1,
                team2=team2,
                league=league,
                team1_stats=team1_stats,
                team2_stats=team2_stats,
                head_to_head=h2h_stats,
                patch_impact=self._analyze_patch_impact(patch, team1_stats, team2_stats),
                match_importance=match_importance,
                team1_win_probability=team1_prob,
                team2_win_probability=team2_prob,
                confidence_level=confidence,
                prediction_quality=quality,
                key_factors=key_factors,
                risk_factors=risk_factors,
                value_opportunities=value_opps,
                recommended_bet=recommendation['bet'] if recommendation['recommended'] else None,
                reasoning=recommendation['reasoning']
            )
            
            # Adiciona à lista
            self.analyses.append(analysis)
            self._save_data()
            
            logger.info(f"Análise pré-jogo criada: {team1} vs {team2} - {team1_prob:.1%} probabilidade")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar partida: {e}")
            raise
    
    def generate_pre_game_report(self, analysis: PreGameAnalysis) -> str:
        """Gera relatório formatado da análise pré-jogo"""
        try:
            report = f"""
🤖 ANÁLISE PRÉ-JOGO AUTOMATIZADA
{'='*60}

🎮 PARTIDA: {analysis.team1} vs {analysis.team2}
🏆 Liga: {analysis.league}
📅 Análise: {analysis.date.strftime('%d/%m/%Y %H:%M')}
⭐ Importância: {analysis.match_importance.title()}

📊 PROBABILIDADES CALCULADAS
{'-'*40}
🟦 {analysis.team1}: {analysis.team1_win_probability:.1%}
🟥 {analysis.team2}: {analysis.team2_win_probability:.1%}

📈 Confiança: {analysis.confidence_level:.1%}
🎯 Qualidade: {analysis.prediction_quality.title()}

📋 ESTATÍSTICAS DOS TIMES
{'-'*40}

🟦 {analysis.team1}:
   Record: {analysis.team1_stats.wins}W-{analysis.team1_stats.losses}L ({analysis.team1_stats.win_rate:.1%})
   Form recente: {' '.join(analysis.team1_stats.last_5_games[-5:])} ({analysis.team1_stats.recent_form_score:.1%})
   Tendência: {analysis.team1_stats.form_trend.title()}
   KDA: {analysis.team1_stats.kill_death_ratio:.2f}
   Força early game: {analysis.team1_stats.early_game_strength:.1%}
   Força late game: {analysis.team1_stats.late_game_strength:.1%}

🟥 {analysis.team2}:
   Record: {analysis.team2_stats.wins}W-{analysis.team2_stats.losses}L ({analysis.team2_stats.win_rate:.1%})
   Form recente: {' '.join(analysis.team2_stats.last_5_games[-5:])} ({analysis.team2_stats.recent_form_score:.1%})
   Tendência: {analysis.team2_stats.form_trend.title()}
   KDA: {analysis.team2_stats.kill_death_ratio:.2f}
   Força early game: {analysis.team2_stats.early_game_strength:.1%}
   Força late game: {analysis.team2_stats.late_game_strength:.1%}

⚔️ HEAD-TO-HEAD
{'-'*40}
Histórico: {analysis.head_to_head.team1_wins}-{analysis.head_to_head.team2_wins} ({analysis.head_to_head.total_games} jogos)
{analysis.team1}: {analysis.head_to_head.team1_win_rate:.1%} | {analysis.team2}: {analysis.head_to_head.team2_win_rate:.1%}
Tendência recente: {analysis.head_to_head.recent_trend.replace('_', ' ').title()}
Último confronto: {analysis.head_to_head.last_meeting_date}

🔍 FATORES CHAVE
{'-'*40}"""
            
            for factor in analysis.key_factors:
                report += f"\n   ✅ {factor}"
            
            if analysis.risk_factors:
                report += f"\n\n⚠️ FATORES DE RISCO\n{'-'*40}"
                for risk in analysis.risk_factors:
                    report += f"\n   ⚠️ {risk}"
            
            if analysis.value_opportunities:
                report += f"\n\n💎 OPORTUNIDADES DE VALUE\n{'-'*40}"
                for opp in analysis.value_opportunities:
                    report += f"\n   💎 {opp}"
            
            report += f"\n\n🎯 RECOMENDAÇÃO\n{'-'*40}"
            if analysis.recommended_bet:
                report += f"\n✅ APOSTA RECOMENDADA: {analysis.recommended_bet}"
            else:
                report += f"\n❌ NENHUMA APOSTA RECOMENDADA"
            
            report += f"\n\n📝 REASONING:\n{analysis.reasoning}"
            
            report += f"\n\n🔄 IMPACTO DO PATCH\n{'-'*40}"
            report += f"{analysis.patch_impact}"
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return f"Erro ao gerar relatório: {e}"
    
    def compare_with_manual_analysis(self, 
                                   pre_game_analysis: PreGameAnalysis,
                                   manual_analysis=None) -> Dict:
        """Compara análise automatizada com análise manual"""
        try:
            if not manual_analysis and self.value_analyzer:
                # Tenta encontrar análise manual recente
                recent_analyses = [a for a in self.value_analyzer.analyses 
                                 if a.team1.name == pre_game_analysis.team1 
                                 or a.team1.name == pre_game_analysis.team2]
                manual_analysis = recent_analyses[-1] if recent_analyses else None
            
            if not manual_analysis:
                return {"error": "Nenhuma análise manual disponível para comparação"}
            
            # Extrai probabilidades manuais
            manual_team1_prob = manual_analysis.your_probability_team1
            manual_team2_prob = 1 - manual_team1_prob
            
            # Calcula diferenças
            prob_diff_team1 = abs(pre_game_analysis.team1_win_probability - manual_team1_prob)
            prob_diff_team2 = abs(pre_game_analysis.team2_win_probability - manual_team2_prob)
            
            # Determina convergência
            convergence = "high" if max(prob_diff_team1, prob_diff_team2) < 0.1 else \
                         "medium" if max(prob_diff_team1, prob_diff_team2) < 0.2 else "low"
            
            comparison = {
                "convergence_level": convergence,
                "probability_differences": {
                    "team1": prob_diff_team1,
                    "team2": prob_diff_team2
                },
                "automated_analysis": {
                    "team1_prob": pre_game_analysis.team1_win_probability,
                    "team2_prob": pre_game_analysis.team2_win_probability,
                    "confidence": pre_game_analysis.confidence_level
                },
                "manual_analysis": {
                    "team1_prob": manual_team1_prob,
                    "team2_prob": manual_team2_prob,
                    "confidence": manual_analysis.confidence_level / 100
                },
                "recommendation": self._generate_combined_recommendation(
                    pre_game_analysis, manual_analysis, convergence
                )
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Erro ao comparar análises: {e}")
            return {"error": str(e)}
    
    def add_match_result(self, result: MatchResult):
        """Adiciona resultado de partida ao histórico"""
        try:
            self.historical_results.append(result)
            self._save_data()
            logger.info(f"Resultado adicionado: {result.team1} vs {result.team2} - Vencedor: {result.winner}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar resultado: {e}")
    
    def get_team_analysis_summary(self, team: str, days: int = 30) -> Dict:
        """Obtém resumo da análise de um time"""
        try:
            if team not in self.team_stats:
                return {"error": f"Time {team} não encontrado na base de dados"}
            
            stats = self.team_stats[team]
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Partidas recentes
            recent_matches = [r for r in self.historical_results 
                            if (r.team1 == team or r.team2 == team) 
                            and datetime.fromisoformat(r.date) >= cutoff_date]
            
            recent_wins = len([r for r in recent_matches 
                             if r.winner == team])
            
            # Análises recentes
            recent_analyses = [a for a in self.analyses 
                             if (a.team1 == team or a.team2 == team)
                             and a.date >= cutoff_date]
            
            return {
                "team": team,
                "period_days": days,
                "overall_stats": {
                    "record": f"{stats.wins}W-{stats.losses}L",
                    "win_rate": stats.win_rate,
                    "recent_form": stats.last_5_games,
                    "form_score": stats.recent_form_score,
                    "form_trend": stats.form_trend
                },
                "recent_performance": {
                    "matches_played": len(recent_matches),
                    "wins": recent_wins,
                    "win_rate": recent_wins / len(recent_matches) if recent_matches else 0
                },
                "strengths": self._identify_team_strengths(stats),
                "weaknesses": self._identify_team_weaknesses(stats),
                "predictions_made": len(recent_analyses),
                "game_style": {
                    "early_game": stats.early_game_strength,
                    "late_game": stats.late_game_strength,
                    "teamfight": stats.teamfight_rating,
                    "macro": stats.macro_rating
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo do time: {e}")
            return {"error": str(e)}
    
    def _calculate_win_probabilities(self, 
                                   team1_stats: TeamStats, 
                                   team2_stats: TeamStats,
                                   h2h_stats: HeadToHeadStats,
                                   importance: str) -> Tuple[float, float]:
        """Calcula probabilidades de vitória baseado em múltiplos fatores"""
        try:
            # Peso dos fatores
            weights = {
                'overall_performance': 0.3,
                'recent_form': 0.25,
                'head_to_head': 0.2,
                'game_style': 0.15,
                'context': 0.1
            }
            
            # 1. Performance geral
            wr_diff = team1_stats.win_rate - team2_stats.win_rate
            overall_score = 0.5 + (wr_diff * 0.5)  # Normaliza entre 0 e 1
            
            # 2. Form recente
            form_diff = team1_stats.recent_form_score - team2_stats.recent_form_score
            form_score = 0.5 + (form_diff * 0.5)
            
            # 3. Head-to-head
            h2h_score = h2h_stats.team1_win_rate if h2h_stats.total_games >= 3 else 0.5
            
            # 4. Estilo de jogo (média das forças)
            team1_style = (team1_stats.early_game_strength + team1_stats.late_game_strength + 
                          team1_stats.teamfight_rating + team1_stats.macro_rating) / 4
            team2_style = (team2_stats.early_game_strength + team2_stats.late_game_strength + 
                          team2_stats.teamfight_rating + team2_stats.macro_rating) / 4
            style_score = team1_style / (team1_style + team2_style) if (team1_style + team2_style) > 0 else 0.5
            
            # 5. Contexto (importância da partida favorece experiência)
            context_score = 0.5
            if importance in ["playoffs", "final"]:
                # Times com mais vitórias tendem a ter mais experiência
                if team1_stats.wins > team2_stats.wins:
                    context_score = 0.55
                elif team2_stats.wins > team1_stats.wins:
                    context_score = 0.45
            
            # Combina todos os fatores
            team1_prob = (
                weights['overall_performance'] * overall_score +
                weights['recent_form'] * form_score +
                weights['head_to_head'] * h2h_score +
                weights['game_style'] * style_score +
                weights['context'] * context_score
            )
            
            # Garante que está entre 0.1 e 0.9
            team1_prob = max(0.1, min(0.9, team1_prob))
            team2_prob = 1 - team1_prob
            
            return team1_prob, team2_prob
            
        except Exception as e:
            logger.error(f"Erro ao calcular probabilidades: {e}")
            return 0.5, 0.5
    
    def _calculate_confidence(self, 
                            team1_stats: TeamStats, 
                            team2_stats: TeamStats,
                            h2h_stats: HeadToHeadStats) -> float:
        """Calcula nível de confiança da análise"""
        try:
            confidence_factors = []
            
            # Dados disponíveis
            total_games = team1_stats.wins + team1_stats.losses + team2_stats.wins + team2_stats.losses
            if total_games >= 20:
                confidence_factors.append(0.9)
            elif total_games >= 10:
                confidence_factors.append(0.7)
            else:
                confidence_factors.append(0.4)
            
            # Head-to-head
            if h2h_stats.total_games >= 5:
                confidence_factors.append(0.8)
            elif h2h_stats.total_games >= 2:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.3)
            
            # Form recente
            if len(team1_stats.last_5_games) >= 5 and len(team2_stats.last_5_games) >= 5:
                confidence_factors.append(0.8)
            elif len(team1_stats.last_5_games) >= 3 and len(team2_stats.last_5_games) >= 3:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.4)
            
            # Estabilidade do roster
            roster_factor = (team1_stats.roster_stability + team2_stats.roster_stability) / 2
            confidence_factors.append(roster_factor)
            
            return sum(confidence_factors) / len(confidence_factors)
            
        except Exception as e:
            logger.error(f"Erro ao calcular confiança: {e}")
            return 0.5
    
    def _initialize_sample_data(self):
        """Inicializa dados de exemplo se não existirem"""
        if not self.historical_results:
            logger.info("Inicializando dados de exemplo...")
            self._create_sample_historical_data()
    
    def _create_sample_historical_data(self):
        """Cria dados históricos de exemplo"""
        # Times principais de cada liga
        teams_data = {
            "LCK": [
                ("T1", 18, 2, ["W", "W", "W", "L", "W"], "improving"),
                ("Gen.G", 15, 5, ["W", "L", "W", "W", "L"], "stable"),
                ("KT", 12, 8, ["L", "W", "L", "W", "W"], "improving"),
                ("DRX", 10, 10, ["L", "L", "W", "L", "W"], "declining"),
                ("HLE", 8, 12, ["L", "W", "L", "L", "L"], "declining")
            ],
            "LEC": [
                ("G2", 16, 4, ["W", "W", "L", "W", "W"], "stable"),
                ("FNC", 14, 6, ["W", "W", "W", "L", "W"], "improving"),
                ("MAD", 11, 9, ["L", "W", "W", "L", "W"], "stable"),
                ("VIT", 9, 11, ["W", "L", "L", "W", "L"], "declining"),
                ("BDS", 7, 13, ["L", "L", "W", "L", "L"], "declining")
            ],
            "LCS": [
                ("100T", 17, 3, ["W", "W", "W", "W", "L"], "stable"),
                ("TL", 13, 7, ["W", "L", "W", "W", "W"], "improving"),
                ("C9", 12, 8, ["L", "W", "W", "L", "W"], "stable"),
                ("FLY", 10, 10, ["W", "L", "L", "W", "L"], "declining"),
                ("TSM", 6, 14, ["L", "L", "L", "W", "L"], "declining")
            ],
            "LPL": [
                ("JDG", 19, 1, ["W", "W", "W", "W", "W"], "stable"),
                ("BLG", 16, 4, ["W", "W", "L", "W", "W"], "stable"),
                ("WBG", 14, 6, ["W", "L", "W", "W", "L"], "improving"),
                ("TES", 11, 9, ["L", "W", "L", "W", "W"], "stable"),
                ("IG", 8, 12, ["L", "L", "W", "L", "L"], "declining")
            ]
        }
        
        # Cria estatísticas dos times
        for league, teams in teams_data.items():
            for team_name, wins, losses, form, trend in teams:
                # Cria stats baseadas no record
                wr = wins / (wins + losses)
                
                self.team_stats[team_name] = TeamStats(
                    name=team_name,
                    league=league,
                    wins=wins,
                    losses=losses,
                    avg_game_duration=28 + (wr * 10),  # Times melhores tendem a fechar jogos mais rápido
                    avg_kills_per_game=15 + (wr * 8),
                    avg_deaths_per_game=12 + ((1-wr) * 6),
                    kill_death_ratio=0.8 + (wr * 0.6),
                    early_game_strength=0.3 + (wr * 0.4),
                    late_game_strength=0.4 + (wr * 0.3),
                    teamfight_rating=0.4 + (wr * 0.4),
                    macro_rating=0.3 + (wr * 0.5),
                    last_5_games=form,
                    form_trend=trend,
                    roster_stability=0.9 if wr > 0.7 else 0.8,
                    patch_adaptation=0.4 + (wr * 0.3)
                )
        
        # Cria alguns resultados históricos
        sample_results = [
            MatchResult(
                date=(datetime.now() - timedelta(days=i)).isoformat(),
                team1="T1", team2="Gen.G", winner="T1",
                duration_minutes=32, patch="14.1", league="LCK",
                importance="regular", team1_kills=18, team2_kills=12,
                team1_towers=11, team2_towers=3
            ) for i in range(1, 6)
        ]
        
        self.historical_results.extend(sample_results)
        logger.info(f"Dados de exemplo criados: {len(self.team_stats)} times, {len(self.historical_results)} partidas")
    
    def _load_data(self):
        """Carrega dados do arquivo"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Carrega resultados históricos
                    if 'historical_results' in data:
                        self.historical_results = [
                            MatchResult(**result) for result in data['historical_results']
                        ]
                    
                    # Carrega stats dos times
                    if 'team_stats' in data:
                        self.team_stats = {
                            name: TeamStats(**stats) 
                            for name, stats in data['team_stats'].items()
                        }
                    
                    # Carrega análises
                    if 'analyses' in data:
                        for analysis_data in data['analyses']:
                            analysis_data['date'] = datetime.fromisoformat(analysis_data['date'])
                            analysis_data['team1_stats'] = TeamStats(**analysis_data['team1_stats'])
                            analysis_data['team2_stats'] = TeamStats(**analysis_data['team2_stats'])
                            analysis_data['head_to_head'] = HeadToHeadStats(**analysis_data['head_to_head'])
                            self.analyses.append(PreGameAnalysis(**analysis_data))
                
                logger.info(f"Dados carregados do arquivo")
                
        except Exception as e:
            logger.warning(f"Erro ao carregar dados: {e}")
    
    def _save_data(self):
        """Salva dados no arquivo"""
        try:
            data = {
                'historical_results': [asdict(result) for result in self.historical_results],
                'team_stats': {name: asdict(stats) for name, stats in self.team_stats.items()},
                'analyses': []
            }
            
            # Salva análises
            for analysis in self.analyses:
                analysis_dict = asdict(analysis)
                analysis_dict['date'] = analysis.date.isoformat()
                data['analyses'].append(analysis_dict)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
    
    def _update_team_stats(self):
        """Atualiza estatísticas dos times baseado em resultados recentes"""
        try:
            # Atualiza stats baseado nos últimos 30 dias
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for team_name in self.team_stats:
                recent_matches = [r for r in self.historical_results 
                               if (r.team1 == team_name or r.team2 == team_name)
                               and datetime.fromisoformat(r.date) >= cutoff_date]
                
                if recent_matches:
                    # Atualiza form recente
                    recent_results = []
                    for match in recent_matches[-5:]:  # Últimas 5 partidas
                        if match.winner == team_name:
                            recent_results.append("W")
                        else:
                            recent_results.append("L")
                    
                    self.team_stats[team_name].last_5_games = recent_results
                    
                    # Atualiza tendência
                    if len(recent_results) >= 3:
                        recent_wins = recent_results[-3:].count("W")
                        if recent_wins >= 2:
                            self.team_stats[team_name].form_trend = "improving"
                        elif recent_wins <= 1:
                            self.team_stats[team_name].form_trend = "declining"
                        else:
                            self.team_stats[team_name].form_trend = "stable"
            
        except Exception as e:
            logger.error(f"Erro ao atualizar stats: {e}")
    
    def _create_default_team_stats(self, team_name: str, league: str) -> TeamStats:
        """Cria stats padrão para um time não conhecido"""
        return TeamStats(
            name=team_name,
            league=league,
            wins=10,
            losses=10,
            avg_game_duration=30.0,
            avg_kills_per_game=15.0,
            avg_deaths_per_game=15.0,
            kill_death_ratio=1.0,
            early_game_strength=0.5,
            late_game_strength=0.5,
            teamfight_rating=0.5,
            macro_rating=0.5,
            last_5_games=["W", "L", "W", "L", "W"],
            form_trend="stable",
            roster_stability=0.8,
            patch_adaptation=0.5
        )
    
    def _calculate_head_to_head(self, team1: str, team2: str) -> HeadToHeadStats:
        """Calcula estatísticas head-to-head entre dois times"""
        try:
            h2h_matches = [r for r in self.historical_results 
                          if (r.team1 == team1 and r.team2 == team2) 
                          or (r.team1 == team2 and r.team2 == team1)]
            
            if not h2h_matches:
                return HeadToHeadStats(
                    team1=team1, team2=team2,
                    team1_wins=0, team2_wins=0, total_games=0,
                    avg_game_duration=30.0, last_meeting_date="Nunca",
                    recent_trend="even"
                )
            
            team1_wins = len([m for m in h2h_matches if m.winner == team1])
            team2_wins = len([m for m in h2h_matches if m.winner == team2])
            
            avg_duration = sum(m.duration_minutes for m in h2h_matches) / len(h2h_matches)
            last_meeting = max(h2h_matches, key=lambda x: x.date).date
            
            # Determina tendência recente (últimas 3 partidas)
            recent_matches = sorted(h2h_matches, key=lambda x: x.date)[-3:]
            recent_team1_wins = len([m for m in recent_matches if m.winner == team1])
            
            if recent_team1_wins >= 2:
                trend = "team1_favored"
            elif recent_team1_wins <= 1:
                trend = "team2_favored"
            else:
                trend = "even"
            
            return HeadToHeadStats(
                team1=team1, team2=team2,
                team1_wins=team1_wins, team2_wins=team2_wins,
                total_games=len(h2h_matches),
                avg_game_duration=avg_duration,
                last_meeting_date=last_meeting,
                recent_trend=trend
            )
            
        except Exception as e:
            logger.error(f"Erro ao calcular H2H: {e}")
            return HeadToHeadStats(
                team1=team1, team2=team2,
                team1_wins=0, team2_wins=0, total_games=0,
                avg_game_duration=30.0, last_meeting_date="Erro",
                recent_trend="even"
            )
    
    def _determine_prediction_quality(self, confidence: float, 
                                    team1_stats: TeamStats, 
                                    team2_stats: TeamStats) -> str:
        """Determina qualidade da predição"""
        try:
            # Fatores de qualidade
            quality_score = confidence
            
            # Penaliza se times têm poucos jogos
            total_games = (team1_stats.wins + team1_stats.losses + 
                          team2_stats.wins + team2_stats.losses)
            if total_games < 20:
                quality_score *= 0.8
            
            # Penaliza se form é muito volátil
            if (team1_stats.form_trend == "volatile" or 
                team2_stats.form_trend == "volatile"):
                quality_score *= 0.9
            
            # Bônus para alta estabilidade de roster
            avg_stability = (team1_stats.roster_stability + team2_stats.roster_stability) / 2
            quality_score *= (0.9 + avg_stability * 0.1)
            
            if quality_score >= 0.8:
                return "excellent"
            elif quality_score >= 0.6:
                return "good"
            elif quality_score >= 0.4:
                return "moderate"
            else:
                return "poor"
                
        except Exception as e:
            logger.error(f"Erro ao determinar qualidade: {e}")
            return "moderate"
    
    def _identify_key_factors(self, team1_stats: TeamStats, 
                            team2_stats: TeamStats,
                            h2h_stats: HeadToHeadStats) -> List[str]:
        """Identifica fatores chave para a análise"""
        factors = []
        
        try:
            # Diferença significativa de win rate
            wr_diff = abs(team1_stats.win_rate - team2_stats.win_rate)
            if wr_diff > 0.2:
                better_team = team1_stats.name if team1_stats.win_rate > team2_stats.win_rate else team2_stats.name
                factors.append(f"{better_team} tem win rate significativamente superior ({wr_diff:.1%} diferença)")
            
            # Form recente
            form_diff = abs(team1_stats.recent_form_score - team2_stats.recent_form_score)
            if form_diff > 0.4:
                better_form = team1_stats.name if team1_stats.recent_form_score > team2_stats.recent_form_score else team2_stats.name
                factors.append(f"{better_form} em forma muito superior recentemente")
            
            # Head-to-head dominance
            if h2h_stats.total_games >= 3:
                if h2h_stats.team1_win_rate >= 0.7:
                    factors.append(f"{team1_stats.name} domina o H2H ({h2h_stats.team1_wins}-{h2h_stats.team2_wins})")
                elif h2h_stats.team2_win_rate >= 0.7:
                    factors.append(f"{team2_stats.name} domina o H2H ({h2h_stats.team2_wins}-{h2h_stats.team1_wins})")
            
            # Estilos de jogo complementares
            if abs(team1_stats.early_game_strength - team2_stats.late_game_strength) > 0.3:
                factors.append("Estilos de jogo contrastantes - early vs late game")
            
            # Tendências de form
            if team1_stats.form_trend == "improving" and team2_stats.form_trend == "declining":
                factors.append(f"{team1_stats.name} melhorando enquanto {team2_stats.name} declina")
            elif team2_stats.form_trend == "improving" and team1_stats.form_trend == "declining":
                factors.append(f"{team2_stats.name} melhorando enquanto {team1_stats.name} declina")
            
            return factors[:5]  # Máximo 5 fatores
            
        except Exception as e:
            logger.error(f"Erro ao identificar fatores chave: {e}")
            return ["Erro na análise de fatores"]
    
    def _identify_risk_factors(self, team1_stats: TeamStats, 
                             team2_stats: TeamStats,
                             importance: str) -> List[str]:
        """Identifica fatores de risco"""
        risks = []
        
        try:
            # Instabilidade de roster
            if team1_stats.roster_stability < 0.8 or team2_stats.roster_stability < 0.8:
                risks.append("Mudanças recentes de roster podem afetar performance")
            
            # Poucos dados
            total_games = (team1_stats.wins + team1_stats.losses + 
                          team2_stats.wins + team2_stats.losses)
            if total_games < 20:
                risks.append("Base de dados limitada - menor confiabilidade")
            
            # Volatilidade de form
            if (len(set(team1_stats.last_5_games)) > 2 or 
                len(set(team2_stats.last_5_games)) > 2):
                risks.append("Form volátil recente aumenta incerteza")
            
            # Pressão de playoffs
            if importance in ["playoffs", "final"]:
                risks.append("Pressão de playoffs pode alterar performance esperada")
            
            # Times muito equilibrados
            wr_diff = abs(team1_stats.win_rate - team2_stats.win_rate)
            if wr_diff < 0.1:
                risks.append("Times muito equilibrados - resultado imprevisível")
            
            return risks[:4]  # Máximo 4 riscos
            
        except Exception as e:
            logger.error(f"Erro ao identificar riscos: {e}")
            return ["Erro na análise de riscos"]
    
    def _identify_value_opportunities(self, team1_prob: float, 
                                    team2_prob: float,
                                    confidence: float) -> List[str]:
        """Identifica oportunidades de value"""
        opportunities = []
        
        try:
            # Value baseado em probabilidade vs odds típicas
            if team1_prob > 0.6 and confidence > 0.7:
                opportunities.append(f"Time 1 com alta probabilidade ({team1_prob:.1%}) e boa confiança")
            
            if team2_prob > 0.6 and confidence > 0.7:
                opportunities.append(f"Time 2 com alta probabilidade ({team2_prob:.1%}) e boa confiança")
            
            # Upset potential
            if 0.3 <= team1_prob <= 0.4 and confidence > 0.6:
                opportunities.append("Potencial upset com value no underdog")
            elif 0.3 <= team2_prob <= 0.4 and confidence > 0.6:
                opportunities.append("Potencial upset com value no underdog")
            
            # Alta confiança
            if confidence > 0.8:
                opportunities.append("Alta confiança na análise - boa oportunidade")
            
            return opportunities[:3]  # Máximo 3 oportunidades
            
        except Exception as e:
            logger.error(f"Erro ao identificar oportunidades: {e}")
            return ["Erro na análise de oportunidades"]
    
    def _generate_recommendation(self, team1: str, team2: str,
                               team1_prob: float, team2_prob: float,
                               confidence: float, key_factors: List[str]) -> Dict:
        """Gera recomendação final"""
        try:
            # Critérios para recomendação
            min_prob_threshold = 0.55  # Mínimo 55% probabilidade
            min_confidence = 0.6       # Mínimo 60% confiança
            
            recommendation = {"recommended": False, "bet": None, "reasoning": ""}
            
            if confidence < min_confidence:
                recommendation["reasoning"] = f"Confiança insuficiente ({confidence:.1%} < {min_confidence:.1%})"
                return recommendation
            
            if team1_prob >= min_prob_threshold:
                recommendation["recommended"] = True
                recommendation["bet"] = team1
                recommendation["reasoning"] = f"""
Análise automatizada recomenda {team1}:
• Probabilidade calculada: {team1_prob:.1%}
• Confiança: {confidence:.1%}
• Fatores principais: {', '.join(key_factors[:2])}
"""
            elif team2_prob >= min_prob_threshold:
                recommendation["recommended"] = True
                recommendation["bet"] = team2
                recommendation["reasoning"] = f"""
Análise automatizada recomenda {team2}:
• Probabilidade calculada: {team2_prob:.1%}
• Confiança: {confidence:.1%}
• Fatores principais: {', '.join(key_factors[:2])}
"""
            else:
                recommendation["reasoning"] = f"""
Nenhuma aposta recomendada:
• Probabilidades muito equilibradas ({team1_prob:.1%} vs {team2_prob:.1%})
• Não atende critério mínimo de {min_prob_threshold:.1%}
"""
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendação: {e}")
            return {"recommended": False, "bet": None, "reasoning": "Erro na análise"}
    
    def _analyze_patch_impact(self, patch: str, 
                            team1_stats: TeamStats, 
                            team2_stats: TeamStats) -> str:
        """Analisa impacto do patch"""
        try:
            # Simulação básica de impacto de patch
            team1_adaptation = team1_stats.patch_adaptation
            team2_adaptation = team2_stats.patch_adaptation
            
            if abs(team1_adaptation - team2_adaptation) > 0.2:
                better_team = team1_stats.name if team1_adaptation > team2_adaptation else team2_stats.name
                return f"Patch favorece {better_team} que se adapta melhor às mudanças"
            else:
                return "Patch tem impacto neutro - ambos os times se adaptam similarmente"
                
        except Exception as e:
            logger.error(f"Erro ao analisar patch: {e}")
            return "Análise de patch indisponível"
    
    def _generate_combined_recommendation(self, pre_game: PreGameAnalysis,
                                        manual_analysis, convergence: str) -> Dict:
        """Gera recomendação combinada entre análises automática e manual"""
        try:
            if convergence == "high":
                return {
                    "recommendation": "Strong confidence",
                    "reasoning": "Análises automática e manual convergem - alta confiança na predição"
                }
            elif convergence == "medium":
                return {
                    "recommendation": "Moderate confidence", 
                    "reasoning": "Análises parcialmente convergem - confiança moderada"
                }
            else:
                return {
                    "recommendation": "Low confidence",
                    "reasoning": "Análises divergem significativamente - investigar discrepâncias"
                }
                
        except Exception as e:
            logger.error(f"Erro na recomendação combinada: {e}")
            return {"recommendation": "Error", "reasoning": "Erro no cálculo"}
    
    def _identify_team_strengths(self, stats: TeamStats) -> List[str]:
        """Identifica pontos fortes de um time"""
        strengths = []
        
        if stats.win_rate > 0.7:
            strengths.append("Win rate excelente")
        if stats.recent_form_score > 0.6:
            strengths.append("Boa forma recente")
        if stats.early_game_strength > 0.7:
            strengths.append("Early game forte")
        if stats.late_game_strength > 0.7:
            strengths.append("Late game forte")
        if stats.teamfight_rating > 0.7:
            strengths.append("Teamfights superiores")
        if stats.macro_rating > 0.7:
            strengths.append("Macro game sólido")
            
        return strengths[:3]
    
    def _identify_team_weaknesses(self, stats: TeamStats) -> List[str]:
        """Identifica pontos fracos de um time"""
        weaknesses = []
        
        if stats.win_rate < 0.4:
            weaknesses.append("Win rate baixo")
        if stats.recent_form_score < 0.4:
            weaknesses.append("Forma recente ruim")
        if stats.early_game_strength < 0.3:
            weaknesses.append("Early game fraco")
        if stats.late_game_strength < 0.3:
            weaknesses.append("Problemas no late game")
        if stats.roster_stability < 0.7:
            weaknesses.append("Instabilidade de roster")
            
        return weaknesses[:3]


def create_default_pre_game_analyzer(bankroll_manager=None, value_analyzer=None):
    """Cria analyzer com configurações padrão"""
    return PreGameAnalyzer(
        bankroll_manager=bankroll_manager,
        value_analyzer=value_analyzer
    )


if __name__ == "__main__":
    # Teste básico
    analyzer = create_default_pre_game_analyzer()
    
    print("🚀 Pre-Game Analyzer inicializado")
    
    # Analisa uma partida
    analysis = analyzer.analyze_upcoming_match(
        team1="T1",
        team2="Gen.G", 
        league="LCK",
        match_importance="final"
    )
    
    # Gera relatório
    report = analyzer.generate_pre_game_report(analysis)
    print(report) 