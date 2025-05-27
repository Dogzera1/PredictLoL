#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Histórico de Apostas para Value Betting
Tracking completo de reds, greens, ROI e performance das tips
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import os

logger = logging.getLogger(__name__)

class BetStatus(Enum):
    """Status das apostas"""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"
    CASHOUT = "cashout"

class BetType(Enum):
    """Tipos de apostas"""
    VALUE_BET = "value_bet"
    LIVE_BET = "live_bet"
    PREDICTION = "prediction"

@dataclass
class BetRecord:
    """Registro individual de aposta"""
    id: str
    timestamp: datetime
    match: str
    league: str
    bet_type: BetType
    favored_team: str
    predicted_winner: str
    win_probability: float
    market_odds: float
    expected_value: float
    value_percentage: float
    units: float
    stake_amount: float
    confidence: str
    status: BetStatus
    result_odds: Optional[float] = None
    profit_loss: Optional[float] = None
    actual_winner: Optional[str] = None
    match_duration: Optional[int] = None  # em minutos
    notes: Optional[str] = None

class BettingHistorySystem:
    """Sistema de histórico de apostas com análise de performance"""
    
    def __init__(self, data_file: str = "betting_history.json"):
        self.data_file = data_file
        self.bet_records: List[BetRecord] = []
        self.load_history()
        logger.info("📊 Sistema de Histórico de Apostas inicializado")
    
    def load_history(self):
        """Carregar histórico do arquivo"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for record_data in data:
                    # Converter timestamp string para datetime
                    record_data['timestamp'] = datetime.fromisoformat(record_data['timestamp'])
                    
                    # Converter enums
                    record_data['bet_type'] = BetType(record_data['bet_type'])
                    record_data['status'] = BetStatus(record_data['status'])
                    
                    # Criar objeto BetRecord
                    bet_record = BetRecord(**record_data)
                    self.bet_records.append(bet_record)
                
                logger.info(f"📚 {len(self.bet_records)} registros carregados do histórico")
            else:
                logger.info("📝 Criando novo arquivo de histórico")
                self.bet_records = []
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar histórico: {e}")
            self.bet_records = []
    
    def save_history(self):
        """Salvar histórico no arquivo"""
        try:
            data = []
            for record in self.bet_records:
                record_dict = asdict(record)
                # Converter datetime para string
                record_dict['timestamp'] = record.timestamp.isoformat()
                # Converter enums para string
                record_dict['bet_type'] = record.bet_type.value
                record_dict['status'] = record.status.value
                data.append(record_dict)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Histórico salvo: {len(self.bet_records)} registros")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar histórico: {e}")
    
    def add_bet(self, opportunity: Dict) -> str:
        """Adicionar nova aposta ao histórico"""
        try:
            bet_id = f"bet_{int(datetime.now().timestamp())}_{len(self.bet_records)}"
            
            bet_record = BetRecord(
                id=bet_id,
                timestamp=datetime.now(),
                match=opportunity['match'],
                league=opportunity['league'],
                bet_type=BetType.VALUE_BET,
                favored_team=opportunity['favored_team'],
                predicted_winner=opportunity['favored_team'],
                win_probability=opportunity['win_probability'],
                market_odds=opportunity['market_odds'],
                expected_value=opportunity['expected_value'],
                value_percentage=opportunity['value_percentage'],
                units=opportunity.get('units', 0),
                stake_amount=opportunity.get('stake_amount', 0),
                confidence=opportunity['confidence'],
                status=BetStatus.PENDING
            )
            
            self.bet_records.append(bet_record)
            self.save_history()
            
            logger.info(f"✅ Nova aposta adicionada: {bet_id}")
            return bet_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar aposta: {e}")
            return ""
    
    def update_bet_result(self, bet_id: str, won: bool, actual_winner: str = None, 
                         match_duration: int = None, notes: str = None) -> bool:
        """Atualizar resultado de uma aposta"""
        try:
            for bet in self.bet_records:
                if bet.id == bet_id:
                    bet.status = BetStatus.WON if won else BetStatus.LOST
                    bet.actual_winner = actual_winner
                    bet.match_duration = match_duration
                    bet.notes = notes
                    
                    # Calcular profit/loss
                    if won:
                        bet.result_odds = bet.market_odds
                        bet.profit_loss = bet.stake_amount * (bet.market_odds - 1)
                    else:
                        bet.result_odds = 0
                        bet.profit_loss = -bet.stake_amount
                    
                    self.save_history()
                    logger.info(f"📊 Resultado atualizado para {bet_id}: {'GREEN' if won else 'RED'}")
                    return True
            
            logger.warning(f"⚠️ Aposta {bet_id} não encontrada")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar resultado: {e}")
            return False
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """Obter estatísticas de performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_bets = [bet for bet in self.bet_records 
                          if bet.timestamp >= cutoff_date and bet.status in [BetStatus.WON, BetStatus.LOST]]
            
            if not recent_bets:
                return self._get_empty_stats()
            
            # Estatísticas básicas
            total_bets = len(recent_bets)
            greens = len([bet for bet in recent_bets if bet.status == BetStatus.WON])
            reds = len([bet for bet in recent_bets if bet.status == BetStatus.LOST])
            win_rate = (greens / total_bets) * 100 if total_bets > 0 else 0
            
            # Estatísticas financeiras
            total_staked = sum(bet.stake_amount for bet in recent_bets)
            total_profit = sum(bet.profit_loss or 0 for bet in recent_bets)
            roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0
            
            # Estatísticas por confiança
            confidence_stats = self._calculate_confidence_stats(recent_bets)
            
            # Estatísticas por liga
            league_stats = self._calculate_league_stats(recent_bets)
            
            # Sequências
            current_streak = self._calculate_current_streak()
            best_streak = self._calculate_best_streak(recent_bets)
            worst_streak = self._calculate_worst_streak(recent_bets)
            
            # Unidades
            total_units = sum(bet.units for bet in recent_bets)
            units_profit = sum((bet.profit_loss or 0) / 100 for bet in recent_bets)  # Assumindo 1 unidade = R$ 100
            
            return {
                'period_days': days,
                'total_bets': total_bets,
                'greens': greens,
                'reds': reds,
                'win_rate': win_rate,
                'total_staked': total_staked,
                'total_profit': total_profit,
                'roi': roi,
                'total_units': total_units,
                'units_profit': units_profit,
                'current_streak': current_streak,
                'best_streak': best_streak,
                'worst_streak': worst_streak,
                'confidence_stats': confidence_stats,
                'league_stats': league_stats,
                'avg_odds': sum(bet.market_odds for bet in recent_bets) / total_bets,
                'avg_value': sum(bet.value_percentage for bet in recent_bets) / total_bets,
                'avg_units': sum(bet.units for bet in recent_bets) / total_bets
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
            return self._get_empty_stats()
    
    def _get_empty_stats(self) -> Dict:
        """Retornar estatísticas vazias"""
        return {
            'period_days': 0,
            'total_bets': 0,
            'greens': 0,
            'reds': 0,
            'win_rate': 0,
            'total_staked': 0,
            'total_profit': 0,
            'roi': 0,
            'total_units': 0,
            'units_profit': 0,
            'current_streak': {'type': 'none', 'count': 0},
            'best_streak': {'type': 'win', 'count': 0},
            'worst_streak': {'type': 'loss', 'count': 0},
            'confidence_stats': {},
            'league_stats': {},
            'avg_odds': 0,
            'avg_value': 0,
            'avg_units': 0
        }
    
    def _calculate_confidence_stats(self, bets: List[BetRecord]) -> Dict:
        """Calcular estatísticas por nível de confiança"""
        confidence_data = {}
        
        for confidence in ['Alta', 'Média', 'Baixa']:
            conf_bets = [bet for bet in bets if bet.confidence == confidence]
            if conf_bets:
                greens = len([bet for bet in conf_bets if bet.status == BetStatus.WON])
                total = len(conf_bets)
                win_rate = (greens / total) * 100
                profit = sum(bet.profit_loss or 0 for bet in conf_bets)
                
                confidence_data[confidence] = {
                    'total': total,
                    'greens': greens,
                    'reds': total - greens,
                    'win_rate': win_rate,
                    'profit': profit
                }
        
        return confidence_data
    
    def _calculate_league_stats(self, bets: List[BetRecord]) -> Dict:
        """Calcular estatísticas por liga"""
        league_data = {}
        
        leagues = set(bet.league for bet in bets)
        for league in leagues:
            league_bets = [bet for bet in bets if bet.league == league]
            greens = len([bet for bet in league_bets if bet.status == BetStatus.WON])
            total = len(league_bets)
            win_rate = (greens / total) * 100 if total > 0 else 0
            profit = sum(bet.profit_loss or 0 for bet in league_bets)
            
            league_data[league] = {
                'total': total,
                'greens': greens,
                'reds': total - greens,
                'win_rate': win_rate,
                'profit': profit
            }
        
        return league_data
    
    def _calculate_current_streak(self) -> Dict:
        """Calcular sequência atual"""
        if not self.bet_records:
            return {'type': 'none', 'count': 0}
        
        # Ordenar por timestamp (mais recente primeiro)
        sorted_bets = sorted([bet for bet in self.bet_records 
                            if bet.status in [BetStatus.WON, BetStatus.LOST]], 
                           key=lambda x: x.timestamp, reverse=True)
        
        if not sorted_bets:
            return {'type': 'none', 'count': 0}
        
        current_status = sorted_bets[0].status
        count = 1
        
        for bet in sorted_bets[1:]:
            if bet.status == current_status:
                count += 1
            else:
                break
        
        streak_type = 'win' if current_status == BetStatus.WON else 'loss'
        return {'type': streak_type, 'count': count}
    
    def _calculate_best_streak(self, bets: List[BetRecord]) -> Dict:
        """Calcular melhor sequência de vitórias"""
        if not bets:
            return {'type': 'win', 'count': 0}
        
        sorted_bets = sorted(bets, key=lambda x: x.timestamp)
        max_streak = 0
        current_streak = 0
        
        for bet in sorted_bets:
            if bet.status == BetStatus.WON:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return {'type': 'win', 'count': max_streak}
    
    def _calculate_worst_streak(self, bets: List[BetRecord]) -> Dict:
        """Calcular pior sequência de derrotas"""
        if not bets:
            return {'type': 'loss', 'count': 0}
        
        sorted_bets = sorted(bets, key=lambda x: x.timestamp)
        max_streak = 0
        current_streak = 0
        
        for bet in sorted_bets:
            if bet.status == BetStatus.LOST:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return {'type': 'loss', 'count': max_streak}
    
    def get_recent_bets(self, limit: int = 10) -> List[BetRecord]:
        """Obter apostas recentes"""
        sorted_bets = sorted(self.bet_records, key=lambda x: x.timestamp, reverse=True)
        return sorted_bets[:limit]
    
    def get_pending_bets(self) -> List[BetRecord]:
        """Obter apostas pendentes"""
        return [bet for bet in self.bet_records if bet.status == BetStatus.PENDING]
    
    def simulate_historical_data(self, count: int = 50):
        """Simular dados históricos para demonstração"""
        try:
            import random
            from datetime import datetime, timedelta
            
            # Times e ligas para simulação
            teams_by_league = {
                'LCK': [('T1', 'GEN'), ('DK', 'KT'), ('DRX', 'BRO')],
                'LPL': [('JDG', 'BLG'), ('WBG', 'TES'), ('EDG', 'IG')],
                'LEC': [('G2', 'FNC'), ('MAD', 'VIT'), ('SK', 'BDS')],
                'LCS': [('C9', 'TL'), ('TSM', '100T'), ('FLY', 'EG')],
                'CBLOL': [('LOUD', 'FURIA'), ('RED', 'KBM'), ('VK', 'PNG')]
            }
            
            # Gerar apostas históricas
            for i in range(count):
                # Data aleatória nos últimos 60 dias
                days_ago = random.randint(1, 60)
                timestamp = datetime.now() - timedelta(days=days_ago)
                
                # Liga e times aleatórios
                league = random.choice(list(teams_by_league.keys()))
                team_pair = random.choice(teams_by_league[league])
                match = f"{team_pair[0]} vs {team_pair[1]}"
                
                # Dados da aposta
                win_prob = random.uniform(0.45, 0.85)
                odds = random.uniform(1.5, 3.5)
                ev = (win_prob * odds) - 1
                value_pct = ev * 100
                
                confidence = random.choice(['Alta', 'Média', 'Baixa'])
                units = random.uniform(0.5, 3.0)
                stake = units * 100
                
                # Resultado (baseado na probabilidade real)
                won = random.random() < win_prob
                
                bet_record = BetRecord(
                    id=f"sim_bet_{i}_{int(timestamp.timestamp())}",
                    timestamp=timestamp,
                    match=match,
                    league=league,
                    bet_type=BetType.VALUE_BET,
                    favored_team=team_pair[0],
                    predicted_winner=team_pair[0],
                    win_probability=win_prob,
                    market_odds=odds,
                    expected_value=ev,
                    value_percentage=value_pct,
                    units=units,
                    stake_amount=stake,
                    confidence=confidence,
                    status=BetStatus.WON if won else BetStatus.LOST,
                    result_odds=odds if won else 0,
                    profit_loss=stake * (odds - 1) if won else -stake,
                    actual_winner=team_pair[0] if won else team_pair[1],
                    match_duration=random.randint(25, 45)
                )
                
                self.bet_records.append(bet_record)
            
            self.save_history()
            logger.info(f"🎭 {count} apostas históricas simuladas adicionadas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao simular dados históricos: {e}")
    
    def export_to_csv(self, filename: str = None) -> str:
        """Exportar histórico para CSV"""
        try:
            import csv
            
            if not filename:
                filename = f"betting_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id', 'timestamp', 'match', 'league', 'bet_type', 'favored_team',
                    'win_probability', 'market_odds', 'value_percentage', 'units',
                    'stake_amount', 'confidence', 'status', 'profit_loss', 'actual_winner'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for bet in self.bet_records:
                    row = {
                        'id': bet.id,
                        'timestamp': bet.timestamp.isoformat(),
                        'match': bet.match,
                        'league': bet.league,
                        'bet_type': bet.bet_type.value,
                        'favored_team': bet.favored_team,
                        'win_probability': bet.win_probability,
                        'market_odds': bet.market_odds,
                        'value_percentage': bet.value_percentage,
                        'units': bet.units,
                        'stake_amount': bet.stake_amount,
                        'confidence': bet.confidence,
                        'status': bet.status.value,
                        'profit_loss': bet.profit_loss,
                        'actual_winner': bet.actual_winner
                    }
                    writer.writerow(row)
            
            logger.info(f"📊 Histórico exportado para {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar CSV: {e}")
            return "" 