#!/usr/bin/env python3
"""
Portfolio Manager - Sistema Inteligente de Gerenciamento de Portfolio
Funcionalidades:
- Diversificação automática de apostas
- Risk management inteligente
- ROI tracking por categoria
- Balanceamento de portfolio
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BetPosition:
    """Posição de aposta no portfolio"""
    id: str
    sport: str
    league: str
    team1: str
    team2: str
    bet_type: str
    stake: float
    odds: float
    probability: float
    expected_value: float
    risk_level: str
    timestamp: datetime
    status: str = "pending"  # pending, won, lost
    profit_loss: float = 0.0

@dataclass
class SportCategory:
    """Categoria de esporte no portfolio"""
    name: str
    allocation_percentage: float
    current_exposure: float
    roi: float
    win_rate: float
    total_bets: int
    risk_tolerance: str

class PortfolioManager:
    """Gerenciador inteligente de portfolio de apostas"""
    
    def __init__(self, total_bankroll: float = 10000.0):
        self.total_bankroll = total_bankroll
        self.current_bankroll = total_bankroll
        self.positions: List[BetPosition] = []
        self.sport_categories: Dict[str, SportCategory] = {}
        self.max_risk_per_bet = 0.05  # 5% máximo por aposta
        self.max_exposure_per_sport = 0.25  # 25% máximo por esporte
        
        # Configuração inicial das categorias
        self._initialize_sport_categories()
        
        # Histórico para análise
        self.performance_history = []
        
        logger.info("🏦 Portfolio Manager inicializado")
    
    def _initialize_sport_categories(self):
        """Inicializa categorias de esporte com alocações padrão"""
        default_categories = {
            "football": SportCategory("Football", 0.40, 0.0, 0.0, 0.0, 0, "medium"),
            "basketball": SportCategory("Basketball", 0.25, 0.0, 0.0, 0.0, 0, "medium"), 
            "tennis": SportCategory("Tennis", 0.15, 0.0, 0.0, 0.0, 0, "low"),
            "baseball": SportCategory("Baseball", 0.10, 0.0, 0.0, 0.0, 0, "low"),
            "other": SportCategory("Other Sports", 0.10, 0.0, 0.0, 0.0, 0, "high")
        }
        
        self.sport_categories = default_categories
        logger.info("📊 Categorias de esporte inicializadas")
    
    def add_bet_position(self, bet_data: Dict) -> Optional[BetPosition]:
        """Adiciona nova posição ao portfolio"""
        try:
            # Criar posição
            position = BetPosition(
                id=f"bet_{len(self.positions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                sport=bet_data.get('sport', 'other').lower(),
                league=bet_data.get('league', 'unknown'),
                team1=bet_data.get('team1', 'Team1'),
                team2=bet_data.get('team2', 'Team2'),
                bet_type=bet_data.get('bet_type', 'moneyline'),
                stake=0.0,  # Será calculado
                odds=bet_data.get('odds', 2.0),
                probability=bet_data.get('probability', 0.5),
                expected_value=0.0,  # Será calculado
                risk_level=self._calculate_risk_level(bet_data),
                timestamp=datetime.now()
            )
            
            # Calcular stake ótimo
            optimal_stake = self.calculate_optimal_stake(position)
            
            if optimal_stake > 0:
                position.stake = optimal_stake
                position.expected_value = self._calculate_expected_value(position)
                
                # Verificar se posição é aceitável
                if self._validate_position(position):
                    self.positions.append(position)
                    self._update_category_exposure(position)
                    
                    logger.info(f"✅ Posição adicionada: {position.team1} vs {position.team2} - Stake: ${position.stake:.2f}")
                    return position
                else:
                    logger.warning(f"⚠️ Posição rejeitada por risk management: {position.team1} vs {position.team2}")
            else:
                logger.warning(f"⚠️ Stake calculado como 0: {position.team1} vs {position.team2}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar posição: {e}")
        
        return None
    
    def calculate_optimal_stake(self, position: BetPosition) -> float:
        """Calcula stake ótimo baseado em Kelly Criterion modificado"""
        try:
            # Kelly Criterion: f = (bp - q) / b
            # f = stake fraction
            # b = odds - 1 (decimal odds - 1)
            # p = probability of winning
            # q = probability of losing (1 - p)
            
            b = position.odds - 1
            p = position.probability
            q = 1 - p
            
            if b <= 0 or p <= 0:
                return 0.0
            
            # Kelly fraction
            kelly_fraction = (b * p - q) / b
            
            # Kelly só recomenda apostar se EV > 0
            if kelly_fraction <= 0:
                return 0.0
            
            # Aplicar limitações de risk management
            # 1. Máximo 5% do bankroll por aposta
            max_stake_risk = self.current_bankroll * self.max_risk_per_bet
            
            # 2. Limitação por categoria de esporte
            sport_category = self.sport_categories.get(position.sport, self.sport_categories['other'])
            max_allocation = self.current_bankroll * sport_category.allocation_percentage
            current_exposure = sport_category.current_exposure
            available_for_sport = max_allocation - current_exposure
            
            # 3. Kelly conservador (25% do Kelly completo para reduzir risco)
            conservative_kelly = kelly_fraction * 0.25
            kelly_stake = self.current_bankroll * conservative_kelly
            
            # 4. Ajuste por nível de risco
            risk_multiplier = self._get_risk_multiplier(position.risk_level)
            kelly_stake *= risk_multiplier
            
            # Usar o menor valor entre todos os limites
            optimal_stake = min(
                kelly_stake,
                max_stake_risk,
                available_for_sport,
                self.current_bankroll * 0.1  # Nunca mais que 10%
            )
            
            # Arredondar para 2 casas decimais
            return round(max(0.0, optimal_stake), 2)
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de stake: {e}")
            return 0.0
    
    def _calculate_risk_level(self, bet_data: Dict) -> str:
        """Calcula nível de risco da aposta"""
        try:
            probability = bet_data.get('probability', 0.5)
            odds = bet_data.get('odds', 2.0)
            confidence = bet_data.get('confidence', 'medium')
            
            # Risk score baseado em múltiplos fatores
            risk_score = 0
            
            # Fator 1: Probabilidade
            if probability >= 0.7:
                risk_score += 1  # Baixo risco
            elif probability >= 0.55:
                risk_score += 2  # Médio risco  
            else:
                risk_score += 3  # Alto risco
            
            # Fator 2: Odds
            if odds <= 1.5:
                risk_score += 1  # Baixo risco
            elif odds <= 2.5:
                risk_score += 2  # Médio risco
            else:
                risk_score += 3  # Alto risco
            
            # Fator 3: Confiança
            confidence_map = {'muito alta': 1, 'alta': 1, 'média': 2, 'baixa': 3, 'muito baixa': 3}
            risk_score += confidence_map.get(confidence.lower(), 2)
            
            # Classificar risco
            if risk_score <= 4:
                return 'low'
            elif risk_score <= 6:
                return 'medium'
            else:
                return 'high'
                
        except Exception:
            return 'medium'
    
    def _get_risk_multiplier(self, risk_level: str) -> float:
        """Retorna multiplicador baseado no nível de risco"""
        multipliers = {
            'low': 1.0,      # 100% do stake calculado
            'medium': 0.75,  # 75% do stake calculado
            'high': 0.5      # 50% do stake calculado
        }
        return multipliers.get(risk_level, 0.75)
    
    def _calculate_expected_value(self, position: BetPosition) -> float:
        """Calcula valor esperado da posição"""
        try:
            # EV = (Probability * Profit) - (1 - Probability) * Loss
            potential_profit = position.stake * (position.odds - 1)
            potential_loss = position.stake
            
            ev = (position.probability * potential_profit) - ((1 - position.probability) * potential_loss)
            return round(ev, 2)
            
        except Exception:
            return 0.0
    
    def _validate_position(self, position: BetPosition) -> bool:
        """Valida se posição atende critérios de risk management"""
        try:
            # 1. EV deve ser positivo
            if position.expected_value <= 0:
                return False
            
            # 2. Stake não pode exceder limites
            if position.stake > self.current_bankroll * self.max_risk_per_bet:
                return False
            
            # 3. Não pode exceder exposição máxima por esporte
            sport_category = self.sport_categories.get(position.sport, self.sport_categories['other'])
            max_sport_exposure = self.current_bankroll * sport_category.allocation_percentage
            
            if sport_category.current_exposure + position.stake > max_sport_exposure:
                return False
            
            # 4. Bankroll deve ser suficiente
            if position.stake > self.current_bankroll:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _update_category_exposure(self, position: BetPosition):
        """Atualiza exposição da categoria"""
        sport = position.sport
        if sport in self.sport_categories:
            self.sport_categories[sport].current_exposure += position.stake
            self.sport_categories[sport].total_bets += 1
    
    def update_position_result(self, position_id: str, won: bool, actual_profit: float = None):
        """Atualiza resultado de uma posição"""
        try:
            position = next((p for p in self.positions if p.id == position_id), None)
            
            if not position:
                logger.warning(f"⚠️ Posição não encontrada: {position_id}")
                return
            
            if won:
                position.status = "won"
                position.profit_loss = actual_profit or (position.stake * (position.odds - 1))
                self.current_bankroll += position.profit_loss
            else:
                position.status = "lost" 
                position.profit_loss = -position.stake
                self.current_bankroll += position.profit_loss  # Subtrai a perda
            
            # Atualizar estatísticas da categoria
            self._update_category_stats(position)
            
            # Adicionar ao histórico
            self.performance_history.append({
                'timestamp': datetime.now(),
                'position_id': position_id,
                'result': 'win' if won else 'loss',
                'profit_loss': position.profit_loss,
                'new_bankroll': self.current_bankroll
            })
            
            logger.info(f"📊 Posição atualizada: {position_id} - {'WIN' if won else 'LOSS'} - P&L: ${position.profit_loss:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar posição: {e}")
    
    def _update_category_stats(self, position: BetPosition):
        """Atualiza estatísticas da categoria após resultado"""
        sport = position.sport
        if sport not in self.sport_categories:
            return
        
        category = self.sport_categories[sport]
        
        # Atualizar exposição (remover stake da exposição atual)
        category.current_exposure = max(0, category.current_exposure - position.stake)
        
        # Calcular ROI e win rate
        sport_positions = [p for p in self.positions if p.sport == sport and p.status in ['won', 'lost']]
        
        if sport_positions:
            total_stakes = sum(p.stake for p in sport_positions)
            total_profit = sum(p.profit_loss for p in sport_positions)
            wins = len([p for p in sport_positions if p.status == 'won'])
            
            category.roi = (total_profit / total_stakes) * 100 if total_stakes > 0 else 0
            category.win_rate = (wins / len(sport_positions)) * 100
    
    def get_portfolio_summary(self) -> Dict:
        """Retorna resumo completo do portfolio"""
        try:
            # Posições ativas
            active_positions = [p for p in self.positions if p.status == 'pending']
            completed_positions = [p for p in self.positions if p.status in ['won', 'lost']]
            
            # Métricas gerais
            total_exposure = sum(p.stake for p in active_positions)
            total_profit_loss = sum(p.profit_loss for p in completed_positions)
            
            # ROI geral
            total_stakes = sum(p.stake for p in completed_positions)
            overall_roi = (total_profit_loss / total_stakes * 100) if total_stakes > 0 else 0
            
            # Win rate geral
            wins = len([p for p in completed_positions if p.status == 'won'])
            overall_win_rate = (wins / len(completed_positions) * 100) if completed_positions else 0
            
            # Exposição por esporte
            sport_exposure = {}
            for sport, category in self.sport_categories.items():
                sport_exposure[sport] = {
                    'allocation': category.allocation_percentage * 100,
                    'current_exposure': category.current_exposure,
                    'exposure_percentage': (category.current_exposure / self.current_bankroll * 100) if self.current_bankroll > 0 else 0,
                    'roi': category.roi,
                    'win_rate': category.win_rate,
                    'total_bets': category.total_bets
                }
            
            return {
                'bankroll': {
                    'initial': self.total_bankroll,
                    'current': self.current_bankroll,
                    'profit_loss': self.current_bankroll - self.total_bankroll,
                    'profit_percentage': ((self.current_bankroll - self.total_bankroll) / self.total_bankroll * 100) if self.total_bankroll > 0 else 0
                },
                'positions': {
                    'active': len(active_positions),
                    'completed': len(completed_positions),
                    'total_exposure': total_exposure,
                    'exposure_percentage': (total_exposure / self.current_bankroll * 100) if self.current_bankroll > 0 else 0
                },
                'performance': {
                    'overall_roi': overall_roi,
                    'overall_win_rate': overall_win_rate,
                    'total_profit_loss': total_profit_loss,
                    'total_bets': len(completed_positions)
                },
                'sport_breakdown': sport_exposure,
                'risk_metrics': self._calculate_risk_metrics()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resumo: {e}")
            return {}
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calcula métricas de risco do portfolio"""
        try:
            if not self.performance_history:
                return {'max_drawdown': 0, 'volatility': 0, 'sharpe_ratio': 0}
            
            # Extrair retornos
            returns = []
            bankroll_values = [self.total_bankroll]
            
            for record in self.performance_history:
                bankroll_values.append(record['new_bankroll'])
            
            # Calcular retornos percentuais
            for i in range(1, len(bankroll_values)):
                if bankroll_values[i-1] > 0:
                    daily_return = (bankroll_values[i] - bankroll_values[i-1]) / bankroll_values[i-1]
                    returns.append(daily_return)
            
            if not returns:
                return {'max_drawdown': 0, 'volatility': 0, 'sharpe_ratio': 0}
            
            # Max Drawdown
            peak = bankroll_values[0]
            max_drawdown = 0
            
            for value in bankroll_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # Volatilidade (desvio padrão dos retornos)
            volatility = np.std(returns) if len(returns) > 1 else 0
            
            # Sharpe Ratio simplificado (assumindo risk-free rate = 0)
            mean_return = np.mean(returns) if returns else 0
            sharpe_ratio = mean_return / volatility if volatility > 0 else 0
            
            return {
                'max_drawdown': max_drawdown * 100,
                'volatility': volatility * 100,
                'sharpe_ratio': sharpe_ratio
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de métricas de risco: {e}")
            return {'max_drawdown': 0, 'volatility': 0, 'sharpe_ratio': 0}
    
    def get_recommendations(self) -> List[str]:
        """Gera recomendações baseadas na performance do portfolio"""
        recommendations = []
        
        try:
            summary = self.get_portfolio_summary()
            
            # Análise de exposição
            total_exposure_pct = summary['positions']['exposure_percentage']
            if total_exposure_pct > 50:
                recommendations.append("⚠️ Exposição total alta (>50%). Considere reduzir posições.")
            elif total_exposure_pct < 20:
                recommendations.append("💡 Exposição baixa. Oportunidade para mais posições de qualidade.")
            
            # Análise de performance
            overall_roi = summary['performance']['overall_roi']
            if overall_roi < -10:
                recommendations.append("🔴 ROI negativo. Revisar estratégia e risk management.")
            elif overall_roi > 20:
                recommendations.append("🟢 Excelente performance! Manter estratégia atual.")
            
            # Análise por esporte
            for sport, data in summary['sport_breakdown'].items():
                if data['total_bets'] >= 5:  # Apenas esportes com dados suficientes
                    if data['roi'] < -15:
                        recommendations.append(f"📉 {sport.title()}: ROI muito baixo ({data['roi']:.1f}%). Considere pausar apostas neste esporte.")
                    elif data['roi'] > 25:
                        recommendations.append(f"📈 {sport.title()}: Excelente ROI ({data['roi']:.1f}%)! Considere aumentar alocação.")
            
            # Análise de diversificação
            active_sports = len([s for s, d in summary['sport_breakdown'].items() if d['current_exposure'] > 0])
            if active_sports <= 2:
                recommendations.append("🎯 Portfolio pouco diversificado. Considere apostas em mais esportes.")
            
            # Risk metrics
            risk_metrics = summary.get('risk_metrics', {})
            max_drawdown = risk_metrics.get('max_drawdown', 0)
            if max_drawdown > 20:
                recommendations.append(f"⚠️ Drawdown alto ({max_drawdown:.1f}%). Considere reduzir stakes.")
            
            if not recommendations:
                recommendations.append("✅ Portfolio bem balanceado. Continue monitorando performance.")
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar recomendações: {e}")
            recommendations.append("❌ Erro ao analisar portfolio. Verifique dados.")
        
        return recommendations
    
    def rebalance_portfolio(self):
        """Rebalanceia portfolio baseado na performance"""
        try:
            logger.info("🔄 Iniciando rebalanceamento do portfolio...")
            
            # Analisar performance por esporte
            for sport, category in self.sport_categories.items():
                if category.total_bets >= 10:  # Dados suficientes para análise
                    
                    # Ajustar alocação baseado em ROI
                    if category.roi > 20:  # Performance excelente
                        # Aumentar alocação em 5% (máximo)
                        new_allocation = min(category.allocation_percentage + 0.05, 0.5)
                        category.allocation_percentage = new_allocation
                        logger.info(f"📈 {sport}: Alocação aumentada para {new_allocation*100:.1f}%")
                        
                    elif category.roi < -15:  # Performance ruim
                        # Reduzir alocação em 5% (mínimo 5%)
                        new_allocation = max(category.allocation_percentage - 0.05, 0.05)
                        category.allocation_percentage = new_allocation
                        logger.info(f"📉 {sport}: Alocação reduzida para {new_allocation*100:.1f}%")
            
            # Normalizar alocações para somar 100%
            total_allocation = sum(cat.allocation_percentage for cat in self.sport_categories.values())
            if total_allocation != 1.0:
                for category in self.sport_categories.values():
                    category.allocation_percentage /= total_allocation
            
            logger.info("✅ Rebalanceamento concluído")
            
        except Exception as e:
            logger.error(f"❌ Erro no rebalanceamento: {e}")
    
    def export_portfolio_data(self) -> Dict:
        """Exporta dados do portfolio para backup/análise"""
        try:
            return {
                'portfolio_info': {
                    'total_bankroll': self.total_bankroll,
                    'current_bankroll': self.current_bankroll,
                    'export_timestamp': datetime.now().isoformat()
                },
                'positions': [
                    {
                        'id': p.id,
                        'sport': p.sport,
                        'league': p.league,
                        'matchup': f"{p.team1} vs {p.team2}",
                        'bet_type': p.bet_type,
                        'stake': p.stake,
                        'odds': p.odds,
                        'probability': p.probability,
                        'expected_value': p.expected_value,
                        'risk_level': p.risk_level,
                        'status': p.status,
                        'profit_loss': p.profit_loss,
                        'timestamp': p.timestamp.isoformat()
                    } for p in self.positions
                ],
                'sport_categories': {
                    sport: {
                        'allocation_percentage': cat.allocation_percentage,
                        'current_exposure': cat.current_exposure,
                        'roi': cat.roi,
                        'win_rate': cat.win_rate,
                        'total_bets': cat.total_bets,
                        'risk_tolerance': cat.risk_tolerance
                    } for sport, cat in self.sport_categories.items()
                },
                'performance_history': self.performance_history[-100:],  # Últimos 100 registros
                'summary': self.get_portfolio_summary()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar dados: {e}")
            return {}


# Exemplo de uso
if __name__ == "__main__":
    # Inicializar portfolio manager
    portfolio = PortfolioManager(total_bankroll=10000.0)
    
    # Exemplo de adição de posição
    bet_data = {
        'sport': 'football',
        'league': 'Premier League',
        'team1': 'Manchester City',
        'team2': 'Liverpool',
        'bet_type': 'moneyline',
        'odds': 2.1,
        'probability': 0.6,
        'confidence': 'alta'
    }
    
    position = portfolio.add_bet_position(bet_data)
    if position:
        print(f"✅ Posição adicionada: ${position.stake:.2f} stake")
        
        # Simular resultado
        portfolio.update_position_result(position.id, won=True)
        
        # Ver resumo
        summary = portfolio.get_portfolio_summary()
        print(f"💰 Bankroll atual: ${summary['bankroll']['current']:.2f}")
        print(f"📊 ROI: {summary['performance']['overall_roi']:.2f}%") 