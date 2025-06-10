#!/usr/bin/env python3
"""
Betting Tracker para Apostas LoL
Sistema completo de tracking visual e análise de performance

Funcionalidades:
- Dashboard visual de performance
- Gráficos de tendências
- Análise de streaks e padrões
- Tracking por liga, time, período
- Métricas avançadas de performance
- Relatórios exportáveis
- Integração total com bankroll e value analyzer
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

# Logger local simples
class SimpleLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

logger = SimpleLogger()


class PerformanceLevel(Enum):
    """Níveis de performance"""
    EXCELLENT = "excellent"    # ROI > 20%
    GOOD = "good"             # ROI 10-20%
    AVERAGE = "average"       # ROI 0-10%
    POOR = "poor"            # ROI < 0%


class TrendDirection(Enum):
    """Direção da tendência"""
    UPWARD = "upward"         # Melhorando
    DOWNWARD = "downward"     # Piorando
    STABLE = "stable"         # Estável
    VOLATILE = "volatile"     # Volátil


@dataclass
class PerformanceMetrics:
    """Métricas de performance detalhadas"""
    total_bets: int = 0
    won_bets: int = 0
    lost_bets: int = 0
    pending_bets: int = 0
    
    win_rate: float = 0.0
    roi: float = 0.0
    total_staked: float = 0.0
    total_profit: float = 0.0
    
    avg_odds: float = 0.0
    avg_stake: float = 0.0
    avg_confidence: float = 0.0
    avg_ev: float = 0.0
    
    best_streak: int = 0
    worst_streak: int = 0
    current_streak: int = 0
    streak_type: str = "none"  # win/loss/none
    
    bankroll_start: float = 0.0
    bankroll_current: float = 0.0
    bankroll_peak: float = 0.0
    bankroll_low: float = 0.0
    
    performance_level: str = "average"
    trend_direction: str = "stable"


@dataclass
class StreakInfo:
    """Informações sobre sequências"""
    type: str              # "win" ou "loss"
    length: int
    start_date: datetime
    end_date: datetime
    profit: float
    bets: List[str]        # IDs das apostas


class BettingTracker:
    """
    Sistema Completo de Tracking de Apostas
    
    Funcionalidades principais:
    - Dashboard visual completo
    - Análise de performance por múltiplos critérios
    - Tracking de tendências e padrões
    - Geração de gráficos ASCII
    - Relatórios exportáveis
    - Integração com bankroll manager
    """
    
    def __init__(self, 
                 data_file: str = "bot/data/personal_betting/betting_tracker.json",
                 bankroll_manager=None,
                 value_analyzer=None):
        """
        Inicializa o tracking system
        
        Args:
            data_file: Arquivo para persistir dados de tracking
            bankroll_manager: Instance do bankroll manager
            value_analyzer: Instance do value analyzer
        """
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        self.bankroll_manager = bankroll_manager
        self.value_analyzer = value_analyzer
        
        # Cria diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Dados de tracking
        self.tracking_data = {
            'sessions': [],
            'daily_snapshots': [],
            'performance_history': [],
            'streaks': [],
            'league_stats': {},
            'monthly_summary': {}
        }
        
        # Carrega dados existentes
        self._load_data()
        
        logger.info(f"Betting Tracker inicializado")
    
    def generate_dashboard(self, period_days: int = 30) -> str:
        """
        Gera dashboard visual completo
        
        Args:
            period_days: Período para análise
            
        Returns:
            Dashboard formatado
        """
        try:
            metrics = self.calculate_performance_metrics(period_days)
            
            dashboard = f"""
🏆 BETTING TRACKER DASHBOARD
{'='*80}
📅 Período: Últimos {period_days} dias
🕐 Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}

💰 PERFORMANCE GERAL
{self._generate_performance_section(metrics)}

📊 ESTATÍSTICAS DETALHADAS
{self._generate_detailed_stats(metrics)}

📈 GRÁFICO DE BANKROLL
{self._generate_bankroll_chart(period_days)}

🔥 ANÁLISE DE STREAKS
{self._generate_streak_analysis(metrics)}

🏆 PERFORMANCE POR LIGA
{self._generate_league_breakdown()}

📋 TENDÊNCIAS E INSIGHTS
{self._generate_insights(metrics, period_days)}

