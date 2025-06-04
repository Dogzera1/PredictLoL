from __future__ import annotations

import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..utils.constants import (
    MIN_CONFIDENCE_FOR_TIP,
    MIN_EV_FOR_TIP,
    MIN_UNITS,
    MAX_UNITS,
    MIN_ODDS,
    MAX_ODDS,
    UNITS_CONFIG,
    LEAGUE_TIERS,
)
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class TipRecommendation:
    """Recomendação de tip profissional"""
    units: float
    risk_level: str
    confidence_percentage: float
    ev_percentage: float
    bet_amount: float
    percentage_of_bankroll: float
    reasoning: str
    category: Dict[str, Any]
    modifiers_applied: Dict[str, float]
    
    def is_valid(self) -> bool:
        """Verifica se a recomendação é válida"""
        return (
            self.units >= MIN_UNITS and
            self.confidence_percentage >= (MIN_CONFIDENCE_FOR_TIP * 100) and
            self.ev_percentage >= (MIN_EV_FOR_TIP * 100)
        )
    
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


class ProfessionalUnitsSystem:
    """
    Sistema profissional de cálculo de unidades para apostas em LoL
    
    Características:
    - Cálculo baseado em confiança, EV e tier da liga
    - Gestão de bankroll profissional
    - Múltiplos níveis de risco (0.5 a 5.0 unidades)
    - Validação rigorosa de critérios
    - Explicações detalhadas dos cálculos
    """

    def __init__(self, bankroll: float = 1000.0):
        """
        Inicializa o sistema de unidades
        
        Args:
            bankroll: Bankroll total em reais/dólares (1 unidade = 1% do bankroll)
        """
        if bankroll <= 0:
            raise ValueError("Bankroll deve ser maior que zero")
        
        self.bankroll = float(bankroll)
        self.unit_value = self.bankroll * 0.01  # 1 unidade = 1% do bankroll
        
        logger.info(f"ProfessionalUnitsSystem inicializado - Bankroll: R${bankroll:.2f} | 1 unidade = R${self.unit_value:.2f}")

    def calculate_units(
        self, 
        confidence: float, 
        ev_percentage: float, 
        league_tier: int = 2,
        odds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula unidades de aposta baseado nos critérios profissionais
        
        Args:
            confidence: Confiança na predição (0.0 a 1.0)
            ev_percentage: Expected Value em porcentagem (0.0 a 100.0)
            league_tier: Tier da liga (1=top, 2=regional, 3=menor)
            odds: Odds da aposta (opcional, para validação adicional)
            
        Returns:
            Dicionário com resultado do cálculo
        """
        try:
            logger.debug(f"Calculando unidades: conf={confidence:.2f}, ev={ev_percentage:.2f}%, tier={league_tier}")
            
            # Validação de entrada
            validation_result = self._validate_inputs(confidence, ev_percentage, league_tier, odds)
            if not validation_result["valid"]:
                return validation_result
            
            # Normaliza EV para decimal
            ev_decimal = ev_percentage / 100.0
            
            # Encontra categoria de risco apropriada
            units_category = self._get_units_category(confidence, ev_decimal)
            
            if not units_category:
                return {
                    "valid": False,
                    "reason": "Critérios não atendem padrões profissionais mínimos",
                    "units": 0.0,
                    "risk_level": "Rejeitado",
                    "details": "Confiança ou EV abaixo do mínimo exigido"
                }
            
            # Calcula unidades base
            base_units = units_category["units"]
            
            # Aplica modificadores
            final_units = self._apply_modifiers(
                base_units, 
                confidence, 
                ev_decimal, 
                league_tier, 
                odds
            )
            
            # Valida limites finais
            final_units = max(MIN_UNITS, min(MAX_UNITS, final_units))
            
            # Calcula valores monetários
            bet_amount = final_units * self.unit_value
            percentage_of_bankroll = (bet_amount / self.bankroll) * 100
            
            # Resultado completo
            result = {
                "valid": True,
                "units": round(final_units, 1),
                "risk_level": units_category["risk_level"],
                "category": units_category,
                "bet_amount": round(bet_amount, 2),
                "percentage_of_bankroll": round(percentage_of_bankroll, 2),
                "reasoning": self._generate_reasoning(
                    confidence, ev_decimal, league_tier, final_units, units_category
                ),
                "modifiers_applied": {
                    "league_tier_modifier": self._get_league_tier_modifier(league_tier),
                    "confidence_bonus": self._get_confidence_bonus(confidence),
                    "ev_multiplier": self._get_ev_multiplier(ev_decimal),
                    "odds_adjustment": self._get_odds_adjustment(odds) if odds else 0.0
                }
            }
            
            logger.info(f"Unidades calculadas: {final_units} ({units_category['risk_level']}) - R${bet_amount:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao calcular unidades: {e}")
            return {
                "valid": False,
                "reason": f"Erro interno: {e}",
                "units": 0.0,
                "risk_level": "Erro",
                "details": str(e)
            }

    def calculate_tip(
        self, 
        confidence_percentage: float, 
        ev_percentage: float, 
        league_tier: str = "tier_2",
        market_type: str = "ML"
    ) -> TipRecommendation:
        """
        Calcula recomendação de tip profissional
        
        Args:
            confidence_percentage: Confiança em porcentagem (0-100)
            ev_percentage: Expected Value em porcentagem
            league_tier: Tier da liga ("tier_1", "tier_2", "tier_3")
            market_type: Tipo de mercado ("ML", "Handicap", etc.)
            
        Returns:
            TipRecommendation com todos os dados
        """
        # Converte inputs para formato do sistema
        confidence = confidence_percentage / 100.0
        tier_mapping = {"tier_1": 1, "tier_2": 2, "tier_3": 3}
        league_tier_int = tier_mapping.get(league_tier, 2)
        
        # Calcula usando método principal
        result = self.calculate_units(confidence, ev_percentage, league_tier_int)
        
        if not result["valid"]:
            # Retorna recomendação inválida
            return TipRecommendation(
                units=0.0,
                risk_level="Rejeitado",
                confidence_percentage=confidence_percentage,
                ev_percentage=ev_percentage,
                bet_amount=0.0,
                percentage_of_bankroll=0.0,
                reasoning=result.get("reason", "Critérios não atendidos"),
                category={},
                modifiers_applied={}
            )
        
        # Retorna recomendação válida
        return TipRecommendation(
            units=result["units"],
            risk_level=result["risk_level"],
            confidence_percentage=confidence_percentage,
            ev_percentage=ev_percentage,
            bet_amount=result["bet_amount"],
            percentage_of_bankroll=result["percentage_of_bankroll"],
            reasoning=result["reasoning"],
            category=result["category"],
            modifiers_applied=result["modifiers_applied"]
        )

    def _validate_inputs(
        self, 
        confidence: float, 
        ev_percentage: float, 
        league_tier: int, 
        odds: Optional[float]
    ) -> Dict[str, Any]:
        """Valida entradas do cálculo"""
        errors = []
        
        # Valida confiança
        if not (0.0 <= confidence <= 1.0):
            errors.append(f"Confiança deve estar entre 0.0 e 1.0 (recebido: {confidence})")
        elif confidence < MIN_CONFIDENCE_FOR_TIP:
            errors.append(f"Confiança abaixo do mínimo profissional ({MIN_CONFIDENCE_FOR_TIP:.0%})")
        
        # Valida EV
        if ev_percentage < 0:
            errors.append(f"EV não pode ser negativo (recebido: {ev_percentage}%)")
        elif ev_percentage < (MIN_EV_FOR_TIP * 100):
            errors.append(f"EV abaixo do mínimo profissional ({MIN_EV_FOR_TIP:.0%})")
        
        # Valida tier da liga
        if league_tier not in [1, 2, 3]:
            errors.append(f"Tier da liga deve ser 1, 2 ou 3 (recebido: {league_tier})")
        
        # Valida odds (se fornecidas)
        if odds is not None:
            if odds < MIN_ODDS or odds > MAX_ODDS:
                errors.append(f"Odds fora do range profissional ({MIN_ODDS}-{MAX_ODDS})")
        
        if errors:
            return {
                "valid": False,
                "reason": "Parâmetros inválidos",
                "units": 0.0,
                "risk_level": "Inválido",
                "details": "; ".join(errors)
            }
        
        return {"valid": True}

    def _get_units_category(self, confidence: float, ev_decimal: float) -> Optional[Dict[str, Any]]:
        """Determina categoria de unidades baseada em confiança e EV"""
        logger.debug(f"Buscando categoria: conf={confidence:.3f}, ev_decimal={ev_decimal:.4f}")
        
        # Ordena categorias por prioridade (mais restritivas primeiro)
        sorted_categories = sorted(
            UNITS_CONFIG.items(),
            key=lambda x: x[1]["units"],
            reverse=True
        )
        
        for category_name, category in sorted_categories:
            logger.debug(f"Testando {category_name}: min_conf={category['min_confidence']:.3f}, min_ev={category['min_ev']:.4f}")
            if (confidence >= category["min_confidence"] and 
                ev_decimal >= category["min_ev"]):
                logger.debug(f"Categoria selecionada: {category_name}")
                return category
        
        logger.debug("Nenhuma categoria encontrada!")
        return None

    def _apply_modifiers(
        self, 
        base_units: float, 
        confidence: float, 
        ev_decimal: float, 
        league_tier: int,
        odds: Optional[float]
    ) -> float:
        """Aplica modificadores ao cálculo de unidades"""
        modified_units = base_units
        
        # 1. Modificador por tier da liga
        tier_modifier = self._get_league_tier_modifier(league_tier)
        modified_units *= tier_modifier
        
        # 2. Bônus por alta confiança
        confidence_bonus = self._get_confidence_bonus(confidence)
        modified_units += confidence_bonus
        
        # 3. Multiplicador por EV excepcional
        ev_multiplier = self._get_ev_multiplier(ev_decimal)
        modified_units *= ev_multiplier
        
        # 4. Ajuste por odds (se disponível)
        if odds:
            odds_adjustment = self._get_odds_adjustment(odds)
            modified_units *= (1 + odds_adjustment)
        
        return modified_units

    def _get_league_tier_modifier(self, league_tier: int) -> float:
        """Modificador baseado no tier da liga"""
        modifiers = {
            1: 1.2,   # Tier 1 (LPL, LCK, LEC, LCS) - mais confiável
            2: 1.0,   # Tier 2 (CBLOL, LLA, etc.) - padrão
            3: 0.8    # Tier 3 (Ligas menores) - menos confiável
        }
        return modifiers.get(league_tier, 1.0)

    def _get_confidence_bonus(self, confidence: float) -> float:
        """Bônus adicional para confiança muito alta"""
        if confidence >= 0.95:
            return 0.5  # +0.5 unidades para confiança >= 95%
        elif confidence >= 0.90:
            return 0.3  # +0.3 unidades para confiança >= 90%
        elif confidence >= 0.85:
            return 0.2  # +0.2 unidades para confiança >= 85%
        return 0.0

    def _get_ev_multiplier(self, ev_decimal: float) -> float:
        """Multiplicador baseado no EV"""
        if ev_decimal >= 0.20:      # >= 20% EV
            return 1.3
        elif ev_decimal >= 0.15:    # >= 15% EV
            return 1.2
        elif ev_decimal >= 0.10:    # >= 10% EV
            return 1.1
        return 1.0

    def _get_odds_adjustment(self, odds: float) -> float:
        """Ajuste baseado nas odds (favorece odds medianas)"""
        if 1.80 <= odds <= 2.20:  # Odds ideais para value betting
            return 0.1   # +10%
        elif 1.50 <= odds <= 1.79 or 2.21 <= odds <= 2.80:  # Odds boas
            return 0.05  # +5%
        elif odds < 1.30 or odds > 3.50:  # Odds extremas
            return -0.1  # -10%
        return 0.0

    def _generate_reasoning(
        self, 
        confidence: float, 
        ev_decimal: float, 
        league_tier: int, 
        final_units: float,
        category: Dict[str, Any]
    ) -> str:
        """Gera explicação detalhada do cálculo"""
        tier_names = {1: "Tier 1 (Top)", 2: "Tier 2 (Regional)", 3: "Tier 3 (Menor)"}
        
        reasoning = f"""📊 **Cálculo de Unidades Profissional**

🎯 **Critérios Base:**
• Confiança: {confidence:.1%} (mín: {category['min_confidence']:.0%})
• Expected Value: {ev_decimal:.1%} (mín: {category['min_ev']:.0%})
• Liga: {tier_names.get(league_tier, 'Desconhecida')}

💰 **Resultado:**
• Categoria: {category['risk_level']}
• Unidades: {final_units:.1f} de {MAX_UNITS}
• Valor da aposta: R${final_units * self.unit_value:.2f}
• % do bankroll: {(final_units * self.unit_value / self.bankroll) * 100:.1f}%"""

        return reasoning

    def get_units_explanation(self) -> str:
        """Retorna explicação completa do sistema de unidades"""
        return f"""🏦 **Sistema de Unidades Profissionais**

💰 **Configuração Atual:**
• Bankroll: R${self.bankroll:.2f}
• 1 Unidade = R${self.unit_value:.2f} (1% do bankroll)
• Range: {MIN_UNITS} - {MAX_UNITS} unidades

📊 **Níveis de Risco:**
• 🔥 5.0 un. - Risco Muito Alto (90%+ conf, 15%+ EV)
• 🔥 4.0 un. - Risco Alto (85%+ conf, 12%+ EV)
• 🟠 3.0 un. - Risco Alto (80%+ conf, 10%+ EV)
• 🟡 2.5 un. - Risco Médio-Alto (75%+ conf, 8%+ EV)
• 🟢 2.0 un. - Risco Médio (70%+ conf, 6%+ EV)
• 🔵 1.0 un. - Risco Baixo (65%+ conf, 5%+ EV)
• ⚪ 0.5 un. - Risco Mínimo (60%+ conf, 3%+ EV)

🎮 **Modificadores:**
• Tier 1 (LPL/LCK/LEC/LCS): +20%
• Tier 2 (CBLOL/LLA/etc): padrão
• Tier 3 (Ligas menores): -20%
• Confiança 95%+: +0.5 unidades
• EV 20%+: +30% multiplicador
• Odds ideais (1.80-2.20): +10%

⚠️ **Critérios Mínimos:**
• Confiança mínima: {MIN_CONFIDENCE_FOR_TIP:.0%}
• EV mínimo: {MIN_EV_FOR_TIP:.0%}
• Odds aceitas: {MIN_ODDS} - {MAX_ODDS}"""

    def update_bankroll(self, new_bankroll: float) -> None:
        """Atualiza o bankroll e recalcula valor da unidade"""
        if new_bankroll <= 0:
            raise ValueError("Novo bankroll deve ser maior que zero")
        
        old_bankroll = self.bankroll
        old_unit_value = self.unit_value
        
        self.bankroll = float(new_bankroll)
        self.unit_value = self.bankroll * 0.01
        
        logger.info(f"Bankroll atualizado: R${old_bankroll:.2f} → R${new_bankroll:.2f}")
        logger.info(f"Valor da unidade: R${old_unit_value:.2f} → R${self.unit_value:.2f}")

    def calculate_kelly_criterion(self, win_probability: float, odds: float) -> float:
        """
        Calcula fração de Kelly como referência adicional
        
        Args:
            win_probability: Probabilidade de vitória (0.0 a 1.0)
            odds: Odds decimais
            
        Returns:
            Fração de Kelly (porcentagem do bankroll)
        """
        if not (0.0 < win_probability < 1.0) or odds <= 1.0:
            return 0.0
        
        # Fórmula de Kelly: f = (bp - q) / b
        # onde: b = odds - 1, p = win_probability, q = 1 - p
        b = odds - 1
        p = win_probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Kelly conservador (25% do Kelly completo)
        conservative_kelly = max(0.0, kelly_fraction * 0.25)
        
        return min(conservative_kelly, 0.05)  # Máximo 5% do bankroll

    def get_risk_assessment(self, units: float) -> str:
        """Avalia nível de risco de uma aposta"""
        risk_percentage = (units / MAX_UNITS) * 100
        
        if units >= 4.5:
            return f"🔥 RISCO EXTREMO ({risk_percentage:.0f}%)"
        elif units >= 3.5:
            return f"🔥 RISCO MUITO ALTO ({risk_percentage:.0f}%)"
        elif units >= 2.5:
            return f"🟠 RISCO ALTO ({risk_percentage:.0f}%)"
        elif units >= 1.5:
            return f"🟡 RISCO MÉDIO ({risk_percentage:.0f}%)"
        elif units >= 1.0:
            return f"🟢 RISCO BAIXO ({risk_percentage:.0f}%)"
        else:
            return f"🔵 RISCO MÍNIMO ({risk_percentage:.0f}%)"

    def validate_tip_criteria(self, analysis_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida se uma análise atende critérios para tip profissional
        
        Args:
            analysis_data: Dados da análise com confidence, ev, etc.
            
        Returns:
            Tupla (válido, motivo)
        """
        confidence = analysis_data.get("confidence", 0.0)
        ev_percentage = analysis_data.get("ev_percentage", 0.0)
        odds = analysis_data.get("odds")
        
        # Critérios mínimos
        if confidence < MIN_CONFIDENCE_FOR_TIP:
            return False, f"Confiança muito baixa ({confidence:.1%} < {MIN_CONFIDENCE_FOR_TIP:.0%})"
        
        if ev_percentage < (MIN_EV_FOR_TIP * 100):
            return False, f"EV muito baixo ({ev_percentage:.1f}% < {MIN_EV_FOR_TIP:.0%})"
        
        if odds and (odds < MIN_ODDS or odds > MAX_ODDS):
            return False, f"Odds fora do range profissional ({odds:.2f})"
        
        # Calcula unidades para validação adicional
        units_result = self.calculate_units(confidence, ev_percentage)
        
        if not units_result["valid"] or units_result["units"] < MIN_UNITS:
            return False, "Não atende critérios de unidades mínimas"
        
        return True, f"Critérios atendidos - {units_result['units']:.1f} unidades ({units_result['risk_level']})" 
