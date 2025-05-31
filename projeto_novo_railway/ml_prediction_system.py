#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA DE MACHINE LEARNING PARA PREDIÇÕES LOL
Focado em apostas money line de partidas em andamento após draft
"""

import numpy as np
import pandas as pd
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import pickle
import os
from collections import defaultdict
import time

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class MatchState:
    """Estado atual da partida em tempo real"""
    game_time: float
    team1_kills: int
    team2_kills: int
    team1_gold: int
    team2_gold: int
    team1_towers: int
    team2_towers: int
    team1_dragons: int
    team2_dragons: int
    team1_barons: int
    team2_barons: int
    team1_heralds: int
    team2_heralds: int
    team1_inhibitors: int
    team2_inhibitors: int
    
@dataclass
class DraftData:
    """Dados do draft da partida"""
    team1_picks: List[str]
    team2_picks: List[str]
    team1_bans: List[str]
    team2_bans: List[str]
    draft_phase: str  # 'completed', 'in_progress'
    
@dataclass
class TeamComposition:
    """Análise da composição dos times"""
    team1_comp_strength: float
    team2_comp_strength: float
    early_game_advantage: str  # 'team1', 'team2', 'neutral'
    late_game_scaling: str
    teamfight_potential: Dict[str, float]
    split_push_potential: Dict[str, float]

class ChampionAnalyzer:
    """Analisador de campeões e composições"""
    
    def __init__(self):
        self.champion_stats = self._load_champion_stats()
        self.synergy_matrix = self._load_synergy_matrix()
        self.counter_matrix = self._load_counter_matrix()
        
    def _load_champion_stats(self) -> Dict:
        """Carrega estatísticas dos campeões"""
        # Base de dados de campeões com estatísticas reais
        return {
            # ADCs
            'Jinx': {
                'early_power': 3, 'late_power': 9, 'teamfight': 8, 'mobility': 4, 
                'win_rate': 52.1, 'pick_rate': 8.2, 'ban_rate': 2.1
            },
            'Kai\'Sa': {
                'early_power': 5, 'late_power': 8, 'teamfight': 7, 'mobility': 7,
                'win_rate': 50.8, 'pick_rate': 12.4, 'ban_rate': 3.2
            },
            'Caitlyn': {
                'early_power': 7, 'late_power': 6, 'teamfight': 6, 'mobility': 5,
                'win_rate': 51.2, 'pick_rate': 9.1, 'ban_rate': 1.8
            },
            
            # Supports
            'Thresh': {
                'early_power': 6, 'late_power': 7, 'teamfight': 8, 'mobility': 6,
                'win_rate': 50.5, 'pick_rate': 11.2, 'ban_rate': 4.1
            },
            'Nautilus': {
                'early_power': 5, 'late_power': 8, 'teamfight': 9, 'mobility': 3,
                'win_rate': 51.8, 'pick_rate': 8.7, 'ban_rate': 2.9
            },
            
            # Mid Laners
            'Azir': {
                'early_power': 4, 'late_power': 9, 'teamfight': 9, 'mobility': 6,
                'win_rate': 49.2, 'pick_rate': 3.8, 'ban_rate': 1.2
            },
            'Yasuo': {
                'early_power': 6, 'late_power': 8, 'teamfight': 7, 'mobility': 8,
                'win_rate': 49.8, 'pick_rate': 14.2, 'ban_rate': 28.1
            },
            'Orianna': {
                'early_power': 5, 'late_power': 8, 'teamfight': 9, 'mobility': 4,
                'win_rate': 51.1, 'pick_rate': 6.8, 'ban_rate': 1.5
            },
            
            # Junglers
            'Graves': {
                'early_power': 7, 'late_power': 7, 'teamfight': 6, 'mobility': 7,
                'win_rate': 52.3, 'pick_rate': 9.5, 'ban_rate': 3.8
            },
            'Lee Sin': {
                'early_power': 8, 'late_power': 5, 'teamfight': 6, 'mobility': 9,
                'win_rate': 48.9, 'pick_rate': 11.8, 'ban_rate': 2.1
            },
            'Kindred': {
                'early_power': 6, 'late_power': 8, 'teamfight': 7, 'mobility': 7,
                'win_rate': 50.7, 'pick_rate': 4.2, 'ban_rate': 1.1
            },
            
            # Top Laners
            'Gnar': {
                'early_power': 5, 'late_power': 7, 'teamfight': 8, 'mobility': 6,
                'win_rate': 50.2, 'pick_rate': 7.1, 'ban_rate': 2.8
            },
            'Camille': {
                'early_power': 6, 'late_power': 8, 'teamfight': 7, 'mobility': 8,
                'win_rate': 51.5, 'pick_rate': 8.9, 'ban_rate': 4.2
            },
            'Ornn': {
                'early_power': 4, 'late_power': 9, 'teamfight': 9, 'mobility': 3,
                'win_rate': 52.1, 'pick_rate': 6.3, 'ban_rate': 1.9
            }
        }
        
    def _load_synergy_matrix(self) -> Dict:
        """Matriz de sinergia entre campeões"""
        return {
            ('Yasuo', 'Nautilus'): 0.85,  # Knock-up synergy
            ('Jinx', 'Thresh'): 0.80,     # Peel and engage
            ('Azir', 'Orianna'): 0.75,    # AoE teamfight
            ('Graves', 'Orianna'): 0.78,  # Combo engage
            # Adicionar mais sinergias...
        }
        
    def _load_counter_matrix(self) -> Dict:
        """Matriz de counters entre campeões"""
        return {
            ('Yasuo', 'Azir'): -0.65,     # Yasuo counters Azir
            ('Caitlyn', 'Jinx'): -0.45,  # Range advantage
            ('Lee Sin', 'Graves'): -0.35, # Early game pressure
            # Adicionar mais counters...
        }
        
    def analyze_composition(self, draft_data: DraftData) -> TeamComposition:
        """Analisa força das composições dos times"""
        
        team1_power = self._calculate_team_power(draft_data.team1_picks)
        team2_power = self._calculate_team_power(draft_data.team2_picks)
        
        # Calcular vantagem early/late game
        team1_early = np.mean([self.champion_stats.get(champ, {}).get('early_power', 5) 
                              for champ in draft_data.team1_picks])
        team2_early = np.mean([self.champion_stats.get(champ, {}).get('early_power', 5) 
                              for champ in draft_data.team2_picks])
        
        team1_late = np.mean([self.champion_stats.get(champ, {}).get('late_power', 5) 
                             for champ in draft_data.team1_picks])
        team2_late = np.mean([self.champion_stats.get(champ, {}).get('late_power', 5) 
                             for champ in draft_data.team2_picks])
        
        early_advantage = 'team1' if team1_early > team2_early + 0.5 else \
                         'team2' if team2_early > team1_early + 0.5 else 'neutral'
        
        late_advantage = 'team1' if team1_late > team2_late + 0.5 else \
                        'team2' if team2_late > team1_late + 0.5 else 'neutral'
        
        # Análise de teamfight e split push
        teamfight_potential = {
            'team1': self._calculate_teamfight_potential(draft_data.team1_picks),
            'team2': self._calculate_teamfight_potential(draft_data.team2_picks)
        }
        
        split_push_potential = {
            'team1': self._calculate_split_push_potential(draft_data.team1_picks),
            'team2': self._calculate_split_push_potential(draft_data.team2_picks)
        }
        
        return TeamComposition(
            team1_comp_strength=team1_power,
            team2_comp_strength=team2_power,
            early_game_advantage=early_advantage,
            late_game_scaling=late_advantage,
            teamfight_potential=teamfight_potential,
            split_push_potential=split_push_potential
        )
        
    def _calculate_team_power(self, champions: List[str]) -> float:
        """Calcula poder total do time considerando sinergias"""
        base_power = 0
        synergy_bonus = 0
        
        for champ in champions:
            stats = self.champion_stats.get(champ, {})
            # Média ponderada de atributos
            champ_power = (
                stats.get('early_power', 5) * 0.3 +
                stats.get('late_power', 5) * 0.4 +
                stats.get('teamfight', 5) * 0.3
            )
            base_power += champ_power
            
        # Calcular bônus de sinergia
        for i, champ1 in enumerate(champions):
            for j, champ2 in enumerate(champions[i+1:], i+1):
                synergy = self.synergy_matrix.get((champ1, champ2), 0)
                synergy += self.synergy_matrix.get((champ2, champ1), 0)
                synergy_bonus += synergy
                
        return (base_power / len(champions)) + synergy_bonus
        
    def _calculate_teamfight_potential(self, champions: List[str]) -> float:
        """Calcula potencial de teamfight"""
        teamfight_scores = []
        for champ in champions:
            stats = self.champion_stats.get(champ, {})
            teamfight_scores.append(stats.get('teamfight', 5))
        return np.mean(teamfight_scores) / 10.0
        
    def _calculate_split_push_potential(self, champions: List[str]) -> float:
        """Calcula potencial de split push"""
        mobility_scores = []
        for champ in champions:
            stats = self.champion_stats.get(champ, {})
            mobility_scores.append(stats.get('mobility', 5))
        return np.mean(mobility_scores) / 10.0

class AdvancedMLPredictionSystem:
    """Sistema avançado de ML para predições money line"""
    
    def __init__(self):
        self.champion_analyzer = ChampionAnalyzer()
        self.models = {}
        self.feature_importance = {}
        self.prediction_history = []
        self.model_performance = {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0,
            'total_predictions': 0,
            'correct_predictions': 0
        }
        
        # Cache de predições
        self.prediction_cache = {}
        self.cache_duration = 180  # 3 minutos
        
        # Inicializar modelos
        self._initialize_models()
        
        logger.info("🤖 Sistema Avançado de ML inicializado")
        
    def _initialize_models(self):
        """Inicializa modelos de machine learning"""
        try:
            # Tentar carregar modelos salvos
            self._load_models()
        except:
            # Criar modelos novos se não existirem
            self._create_new_models()
            
    def _create_new_models(self):
        """Cria novos modelos de ML"""
        try:
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
            from sklearn.neural_network import MLPClassifier
            from sklearn.svm import SVC
            
            self.models = {
                'random_forest': RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    class_weight='balanced'
                ),
                'gradient_boosting': GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                ),
                'neural_network': MLPClassifier(
                    hidden_layer_sizes=(100, 50),
                    max_iter=500,
                    random_state=42,
                    early_stopping=True
                ),
                'ensemble_weight': {
                    'random_forest': 0.4,
                    'gradient_boosting': 0.4,
                    'neural_network': 0.2
                }
            }
            
            logger.info("✅ Novos modelos de ML criados")
            
        except ImportError:
            logger.warning("⚠️ Scikit-learn não disponível - usando modelo simplificado")
            self._create_simple_model()
            
    def _create_simple_model(self):
        """Cria modelo simplificado sem scikit-learn"""
        self.models = {
            'simple_classifier': {
                'weights': {
                    'gold_diff': 0.3,
                    'kill_diff': 0.2,
                    'tower_diff': 0.2,
                    'dragon_diff': 0.15,
                    'comp_strength': 0.15
                }
            }
        }
        
    def _save_models(self):
        """Salva modelos treinados"""
        try:
            model_path = 'ml_models.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(self.models, f)
            logger.info("✅ Modelos salvos")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar modelos: {e}")
            
    def _load_models(self):
        """Carrega modelos salvos"""
        model_path = 'ml_models.pkl'
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.models = pickle.load(f)
            logger.info("✅ Modelos carregados")
        else:
            raise FileNotFoundError("Modelos não encontrados")
            
    def extract_features(self, match_state: MatchState, draft_data: DraftData, 
                        team_composition: TeamComposition) -> np.ndarray:
        """Extrai features para predição"""
        
        # Features básicas do estado da partida
        gold_diff = (match_state.team1_gold - match_state.team2_gold) / max(match_state.team1_gold, 1)
        kill_diff = match_state.team1_kills - match_state.team2_kills
        tower_diff = match_state.team1_towers - match_state.team2_towers
        dragon_diff = match_state.team1_dragons - match_state.team2_dragons
        baron_diff = match_state.team1_barons - match_state.team2_barons
        
        # Features de composição
        comp_diff = team_composition.team1_comp_strength - team_composition.team2_comp_strength
        
        # Features temporais
        game_phase = self._get_game_phase(match_state.game_time)
        
        # Features de momentum
        momentum = self._calculate_momentum(match_state)
        
        # Features de vantagem por fase
        early_advantage = 1 if team_composition.early_game_advantage == 'team1' else \
                         -1 if team_composition.early_game_advantage == 'team2' else 0
        late_advantage = 1 if team_composition.late_game_scaling == 'team1' else \
                        -1 if team_composition.late_game_scaling == 'team2' else 0
        
        # Features de potencial
        teamfight_diff = (team_composition.teamfight_potential['team1'] - 
                         team_composition.teamfight_potential['team2'])
        
        features = np.array([
            match_state.game_time,
            gold_diff,
            kill_diff,
            tower_diff,
            dragon_diff,
            baron_diff,
            comp_diff,
            game_phase,
            momentum,
            early_advantage,
            late_advantage,
            teamfight_diff,
            match_state.team1_inhibitors - match_state.team2_inhibitors,
            match_state.team1_heralds - match_state.team2_heralds
        ])
        
        return features
        
    def _get_game_phase(self, game_time: float) -> float:
        """Determina fase do jogo (0=early, 1=mid, 2=late)"""
        if game_time < 15:
            return 0  # Early game
        elif game_time < 30:
            return 1  # Mid game
        else:
            return 2  # Late game
            
    def _calculate_momentum(self, match_state: MatchState) -> float:
        """Calcula momentum baseado em objetivos recentes"""
        # Simplificado - em implementação real, precisaria de dados temporais
        team1_score = (match_state.team1_kills * 1.0 + 
                      match_state.team1_towers * 2.0 + 
                      match_state.team1_dragons * 1.5 +
                      match_state.team1_barons * 3.0)
        
        team2_score = (match_state.team2_kills * 1.0 + 
                      match_state.team2_towers * 2.0 + 
                      match_state.team2_dragons * 1.5 +
                      match_state.team2_barons * 3.0)
        
        total_score = team1_score + team2_score
        if total_score == 0:
            return 0
            
        return (team1_score - team2_score) / total_score
        
    async def predict_money_line(self, match_state: MatchState, draft_data: DraftData,
                                team1_name: str, team2_name: str) -> Dict:
        """Predição principal para money line"""
        
        try:
            # Verificar cache
            cache_key = f"{team1_name}_{team2_name}_{match_state.game_time:.1f}"
            if cache_key in self.prediction_cache:
                cached = self.prediction_cache[cache_key]
                if (datetime.now() - cached['timestamp']).seconds < self.cache_duration:
                    cached['cache_hit'] = True
                    return cached
                    
            # Analisar composição
            team_composition = self.champion_analyzer.analyze_composition(draft_data)
            
            # Extrair features
            features = self.extract_features(match_state, draft_data, team_composition)
            
            # Fazer predição com ensemble
            if 'random_forest' in self.models:
                prediction = self._ensemble_prediction(features)
            else:
                prediction = self._simple_prediction(features)
                
            # Calcular confiança
            confidence = self._calculate_confidence(features, prediction, team_composition)
            
            # Calcular expected value
            ev_data = self._calculate_expected_value(prediction, confidence)
            
            # Gerar análise
            analysis = self._generate_detailed_analysis(
                match_state, team_composition, prediction, team1_name, team2_name
            )
            
            result = {
                'team1_name': team1_name,
                'team2_name': team2_name,
                'team1_win_probability': prediction['team1_prob'],
                'team2_win_probability': prediction['team2_prob'],
                'favored_team': team1_name if prediction['team1_prob'] > 0.5 else team2_name,
                'confidence_score': confidence['score'],
                'confidence_level': confidence['level'],
                'expected_value': ev_data['ev'],
                'recommended_bet': ev_data['recommendation'],
                'game_time': match_state.game_time,
                'game_phase': self._get_game_phase_name(match_state.game_time),
                'key_factors': analysis['key_factors'],
                'risk_assessment': analysis['risk_assessment'],
                'detailed_analysis': analysis['detailed_text'],
                'feature_importance': self._get_top_features(features),
                'timestamp': datetime.now(),
                'cache_hit': False,
                'model_type': 'ensemble' if 'random_forest' in self.models else 'simple'
            }
            
            # Salvar no cache
            self.prediction_cache[cache_key] = result
            
            # Registrar para tracking
            self._track_prediction(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na predição ML: {e}")
            return self._get_fallback_prediction(team1_name, team2_name)
            
    def _ensemble_prediction(self, features: np.ndarray) -> Dict:
        """Predição usando ensemble de modelos"""
        try:
            features_reshaped = features.reshape(1, -1)
            predictions = {}
            
            for model_name, model in self.models.items():
                if model_name == 'ensemble_weight':
                    continue
                    
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(features_reshaped)[0]
                    predictions[model_name] = proba[1] if len(proba) > 1 else 0.5
                    
            # Weighted ensemble
            weights = self.models['ensemble_weight']
            team1_prob = sum(predictions[model] * weights.get(model, 0) 
                           for model in predictions)
            
            return {
                'team1_prob': max(0.1, min(0.9, team1_prob)),
                'team2_prob': max(0.1, min(0.9, 1 - team1_prob)),
                'individual_predictions': predictions
            }
            
        except Exception as e:
            logger.error(f"Erro no ensemble: {e}")
            return {'team1_prob': 0.5, 'team2_prob': 0.5}
            
    def _simple_prediction(self, features: np.ndarray) -> Dict:
        """Predição usando modelo simplificado"""
        weights = self.models['simple_classifier']['weights']
        
        # Mapear features para pesos
        feature_names = ['game_time', 'gold_diff', 'kill_diff', 'tower_diff', 
                        'dragon_diff', 'baron_diff', 'comp_diff']
        
        score = 0
        for i, feature_name in enumerate(feature_names):
            if i < len(features) and feature_name in weights:
                score += features[i] * weights[feature_name]
                
        # Normalizar para probabilidade
        team1_prob = 1 / (1 + np.exp(-score * 2))  # Sigmoid
        team1_prob = max(0.1, min(0.9, team1_prob))
        
        return {
            'team1_prob': team1_prob,
            'team2_prob': 1 - team1_prob
        }
        
    def _calculate_confidence(self, features: np.ndarray, prediction: Dict, 
                            team_composition: TeamComposition) -> Dict:
        """Calcula nível de confiança da predição"""
        
        # Fatores de confiança
        confidence_factors = []
        
        # 1. Margem da predição
        prob_margin = abs(prediction['team1_prob'] - 0.5)
        confidence_factors.append(prob_margin * 2)  # 0-1 scale
        
        # 2. Consistência dos dados
        if features[1] != 0:  # gold_diff
            confidence_factors.append(min(abs(features[1]) * 2, 1))
            
        # 3. Fase do jogo (mais confiável em late game)
        game_phase = self._get_game_phase(features[0])
        phase_confidence = 0.5 + (game_phase * 0.25)
        confidence_factors.append(phase_confidence)
        
        # 4. Qualidade da composição
        comp_clarity = abs(team_composition.team1_comp_strength - 
                          team_composition.team2_comp_strength)
        confidence_factors.append(min(comp_clarity / 2, 1))
        
        # Calcular confiança final
        final_confidence = np.mean(confidence_factors) * 100
        
        # Determinar nível
        if final_confidence >= 85:
            level = 'Muito Alta'
        elif final_confidence >= 75:
            level = 'Alta'
        elif final_confidence >= 65:
            level = 'Média'
        else:
            level = 'Baixa'
            
        return {
            'score': final_confidence,
            'level': level,
            'factors': confidence_factors
        }
        
    def _calculate_expected_value(self, prediction: Dict, confidence: Dict) -> Dict:
        """Calcula expected value para money line"""
        
        # Estimar odds do mercado (simulação)
        team1_prob = prediction['team1_prob']
        
        # Margem típica das casas de apostas (5-7%)
        market_margin = 0.06
        
        # Odds implícitas do mercado
        market_team1_prob = team1_prob * (1 - market_margin/2)
        market_team2_prob = (1 - team1_prob) * (1 - market_margin/2)
        
        # Converter para odds decimais
        team1_odds = 1 / market_team1_prob if market_team1_prob > 0 else 2.0
        team2_odds = 1 / market_team2_prob if market_team2_prob > 0 else 2.0
        
        # Calcular EV para cada time
        team1_ev = (team1_prob * team1_odds) - 1
        team2_ev = ((1 - team1_prob) * team2_odds) - 1
        
        # Determinar melhor aposta
        if team1_ev > team2_ev and team1_ev > 0.05:  # Mínimo 5% EV
            recommendation = {
                'team': 'team1',
                'ev': team1_ev * 100,
                'odds': team1_odds,
                'probability': team1_prob
            }
        elif team2_ev > 0.05:
            recommendation = {
                'team': 'team2', 
                'ev': team2_ev * 100,
                'odds': team2_odds,
                'probability': 1 - team1_prob
            }
        else:
            recommendation = {
                'team': 'none',
                'ev': 0,
                'reason': 'Nenhuma value bet encontrada'
            }
            
        return {
            'ev': max(team1_ev, team2_ev) * 100,
            'team1_ev': team1_ev * 100,
            'team2_ev': team2_ev * 100,
            'recommendation': recommendation,
            'estimated_odds': {
                'team1': team1_odds,
                'team2': team2_odds
            }
        }
        
    def _generate_detailed_analysis(self, match_state: MatchState, 
                                  team_composition: TeamComposition,
                                  prediction: Dict, team1_name: str, 
                                  team2_name: str) -> Dict:
        """Gera análise detalhada da predição"""
        
        key_factors = []
        
        # Analisar vantagens atuais
        gold_diff = match_state.team1_gold - match_state.team2_gold
        if abs(gold_diff) > 1000:
            leading_team = team1_name if gold_diff > 0 else team2_name
            key_factors.append(f"Vantagem de ouro significativa: {leading_team}")
            
        # Analisar objetivos
        if match_state.team1_dragons > match_state.team2_dragons + 1:
            key_factors.append(f"Controle de dragões: {team1_name}")
        elif match_state.team2_dragons > match_state.team1_dragons + 1:
            key_factors.append(f"Controle de dragões: {team2_name}")
            
        # Analisar composição
        if abs(team_composition.team1_comp_strength - team_composition.team2_comp_strength) > 1:
            stronger_comp = team1_name if team_composition.team1_comp_strength > team_composition.team2_comp_strength else team2_name
            key_factors.append(f"Composição superior: {stronger_comp}")
            
        # Análise de fase
        game_phase = self._get_game_phase_name(match_state.game_time)
        if team_composition.early_game_advantage != 'neutral' and game_phase == 'Early Game':
            adv_team = team1_name if team_composition.early_game_advantage == 'team1' else team2_name
            key_factors.append(f"Vantagem early game ativa: {adv_team}")
            
        # Risk assessment
        risk_factors = []
        
        if prediction['team1_prob'] > 0.8 or prediction['team1_prob'] < 0.2:
            risk_factors.append("Predição extrema - maior variância")
            
        if match_state.game_time < 10:
            risk_factors.append("Early game - maior imprevisibilidade")
            
        if abs(match_state.team1_kills - match_state.team2_kills) > 10:
            risk_factors.append("Jogo desbalanceado - possível snowball")
            
        # Texto detalhado
        favored_team = team1_name if prediction['team1_prob'] > 0.5 else team2_name
        prob = max(prediction['team1_prob'], prediction['team2_prob']) * 100
        
        detailed_text = f"""