🎯 RECOMENDAÇÕES
{self._generate_recommendations(metrics)}

{'='*80}
"""
            return dashboard
            
        except Exception as e:
            logger.error(f"Erro ao gerar dashboard: {e}")
            return f"Erro ao gerar dashboard: {e}"
    
    def calculate_performance_metrics(self, period_days: int = 30) -> PerformanceMetrics:
        """Calcula métricas de performance detalhadas"""
        try:
            if not self.bankroll_manager:
                return PerformanceMetrics()
            
            cutoff_date = datetime.now() - timedelta(days=period_days)
            
            # Pega apostas do período
            period_bets = []
            for bet in self.bankroll_manager.bets:
                bet_date = datetime.fromisoformat(bet.date)
                if bet_date >= cutoff_date:
                    period_bets.append(bet)
            
            if not period_bets:
                return PerformanceMetrics()
            
            # Calcula métricas básicas
            total_bets = len(period_bets)
            won_bets = len([b for b in period_bets if b.status == "won"])
            lost_bets = len([b for b in period_bets if b.status == "lost"])
            pending_bets = len([b for b in period_bets if b.status == "pending"])
            
            win_rate = (won_bets / (won_bets + lost_bets) * 100) if (won_bets + lost_bets) > 0 else 0
            
            resolved_bets = [b for b in period_bets if b.status in ["won", "lost"]]
            total_staked = sum(b.amount for b in resolved_bets)
            total_profit = sum(b.profit for b in resolved_bets)
            roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
            
            # Métricas avançadas
            avg_odds = sum(b.odds for b in resolved_bets) / len(resolved_bets) if resolved_bets else 0
            avg_stake = sum(b.amount for b in resolved_bets) / len(resolved_bets) if resolved_bets else 0
            avg_confidence = sum(b.confidence for b in resolved_bets) / len(resolved_bets) if resolved_bets else 0
            avg_ev = sum(b.ev_percentage for b in resolved_bets) / len(resolved_bets) if resolved_bets else 0
            
            # Análise de streaks
            streak_info = self._calculate_streaks(resolved_bets)
            
            # Informações de bankroll
            bankroll_start = self.bankroll_manager.settings.initial_bankroll
            bankroll_current = self.bankroll_manager.settings.current_bankroll
            
            # Determina nível de performance
            performance_level = self._determine_performance_level(roi, win_rate)
            
            # Determina tendência
            trend_direction = self._determine_trend_direction(period_bets)
            
            return PerformanceMetrics(
                total_bets=total_bets,
                won_bets=won_bets,
                lost_bets=lost_bets,
                pending_bets=pending_bets,
                win_rate=win_rate,
                roi=roi,
                total_staked=total_staked,
                total_profit=total_profit,
                avg_odds=avg_odds,
                avg_stake=avg_stake,
                avg_confidence=avg_confidence,
                avg_ev=avg_ev,
                best_streak=streak_info['best_win_streak'],
                worst_streak=streak_info['worst_loss_streak'],
                current_streak=streak_info['current_streak_length'],
                streak_type=streak_info['current_streak_type'],
                bankroll_start=bankroll_start,
                bankroll_current=bankroll_current,
                bankroll_peak=max(bankroll_start, bankroll_current),
                bankroll_low=min(bankroll_start, bankroll_current),
                performance_level=performance_level,
                trend_direction=trend_direction
            )
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {e}")
            return PerformanceMetrics()
    
    def generate_ascii_chart(self, data: List[float], title: str, width: int = 60, height: int = 10) -> str:
        """Gera gráfico ASCII simples"""
        try:
            if not data or len(data) < 2:
                return f"{title}: Dados insuficientes"
            
            # Normaliza dados
            min_val = min(data)
            max_val = max(data)
            
            if max_val == min_val:
                # Dados constantes
                line = "─" * width
                return f"{title}\n{line}"
            
            # Escala os dados
            range_val = max_val - min_val
            scaled_data = [(val - min_val) / range_val for val in data]
            
            # Cria o gráfico
            chart_lines = []
            
            # Linha do título
            chart_lines.append(f"📊 {title}")
            chart_lines.append("┌" + "─" * width + "┐")
            
            # Dados do gráfico
            for i in range(height):
                level = 1 - (i / (height - 1))  # De 1.0 a 0.0
                line = "│"
                
                for j in range(width):
                    data_index = int(j * (len(data) - 1) / (width - 1))
                    if scaled_data[data_index] >= level:
                        line += "█"
                    else:
                        line += " "
                
                line += "│"
                chart_lines.append(line)
            
            # Linha inferior
            chart_lines.append("└" + "─" * width + "┘")
            
            # Legendas
            chart_lines.append(f"Min: {min_val:.2f} | Max: {max_val:.2f} | Atual: {data[-1]:.2f}")
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            return f"Erro ao gerar gráfico: {e}"
    
    def analyze_betting_patterns(self, period_days: int = 90) -> Dict:
        """Analisa padrões de apostas"""
        try:
            if not self.bankroll_manager:
                return {"error": "Bankroll manager não disponível"}
            
            cutoff_date = datetime.now() - timedelta(days=period_days)
            
            period_bets = []
            for bet in self.bankroll_manager.bets:
                bet_date = datetime.fromisoformat(bet.date)
                if bet_date >= cutoff_date and bet.status in ["won", "lost"]:
                    period_bets.append(bet)
            
            if not period_bets:
                return {"message": "Nenhuma aposta no período"}
            
            # Análise por dia da semana
            weekday_stats = {}
            for bet in period_bets:
                bet_date = datetime.fromisoformat(bet.date)
                weekday = bet_date.strftime('%A')
                
                if weekday not in weekday_stats:
                    weekday_stats[weekday] = {'bets': 0, 'wins': 0, 'profit': 0.0}
                
                weekday_stats[weekday]['bets'] += 1
                if bet.status == "won":
                    weekday_stats[weekday]['wins'] += 1
                weekday_stats[weekday]['profit'] += bet.profit
            
            # Calcula win rate por dia
            for day in weekday_stats:
                stats = weekday_stats[day]
                stats['win_rate'] = (stats['wins'] / stats['bets'] * 100) if stats['bets'] > 0 else 0
            
            # Análise por odds range
            odds_ranges = {
                "1.00-1.50": {"bets": 0, "wins": 0, "profit": 0.0},
                "1.51-2.00": {"bets": 0, "wins": 0, "profit": 0.0},
                "2.01-3.00": {"bets": 0, "wins": 0, "profit": 0.0},
                "3.01+": {"bets": 0, "wins": 0, "profit": 0.0}
            }
            
            for bet in period_bets:
                if bet.odds <= 1.50:
                    range_key = "1.00-1.50"
                elif bet.odds <= 2.00:
                    range_key = "1.51-2.00"
                elif bet.odds <= 3.00:
                    range_key = "2.01-3.00"
                else:
                    range_key = "3.01+"
                
                odds_ranges[range_key]['bets'] += 1
                if bet.status == "won":
                    odds_ranges[range_key]['wins'] += 1
                odds_ranges[range_key]['profit'] += bet.profit
            
            # Calcula win rate por range
            for range_key in odds_ranges:
                stats = odds_ranges[range_key]
                stats['win_rate'] = (stats['wins'] / stats['bets'] * 100) if stats['bets'] > 0 else 0
            
            # Análise por size de aposta
            bet_sizes = sorted([bet.amount for bet in period_bets])
            if bet_sizes:
                q1 = bet_sizes[len(bet_sizes)//4]
                q3 = bet_sizes[3*len(bet_sizes)//4]
                
                size_ranges = {
                    f"Pequenas (≤R${q1:.0f})": {"bets": 0, "wins": 0, "profit": 0.0},
                    f"Médias (R${q1:.0f}-R${q3:.0f})": {"bets": 0, "wins": 0, "profit": 0.0},
                    f"Grandes (>R${q3:.0f})": {"bets": 0, "wins": 0, "profit": 0.0}
                }
                
                for bet in period_bets:
                    if bet.amount <= q1:
                        range_key = f"Pequenas (≤R${q1:.0f})"
                    elif bet.amount <= q3:
                        range_key = f"Médias (R${q1:.0f}-R${q3:.0f})"
                    else:
                        range_key = f"Grandes (>R${q3:.0f})"
                    
                    size_ranges[range_key]['bets'] += 1
                    if bet.status == "won":
                        size_ranges[range_key]['wins'] += 1
                    size_ranges[range_key]['profit'] += bet.profit
                
                # Calcula win rate por size
                for range_key in size_ranges:
                    stats = size_ranges[range_key]
                    stats['win_rate'] = (stats['wins'] / stats['bets'] * 100) if stats['bets'] > 0 else 0
            else:
                size_ranges = {}
            
            return {
                "period_days": period_days,
                "total_bets_analyzed": len(period_bets),
                "weekday_performance": weekday_stats,
                "odds_range_performance": odds_ranges,
                "bet_size_performance": size_ranges
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar padrões: {e}")
            return {"error": str(e)}
    
    def export_performance_report(self, period_days: int = 30, format_type: str = "detailed") -> str:
        """Exporta relatório de performance completo"""
        try:
            metrics = self.calculate_performance_metrics(period_days)
            patterns = self.analyze_betting_patterns(period_days)
            
            if format_type == "summary":
                return self._generate_summary_report(metrics, period_days)
            else:
                return self._generate_detailed_report(metrics, patterns, period_days)
                
        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            return f"Erro ao exportar relatório: {e}"
    
    def track_session(self, session_name: str = None) -> Dict:
        """Inicia tracking de uma sessão de apostas"""
        try:
            session_id = f"session_{int(datetime.now().timestamp())}"
            session_name = session_name or f"Sessão {datetime.now().strftime('%d/%m %H:%M')}"
            
            session = {
                'id': session_id,
                'name': session_name,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'bets_placed': [],
                'starting_bankroll': self.bankroll_manager.settings.current_bankroll if self.bankroll_manager else 0,
                'ending_bankroll': None,
                'session_profit': 0.0,
                'bets_count': 0,
                'wins': 0,
                'active': True
            }
            
            self.tracking_data['sessions'].append(session)
            self._save_data()
            
            logger.info(f"Sessão iniciada: {session_name}")
            
            return {
                "success": True,
                "session_id": session_id,
                "session_name": session_name,
                "message": f"Sessão '{session_name}' iniciada"
            }
            
        except Exception as e:
            logger.error(f"Erro ao iniciar sessão: {e}")
            return {"success": False, "error": str(e)}
    
    def end_session(self, session_id: str) -> Dict:
        """Finaliza uma sessão de tracking"""
        try:
            session = None
            for s in self.tracking_data['sessions']:
                if s['id'] == session_id and s['active']:
                    session = s
                    break
            
            if not session:
                return {"success": False, "error": "Sessão não encontrada ou já finalizada"}
            
            session['end_time'] = datetime.now().isoformat()
            session['ending_bankroll'] = self.bankroll_manager.settings.current_bankroll if self.bankroll_manager else 0
            session['session_profit'] = session['ending_bankroll'] - session['starting_bankroll']
            session['active'] = False
            
            self._save_data()
            
            logger.info(f"Sessão finalizada: {session['name']}")
            
            return {
                "success": True,
                "session_summary": {
                    "name": session['name'],
                    "duration": self._calculate_session_duration(session),
                    "bets_placed": session['bets_count'],
                    "wins": session['wins'],
                    "win_rate": (session['wins'] / session['bets_count'] * 100) if session['bets_count'] > 0 else 0,
                    "profit": session['session_profit']
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao finalizar sessão: {e}")
            return {"success": False, "error": str(e)}
    
    def create_daily_snapshot(self) -> Dict:
        """Cria snapshot diário do estado"""
        try:
            today = datetime.now().date().isoformat()
            
            # Remove snapshot do dia se já existir
            self.tracking_data['daily_snapshots'] = [
                s for s in self.tracking_data['daily_snapshots'] 
                if s['date'] != today
            ]
            
            metrics = self.calculate_performance_metrics(1)  # Últimas 24h
            
            snapshot = {
                'date': today,
                'bankroll': self.bankroll_manager.settings.current_bankroll if self.bankroll_manager else 0,
                'daily_bets': metrics.total_bets,
                'daily_profit': metrics.total_profit,
                'daily_win_rate': metrics.win_rate,
                'cumulative_roi': metrics.roi
            }
            
            self.tracking_data['daily_snapshots'].append(snapshot)
            
            # Mantém apenas últimos 90 dias
            cutoff_date = (datetime.now() - timedelta(days=90)).date().isoformat()
            self.tracking_data['daily_snapshots'] = [
                s for s in self.tracking_data['daily_snapshots']
                if s['date'] >= cutoff_date
            ]
            
            self._save_data()
            
            return {"success": True, "snapshot": snapshot}
            
        except Exception as e:
            logger.error(f"Erro ao criar snapshot: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_performance_section(self, metrics: PerformanceMetrics) -> str:
        """Gera seção de performance do dashboard"""
        # Emojis baseados na performance
        performance_emoji = {
            "excellent": "🚀",
            "good": "📈", 
            "average": "📊",
            "poor": "📉"
        }
        
        trend_emoji = {
            "upward": "⬆️",
            "downward": "⬇️", 
            "stable": "➡️",
            "volatile": "🔄"
        }
        
        emoji = performance_emoji.get(metrics.performance_level, "📊")
        trend = trend_emoji.get(metrics.trend_direction, "➡️")
        
        bankroll_change = metrics.bankroll_current - metrics.bankroll_start
        bankroll_change_pct = (bankroll_change / metrics.bankroll_start * 100) if metrics.bankroll_start > 0 else 0
        
        return f"""
