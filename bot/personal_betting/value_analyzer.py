#!/usr/bin/env python3
"""
Manual Value Analyzer para Apostas LoL
Sistema para análise manual de value bets em League of Legends

Funcionalidades:
- Análise de probabilidades vs odds de mercado
- Cálculo automático de Expected Value
- Identificação de value bets
- Comparação de múltiplas casas de apostas
- Integração com bankroll manager
- Histórico de análises
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Logger local simples
class SimpleLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")

logger = SimpleLogger()


class AnalysisQuality(Enum):
    """Qualidade da análise"""
    EXCELLENT = "excellent"    # 90%+ confiança
    GOOD = "good"             # 75-89% confiança
    MODERATE = "moderate"     # 60-74% confiança
    POOR = "poor"            # <60% confiança


class ValueRating(Enum):
    """Rating do value da aposta"""
    EXCEPTIONAL = "exceptional"  # EV > 15%
    EXCELLENT = "excellent"      # EV 10-15%
    GOOD = "good"               # EV 5-10%
    MODERATE = "moderate"       # EV 0-5%
    POOR = "poor"              # EV < 0%


@dataclass
class TeamAnalysis:
    """Análise detalhada de um time"""
    name: str
    recent_form: str           # "5W-0L", "3W-2L", etc
    key_players_status: str    # "Full roster", "Sub jungle", etc
    meta_adaptation: int       # 1-10 scale
    individual_skill: int      # 1-10 scale
    teamwork_level: int        # 1-10 scale
    coaching_impact: int       # 1-10 scale
    motivation_level: int      # 1-10 scale
    notes: str = ""


@dataclass
class MatchAnalysis:
    """Análise completa de uma partida"""
    id: str
    date: datetime
    league: str
    team1: TeamAnalysis
    team2: TeamAnalysis
    
    # Análise contextual
    importance_level: int      # 1-10 (playoffs vs regular season)
    patch_impact: str         # Como o patch afeta os times
    historical_h2h: str       # Head-to-head histórico
    
    # Sua análise
    your_probability_team1: float  # 0-1
    confidence_level: int          # 1-100
    reasoning: str
    
    # Odds de mercado
    market_odds: Dict[str, Dict[str, float]]  # {"bet365": {"team1": 1.85, "team2": 2.10}}
    
    # Cálculos automáticos
    expected_values: Dict[str, float] = None
    best_value_bet: Optional[str] = None
    analysis_quality: str = "moderate"
    value_rating: str = "moderate"
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        data = {
            'id': self.id,
            'date': self.date.isoformat(),
            'league': self.league,
            'team1': self.team1.__dict__,
            'team2': self.team2.__dict__,
            'importance_level': self.importance_level,
            'patch_impact': self.patch_impact,
            'historical_h2h': self.historical_h2h,
            'your_probability_team1': self.your_probability_team1,
            'confidence_level': self.confidence_level,
            'reasoning': self.reasoning,
            'market_odds': self.market_odds,
            'expected_values': self.expected_values,
            'best_value_bet': self.best_value_bet,
            'analysis_quality': self.analysis_quality,
            'value_rating': self.value_rating
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MatchAnalysis':
        """Cria MatchAnalysis a partir de dicionário"""
        data['date'] = datetime.fromisoformat(data['date'])
        data['team1'] = TeamAnalysis(**data['team1'])
        data['team2'] = TeamAnalysis(**data['team2'])
        return cls(**data)


class ManualValueAnalyzer:
    """
    Sistema Completo de Análise Manual de Value Bets
    
    Funcionalidades principais:
    - Análise detalhada de times e partidas
    - Cálculo automático de Expected Value
    - Comparação de odds entre casas
    - Identificação de value bets
    - Histórico de análises
    - Integração com bankroll manager
    """
    
    def __init__(self, data_file: str = "bot/data/personal_betting/value_analysis.json"):
        """Inicializa o analisador de value"""
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Cria diretório se não existir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Lista de análises
        self.analyses: List[MatchAnalysis] = []
        
        # Carrega dados existentes
        self._load_data()
        
        logger.info(f"Manual Value Analyzer inicializado - {len(self.analyses)} análises carregadas")
    
    def create_team_analysis(self, 
                           name: str,
                           recent_form: str = "Unknown",
                           key_players_status: str = "Full roster",
                           meta_adaptation: int = 5,
                           individual_skill: int = 5,
                           teamwork_level: int = 5,
                           coaching_impact: int = 5,
                           motivation_level: int = 5,
                           notes: str = "") -> TeamAnalysis:
        """Cria análise detalhada de um time"""
        return TeamAnalysis(
            name=name,
            recent_form=recent_form,
            key_players_status=key_players_status,
            meta_adaptation=meta_adaptation,
            individual_skill=individual_skill,
            teamwork_level=teamwork_level,
            coaching_impact=coaching_impact,
            motivation_level=motivation_level,
            notes=notes
        )
    
    def analyze_match(self,
                     league: str,
                     team1_analysis: TeamAnalysis,
                     team2_analysis: TeamAnalysis,
                     your_probability_team1: float,
                     confidence_level: int,
                     reasoning: str,
                     market_odds: Dict[str, Dict[str, float]],
                     importance_level: int = 5,
                     patch_impact: str = "Neutral",
                     historical_h2h: str = "Even") -> MatchAnalysis:
        """
        Realiza análise completa de uma partida
        
        Args:
            league: Liga da partida
            team1_analysis: Análise do time 1
            team2_analysis: Análise do time 2
            your_probability_team1: Sua probabilidade para team1 (0-1)
            confidence_level: Sua confiança na análise (1-100)
            reasoning: Justificativa da análise
            market_odds: Odds do mercado {"casa": {"team1": 1.85, "team2": 2.10}}
            importance_level: Importância da partida (1-10)
            patch_impact: Como o patch afeta a partida
            historical_h2h: Histórico head-to-head
            
        Returns:
            Análise completa com cálculos de value
        """
        try:
            # Cria ID único
            analysis_id = f"analysis_{int(datetime.now().timestamp())}"
            
            # Cria análise base
            analysis = MatchAnalysis(
                id=analysis_id,
                date=datetime.now(),
                league=league,
                team1=team1_analysis,
                team2=team2_analysis,
                importance_level=importance_level,
                patch_impact=patch_impact,
                historical_h2h=historical_h2h,
                your_probability_team1=your_probability_team1,
                confidence_level=confidence_level,
                reasoning=reasoning,
                market_odds=market_odds
            )
            
            # Calcula Expected Values
            self._calculate_expected_values(analysis)
            
            # Determina qualidade da análise
            self._determine_analysis_quality(analysis)
            
            # Determina rating do value
            self._determine_value_rating(analysis)
            
            # Adiciona à lista
            self.analyses.append(analysis)
            
            # Salva dados
            self._save_data()
            
            logger.info(f"Análise criada: {team1_analysis.name} vs {team2_analysis.name}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar partida: {e}")
            raise
    
    def find_value_bets(self, 
                       min_ev: float = 5.0,
                       min_confidence: int = 70,
                       max_age_hours: int = 24) -> List[Dict]:
        """
        Encontra value bets baseado em critérios
        
        Args:
            min_ev: EV mínimo em %
            min_confidence: Confiança mínima
            max_age_hours: Idade máxima da análise em horas
            
        Returns:
            Lista de value bets encontrados
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            value_bets = []
            
            for analysis in self.analyses:
                # Filtra por idade
                if analysis.date < cutoff_time:
                    continue
                
                # Filtra por confiança
                if analysis.confidence_level < min_confidence:
                    continue
                
                # Verifica se tem EVs calculados
                if not analysis.expected_values:
                    continue
                
                # Procura value bets
                for casa, evs in analysis.expected_values.items():
                    for team, ev in evs.items():
                        if ev >= min_ev:
                            # Encontrou value bet
                            team_name = analysis.team1.name if team == 'team1' else analysis.team2.name
                            opponent = analysis.team2.name if team == 'team1' else analysis.team1.name
                            odds = analysis.market_odds[casa][team]
                            
                            value_bet = {
                                'analysis_id': analysis.id,
                                'league': analysis.league,
                                'team': team_name,
                                'opponent': opponent,
                                'casa_apostas': casa,
                                'odds': odds,
                                'ev_percentage': round(ev, 2),
                                'confidence': analysis.confidence_level,
                                'your_probability': analysis.your_probability_team1 if team == 'team1' else (1 - analysis.your_probability_team1),
                                'reasoning': analysis.reasoning,
                                'value_rating': analysis.value_rating,
                                'analysis_quality': analysis.analysis_quality,
                                'date': analysis.date.strftime("%d/%m/%Y %H:%M")
                            }
                            value_bets.append(value_bet)
            
            # Ordena por EV decrescente
            value_bets.sort(key=lambda x: x['ev_percentage'], reverse=True)
            
            return value_bets
            
        except Exception as e:
            logger.error(f"Erro ao encontrar value bets: {e}")
            return []
    
    def compare_bookmakers(self, analysis: MatchAnalysis) -> Dict:
        """
        Compara odds entre casas de apostas
        
        Args:
            analysis: Análise da partida
            
        Returns:
            Comparação detalhada das odds
        """
        try:
            if not analysis.market_odds:
                return {"error": "Nenhuma odd disponível"}
            
            team1_best = {"casa": "", "odds": 0, "ev": 0}
            team2_best = {"casa": "", "odds": 0, "ev": 0}
            
            comparison = {
                "team1_name": analysis.team1.name,
                "team2_name": analysis.team2.name,
                "your_probabilities": {
                    "team1": analysis.your_probability_team1,
                    "team2": 1 - analysis.your_probability_team1
                },
                "bookmakers": {},
                "best_odds": {},
                "arbitrage_opportunity": False
            }
            
            # Analisa cada casa
            for casa, odds in analysis.market_odds.items():
                team1_odds = odds.get('team1', 0)
                team2_odds = odds.get('team2', 0)
                
                # Calcula probabilidades implícitas
                team1_implied = 1 / team1_odds if team1_odds > 0 else 0
                team2_implied = 1 / team2_odds if team2_odds > 0 else 0
                margin = (team1_implied + team2_implied - 1) * 100
                
                # Calcula EVs
                team1_ev = (analysis.your_probability_team1 * team1_odds - 1) * 100
                team2_ev = ((1 - analysis.your_probability_team1) * team2_odds - 1) * 100
                
                comparison["bookmakers"][casa] = {
                    "team1_odds": team1_odds,
                    "team2_odds": team2_odds,
                    "team1_implied_prob": round(team1_implied, 3),
                    "team2_implied_prob": round(team2_implied, 3),
                    "margin": round(margin, 2),
                    "team1_ev": round(team1_ev, 2),
                    "team2_ev": round(team2_ev, 2)
                }
                
                # Atualiza melhores odds
                if team1_odds > team1_best["odds"]:
                    team1_best = {"casa": casa, "odds": team1_odds, "ev": team1_ev}
                
                if team2_odds > team2_best["odds"]:
                    team2_best = {"casa": casa, "odds": team2_odds, "ev": team2_ev}
            
            comparison["best_odds"] = {
                "team1": team1_best,
                "team2": team2_best
            }
            
            # Verifica oportunidade de arbitragem
            best_team1_inv = 1 / team1_best["odds"] if team1_best["odds"] > 0 else 1
            best_team2_inv = 1 / team2_best["odds"] if team2_best["odds"] > 0 else 1
            if (best_team1_inv + best_team2_inv) < 1:
                comparison["arbitrage_opportunity"] = True
                comparison["arbitrage_profit"] = round((1 - (best_team1_inv + best_team2_inv)) * 100, 2)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Erro ao comparar casas de apostas: {e}")
            return {"error": str(e)}
    
    def generate_betting_recommendation(self, 
                                      analysis: MatchAnalysis,
                                      bankroll_manager=None) -> Dict:
        """
        Gera recomendação de aposta baseada na análise
        
        Args:
            analysis: Análise da partida
            bankroll_manager: Manager de bankroll (opcional)
            
        Returns:
            Recomendação completa de aposta
        """
        try:
            # Encontra a melhor aposta
            if not analysis.expected_values or not analysis.best_value_bet:
                return {
                    "recommended": False,
                    "reason": "Nenhuma aposta com value positivo identificada"
                }
            
            # Parse do melhor bet
            casa, team = analysis.best_value_bet.split('_')
            best_ev = analysis.expected_values[casa][team]
            
            if best_ev <= 0:
                return {
                    "recommended": False,
                    "reason": f"Melhor EV disponível: {best_ev:.2f}% (negativo)"
                }
            
            # Informações da aposta
            team_name = analysis.team1.name if team == 'team1' else analysis.team2.name
            opponent = analysis.team2.name if team == 'team1' else analysis.team1.name
            odds = analysis.market_odds[casa][team]
            your_prob = analysis.your_probability_team1 if team == 'team1' else (1 - analysis.your_probability_team1)
            
            recommendation = {
                "recommended": True,
                "team": team_name,
                "opponent": opponent,
                "league": analysis.league,
                "casa_apostas": casa,
                "odds": odds,
                "ev_percentage": round(best_ev, 2),
                "your_probability": round(your_prob * 100, 1),
                "confidence": analysis.confidence_level,
                "reasoning": analysis.reasoning,
                "value_rating": analysis.value_rating,
                "analysis_quality": analysis.analysis_quality
            }
            
            # Integração com bankroll manager
            if bankroll_manager:
                bet_calc = bankroll_manager.calculate_bet_size(
                    confidence=analysis.confidence_level,
                    odds=odds,
                    your_probability=your_prob,
                    league=analysis.league,
                    reasoning=analysis.reasoning
                )
                
                recommendation["bankroll_recommendation"] = bet_calc
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendação: {e}")
            return {"recommended": False, "error": str(e)}
    
    def get_analysis_summary(self, days: int = 30) -> Dict:
        """Obtém resumo das análises"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_analyses = [a for a in self.analyses if a.date >= cutoff_date]
            
            if not recent_analyses:
                return {"message": f"Nenhuma análise nos últimos {days} dias", "total": 0}
            
            # Estatísticas básicas
            total = len(recent_analyses)
            by_quality = {}
            by_value_rating = {}
            total_value_bets = 0
            avg_confidence = sum(a.confidence_level for a in recent_analyses) / total
            
            # Conta por qualidade e value rating
            for analysis in recent_analyses:
                quality = analysis.analysis_quality
                value_rating = analysis.value_rating
                
                by_quality[quality] = by_quality.get(quality, 0) + 1
                by_value_rating[value_rating] = by_value_rating.get(value_rating, 0) + 1
                
                # Conta value bets
                if analysis.expected_values:
                    for casa_evs in analysis.expected_values.values():
                        for ev in casa_evs.values():
                            if ev > 0:
                                total_value_bets += 1
            
            return {
                "period_days": days,
                "total_analyses": total,
                "average_confidence": round(avg_confidence, 1),
                "by_quality": by_quality,
                "by_value_rating": by_value_rating,
                "total_value_bets_found": total_value_bets,
                "value_bet_rate": round((total_value_bets / total * 100), 1) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return {"error": str(e)}
    
    def export_analysis_report(self, analysis: MatchAnalysis) -> str:
        """Exporta relatório formatado de uma análise"""
        try:
            comparison = self.compare_bookmakers(analysis)
            
            report = f"""
