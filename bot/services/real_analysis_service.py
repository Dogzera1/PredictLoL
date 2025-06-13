from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from ..api_clients.lolesports_api_client import LoLEsportsAPIClient
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class RealAnalysisService:
    """
    Serviço de análise que usa dados reais da API LoL Esports
    Substitui os dados hardcoded por análises baseadas em dados reais
    """
    
    def __init__(self):
        self.api_client = LoLEsportsAPIClient()
        self.teams_cache = {}
        self.leagues_cache = {}
        self.cache_expiry = 3600  # 1 hora
        self.last_cache_update = 0
    
    async def __aenter__(self):
        await self.api_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.api_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def _update_cache_if_needed(self):
        """Atualiza cache de times e ligas se necessário"""
        current_time = datetime.now().timestamp()
        
        if current_time - self.last_cache_update > self.cache_expiry:
            logger.info("Atualizando cache de times e ligas...")
            
            try:
                # Buscar times
                teams = await self.api_client.get_teams()
                self.teams_cache = {}
                for team in teams:
                    team_name = team.get('name')
                    if team_name and isinstance(team_name, str) and team_name.strip():
                        self.teams_cache[team_name.lower()] = team
                        
                        # Também adicionar por código se disponível
                        team_code = team.get('code')
                        if team_code and isinstance(team_code, str) and team_code.strip():
                            self.teams_cache[team_code.lower()] = team
                
                # Buscar ligas
                leagues = await self.api_client.get_leagues()
                self.leagues_cache = {}
                for league in leagues:
                    league_name = league.get('name')
                    if league_name and isinstance(league_name, str) and league_name.strip():
                        self.leagues_cache[league_name.lower()] = league
                
                self.last_cache_update = current_time
                logger.info(f"Cache atualizado: {len(self.teams_cache)} times, {len(self.leagues_cache)} ligas")
                
            except Exception as e:
                logger.error(f"Erro ao atualizar cache: {e}")
    
    def _find_team_by_name(self, team_name: str) -> Optional[Dict]:
        """Encontra um time pelo nome (busca flexível)"""
        team_name_lower = team_name.lower()
        
        # Busca exata
        if team_name_lower in self.teams_cache:
            return self.teams_cache[team_name_lower]
        
        # Busca parcial
        for cached_name, team_data in self.teams_cache.items():
            if team_name_lower in cached_name or cached_name in team_name_lower:
                return team_data
        
        # Busca por código/abreviação
        for team_data in self.teams_cache.values():
            if team_data.get('code', '').lower() == team_name_lower:
                return team_data
        
        return None
    
    async def analyze_match(self, team1_name: str, team2_name: str) -> Dict[str, Any]:
        """
        Analisa uma partida entre dois times usando dados reais
        
        Args:
            team1_name: Nome do primeiro time
            team2_name: Nome do segundo time
            
        Returns:
            Dicionário com análise completa da partida
        """
        await self._update_cache_if_needed()
        
        # Encontrar times
        team1_data = self._find_team_by_name(team1_name)
        team2_data = self._find_team_by_name(team2_name)
        
        if not team1_data or not team2_data:
            return self._generate_fallback_analysis(team1_name, team2_name, "Times não encontrados na base de dados")
        
        try:
            # Análise baseada em dados reais
            analysis = await self._perform_real_analysis(team1_data, team2_data)
            
            return {
                "success": True,
                "team1": {
                    "name": team1_data.get('name', team1_name),
                    "probability": analysis['team1_probability'],
                    "odds_range": analysis['team1_odds_range']
                },
                "team2": {
                    "name": team2_data.get('name', team2_name),
                    "probability": analysis['team2_probability'],
                    "odds_range": analysis['team2_odds_range']
                },
                "confidence": analysis['confidence'],
                "recommendation": analysis['recommendation'],
                "analysis_details": analysis['details'],
                "data_source": "real_api"
            }
            
        except Exception as e:
            logger.error(f"Erro na análise real: {e}")
            return self._generate_fallback_analysis(team1_name, team2_name, f"Erro na análise: {str(e)}")
    
    async def _perform_real_analysis(self, team1_data: Dict, team2_data: Dict) -> Dict[str, Any]:
        """Realiza análise baseada em dados reais dos times"""
        
        # Extrair informações dos times
        team1_name = team1_data.get('name', 'Time 1')
        team2_name = team2_data.get('name', 'Time 2')
        
        # Análise baseada em dados disponíveis
        team1_score = self._calculate_team_strength(team1_data)
        team2_score = self._calculate_team_strength(team2_data)
        
        total_score = team1_score + team2_score
        
        if total_score > 0:
            team1_prob = (team1_score / total_score) * 100
            team2_prob = (team2_score / total_score) * 100
        else:
            # Fallback para análise equilibrada
            team1_prob = 50.0
            team2_prob = 50.0
        
        # Calcular odds sugeridas
        team1_odds_min = max(1.01, 1 / (team1_prob / 100) * 0.95)
        team1_odds_max = max(1.01, 1 / (team1_prob / 100) * 1.05)
        
        team2_odds_min = max(1.01, 1 / (team2_prob / 100) * 0.95)
        team2_odds_max = max(1.01, 1 / (team2_prob / 100) * 1.05)
        
        # Determinar confiança baseada na diferença
        prob_diff = abs(team1_prob - team2_prob)
        confidence = min(95, max(60, 60 + prob_diff))
        
        # Gerar recomendação
        if team1_prob > team2_prob:
            favorite = team1_name
            favorite_prob = team1_prob
            underdog = team2_name
        else:
            favorite = team2_name
            favorite_prob = team2_prob
            underdog = team1_name
        
        if prob_diff > 20:
            recommendation = f"{favorite} é forte favorito - busque odds acima de {1/(favorite_prob/100)*0.9:.2f}"
        elif prob_diff > 10:
            recommendation = f"{favorite} ligeiramente favorito - analise value cuidadosamente"
        else:
            recommendation = f"Partida equilibrada - considere {underdog} como underdog value"
        
        return {
            "team1_probability": round(team1_prob, 1),
            "team2_probability": round(team2_prob, 1),
            "team1_odds_range": (round(team1_odds_min, 2), round(team1_odds_max, 2)),
            "team2_odds_range": (round(team2_odds_min, 2), round(team2_odds_max, 2)),
            "confidence": round(confidence, 1),
            "recommendation": recommendation,
            "details": {
                "team1_strength": team1_score,
                "team2_strength": team2_score,
                "analysis_method": "real_data_based",
                "data_quality": "high" if total_score > 0 else "medium"
            }
        }
    
    def _calculate_team_strength(self, team_data: Dict) -> float:
        """Calcula força do time baseado nos dados disponíveis"""
        strength = 50.0  # Base strength
        
        # Fatores que podem influenciar a força (baseado nos dados da API)
        if 'wins' in team_data and 'losses' in team_data:
            wins = team_data.get('wins', 0)
            losses = team_data.get('losses', 0)
            total_games = wins + losses
            
            if total_games > 0:
                win_rate = wins / total_games
                strength += (win_rate - 0.5) * 40  # Ajuste baseado na taxa de vitória
        
        # Outros fatores que podem estar disponíveis
        if 'rating' in team_data:
            rating = team_data.get('rating', 1000)
            strength += (rating - 1000) / 20  # Normalizar rating
        
        if 'recent_form' in team_data:
            form = team_data.get('recent_form', 0)
            strength += form * 5
        
        return max(10.0, min(90.0, strength))  # Limitar entre 10 e 90
    
    def _generate_fallback_analysis(self, team1_name: str, team2_name: str, reason: str) -> Dict[str, Any]:
        """Gera análise de fallback quando dados reais não estão disponíveis"""
        return {
            "success": False,
            "team1": {
                "name": team1_name,
                "probability": 50.0,
                "odds_range": (1.90, 2.10)
            },
            "team2": {
                "name": team2_name,
                "probability": 50.0,
                "odds_range": (1.90, 2.10)
            },
            "confidence": 60.0,
            "recommendation": "Dados insuficientes - análise manual recomendada",
            "analysis_details": {
                "reason": reason,
                "data_source": "fallback",
                "suggestion": "Verifique nomes dos times ou tente novamente mais tarde"
            },
            "data_source": "fallback"
        }
    
    async def predict_post_draft(self, team1_name: str, team2_name: str, 
                               team1_composition: Optional[List[str]] = None,
                               team2_composition: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Previsão pós-draft com análise de composição
        
        Args:
            team1_name: Nome do primeiro time
            team2_name: Nome do segundo time
            team1_composition: Composição do time 1 (opcional)
            team2_composition: Composição do time 2 (opcional)
            
        Returns:
            Dicionário com previsão pós-draft
        """
        # Primeiro, fazer análise básica dos times
        base_analysis = await self.analyze_match(team1_name, team2_name)
        
        if not base_analysis["success"]:
            return base_analysis
        
        # Se composições foram fornecidas, ajustar previsão
        if team1_composition and team2_composition:
            composition_analysis = self._analyze_compositions(team1_composition, team2_composition)
            
            # Ajustar probabilidades baseado na composição
            base_prob1 = base_analysis["team1"]["probability"]
            base_prob2 = base_analysis["team2"]["probability"]
            
            comp_adjustment = composition_analysis["team1_advantage"]
            
            adjusted_prob1 = max(5, min(95, base_prob1 + comp_adjustment))
            adjusted_prob2 = 100 - adjusted_prob1
            
            base_analysis["team1"]["probability"] = round(adjusted_prob1, 1)
            base_analysis["team2"]["probability"] = round(adjusted_prob2, 1)
            base_analysis["confidence"] = min(95, base_analysis["confidence"] + 10)
            base_analysis["composition_analysis"] = composition_analysis
        
        base_analysis["prediction_type"] = "post_draft"
        return base_analysis
    
    def _analyze_compositions(self, comp1: List[str], comp2: List[str]) -> Dict[str, Any]:
        """Análise básica de composições (pode ser expandida)"""
        # Análise simplificada - pode ser muito mais complexa
        
        # Contar tipos de campeões (exemplo básico)
        comp1_score = len(comp1) * 10  # Base score
        comp2_score = len(comp2) * 10
        
        # Vantagem relativa
        if comp1_score > comp2_score:
            advantage = min(15, (comp1_score - comp2_score) / comp2_score * 100)
        else:
            advantage = max(-15, (comp1_score - comp2_score) / comp2_score * 100)
        
        return {
            "team1_advantage": advantage,
            "analysis": "Análise básica de composição - sistema pode ser expandido",
            "quality": "basic"
        }
    
    async def get_available_teams(self) -> List[str]:
        """Retorna lista de times disponíveis na API"""
        await self._update_cache_if_needed()
        return list(self.teams_cache.keys())
    
    async def get_team_info(self, team_name: str) -> Optional[Dict]:
        """Retorna informações detalhadas de um time"""
        await self._update_cache_if_needed()
        return self._find_team_by_name(team_name) 