💰 Bankroll: R$ {metrics.bankroll_current:.2f} ({bankroll_change_pct:+.1f}%)
📊 Total de Apostas: {metrics.total_bets} ({metrics.won_bets}W-{metrics.lost_bets}L-{metrics.pending_bets}P)
🏆 Win Rate: {metrics.win_rate:.1f}%
📈 ROI: {metrics.roi:+.2f}% {emoji}
💵 Lucro Total: R$ {metrics.total_profit:+.2f}
📊 Tendência: {metrics.trend_direction.title()} {trend}

🔥 Streak Atual: {metrics.current_streak} {metrics.streak_type}s
⭐ Melhor Streak: {metrics.best_streak} vitórias
💔 Pior Streak: {metrics.worst_streak} derrotas"""
    
    def _generate_detailed_stats(self, metrics: PerformanceMetrics) -> str:
        """Gera estatísticas detalhadas"""
        return f"""
📊 Odds Média: {metrics.avg_odds:.2f}
💰 Stake Média: R$ {metrics.avg_stake:.2f}
🎯 Confiança Média: {metrics.avg_confidence:.1f}%
📈 EV Médio: {metrics.avg_ev:+.2f}%

💳 Bankroll Inicial: R$ {metrics.bankroll_start:.2f}
📊 Bankroll Atual: R$ {metrics.bankroll_current:.2f}
🚀 Bankroll Máximo: R$ {metrics.bankroll_peak:.2f}
📉 Bankroll Mínimo: R$ {metrics.bankroll_low:.2f}"""
    
    def _generate_bankroll_chart(self, period_days: int) -> str:
        """Gera gráfico de evolução do bankroll"""
        try:
            # Pega snapshots do período
            cutoff_date = (datetime.now() - timedelta(days=period_days)).date().isoformat()
            
            snapshots = [
                s for s in self.tracking_data['daily_snapshots']
                if s['date'] >= cutoff_date
            ]
            
            if len(snapshots) < 2:
                return "Dados insuficientes para gráfico (mín. 2 dias)"
            
            # Extrai valores do bankroll
            bankroll_values = [s['bankroll'] for s in snapshots]
            
            return self.generate_ascii_chart(
                bankroll_values, 
                f"Evolução do Bankroll ({len(snapshots)} dias)",
                width=50,
                height=8
            )
            
        except Exception as e:
            return f"Erro ao gerar gráfico: {e}"
    
    def _generate_streak_analysis(self, metrics: PerformanceMetrics) -> str:
        """Gera análise de streaks"""
        if metrics.current_streak == 0:
            streak_status = "Nenhuma streak ativa"
        else:
            streak_status = f"{metrics.current_streak} {metrics.streak_type}s consecutiva{'s' if metrics.current_streak > 1 else ''}"
        
        return f"""