📊 RELATÓRIO DE ANÁLISE DE VALUE
{'='*50}

🎮 PARTIDA: {analysis.team1.name} vs {analysis.team2.name}
🏆 Liga: {analysis.league}
📅 Data: {analysis.date.strftime('%d/%m/%Y %H:%M')}
⭐ Importância: {analysis.importance_level}/10

👥 ANÁLISE DOS TIMES:

🔵 {analysis.team1.name}:
   📈 Forma recente: {analysis.team1.recent_form}
   👨‍💼 Status do roster: {analysis.team1.key_players_status}
   🎯 Adaptação ao meta: {analysis.team1.meta_adaptation}/10
   💪 Skill individual: {analysis.team1.individual_skill}/10
   🤝 Trabalho em equipe: {analysis.team1.teamwork_level}/10
   🧠 Impacto do coach: {analysis.team1.coaching_impact}/10
   🔥 Motivação: {analysis.team1.motivation_level}/10
   📝 Notas: {analysis.team1.notes}

🔴 {analysis.team2.name}:
   📈 Forma recente: {analysis.team2.recent_form}
   👨‍💼 Status do roster: {analysis.team2.key_players_status}
   🎯 Adaptação ao meta: {analysis.team2.meta_adaptation}/10
   💪 Skill individual: {analysis.team2.individual_skill}/10
   🤝 Trabalho em equipe: {analysis.team2.teamwork_level}/10
   🧠 Impacto do coach: {analysis.team2.coaching_impact}/10
   🔥 Motivação: {analysis.team2.motivation_level}/10
   📝 Notas: {analysis.team2.notes}

