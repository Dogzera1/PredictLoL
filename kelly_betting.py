#!/usr/bin/env python3
"""
Kelly Betting System - Sistema Automático de Kelly Criterion
Funcionalidades:
- Cálculo automático de Kelly Criterion
- Sizing ótimo de apostas
- Risk management integrado
- Multiple bet optimization
"""

import logging
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BetOpportunity:
    """Oportunidade de aposta para análise Kelly"""
    id: str
    description: str
    probability: float
    odds: float
    confidence_level: float
    max_stake: float
    min_odds: float = 1.01
    sport: str = "unknown"
    league: str = "unknown"

@dataclass
class KellyResult:
    """Resultado do cálculo Kelly"""
    bet_id: str
    kelly_fraction: float
    recommended_stake: float
    expected_value: float
    expected_growth: float
    risk_level: str
    should_bet: bool
    reason: str

class KellyBetting:
    """Sistema automático de Kelly Criterion para sizing ótimo"""
    
    def __init__(self, bankroll: float = 10000.0):
        self.bankroll = bankroll
        self.initial_bankroll = bankroll
        
        # Configurações de risk management
        self.max_kelly_fraction = 0.25  # Máximo 25% do Kelly completo
        self.min_kelly_fraction = 0.01  # Mínimo 1% para apostar
        self.max_single_bet = 0.05      # Máximo 5% do bankroll por aposta
        self.min_probability = 0.51     # Mínima probabilidade para apostar
        self.min_odds = 1.01           # Mínimas odds para apostar
        
        # Histórico de apostas
        self.bet_history: List[Dict] = []
        self.performance_metrics = {
            'total_bets': 0,
            'winning_bets': 0,
            'total_staked': 0.0,
            'total_profit': 0.0,
            'avg_kelly_fraction': 0.0,
            'max_drawdown': 0.0
        }
        
        logger.info("🎯 Kelly Betting System inicializado")
    
    def calculate_kelly_fraction(self, probability: float, odds: float) -> float:
        """
        Calcula a fração Kelly ótima
        
        Fórmula: f* = (bp - q) / b
        Onde:
        - f* = fração Kelly (% do bankroll para apostar)
        - b = odds - 1 (net odds)
        - p = probabilidade de ganhar
        - q = probabilidade de perder (1 - p)
        """
        try:
            if probability <= 0 or probability >= 1:
                return 0.0
            
            if odds <= 1.0:
                return 0.0
            
            b = odds - 1  # Net odds
            p = probability
            q = 1 - probability
            
            # Fórmula Kelly
            kelly_fraction = (b * p - q) / b
            
            # Kelly só recomenda apostar se houver vantagem
            if kelly_fraction <= 0:
                return 0.0
            
            return kelly_fraction
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo Kelly: {e}")
            return 0.0
    
    def calculate_fractional_kelly(self, kelly_fraction: float, fraction: float = 0.25) -> float:
        """
        Calcula Kelly fracionário para reduzir volatilidade
        
        Args:
            kelly_fraction: Fração Kelly completa
            fraction: Fração do Kelly a usar (default: 25%)
        """
        return kelly_fraction * fraction
    
    def calculate_expected_value(self, probability: float, odds: float, stake: float) -> float:
        """Calcula valor esperado de uma aposta"""
        try:
            profit_if_win = stake * (odds - 1)
            loss_if_lose = stake
            
            ev = (probability * profit_if_win) - ((1 - probability) * loss_if_lose)
            return ev
            
        except Exception:
            return 0.0
    
    def calculate_expected_growth(self, probability: float, odds: float, kelly_fraction: float) -> float:
        """
        Calcula crescimento esperado usando Kelly
        
        Fórmula: G = p * ln(1 + b*f) + q * ln(1 - f)
        """
        try:
            if kelly_fraction <= 0 or kelly_fraction >= 1:
                return 0.0
            
            b = odds - 1
            p = probability
            q = 1 - probability
            f = kelly_fraction
            
            # Verificar limites para evitar ln de números negativos
            if (1 + b * f) <= 0 or (1 - f) <= 0:
                return 0.0
            
            growth = p * math.log(1 + b * f) + q * math.log(1 - f)
            return growth
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de crescimento: {e}")
            return 0.0
    
    def analyze_bet_opportunity(self, opportunity: BetOpportunity) -> KellyResult:
        """Analisa oportunidade de aposta usando Kelly"""
        try:
            # Calcular Kelly fraction
            kelly_fraction = self.calculate_kelly_fraction(
                opportunity.probability, 
                opportunity.odds
            )
            
            # Aplicar Kelly fracionário (conservador)
            conservative_kelly = self.calculate_fractional_kelly(
                kelly_fraction, 
                self.max_kelly_fraction
            )
            
            # Calcular stake recomendado
            recommended_stake = self.bankroll * conservative_kelly
            
            # Aplicar limitações de risk management
            recommended_stake = min(
                recommended_stake,
                self.bankroll * self.max_single_bet,  # Máximo 5% do bankroll
                opportunity.max_stake                  # Limite da oportunidade
            )
            
            # Arredondar stake
            recommended_stake = round(recommended_stake, 2)
            
            # Calcular métricas
            expected_value = self.calculate_expected_value(
                opportunity.probability,
                opportunity.odds,
                recommended_stake
            )
            
            expected_growth = self.calculate_expected_growth(
                opportunity.probability,
                opportunity.odds,
                conservative_kelly
            )
            
            # Determinar se deve apostar
            should_bet, reason = self._should_place_bet(
                opportunity, kelly_fraction, conservative_kelly, recommended_stake
            )
            
            # Determinar nível de risco
            risk_level = self._calculate_risk_level(
                kelly_fraction, opportunity.probability, opportunity.odds
            )
            
            return KellyResult(
                bet_id=opportunity.id,
                kelly_fraction=kelly_fraction,
                recommended_stake=recommended_stake,
                expected_value=expected_value,
                expected_growth=expected_growth,
                risk_level=risk_level,
                should_bet=should_bet,
                reason=reason
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na análise Kelly: {e}")
            return KellyResult(
                bet_id=opportunity.id,
                kelly_fraction=0.0,
                recommended_stake=0.0,
                expected_value=0.0,
                expected_growth=0.0,
                risk_level="high",
                should_bet=False,
                reason=f"Erro na análise: {str(e)}"
            )
    
    def _should_place_bet(self, opportunity: BetOpportunity, kelly_fraction: float, 
                         conservative_kelly: float, recommended_stake: float) -> Tuple[bool, str]:
        """Determina se a aposta deve ser feita baseado em critérios"""
        
        # Critério 1: Kelly deve ser positivo
        if kelly_fraction <= 0:
            return False, "Kelly negativo - sem vantagem matemática"
        
        # Critério 2: Kelly deve ser maior que mínimo
        if kelly_fraction < self.min_kelly_fraction:
            return False, f"Kelly muito baixo ({kelly_fraction:.3f} < {self.min_kelly_fraction})"
        
        # Critério 3: Probabilidade mínima
        if opportunity.probability < self.min_probability:
            return False, f"Probabilidade muito baixa ({opportunity.probability:.3f} < {self.min_probability})"
        
        # Critério 4: Odds mínimas
        if opportunity.odds < self.min_odds:
            return False, f"Odds muito baixas ({opportunity.odds} < {self.min_odds})"
        
        # Critério 5: Stake mínimo
        if recommended_stake < 1.0:  # Mínimo $1
            return False, f"Stake muito baixo (${recommended_stake:.2f} < $1.00)"
        
        # Critério 6: Bankroll suficiente
        if recommended_stake > self.bankroll:
            return False, f"Bankroll insuficiente (${recommended_stake:.2f} > ${self.bankroll:.2f})"
        
        # Critério 7: Confiança na estimativa
        if opportunity.confidence_level < 0.7:
            return False, f"Confiança baixa na probabilidade ({opportunity.confidence_level:.3f} < 0.70)"
        
        return True, f"✅ Aposta recomendada - Kelly: {kelly_fraction:.3f}, EV+: {self.calculate_expected_value(opportunity.probability, opportunity.odds, recommended_stake):.2f}"
    
    def _calculate_risk_level(self, kelly_fraction: float, probability: float, odds: float) -> str:
        """Calcula nível de risco da aposta"""
        risk_score = 0
        
        # Fator 1: Kelly fraction
        if kelly_fraction > 0.1:
            risk_score += 2
        elif kelly_fraction > 0.05:
            risk_score += 1
        
        # Fator 2: Probabilidade
        if probability < 0.6:
            risk_score += 2
        elif probability < 0.7:
            risk_score += 1
        
        # Fator 3: Odds
        if odds > 3.0:
            risk_score += 2
        elif odds > 2.0:
            risk_score += 1
        
        # Classificar risco
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    def optimize_multiple_bets(self, opportunities: List[BetOpportunity]) -> List[KellyResult]:
        """
        Otimiza múltiplas apostas considerando correlação e limitações de bankroll
        """
        try:
            logger.info(f"🔄 Otimizando {len(opportunities)} oportunidades...")
            
            # Analisar cada oportunidade individualmente
            individual_results = []
            for opp in opportunities:
                result = self.analyze_bet_opportunity(opp)
                individual_results.append(result)
            
            # Filtrar apenas apostas viáveis
            viable_bets = [r for r in individual_results if r.should_bet]
            
            if not viable_bets:
                logger.info("❌ Nenhuma aposta viável encontrada")
                return individual_results
            
            # Ordenar por Kelly fraction decrescente
            viable_bets.sort(key=lambda x: x.kelly_fraction, reverse=True)
            
            # Aplicar limitação de bankroll total
            optimized_results = []
            total_allocated = 0.0
            max_total_allocation = self.bankroll * 0.25  # Máximo 25% do bankroll total
            
            for result in viable_bets:
                if total_allocated + result.recommended_stake <= max_total_allocation:
                    optimized_results.append(result)
                    total_allocated += result.recommended_stake
                    logger.info(f"✅ Adicionada: {result.bet_id} - ${result.recommended_stake:.2f}")
                else:
                    # Ajustar stake para caber no limite restante
                    remaining_allocation = max_total_allocation - total_allocated
                    if remaining_allocation >= 1.0:  # Mínimo $1
                        adjusted_result = KellyResult(
                            bet_id=result.bet_id,
                            kelly_fraction=result.kelly_fraction,
                            recommended_stake=remaining_allocation,
                            expected_value=self.calculate_expected_value(
                                opportunities[viable_bets.index(result)].probability,
                                opportunities[viable_bets.index(result)].odds,
                                remaining_allocation
                            ),
                            expected_growth=result.expected_growth,
                            risk_level=result.risk_level,
                            should_bet=True,
                            reason=f"Stake ajustado para limite de bankroll: ${remaining_allocation:.2f}"
                        )
                        optimized_results.append(adjusted_result)
                        total_allocated += remaining_allocation
                        logger.info(f"⚠️ Ajustada: {result.bet_id} - ${remaining_allocation:.2f}")
                        break
                    else:
                        logger.info(f"❌ Removida por limite: {result.bet_id}")
            
            # Adicionar apostas rejeitadas aos resultados
            rejected_bet_ids = {r.bet_id for r in optimized_results}
            for result in individual_results:
                if result.bet_id not in rejected_bet_ids:
                    optimized_results.append(result)
            
            logger.info(f"📊 Otimização concluída: {len(optimized_results)} apostas, ${total_allocated:.2f} alocado")
            return optimized_results
            
        except Exception as e:
            logger.error(f"❌ Erro na otimização múltipla: {e}")
            return individual_results if 'individual_results' in locals() else []
    
    def update_bankroll(self, new_bankroll: float):
        """Atualiza bankroll atual"""
        old_bankroll = self.bankroll
        self.bankroll = new_bankroll
        
        # Calcular drawdown
        if new_bankroll < self.initial_bankroll:
            drawdown = (self.initial_bankroll - new_bankroll) / self.initial_bankroll
            if drawdown > self.performance_metrics['max_drawdown']:
                self.performance_metrics['max_drawdown'] = drawdown
        
        logger.info(f"💰 Bankroll atualizado: ${old_bankroll:.2f} → ${new_bankroll:.2f}")
    
    def record_bet_result(self, bet_id: str, won: bool, stake: float, 
                         payout: float = 0.0, actual_odds: float = None):
        """Registra resultado de uma aposta"""
        try:
            profit_loss = payout - stake if won else -stake
            
            bet_record = {
                'bet_id': bet_id,
                'timestamp': datetime.now(),
                'won': won,
                'stake': stake,
                'payout': payout,
                'profit_loss': profit_loss,
                'actual_odds': actual_odds or (payout / stake if stake > 0 and won else 0)
            }
            
            self.bet_history.append(bet_record)
            
            # Atualizar métricas
            self.performance_metrics['total_bets'] += 1
            if won:
                self.performance_metrics['winning_bets'] += 1
            self.performance_metrics['total_staked'] += stake
            self.performance_metrics['total_profit'] += profit_loss
            
            # Atualizar bankroll
            self.update_bankroll(self.bankroll + profit_loss)
            
            logger.info(f"📝 Resultado registrado: {bet_id} - {'WIN' if won else 'LOSS'} - P&L: ${profit_loss:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar resultado: {e}")
    
    def get_performance_summary(self) -> Dict:
        """Retorna resumo da performance do sistema Kelly"""
        try:
            if self.performance_metrics['total_bets'] == 0:
                return {
                    'bankroll': {
                        'initial': self.initial_bankroll,
                        'current': self.bankroll,
                        'profit_loss': 0.0,
                        'profit_percentage': 0.0
                    },
                    'bets': {
                        'total': 0,
                        'wins': 0,
                        'losses': 0,
                        'win_rate': 0.0
                    },
                    'financial': {
                        'total_staked': 0.0,
                        'total_profit': 0.0,
                        'roi': 0.0,
                        'avg_stake': 0.0
                    },
                    'risk': {
                        'max_drawdown': 0.0,
                        'avg_kelly_fraction': 0.0
                    }
                }
            
            win_rate = (self.performance_metrics['winning_bets'] / 
                       self.performance_metrics['total_bets']) * 100
            
            roi = (self.performance_metrics['total_profit'] / 
                  self.performance_metrics['total_staked']) * 100 if self.performance_metrics['total_staked'] > 0 else 0
            
            avg_stake = (self.performance_metrics['total_staked'] / 
                        self.performance_metrics['total_bets'])
            
            profit_percentage = ((self.bankroll - self.initial_bankroll) / 
                               self.initial_bankroll) * 100
            
            return {
                'bankroll': {
                    'initial': self.initial_bankroll,
                    'current': self.bankroll,
                    'profit_loss': self.bankroll - self.initial_bankroll,
                    'profit_percentage': profit_percentage
                },
                'bets': {
                    'total': self.performance_metrics['total_bets'],
                    'wins': self.performance_metrics['winning_bets'],
                    'losses': self.performance_metrics['total_bets'] - self.performance_metrics['winning_bets'],
                    'win_rate': win_rate
                },
                'financial': {
                    'total_staked': self.performance_metrics['total_staked'],
                    'total_profit': self.performance_metrics['total_profit'],
                    'roi': roi,
                    'avg_stake': avg_stake
                },
                'risk': {
                    'max_drawdown': self.performance_metrics['max_drawdown'] * 100,
                    'avg_kelly_fraction': self.performance_metrics['avg_kelly_fraction']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resumo: {e}")
            return {}
    
    def get_kelly_recommendations(self) -> List[str]:
        """Gera recomendações baseadas na performance Kelly"""
        recommendations = []
        
        try:
            summary = self.get_performance_summary()
            
            # Análise de win rate
            win_rate = summary['bets']['win_rate']
            if win_rate < 50 and summary['bets']['total'] >= 10:
                recommendations.append("🔴 Win rate baixo. Revisar estimativas de probabilidade.")
            elif win_rate > 60:
                recommendations.append("🟢 Excelente win rate! Sistema funcionando bem.")
            
            # Análise de ROI
            roi = summary['financial']['roi']
            if roi < -5 and summary['bets']['total'] >= 5:
                recommendations.append("📉 ROI negativo. Considerar Kelly mais conservador.")
            elif roi > 10:
                recommendations.append("📈 ROI positivo! Manter estratégia Kelly atual.")
            
            # Análise de drawdown
            max_drawdown = summary['risk']['max_drawdown']
            if max_drawdown > 20:
                recommendations.append(f"⚠️ Drawdown alto ({max_drawdown:.1f}%). Reduzir fração Kelly.")
            
            # Análise de stake médio
            avg_stake = summary['financial']['avg_stake']
            bankroll_percentage = (avg_stake / self.bankroll) * 100
            if bankroll_percentage > 5:
                recommendations.append("💰 Stakes muito altos. Considerar Kelly mais conservador.")
            elif bankroll_percentage < 1:
                recommendations.append("💡 Stakes baixos. Oportunidade para Kelly menos conservador.")
            
            if not recommendations:
                recommendations.append("✅ Sistema Kelly funcionando adequadamente.")
                
        except Exception as e:
            logger.error(f"❌ Erro ao gerar recomendações: {e}")
            recommendations.append("❌ Erro na análise Kelly.")
        
        return recommendations


# Exemplo de uso
if __name__ == "__main__":
    # Inicializar sistema Kelly
    kelly_system = KellyBetting(bankroll=10000.0)
    
    # Exemplo de oportunidade de aposta
    opportunity = BetOpportunity(
        id="bet_001",
        description="Manchester City vs Liverpool - City Win",
        probability=0.65,
        odds=2.1,
        confidence_level=0.8,
        max_stake=1000.0,
        sport="football",
        league="Premier League"
    )
    
    # Analisar oportunidade
    result = kelly_system.analyze_bet_opportunity(opportunity)
    
    print(f"🎯 Kelly Fraction: {result.kelly_fraction:.3f}")
    print(f"💰 Stake Recomendado: ${result.recommended_stake:.2f}")
    print(f"📊 Valor Esperado: ${result.expected_value:.2f}")
    print(f"🎲 Deve Apostar: {result.should_bet}")
    print(f"📝 Razão: {result.reason}")
    
    # Simular resultado
    if result.should_bet:
        # Simular vitória
        kelly_system.record_bet_result(
            bet_id=result.bet_id,
            won=True,
            stake=result.recommended_stake,
            payout=result.recommended_stake * opportunity.odds
        )
        
        summary = kelly_system.get_performance_summary()
        print(f"\n📈 Performance:")
        print(f"💰 Novo Bankroll: ${summary['bankroll']['current']:.2f}")
        print(f"📊 ROI: {summary['financial']['roi']:.2f}%") 