🔥 Status Atual: {streak_status}
⭐ Record de Vitórias: {metrics.best_streak} consecutivas
💔 Record de Derrotas: {metrics.worst_streak} consecutivas

📊 Análise de Sequências:
   • Consistência: {'Alta' if metrics.best_streak >= 5 else 'Moderada' if metrics.best_streak >= 3 else 'Baixa'}
   • Controle de Risco: {'Bom' if metrics.worst_streak <= 3 else 'Moderado' if metrics.worst_streak <= 5 else 'Precisa Melhorar'}"""
    
    def _generate_league_breakdown(self) -> str:
        """Gera breakdown por liga"""
        try:
            if not self.bankroll_manager:
                return "Dados não disponíveis"
            
            league_stats = {}
            
            for bet in self.bankroll_manager.bets:
                if bet.status in ["won", "lost"]:
                    league = bet.league
                    
                    if league not in league_stats:
                        league_stats[league] = {
                            'bets': 0, 'wins': 0, 'profit': 0.0, 'staked': 0.0
                        }
                    
                    league_stats[league]['bets'] += 1
                    league_stats[league]['staked'] += bet.amount
                    league_stats[league]['profit'] += bet.profit
                    
                    if bet.status == "won":
                        league_stats[league]['wins'] += 1
            
            if not league_stats:
                return "Nenhuma aposta resolvida ainda"
            
            # Ordena por profit
            sorted_leagues = sorted(
                league_stats.items(), 
                key=lambda x: x[1]['profit'], 
                reverse=True
            )
            
            result = ""
            for league, stats in sorted_leagues[:5]:  # Top 5
                win_rate = (stats['wins'] / stats['bets'] * 100) if stats['bets'] > 0 else 0
                roi = (stats['profit'] / stats['staked'] * 100) if stats['staked'] > 0 else 0
                
                profit_emoji = "🟢" if stats['profit'] > 0 else "🔴" if stats['profit'] < 0 else "⚪"
                
                result += f"   {profit_emoji} {league}: {stats['bets']} apostas | {win_rate:.1f}% WR | {roi:+.1f}% ROI\n"
            
            return result.strip()
            
        except Exception as e:
            return f"Erro: {e}"
    
    def _generate_insights(self, metrics: PerformanceMetrics, period_days: int) -> str:
        """Gera insights e análises"""
        insights = []
        
        # Análise de win rate
        if metrics.win_rate >= 60:
            insights.append("🎯 Excelente seleção de apostas - win rate acima de 60%")
        elif metrics.win_rate >= 50:
            insights.append("📊 Win rate sólido - mantendo acima de 50%")
        elif metrics.win_rate >= 40:
            insights.append("⚠️ Win rate abaixo do ideal - revisar critérios")
        else:
            insights.append("🚨 Win rate crítico - reavaliar estratégia urgentemente")
        
        # Análise de ROI
        if metrics.roi >= 15:
            insights.append("🚀 ROI excepcional - estratégia muito eficaz")
        elif metrics.roi >= 5:
            insights.append("📈 ROI positivo sólido - no caminho certo")
        elif metrics.roi >= 0:
            insights.append("📊 ROI positivo marginal - pode melhorar")
        else:
            insights.append("📉 ROI negativo - revisar estratégia")
        
        # Análise de streaks
        if metrics.current_streak >= 5 and metrics.streak_type == "win":
            insights.append("🔥 Em sequência quente! Cuidado com overconfidence")
        elif metrics.current_streak >= 3 and metrics.streak_type == "loss":
            insights.append("❄️ Sequência ruim - considere uma pausa")
        
        # Análise de apostas médias
        if metrics.avg_confidence >= 80:
            insights.append("🎯 Alta confiança média nas análises")
        elif metrics.avg_confidence <= 60:
            insights.append("🤔 Confiança baixa - analise mais antes de apostar")
        
        if metrics.avg_ev >= 10:
            insights.append("💎 Excelente identificação de value bets")
        elif metrics.avg_ev <= 3:
            insights.append("⚠️ EV médio baixo - procure melhores oportunidades")
        
        return "\n".join(f"   {insight}" for insight in insights[:5])  # Top 5
    
    def _generate_recommendations(self, metrics: PerformanceMetrics) -> str:
        """Gera recomendações baseadas na performance"""
        recommendations = []
        
        # Recomendações baseadas em ROI
        if metrics.roi < 0:
            recommendations.append("📉 CRÍTICO: Reduzir tamanho das apostas até reverter tendência")
            recommendations.append("🔍 Revisar critérios de seleção - focar em higher EV")
        elif metrics.roi < 5:
            recommendations.append("⚠️ Ser mais seletivo - apostar apenas em spots de maior confiança")
        
        # Recomendações baseadas em win rate
        if metrics.win_rate < 45:
            recommendations.append("🎯 Aumentar critério mínimo de confiança para 80%+")
            recommendations.append("📊 Focar em análises mais profundas antes de apostar")
        
        # Recomendações baseadas em streaks
        if metrics.worst_streak >= 5:
            recommendations.append("🛑 Implementar stop-loss após 3 derrotas consecutivas")
        
        if metrics.current_streak >= 5 and metrics.streak_type == "win":
            recommendations.append("🔥 Streak quente: manter disciplina, não aumentar stakes")
        
        # Recomendações de bankroll
        bankroll_change = metrics.bankroll_current - metrics.bankroll_start
        if bankroll_change < -metrics.bankroll_start * 0.15:  # -15%
            recommendations.append("🚨 Bankroll down 15%+: reduzir unit size temporariamente")
        
        # Recomendações gerais
        if not recommendations:
            recommendations.append("✅ Performance dentro dos parâmetros - manter estratégia")
            recommendations.append("📈 Considerar aumentar unit size gradualmente se ROI > 10%")
        
        return "\n".join(f"   {rec}" for rec in recommendations[:4])  # Top 4
    
    def _calculate_streaks(self, resolved_bets: List) -> Dict:
        """Calcula informações sobre streaks"""
        if not resolved_bets:
            return {
                'best_win_streak': 0,
                'worst_loss_streak': 0,
                'current_streak_length': 0,
                'current_streak_type': 'none'
            }
        
        # Ordena por data
        sorted_bets = sorted(resolved_bets, key=lambda x: x.date)
        
        best_win_streak = 0
        worst_loss_streak = 0
        current_streak = 0
        current_type = 'none'
        
        temp_win_streak = 0
        temp_loss_streak = 0
        
        for bet in sorted_bets:
            if bet.status == "won":
                temp_win_streak += 1
                temp_loss_streak = 0
                best_win_streak = max(best_win_streak, temp_win_streak)
            else:  # lost
                temp_loss_streak += 1
                temp_win_streak = 0
                worst_loss_streak = max(worst_loss_streak, temp_loss_streak)
        
        # Streak atual
        if temp_win_streak > 0:
            current_streak = temp_win_streak
            current_type = "win"
        elif temp_loss_streak > 0:
            current_streak = temp_loss_streak
            current_type = "loss"
        
        return {
            'best_win_streak': best_win_streak,
            'worst_loss_streak': worst_loss_streak,
            'current_streak_length': current_streak,
            'current_streak_type': current_type
        }
    
    def _determine_performance_level(self, roi: float, win_rate: float) -> str:
        """Determina nível de performance"""
        if roi >= 20 and win_rate >= 60:
            return "excellent"
        elif roi >= 10 and win_rate >= 50:
            return "good"
        elif roi >= 0 and win_rate >= 40:
            return "average"
        else:
            return "poor"
    
    def _determine_trend_direction(self, period_bets: List) -> str:
        """Determina direção da tendência"""
        if not period_bets or len(period_bets) < 5:
            return "stable"
        
        # Analisa últimas 5 apostas vs 5 anteriores
        recent_bets = period_bets[-5:]
        previous_bets = period_bets[-10:-5] if len(period_bets) >= 10 else []
        
        if not previous_bets:
            return "stable"
        
        recent_wins = len([b for b in recent_bets if b.status == "won"])
        previous_wins = len([b for b in previous_bets if b.status == "won"])
        
        recent_wr = recent_wins / len(recent_bets)
        previous_wr = previous_wins / len(previous_bets)
        
        diff = recent_wr - previous_wr
        
        if diff >= 0.2:
            return "upward"
        elif diff <= -0.2:
            return "downward"
        elif abs(diff) <= 0.1:
            return "stable"
        else:
            return "volatile"
    
    def _calculate_session_duration(self, session: Dict) -> str:
        """Calcula duração da sessão"""
        try:
            start = datetime.fromisoformat(session['start_time'])
            end = datetime.fromisoformat(session['end_time'])
            duration = end - start
            
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            
            if hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except:
            return "N/A"
    
    def _generate_summary_report(self, metrics: PerformanceMetrics, period_days: int) -> str:
        """Gera relatório resumido"""
        return f"""
