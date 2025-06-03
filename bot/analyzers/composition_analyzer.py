"""
Analisador de Composições de Times

Sistema avançado para análise de picks & bans, sinergias entre campeões,
matchups por posição e força geral das composições.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
import json
import asyncio
from pathlib import Path

from ..utils.logger_config import get_logger

logger = get_logger(__name__)

class CompositionAnalyzer:
    """
    Analisador principal de composições de times
    
    Responsável por:
    - Análise de força individual dos campeões
    - Cálculo de sinergias internas do time
    - Análise de matchups contra composição inimiga
    - Flexibilidade estratégica da composição
    - Força por fase do jogo (early/mid/late)
    """
    
    def __init__(self):
        self.champions_db: Dict[str, Any] = {}
        self.synergies_db: Dict[str, Any] = {}
        self.counters_db: Dict[str, Any] = {}
        self._initialized: bool = False
    
    async def _ensure_initialized(self) -> None:
        """Garante que as databases estão inicializadas (lazy loading)"""
        if not self._initialized:
            await self._initialize_databases()
            self._initialized = True
    
    async def _initialize_databases(self) -> None:
        """Inicializa todas as databases necessárias"""
        try:
            await asyncio.gather(
                self._load_champions_database(),
                self._load_synergies_database(),
                self._load_counters_database()
            )
            logger.info("✅ Databases de composição carregadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar databases: {e}")
            # Cria databases vazias para funcionamento básico
            await self._create_default_databases()
    
    async def _load_champions_database(self) -> None:
        """Carrega database de campeões"""
        db_path = Path("bot/data/champions_database.json")
        
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                self.champions_db = json.load(f)
        else:
            logger.warning("Database de campeões não encontrada, criando uma básica")
            await self._create_champions_database()
    
    async def _load_synergies_database(self) -> None:
        """Carrega database de sinergias"""
        db_path = Path("bot/data/champion_synergies.json")
        
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                self.synergies_db = json.load(f)
        else:
            logger.warning("Database de sinergias não encontrada, criando uma básica")
            await self._create_synergies_database()
    
    async def _load_counters_database(self) -> None:
        """Carrega database de counters"""
        db_path = Path("bot/data/champion_counters.json")
        
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                self.counters_db = json.load(f)
        else:
            logger.warning("Database de counters não encontrada, criando uma básica")
            await self._create_counters_database()
    
    async def analyze_team_composition(
        self, 
        team_picks: List[Dict[str, Any]], 
        enemy_picks: List[Dict[str, Any]],
        patch_version: str = "14.10"
    ) -> Dict[str, Any]:
        """
        Analisa força completa da composição de um time
        
        Args:
            team_picks: Lista de picks do time [{"champion": "Azir", "position": "mid", "pick_order": 1}]
            enemy_picks: Lista de picks do time inimigo
            patch_version: Versão do patch atual
            
        Returns:
            Dict com análise completa da composição
        """
        # Garante que está inicializado antes de usar
        await self._ensure_initialized()
        
        logger.info(f"🎮 Analisando composição: {[pick['champion'] for pick in team_picks]}")
        
        try:
            # 1. Análise individual dos campeões
            individual_strength = await self._calculate_individual_strength(team_picks, patch_version)
            
            # 2. Análise de sinergias internas
            team_synergies = await self._calculate_team_synergies(team_picks)
            
            # 3. Análise de matchups contra inimigos
            matchup_advantages = await self._calculate_matchup_advantages(team_picks, enemy_picks)
            
            # 4. Flexibilidade estratégica
            strategic_flexibility = await self._calculate_strategic_flexibility(team_picks)
            
            # 5. Força por fase do jogo
            game_phase_strength = await self._calculate_game_phase_strength(team_picks)
            
            # Pontuação final (0-10)
            overall_score = (
                individual_strength * 0.25 +       # 25% peso
                team_synergies * 0.30 +            # 30% peso  
                matchup_advantages * 0.25 +        # 25% peso
                strategic_flexibility * 0.20       # 20% peso
            )
            
            result = {
                "overall_score": round(overall_score, 2),
                "individual_strength": round(individual_strength, 2),
                "team_synergies": round(team_synergies, 2),
                "matchup_advantages": round(matchup_advantages, 2),
                "strategic_flexibility": round(strategic_flexibility, 2),
                "game_phase_strength": game_phase_strength,
                "detailed_analysis": await self._generate_detailed_analysis(team_picks),
                "composition_summary": self._generate_composition_summary(overall_score, team_picks)
            }
            
            logger.info(f"✅ Análise concluída - Score: {overall_score:.2f}/10")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de composição: {e}")
            return self._get_fallback_analysis()
    
    async def _calculate_individual_strength(self, picks: List[Dict], patch: str) -> float:
        """Calcula força individual média dos campeões"""
        if not picks:
            return 5.0
        
        total_strength = 0.0
        
        for pick in picks:
            champion = pick["champion"].lower().replace(" ", "").replace("'", "")
            position = pick.get("position", "").lower()
            
            # Força base do campeão
            champion_data = self.champions_db.get(champion, {})
            base_strength = champion_data.get("base_strength", 5.0)
            
            # Multiplier por posição
            position_data = champion_data.get("positions", {})
            position_multiplier = position_data.get(position, 1.0)
            
            # Força ajustada
            champion_strength = base_strength * position_multiplier
            
            # Ajuste por patch (implementado na Fase 2)
            patch_adjustment = 0.0  # Será implementado com patch analyzer
            
            final_strength = min(10.0, max(1.0, champion_strength + patch_adjustment))
            total_strength += final_strength
        
        return total_strength / len(picks)
    
    async def _calculate_team_synergies(self, picks: List[Dict]) -> float:
        """Calcula sinergias internas do time"""
        if len(picks) < 2:
            return 5.0
        
        synergy_score = 0.0
        combinations_checked = 0
        
        # Analisa todas as combinações 2x2
        for i, pick1 in enumerate(picks):
            for j, pick2 in enumerate(picks[i+1:], i+1):
                champ1 = pick1["champion"].lower().replace(" ", "").replace("'", "")
                champ2 = pick2["champion"].lower().replace(" ", "").replace("'", "")
                
                # Procura sinergia em ambas direções
                synergy_key1 = f"{champ1}_{champ2}"
                synergy_key2 = f"{champ2}_{champ1}"
                
                synergy1 = self.synergies_db.get(synergy_key1, {}).get("synergy_score", 5.0)
                synergy2 = self.synergies_db.get(synergy_key2, {}).get("synergy_score", 5.0)
                
                # Usa a maior sinergia encontrada
                best_synergy = max(synergy1, synergy2)
                synergy_score += best_synergy
                combinations_checked += 1
        
        return synergy_score / combinations_checked if combinations_checked > 0 else 5.0
    
    async def _calculate_matchup_advantages(self, team_picks: List[Dict], enemy_picks: List[Dict]) -> float:
        """Calcula vantagens de matchup contra time inimigo"""
        if not enemy_picks:
            return 5.0
        
        matchup_score = 0.0
        matchups_checked = 0
        
        # Analisa matchups por posição
        for pick in team_picks:
            position = pick.get("position", "").lower()
            champion = pick["champion"].lower().replace(" ", "").replace("'", "")
            
            # Encontra oponente na mesma posição
            enemy_in_position = next(
                (enemy for enemy in enemy_picks if enemy.get("position", "").lower() == position), 
                None
            )
            
            if enemy_in_position:
                enemy_champion = enemy_in_position["champion"].lower().replace(" ", "").replace("'", "")
                matchup_key = f"{champion}_vs_{enemy_champion}"
                
                # Procura dados de matchup
                matchup_data = self.counters_db.get(matchup_key, {})
                advantage = matchup_data.get("advantage", 0.0)  # -1 a +1
                
                # Converte para escala 0-10
                matchup_score += 5.0 + (advantage * 5.0)
                matchups_checked += 1
        
        return matchup_score / matchups_checked if matchups_checked > 0 else 5.0
    
    async def _calculate_strategic_flexibility(self, picks: List[Dict]) -> float:
        """Calcula flexibilidade estratégica da composição"""
        flexibility_factors = []
        
        # 1. Variedade de win conditions
        win_conditions = await self._identify_win_conditions(picks)
        flexibility_factors.append(min(10.0, len(win_conditions) * 2.0))
        
        # 2. Adaptabilidade de estratégias
        strategy_options = await self._calculate_strategy_options(picks)
        flexibility_factors.append(strategy_options)
        
        # 3. Versatilidade de builds
        build_flexibility = await self._calculate_build_flexibility(picks)
        flexibility_factors.append(build_flexibility)
        
        return sum(flexibility_factors) / len(flexibility_factors) if flexibility_factors else 5.0
    
    async def _calculate_game_phase_strength(self, picks: List[Dict]) -> Dict[str, float]:
        """Calcula força por fase do jogo"""
        phases = {"early": 0.0, "mid": 0.0, "late": 0.0}
        
        for pick in picks:
            champion = pick["champion"].lower().replace(" ", "").replace("'", "")
            champion_data = self.champions_db.get(champion, {})
            
            phases["early"] += champion_data.get("early_game", 5.0)
            phases["mid"] += champion_data.get("mid_game", 5.0)
            phases["late"] += champion_data.get("late_game", 5.0)
        
        # Normaliza para 0-10
        num_picks = len(picks) if picks else 1
        for phase in phases:
            phases[phase] = round(phases[phase] / num_picks, 2)
        
        return phases
    
    async def _identify_win_conditions(self, picks: List[Dict]) -> List[str]:
        """Identifica as win conditions da composição"""
        win_conditions = []
        
        # Analisa tipos de campeões para identificar estratégias
        carry_champions = 0
        tank_champions = 0
        utility_champions = 0
        
        for pick in picks:
            champion = pick["champion"].lower().replace(" ", "").replace("'", "")
            champion_data = self.champions_db.get(champion, {})
            champion_type = champion_data.get("type", "unknown")
            
            if champion_type in ["marksman", "mage", "assassin"]:
                carry_champions += 1
            elif champion_type in ["tank", "fighter"]:
                tank_champions += 1
            elif champion_type in ["support", "enchanter"]:
                utility_champions += 1
        
        # Identifica win conditions baseado na composição
        if carry_champions >= 2:
            win_conditions.append("teamfight")
        if tank_champions >= 2:
            win_conditions.append("engage")
        if utility_champions >= 1:
            win_conditions.append("scaling")
        
        # Win conditions adicionais baseadas em campeões específicos
        champion_names = [pick["champion"].lower() for pick in picks]
        
        if any(champ in champion_names for champ in ["fiora", "jax", "tryndamere"]):
            win_conditions.append("split_push")
        if any(champ in champion_names for champ in ["sejuani", "malphite", "amumu"]):
            win_conditions.append("teamfight_engage")
        
        return win_conditions or ["standard"]
    
    async def _calculate_strategy_options(self, picks: List[Dict]) -> float:
        """Calcula opções estratégicas disponíveis"""
        # Implementação básica - será expandida
        return 6.0  # Score padrão
    
    async def _calculate_build_flexibility(self, picks: List[Dict]) -> float:
        """Calcula flexibilidade de builds"""
        # Implementação básica - será expandida  
        return 6.0  # Score padrão
    
    async def _generate_detailed_analysis(self, picks: List[Dict]) -> Dict[str, Any]:
        """Gera análise detalhada da composição"""
        return {
            "composition_type": await self._identify_composition_type(picks),
            "key_synergies": await self._identify_key_synergies(picks),
            "power_spikes": await self._identify_power_spikes(picks),
            "weaknesses": await self._identify_weaknesses(picks),
            "strengths": await self._identify_strengths(picks)
        }
    
    async def _identify_composition_type(self, picks: List[Dict]) -> str:
        """Identifica o tipo da composição"""
        # Análise básica de tipos
        champion_types = []
        for pick in picks:
            champion = pick["champion"].lower().replace(" ", "").replace("'", "")
            champion_data = self.champions_db.get(champion, {})
            champion_types.append(champion_data.get("type", "unknown"))
        
        # Determina tipo predominante
        if champion_types.count("tank") >= 2:
            return "engage_composition"
        elif champion_types.count("mage") >= 2:
            return "poke_composition"
        elif champion_types.count("marksman") >= 1 and champion_types.count("enchanter") >= 1:
            return "protect_the_carry"
        else:
            return "balanced_composition"
    
    async def _identify_key_synergies(self, picks: List[Dict]) -> List[str]:
        """Identifica sinergias chave"""
        # Implementação básica
        return ["team_synergy_1", "team_synergy_2"]
    
    async def _identify_power_spikes(self, picks: List[Dict]) -> Dict[str, str]:
        """Identifica power spikes da composição"""
        return {
            "early": "Level 6 ultimates",
            "mid": "Core items completed", 
            "late": "Full builds + scaling"
        }
    
    async def _identify_weaknesses(self, picks: List[Dict]) -> List[str]:
        """Identifica fraquezas da composição"""
        return ["early_game_vulnerability", "positioning_dependent"]
    
    async def _identify_strengths(self, picks: List[Dict]) -> List[str]:
        """Identifica pontos fortes da composição"""
        return ["teamfight_potential", "scaling_power"]
    
    def _generate_composition_summary(self, score: float, picks: List[Dict]) -> str:
        """Gera resumo da composição"""
        if score >= 8.0:
            return f"COMPOSIÇÃO SUPERIOR ({score:.1f}/10)"
        elif score >= 6.5:
            return f"COMPOSIÇÃO FORTE ({score:.1f}/10)"
        elif score >= 5.0:
            return f"COMPOSIÇÃO EQUILIBRADA ({score:.1f}/10)"
        else:
            return f"COMPOSIÇÃO FRACA ({score:.1f}/10)"
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Retorna análise padrão em caso de erro"""
        return {
            "overall_score": 5.0,
            "individual_strength": 5.0,
            "team_synergies": 5.0,
            "matchup_advantages": 5.0,
            "strategic_flexibility": 5.0,
            "game_phase_strength": {"early": 5.0, "mid": 5.0, "late": 5.0},
            "detailed_analysis": {"error": "Análise indisponível"},
            "composition_summary": "ANÁLISE INDISPONÍVEL"
        }
    
    async def _create_default_databases(self) -> None:
        """Cria databases padrão para funcionamento básico"""
        await asyncio.gather(
            self._create_champions_database(),
            self._create_synergies_database(),
            self._create_counters_database()
        )
    
    async def _create_champions_database(self) -> None:
        """Cria database básica de campeões"""
        # Database mínima para testes
        basic_champions = {
            "azir": {
                "base_strength": 7.8,
                "type": "mage",
                "positions": {"mid": 1.0, "adc": 0.6},
                "early_game": 4.0,
                "mid_game": 7.0,
                "late_game": 9.0
            },
            "graves": {
                "base_strength": 8.2,
                "type": "marksman",
                "positions": {"jungle": 1.0, "adc": 0.7},
                "early_game": 8.0,
                "mid_game": 8.5,
                "late_game": 7.0
            },
            "thresh": {
                "base_strength": 8.0,
                "type": "support",
                "positions": {"support": 1.0},
                "early_game": 7.0,
                "mid_game": 8.0,
                "late_game": 7.5
            }
        }
        
        self.champions_db = basic_champions
        
        # Salva no arquivo
        db_path = Path("bot/data/champions_database.json")
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(basic_champions, f, indent=2, ensure_ascii=False)
        
        logger.info("✅ Database básica de campeões criada")
    
    async def _create_synergies_database(self) -> None:
        """Cria database básica de sinergias"""
        basic_synergies = {
            "azir_graves": {
                "synergy_score": 8.5,
                "reason": "Graves protege Azir early, combo ultimate devastador",
                "historical_winrate": 0.74
            },
            "graves_azir": {
                "synergy_score": 8.5,
                "reason": "Graves protege Azir early, combo ultimate devastador",
                "historical_winrate": 0.74
            }
        }
        
        self.synergies_db = basic_synergies
        
        # Salva no arquivo
        db_path = Path("bot/data/champion_synergies.json")
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(basic_synergies, f, indent=2, ensure_ascii=False)
        
        logger.info("✅ Database básica de sinergias criada")
    
    async def _create_counters_database(self) -> None:
        """Cria database básica de counters"""
        basic_counters = {
            "azir_vs_leblanc": {
                "advantage": -0.3,  # LeBlanc tem vantagem
                "reason": "LeBlanc pode burst Azir facilmente",
                "confidence": 0.8
            },
            "graves_vs_kindred": {
                "advantage": 0.4,   # Graves tem vantagem
                "reason": "Graves domina early jungle vs Kindred",
                "confidence": 0.85
            }
        }
        
        self.counters_db = basic_counters
        
        # Salva no arquivo  
        db_path = Path("bot/data/champion_counters.json")
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(basic_counters, f, indent=2, ensure_ascii=False)
        
        logger.info("✅ Database básica de counters criada") 