🔍 SUA ANÁLISE:
   🎯 {analysis.team1.name}: {analysis.your_probability_team1:.1%}
   🎯 {analysis.team2.name}: {(1-analysis.your_probability_team1):.1%}
   📊 Confiança: {analysis.confidence_level}%
   🧠 Raciocínio: {analysis.reasoning}
   📈 Qualidade: {analysis.analysis_quality}
   💎 Value Rating: {analysis.value_rating}

💰 ODDS E VALUE:"""
            
            if "error" not in comparison:
                for casa, dados in comparison["bookmakers"].items():
                    report += f"""
   🏪 {casa}:
      🔵 {analysis.team1.name}: {dados['team1_odds']} (EV: {dados['team1_ev']:+.2f}%)
      🔴 {analysis.team2.name}: {dados['team2_odds']} (EV: {dados['team2_ev']:+.2f}%)
      📊 Margem: {dados['margin']:.2f}%"""
                
                best_team1 = comparison['best_odds']['team1']
                best_team2 = comparison['best_odds']['team2']
                
                report += f"""

🏆 MELHORES ODDS:
   🔵 {analysis.team1.name}: {best_team1['odds']} ({best_team1['casa']}) - EV: {best_team1['ev']:+.2f}%
   🔴 {analysis.team2.name}: {best_team2['odds']} ({best_team2['casa']}) - EV: {best_team2['ev']:+.2f}%"""
                
                if comparison.get('arbitrage_opportunity'):
                    report += f"""
   