📊 RELATÓRIO RESUMIDO ({period_days} dias)
{'='*50}

💰 Performance: {metrics.roi:+.2f}% ROI | {metrics.win_rate:.1f}% WR
📊 Apostas: {metrics.total_bets} total ({metrics.won_bets}W-{metrics.lost_bets}L)
💵 Resultado: R$ {metrics.total_profit:+.2f}
🎯 Nível: {metrics.performance_level.title()}
📈 Tendência: {metrics.trend_direction.title()}

🔥 Streaks: {metrics.best_streak}W máx | {metrics.worst_streak}L máx
💰 Bankroll: R$ {metrics.bankroll_current:.2f}
"""
    
    def _generate_detailed_report(self, metrics: PerformanceMetrics, patterns: Dict, period_days: int) -> str:
        """Gera relatório detalhado"""
        report = f"""
📊 RELATÓRIO DETALHADO DE PERFORMANCE
{'='*80}
📅 Período: {period_days} dias
🕐 Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}

💰 PERFORMANCE GERAL
{'-'*40}
ROI: {metrics.roi:+.2f}%
Win Rate: {metrics.win_rate:.1f}%
Total Apostas: {metrics.total_bets}
Lucro Total: R$ {metrics.total_profit:+.2f}
Valor Apostado: R$ {metrics.total_staked:.2f}

