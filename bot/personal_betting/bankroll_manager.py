#!/usr/bin/env python3
"""
Personal Bankroll Manager para Apostas LoL
Sistema completo de gestão financeira pessoal
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Logger local simples para evitar dependências
class SimpleLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

logger = SimpleLogger()


class RiskLevel(Enum):
    MINIMAL = "minimal"
    LOW = "low"  
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class BetStatus(Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"


@dataclass
class PersonalBet:
    """Representa uma aposta pessoal"""
    id: str
    date: str
    team: str
    opponent: str
    league: str
    odds: float
    amount: float
    potential_return: float
    reasoning: str
    confidence: float
    ev_percentage: float
    risk_level: str
    status: str = "pending"
    result: Optional[str] = None
    profit: Optional[float] = None
    resolved_date: Optional[str] = None
    notes: Optional[str] = None


@dataclass 
class BankrollSettings:
    """Configurações do bankroll"""
    initial_bankroll: float
    current_bankroll: float
    daily_limit_percentage: float = 10.0
    max_bet_percentage: float = 5.0
    kelly_multiplier: float = 0.25
    min_confidence: float = 60.0
    min_ev: float = 3.0
    risk_tolerance: str = "medium"
    auto_compound: bool = True
    stop_loss_percentage: float = 20.0


class PersonalBankrollManager:
    """Sistema de Gestão de Bankroll Pessoal"""
    
    def __init__(self, data_file: str = "bot/data/personal_betting/bankroll_data.json"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Cria diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Configurações padrão
        self.settings = BankrollSettings(
            initial_bankroll=1000.0,
            current_bankroll=1000.0
        )
        
        # Lista de apostas
        self.bets: List[PersonalBet] = []
        
        # Carrega dados existentes
        self._load_data()
        
        logger.info(f"Bankroll Manager inicializado - R${self.settings.current_bankroll:.2f}")
    
    def setup_bankroll(self, initial_amount: float, settings: Optional[Dict] = None) -> Dict:
        """Configura bankroll inicial"""
        try:
            self.settings.initial_bankroll = initial_amount
            self.settings.current_bankroll = initial_amount
            
            if settings:
                for key, value in settings.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
            
            self._save_data()
            
            return {
                "success": True,
                "message": f"Bankroll configurado com R${initial_amount:.2f}",
                "daily_limit": self.get_daily_limit(),
                "max_bet": self.get_max_bet_amount()
            }
            
        except Exception as e:
            logger.error(f"Erro ao configurar bankroll: {e}")
            return {"success": False, "error": str(e)}
    
    def calculate_bet_size(self, confidence: float, odds: float, your_probability: float, 
                          league: str = "LCK", reasoning: str = "") -> Dict:
        """Calcula tamanho ideal da aposta"""
        try:
            # Validações básicas
            if confidence < self.settings.min_confidence:
                return {
                    "recommended": False,
                    "reason": f"Confiança {confidence:.1f}% abaixo do mínimo ({self.settings.min_confidence:.1f}%)"
                }
            
            # Calcula Expected Value
            ev = (your_probability * odds) - 1
            ev_percentage = ev * 100
            
            if ev_percentage < self.settings.min_ev:
                return {
                    "recommended": False,
                    "reason": f"EV {ev_percentage:.2f}% abaixo do mínimo ({self.settings.min_ev:.1f}%)"
                }
            
            # Kelly Criterion
            if odds <= 1.0 or your_probability <= 0 or your_probability >= 1:
                kelly_fraction = 0
            else:
                b = odds - 1
                p = your_probability
                q = 1 - p
                kelly_fraction = max(0, (b * p - q) / b)
            
            # Kelly conservador
            conservative_kelly = kelly_fraction * self.settings.kelly_multiplier
            
            # Tamanho baseado em Kelly
            kelly_amount = conservative_kelly * self.settings.current_bankroll
            
            # Limites de segurança
            max_bet = self.get_max_bet_amount()
            daily_remaining = self.get_daily_remaining_limit()
            
            # Tamanho final
            final_amount = min(kelly_amount, max_bet, daily_remaining)
            
            # Determina nível de risco
            risk_level = self._determine_risk_level(final_amount)
            
            # Cálculos finais
            percentage_bankroll = (final_amount / self.settings.current_bankroll) * 100
            potential_return = final_amount * odds
            potential_profit = potential_return - final_amount
            
            return {
                "recommended": True,
                "bet_amount": round(final_amount, 2),
                "percentage_bankroll": round(percentage_bankroll, 2),
                "potential_return": round(potential_return, 2),
                "potential_profit": round(potential_profit, 2),
                "ev_percentage": round(ev_percentage, 2),
                "confidence": confidence,
                "risk_level": risk_level,
                "kelly_fraction": round(kelly_fraction, 4),
                "reasoning": reasoning,
                "warnings": self._generate_warnings(final_amount, ev_percentage, confidence)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular aposta: {e}")
            return {"recommended": False, "error": str(e)}
    
    def place_bet(self, team: str, opponent: str, league: str, odds: float, 
                  amount: float, confidence: float, ev_percentage: float, reasoning: str) -> Dict:
        """Registra uma nova aposta"""
        try:
            # Validações
            if amount > self.get_daily_remaining_limit():
                return {"success": False, "error": "Valor excede limite diário restante"}
            
            if amount > self.settings.current_bankroll:
                return {"success": False, "error": "Valor excede bankroll atual"}
            
            # Cria aposta
            bet_id = f"bet_{int(datetime.now().timestamp())}"
            bet = PersonalBet(
                id=bet_id,
                date=datetime.now().isoformat(),
                team=team,
                opponent=opponent,
                league=league,
                odds=odds,
                amount=amount,
                potential_return=amount * odds,
                reasoning=reasoning,
                confidence=confidence,
                ev_percentage=ev_percentage,
                risk_level=self._determine_risk_level(amount)
            )
            
            # Adiciona à lista
            self.bets.append(bet)
            
            # Atualiza bankroll disponível
            self.settings.current_bankroll -= amount
            
            # Salva dados
            self._save_data()
            
            logger.info(f"Aposta registrada: {team} vs {opponent} - R${amount:.2f} @ {odds}")
            
            return {
                "success": True,
                "bet_id": bet_id,
                "message": f"Aposta registrada: {team} @ {odds} - R${amount:.2f}",
                "remaining_bankroll": self.settings.current_bankroll
            }
            
        except Exception as e:
            logger.error(f"Erro ao registrar aposta: {e}")
            return {"success": False, "error": str(e)}
    
    def resolve_bet(self, bet_id: str, won: bool, notes: str = "") -> Dict:
        """Resolve uma aposta"""
        try:
            # Encontra a aposta
            bet = None
            for b in self.bets:
                if b.id == bet_id:
                    bet = b
                    break
            
            if not bet:
                return {"success": False, "error": "Aposta não encontrada"}
            
            if bet.status != "pending":
                return {"success": False, "error": "Aposta já foi resolvida"}
            
            # Atualiza aposta
            bet.status = "won" if won else "lost"
            bet.resolved_date = datetime.now().isoformat()
            bet.notes = notes
            
            if won:
                bet.profit = bet.potential_return - bet.amount
                bet.result = "WIN"
                # Retorna valor apostado + lucro
                self.settings.current_bankroll += bet.potential_return
            else:
                bet.profit = -bet.amount
                bet.result = "LOSS"
                # Valor já foi descontado, não retorna nada
            
            # Salva dados
            self._save_data()
            
            result_msg = "VITÓRIA" if won else "DERROTA"
            logger.info(f"Aposta resolvida: {bet.team} - {result_msg} - Lucro: R${bet.profit:.2f}")
            
            return {
                "success": True,
                "result": result_msg,
                "profit": bet.profit,
                "new_bankroll": self.settings.current_bankroll
            }
            
        except Exception as e:
            logger.error(f"Erro ao resolver aposta: {e}")
            return {"success": False, "error": str(e)}
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """Obtém estatísticas de performance"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filtra apostas do período
            period_bets = []
            for bet in self.bets:
                bet_date = datetime.fromisoformat(bet.date)
                if bet_date >= cutoff_date and bet.status != "pending":
                    period_bets.append(bet)
            
            if not period_bets:
                return {"message": f"Nenhuma aposta resolvida nos últimos {days} dias", "total_bets": 0}
            
            # Cálculos básicos
            total_bets = len(period_bets)
            won_bets = [bet for bet in period_bets if bet.status == "won"]
            
            win_rate = len(won_bets) / total_bets * 100
            total_staked = sum(bet.amount for bet in period_bets)
            total_profit = sum(bet.profit for bet in period_bets)
            roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
            
            # Melhor e pior aposta
            best_bet = max(period_bets, key=lambda x: x.profit)
            worst_bet = min(period_bets, key=lambda x: x.profit)
            
            return {
                "period_days": days,
                "total_bets": total_bets,
                "won_bets": len(won_bets),
                "lost_bets": total_bets - len(won_bets),
                "win_rate": round(win_rate, 2),
                "total_staked": round(total_staked, 2),
                "total_profit": round(total_profit, 2),
                "roi": round(roi, 2),
                "best_bet": {
                    "team": best_bet.team,
                    "profit": best_bet.profit,
                    "odds": best_bet.odds
                },
                "worst_bet": {
                    "team": worst_bet.team,
                    "profit": worst_bet.profit,
                    "odds": worst_bet.odds
                },
                "current_bankroll": self.settings.current_bankroll,
                "bankroll_change": self.settings.current_bankroll - self.settings.initial_bankroll
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {"error": str(e)}
    
    def get_daily_limit(self) -> float:
        """Retorna limite diário de apostas"""
        return self.settings.current_bankroll * (self.settings.daily_limit_percentage / 100)
    
    def get_max_bet_amount(self) -> float:
        """Retorna valor máximo por aposta"""
        return self.settings.current_bankroll * (self.settings.max_bet_percentage / 100)
    
    def get_daily_remaining_limit(self) -> float:
        """Retorna limite diário restante"""
        today = datetime.now().date()
        used_today = 0
        
        for bet in self.bets:
            bet_date = datetime.fromisoformat(bet.date).date()
            if bet_date == today and bet.status == "pending":
                used_today += bet.amount
        
        daily_limit = self.get_daily_limit()
        return max(0, daily_limit - used_today)
    
    def get_pending_bets(self) -> List[Dict]:
        """Retorna apostas pendentes"""
        pending = [bet for bet in self.bets if bet.status == "pending"]
        return [bet.__dict__ for bet in pending]
    
    def generate_report(self) -> str:
        """Gera relatório completo formatado"""
        stats = self.get_performance_stats()
        
        if "error" in stats:
            return f"Erro ao gerar relatório: {stats['error']}"
        
        if stats.get("total_bets", 0) == 0:
            return f"""
🏦 RELATÓRIO DE BANKROLL PESSOAL 🏦

💰 CONFIGURAÇÃO:
   Bankroll: R${self.settings.current_bankroll:.2f}
   Limite Diário: R${self.get_daily_limit():.2f}
   Máximo por Aposta: R${self.get_max_bet_amount():.2f}

📊 STATUS: Sistema pronto para uso!
"""
        
        return f"""
🏦 RELATÓRIO DE BANKROLL PESSOAL 🏦

💰 SITUAÇÃO FINANCEIRA:
   Bankroll Inicial: R${self.settings.initial_bankroll:.2f}
   Bankroll Atual: R${self.settings.current_bankroll:.2f}
   Mudança: R${stats['bankroll_change']:.2f}

📊 PERFORMANCE ({stats['period_days']} dias):
   Total de Apostas: {stats['total_bets']}
   Win Rate: {stats['win_rate']:.1f}%
   ROI: {stats['roi']:.2f}%
   Lucro Total: R${stats['total_profit']:.2f}

🏆 MELHOR/PIOR:
   Melhor: {stats['best_bet']['team']} (+R${stats['best_bet']['profit']:.2f})
   Pior: {stats['worst_bet']['team']} (R${stats['worst_bet']['profit']:.2f})

🎯 LIMITES ATUAIS:
   Limite Diário: R${self.get_daily_limit():.2f}
   Restante Hoje: R${self.get_daily_remaining_limit():.2f}
   Apostas Pendentes: {len(self.get_pending_bets())}
"""
    
    def _determine_risk_level(self, amount: float) -> str:
        """Determina nível de risco"""
        percentage = (amount / self.settings.current_bankroll) * 100
        
        if percentage >= 5.0:
            return "extreme"
        elif percentage >= 3.5:
            return "high"
        elif percentage >= 2.0:
            return "medium"
        elif percentage >= 1.0:
            return "low"
        else:
            return "minimal"
    
    def _generate_warnings(self, amount: float, ev: float, confidence: float) -> List[str]:
        """Gera avisos"""
        warnings = []
        
        risk_level = self._determine_risk_level(amount)
        if risk_level in ["high", "extreme"]:
            warnings.append(f"⚠️ Risco {risk_level.upper()}")
        
        if ev < 5.0:
            warnings.append(f"💡 EV baixo ({ev:.1f}%)")
        
        if confidence < 70:
            warnings.append(f"🤔 Confiança moderada ({confidence:.1f}%)")
        
        return warnings
    
    def _load_data(self):
        """Carrega dados do arquivo"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Carrega configurações
                if 'settings' in data:
                    settings_data = data['settings']
                    for key, value in settings_data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
                
                # Carrega apostas
                if 'bets' in data:
                    for bet_data in data['bets']:
                        bet = PersonalBet(**bet_data)
                        self.bets.append(bet)
                
                logger.info(f"Dados carregados: {len(self.bets)} apostas")
        
        except Exception as e:
            logger.warning(f"Erro ao carregar dados: {e}")
    
    def _save_data(self):
        """Salva dados no arquivo"""
        try:
            data = {
                'settings': self.settings.__dict__,
                'bets': [bet.__dict__ for bet in self.bets],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")


def create_default_manager(initial_bankroll: float = 1000.0) -> PersonalBankrollManager:
    """Cria gerenciador com configurações padrão"""
    manager = PersonalBankrollManager()
    manager.setup_bankroll(initial_bankroll)
    return manager


if __name__ == "__main__":
    # Teste básico
    manager = create_default_manager()
    
    # Configura bankroll
    setup = manager.setup_bankroll(1000.0)
    print("Setup:", setup)
    
    # Calcula aposta
    bet_calc = manager.calculate_bet_size(
        confidence=75.0,
        odds=1.85,
        your_probability=0.65,
        reasoning="T1 em boa forma"
    )
    print("Cálculo:", bet_calc)
    
    print("\n" + manager.generate_report()) 