🔥 OPORTUNIDADE DE ARBITRAGEM DETECTADA!
   💰 Lucro garantido: {comparison['arbitrage_profit']:.2f}%"""
            
            if analysis.best_value_bet:
                casa, team = analysis.best_value_bet.split('_')
                best_ev = analysis.expected_values[casa][team]
                team_name = analysis.team1.name if team == 'team1' else analysis.team2.name
                
                report += f"""

🎯 MELHOR APOSTA IDENTIFICADA:
   🏆 Time: {team_name}
   🏪 Casa: {casa}
   💰 Odds: {analysis.market_odds[casa][team]}
   📈 Expected Value: {best_ev:+.2f}%"""
            
            report += f"""

{'='*50}
📋 Análise ID: {analysis.id}
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")
            return f"Erro ao gerar relatório: {e}"
    
    def _calculate_expected_values(self, analysis: MatchAnalysis):
        """Calcula Expected Values para todas as odds"""
        analysis.expected_values = {}
        best_ev = float('-inf')
        best_bet = None
        
        for casa, odds in analysis.market_odds.items():
            casa_evs = {}
            
            # EV para team1
            if 'team1' in odds:
                team1_ev = (analysis.your_probability_team1 * odds['team1']) - 1
                casa_evs['team1'] = team1_ev * 100
                
                if team1_ev * 100 > best_ev:
                    best_ev = team1_ev * 100
                    best_bet = f"{casa}_team1"
            
            # EV para team2
            if 'team2' in odds:
                team2_prob = 1 - analysis.your_probability_team1
                team2_ev = (team2_prob * odds['team2']) - 1
                casa_evs['team2'] = team2_ev * 100
                
                if team2_ev * 100 > best_ev:
                    best_ev = team2_ev * 100
                    best_bet = f"{casa}_team2"
            
            analysis.expected_values[casa] = casa_evs
        
        analysis.best_value_bet = best_bet if best_ev > 0 else None
    
    def _determine_analysis_quality(self, analysis: MatchAnalysis):
        """Determina qualidade da análise baseada na confiança"""
        confidence = analysis.confidence_level
        
        if confidence >= 90:
            analysis.analysis_quality = "excellent"
        elif confidence >= 75:
            analysis.analysis_quality = "good"
        elif confidence >= 60:
            analysis.analysis_quality = "moderate"
        else:
            analysis.analysis_quality = "poor"
    
    def _determine_value_rating(self, analysis: MatchAnalysis):
        """Determina rating do value baseado no melhor EV"""
        if not analysis.expected_values:
            analysis.value_rating = "poor"
            return
        
        max_ev = float('-inf')
        for casa_evs in analysis.expected_values.values():
            for ev in casa_evs.values():
                max_ev = max(max_ev, ev)
        
        if max_ev >= 15:
            analysis.value_rating = "exceptional"
        elif max_ev >= 10:
            analysis.value_rating = "excellent"
        elif max_ev >= 5:
            analysis.value_rating = "good"
        elif max_ev >= 0:
            analysis.value_rating = "moderate"
        else:
            analysis.value_rating = "poor"
    
    def _load_data(self):
        """Carrega dados do arquivo"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'analyses' in data:
                    for analysis_data in data['analyses']:
                        analysis = MatchAnalysis.from_dict(analysis_data)
                        self.analyses.append(analysis)
                
                logger.info(f"Dados carregados: {len(self.analyses)} análises")
        
        except Exception as e:
            logger.warning(f"Erro ao carregar dados: {e}")
    
    def _save_data(self):
        """Salva dados no arquivo"""
        try:
            data = {
                'analyses': [analysis.to_dict() for analysis in self.analyses],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")


def create_default_analyzer() -> ManualValueAnalyzer:
    """Cria analisador com configurações padrão"""
    return ManualValueAnalyzer()


if __name__ == "__main__":
    # Teste básico
    analyzer = create_default_analyzer()
    
    # Cria análises de times
    t1_analysis = analyzer.create_team_analysis(
        name="T1",
        recent_form="8W-2L",
        key_players_status="Full roster",
        meta_adaptation=9,
        individual_skill=9,
        teamwork_level=8,
        coaching_impact=9,
        motivation_level=8,
        notes="Dominando o meta atual, Faker em grande forma"
    )
    
    gen_analysis = analyzer.create_team_analysis(
        name="Gen.G",
        recent_form="6W-4L", 
        key_players_status="Full roster",
        meta_adaptation=7,
        individual_skill=8,
        teamwork_level=7,
        coaching_impact=7,
        motivation_level=6,
        notes="Inconsistentes recentemente, problemas no late game"
    )
    
    # Odds de mercado de exemplo
    market_odds = {
        "bet365": {"team1": 1.75, "team2": 2.10},
        "betfair": {"team1": 1.80, "team2": 2.05},
        "pinnacle": {"team1": 1.78, "team2": 2.08}
    }
    
    # Analisa partida
    analysis = analyzer.analyze_match(
        league="LCK",
        team1_analysis=t1_analysis,
        team2_analysis=gen_analysis,
        your_probability_team1=0.70,  # 70% chance para T1
        confidence_level=85,
        reasoning="T1 adaptou melhor ao patch atual, Gen.G instável",
        market_odds=market_odds,
        importance_level=8
    )
    
    print("Análise criada:", analysis.id)
    print("Best value bet:", analysis.best_value_bet)
    print("Value rating:", analysis.value_rating)
    
    # Encontra value bets
    value_bets = analyzer.find_value_bets(min_ev=5.0, min_confidence=80)
    print(f"\nValue bets encontrados: {len(value_bets)}")
    
    # Gera recomendação
    recommendation = analyzer.generate_betting_recommendation(analysis)
    print(f"\nRecomendação: {recommendation['recommended']}")
    
    if recommendation['recommended']:
        print(f"Time: {recommendation['team']}")
        print(f"EV: {recommendation['ev_percentage']}%") 