📊 MÉTRICAS DETALHADAS
{'-'*40}
Odds Média: {metrics.avg_odds:.2f}
Stake Média: R$ {metrics.avg_stake:.2f}
Confiança Média: {metrics.avg_confidence:.1f}%
EV Médio: {metrics.avg_ev:+.2f}%

🔥 ANÁLISE DE STREAKS
{'-'*40}
Melhor Streak: {metrics.best_streak} vitórias
Pior Streak: {metrics.worst_streak} derrotas
Streak Atual: {metrics.current_streak} {metrics.streak_type}s

💳 BANKROLL
{'-'*40}
Inicial: R$ {metrics.bankroll_start:.2f}
Atual: R$ {metrics.bankroll_current:.2f}
Máximo: R$ {metrics.bankroll_peak:.2f}
Mínimo: R$ {metrics.bankroll_low:.2f}
"""
        
        # Adiciona padrões se disponível
        if "error" not in patterns:
            report += f"""

📈 ANÁLISE DE PADRÕES
{'-'*40}"""
            
            if patterns.get('weekday_performance'):
                report += "\n\nPerformance por Dia da Semana:"
                for day, stats in patterns['weekday_performance'].items():
                    report += f"\n  {day}: {stats['bets']} apostas | {stats['win_rate']:.1f}% WR | R$ {stats['profit']:+.2f}"
            
            if patterns.get('odds_range_performance'):
                report += "\n\nPerformance por Range de Odds:"
                for range_key, stats in patterns['odds_range_performance'].items():
                    if stats['bets'] > 0:
                        report += f"\n  {range_key}: {stats['bets']} apostas | {stats['win_rate']:.1f}% WR | R$ {stats['profit']:+.2f}"
        
        return report
    
    def _load_data(self):
        """Carrega dados de tracking"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    self.tracking_data.update(loaded_data)
                
                logger.info(f"Dados de tracking carregados")
        
        except Exception as e:
            logger.warning(f"Erro ao carregar dados de tracking: {e}")
    
    def _save_data(self):
        """Salva dados de tracking"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tracking_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados de tracking: {e}")


def create_default_tracker(bankroll_manager=None, value_analyzer=None) -> BettingTracker:
    """Cria tracker com configurações padrão"""
    return BettingTracker(bankroll_manager=bankroll_manager, value_analyzer=value_analyzer)


if __name__ == "__main__":
    # Teste básico
    tracker = create_default_tracker()
    
    print("🚀 Betting Tracker inicializado")
    
    # Simula alguns dados para teste
    dashboard = tracker.generate_dashboard(30)
    print(dashboard)
    
    # Cria snapshot
    snapshot = tracker.create_daily_snapshot()
    print(f"\nSnapshot criado: {snapshot}")
    
    # Analisa padrões
    patterns = tracker.analyze_betting_patterns(90)
    print(f"\nPadrões analisados: {patterns.get('total_bets_analyzed', 0)} apostas")