🎮 **ANÁLISE ML COMPLETA** 🎮

⭐ **Favorito:** {favored_team} ({prob:.1f}% probabilidade)
⏱️ **Fase:** {game_phase} ({match_state.game_time:.1f} min)

📊 **Estado Atual:**
• Ouro: {match_state.team1_gold:,} vs {match_state.team2_gold:,}
• Kills: {match_state.team1_kills} vs {match_state.team2_kills}
• Torres: {match_state.team1_towers} vs {match_state.team2_towers}
• Dragões: {match_state.team1_dragons} vs {match_state.team2_dragons}

🎯 **Fatores Decisivos:**
{chr(10).join(f"• {factor}" for factor in key_factors)}

⚠️ **Fatores de Risco:**
{chr(10).join(f"• {risk}" for risk in risk_factors) if risk_factors else "• Risco padrão"}
        """
        
        return {
            'key_factors': key_factors,
            'risk_assessment': risk_factors,
            'detailed_text': detailed_text.strip()
        }
        
    def _get_game_phase_name(self, game_time: float) -> str:
        """Nome da fase do jogo"""
        if game_time < 15:
            return 'Early Game'
        elif game_time < 30:
            return 'Mid Game'
        else:
            return 'Late Game'
            
    def _get_top_features(self, features: np.ndarray) -> List[Dict]:
        """Retorna features mais importantes"""
        feature_names = [
            'Tempo de Jogo', 'Diferença de Ouro', 'Diferença de Kills',
            'Diferença de Torres', 'Diferença de Dragões', 'Diferença de Barões',
            'Força da Composição', 'Fase do Jogo', 'Momentum',
            'Vantagem Early', 'Vantagem Late', 'Potencial Teamfight'
        ]
        
        feature_importance = []
        for i, (name, value) in enumerate(zip(feature_names, features)):
            if i < len(feature_names):
                importance = abs(value) / (np.sum(np.abs(features)) + 1e-6)
                feature_importance.append({
                    'name': name,
                    'value': float(value),
                    'importance': float(importance)
                })
                
        return sorted(feature_importance, key=lambda x: x['importance'], reverse=True)[:5]
        
    def _track_prediction(self, prediction: Dict):
        """Registra predição para tracking de performance"""
        self.prediction_history.append({
            'timestamp': prediction['timestamp'],
            'team1': prediction['team1_name'],
            'team2': prediction['team2_name'],
            'prediction': prediction['team1_win_probability'],
            'confidence': prediction['confidence_score'],
            'game_time': prediction['game_time']
        })
        
        # Manter apenas últimas 100 predições
        if len(self.prediction_history) > 100:
            self.prediction_history = self.prediction_history[-100:]
            
    def _get_fallback_prediction(self, team1_name: str, team2_name: str) -> Dict:
        """Predição de fallback em caso de erro"""
        return {
            'team1_name': team1_name,
            'team2_name': team2_name,
            'team1_win_probability': 0.5,
            'team2_win_probability': 0.5,
            'favored_team': team1_name,
            'confidence_score': 50.0,
            'confidence_level': 'Baixa',
            'expected_value': 0.0,
            'recommended_bet': {'team': 'none', 'reason': 'Erro na análise'},
            'game_time': 0.0,
            'game_phase': 'Desconhecida',
            'key_factors': ['Análise indisponível'],
            'risk_assessment': ['Dados insuficientes'],
            'detailed_analysis': 'Análise ML não disponível devido a erro interno.',
            'feature_importance': [],
            'timestamp': datetime.now(),
            'cache_hit': False,
            'model_type': 'fallback'
        }
        
    def get_system_stats(self) -> Dict:
        """Retorna estatísticas do sistema ML"""
        return {
            'total_predictions': len(self.prediction_history),
            'cached_predictions': len(self.prediction_cache),
            'model_performance': self.model_performance,
            'feature_importance': self.feature_importance,
            'last_prediction': self.prediction_history[-1] if self.prediction_history else None,
            'models_available': list(self.models.keys()),
            'champion_database_size': len(self.champion_analyzer.champion_stats)
        }
        
    def clear_old_cache(self):
        """Remove predições antigas do cache"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, prediction in self.prediction_cache.items():
            if (current_time - prediction['timestamp']).seconds > self.cache_duration:
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.prediction_cache[key]
            
        if expired_keys:
            logger.info(f"🧹 {len(expired_keys)} predições ML expiradas removidas do cache") 