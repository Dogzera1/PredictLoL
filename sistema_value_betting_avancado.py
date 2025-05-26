#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Avançado de Value Betting para League of Legends
Considera múltiplos fatores: composições, histórico, jogadores, meta, etc.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)

class AdvancedValueBettingSystem:
    """Sistema avançado de value betting com análise profunda"""
    
    def __init__(self):
        self.base_unit = 100  # R$ 100 por unidade
        self.bankroll = 10000  # R$ 10.000
        self.max_units_per_bet = 3  # Máximo 3 unidades por aposta
        self.confidence_threshold = 0.70  # 70% confiança mínima
        self.ev_threshold = 0.04  # 4% EV mínimo
        
        # Pesos para diferentes fatores de análise
        self.analysis_weights = {
            'team_form': 0.25,          # Forma recente dos times
            'head_to_head': 0.20,       # Histórico direto
            'player_performance': 0.20,  # Performance individual
            'composition_synergy': 0.15, # Sinergia das composições
            'meta_adaptation': 0.10,     # Adaptação ao meta
            'league_strength': 0.10      # Força da liga
        }
        
        logger.info("🧠 Sistema Avançado de Value Betting inicializado")
    
    def analyze_match_comprehensive(self, match_data: Dict) -> Dict:
        """Análise abrangente de uma partida considerando todos os fatores"""
        
        team1 = match_data.get('team1', '')
        team2 = match_data.get('team2', '')
        league = match_data.get('league', '')
        
        logger.info(f"🔍 Analisando {team1} vs {team2} ({league})")
        
        # 1. Análise da forma recente dos times
        team1_form = self._analyze_team_form(team1, league)
        team2_form = self._analyze_team_form(team2, league)
        
        # 2. Análise do histórico direto (head-to-head)
        h2h_analysis = self._analyze_head_to_head(team1, team2)
        
        # 3. Análise de performance individual dos jogadores
        player_analysis = self._analyze_player_performance(team1, team2, league)
        
        # 4. Análise de sinergia das composições típicas
        composition_analysis = self._analyze_composition_synergy(team1, team2, league)
        
        # 5. Análise de adaptação ao meta atual
        meta_analysis = self._analyze_meta_adaptation(team1, team2, league)
        
        # 6. Análise da força da liga
        league_analysis = self._analyze_league_strength(league)
        
        # Combinar todas as análises
        comprehensive_analysis = self._combine_analysis_factors(
            team1_form, team2_form, h2h_analysis, player_analysis,
            composition_analysis, meta_analysis, league_analysis
        )
        
        # Calcular probabilidade final
        team1_prob = comprehensive_analysis['team1_probability']
        team2_prob = comprehensive_analysis['team2_probability']
        
        # Simular odds das casas de apostas (seria substituído por API real)
        simulated_odds = self._simulate_bookmaker_odds(team1_prob, team2_prob)
        
        # Analisar value betting
        value_analysis = self._analyze_value_opportunities(
            team1_prob, team2_prob, simulated_odds, comprehensive_analysis
        )
        
        return {
            'match': f"{team1} vs {team2}",
            'league': league,
            'comprehensive_analysis': comprehensive_analysis,
            'value_analysis': value_analysis,
            'recommendation': self._generate_recommendation(value_analysis),
            'confidence_level': comprehensive_analysis['overall_confidence'],
            'analysis_timestamp': datetime.now()
        }
    
    def _analyze_team_form(self, team: str, league: str) -> Dict:
        """Analisa a forma recente do time (últimas 10 partidas)"""
        
        # Dados simulados baseados em times reais
        team_form_data = {
            # LCK Teams
            'T1': {'wins': 8, 'losses': 2, 'avg_game_time': 28.5, 'early_game_rating': 9.2, 'late_game_rating': 9.5},
            'Gen.G Esports': {'wins': 7, 'losses': 3, 'avg_game_time': 31.2, 'early_game_rating': 8.8, 'late_game_rating': 9.0},
            'DRX': {'wins': 6, 'losses': 4, 'avg_game_time': 33.1, 'early_game_rating': 7.5, 'late_game_rating': 8.2},
            'KT Rolster': {'wins': 5, 'losses': 5, 'avg_game_time': 35.8, 'early_game_rating': 7.0, 'late_game_rating': 7.8},
            'Hanwha Life Esports': {'wins': 4, 'losses': 6, 'avg_game_time': 32.4, 'early_game_rating': 6.8, 'late_game_rating': 7.2},
            
            # LPL Teams
            'WBG': {'wins': 7, 'losses': 3, 'avg_game_time': 29.8, 'early_game_rating': 8.5, 'late_game_rating': 8.8},
            'TT': {'wins': 6, 'losses': 4, 'avg_game_time': 31.5, 'early_game_rating': 8.0, 'late_game_rating': 8.3},
            
            # LEC Teams
            'G2 Esports': {'wins': 8, 'losses': 2, 'avg_game_time': 30.2, 'early_game_rating': 8.9, 'late_game_rating': 9.1},
            'Fnatic': {'wins': 6, 'losses': 4, 'avg_game_time': 32.8, 'early_game_rating': 8.2, 'late_game_rating': 8.5},
            'MAD Lions': {'wins': 5, 'losses': 5, 'avg_game_time': 34.1, 'early_game_rating': 7.8, 'late_game_rating': 8.0},
            
            # LTA North Teams
            'Team Liquid': {'wins': 7, 'losses': 3, 'avg_game_time': 31.8, 'early_game_rating': 8.3, 'late_game_rating': 8.6},
            '100 Thieves': {'wins': 6, 'losses': 4, 'avg_game_time': 33.2, 'early_game_rating': 7.9, 'late_game_rating': 8.1}
        }
        
        form_data = team_form_data.get(team, {
            'wins': 5, 'losses': 5, 'avg_game_time': 32.0, 
            'early_game_rating': 7.0, 'late_game_rating': 7.5
        })
        
        # Calcular métricas de forma
        win_rate = form_data['wins'] / (form_data['wins'] + form_data['losses'])
        form_score = (win_rate * 0.6 + 
                     (form_data['early_game_rating'] / 10) * 0.2 + 
                     (form_data['late_game_rating'] / 10) * 0.2)
        
        # Ajustar por tempo médio de jogo (times que fecham rápido são mais dominantes)
        time_factor = max(0.8, min(1.2, 35 / form_data['avg_game_time']))
        form_score *= time_factor
        
        return {
            'team': team,
            'recent_record': f"{form_data['wins']}-{form_data['losses']}",
            'win_rate': win_rate,
            'form_score': min(1.0, form_score),
            'early_game_strength': form_data['early_game_rating'],
            'late_game_strength': form_data['late_game_rating'],
            'avg_game_time': form_data['avg_game_time'],
            'dominance_factor': time_factor
        }
    
    def _analyze_head_to_head(self, team1: str, team2: str) -> Dict:
        """Analisa o histórico direto entre os times"""
        
        # Dados simulados de histórico (seria substituído por dados reais)
        h2h_database = {
            ('T1', 'Gen.G Esports'): {'team1_wins': 6, 'team2_wins': 4, 'avg_games_per_series': 2.8},
            ('T1', 'DRX'): {'team1_wins': 7, 'team2_wins': 3, 'avg_games_per_series': 2.6},
            ('G2 Esports', 'Fnatic'): {'team1_wins': 8, 'team2_wins': 5, 'avg_games_per_series': 2.9},
            ('Team Liquid', '100 Thieves'): {'team1_wins': 5, 'team2_wins': 6, 'avg_games_per_series': 3.1}
        }
        
        # Buscar histórico (tentar ambas as ordens)
        h2h_key = (team1, team2)
        reverse_key = (team2, team1)
        
        if h2h_key in h2h_database:
            h2h_data = h2h_database[h2h_key]
            team1_wins = h2h_data['team1_wins']
            team2_wins = h2h_data['team2_wins']
        elif reverse_key in h2h_database:
            h2h_data = h2h_database[reverse_key]
            team1_wins = h2h_data['team2_wins']  # Inverter
            team2_wins = h2h_data['team1_wins']
        else:
            # Sem histórico, usar valores neutros
            team1_wins = 5
            team2_wins = 5
            h2h_data = {'avg_games_per_series': 2.5}
        
        total_matches = team1_wins + team2_wins
        team1_h2h_rate = team1_wins / total_matches if total_matches > 0 else 0.5
        team2_h2h_rate = team2_wins / total_matches if total_matches > 0 else 0.5
        
        # Calcular fator de competitividade (séries mais longas = mais equilibradas)
        competitiveness = min(1.0, h2h_data['avg_games_per_series'] / 3.0)
        
        return {
            'team1_h2h_winrate': team1_h2h_rate,
            'team2_h2h_winrate': team2_h2h_rate,
            'total_matches': total_matches,
            'competitiveness': competitiveness,
            'h2h_confidence': min(1.0, total_matches / 10),  # Mais jogos = mais confiança
            'series_length_avg': h2h_data['avg_games_per_series']
        }
    
    def _analyze_player_performance(self, team1: str, team2: str, league: str) -> Dict:
        """Analisa a performance individual dos jogadores chave"""
        
        # Dados simulados de performance de jogadores (seria substituído por API real)
        player_ratings = {
            # T1 Players
            'T1': {
                'top': {'name': 'Zeus', 'rating': 9.2, 'form': 'excellent'},
                'jungle': {'name': 'Oner', 'rating': 8.8, 'form': 'good'},
                'mid': {'name': 'Faker', 'rating': 9.5, 'form': 'excellent'},
                'adc': {'name': 'Gumayusi', 'rating': 9.0, 'form': 'excellent'},
                'support': {'name': 'Keria', 'rating': 9.3, 'form': 'excellent'}
            },
            'Gen.G Esports': {
                'top': {'name': 'Kiin', 'rating': 8.5, 'form': 'good'},
                'jungle': {'name': 'Canyon', 'rating': 9.1, 'form': 'excellent'},
                'mid': {'name': 'Chovy', 'rating': 9.4, 'form': 'excellent'},
                'adc': {'name': 'Peyz', 'rating': 8.3, 'form': 'good'},
                'support': {'name': 'Lehends', 'rating': 8.7, 'form': 'good'}
            },
            'G2 Esports': {
                'top': {'name': 'BrokenBlade', 'rating': 8.2, 'form': 'good'},
                'jungle': {'name': 'Yike', 'rating': 8.0, 'form': 'average'},
                'mid': {'name': 'Caps', 'rating': 8.9, 'form': 'excellent'},
                'adc': {'name': 'Hans sama', 'rating': 8.4, 'form': 'good'},
                'support': {'name': 'Mikyx', 'rating': 8.1, 'form': 'good'}
            }
        }
        
        def calculate_team_rating(team_name):
            if team_name not in player_ratings:
                return {'avg_rating': 7.5, 'form_factor': 1.0, 'star_players': 0}
            
            players = player_ratings[team_name]
            ratings = [p['rating'] for p in players.values()]
            avg_rating = sum(ratings) / len(ratings)
            
            # Calcular fator de forma
            form_values = {'excellent': 1.1, 'good': 1.0, 'average': 0.95, 'poor': 0.85}
            form_factor = sum(form_values.get(p['form'], 1.0) for p in players.values()) / len(players)
            
            # Contar jogadores estrela (rating > 9.0)
            star_players = sum(1 for p in players.values() if p['rating'] > 9.0)
            
            return {
                'avg_rating': avg_rating,
                'form_factor': form_factor,
                'star_players': star_players,
                'players': players
            }
        
        team1_analysis = calculate_team_rating(team1)
        team2_analysis = calculate_team_rating(team2)
        
        # Calcular vantagem de jogadores
        rating_diff = team1_analysis['avg_rating'] - team2_analysis['avg_rating']
        form_diff = team1_analysis['form_factor'] - team2_analysis['form_factor']
        star_diff = team1_analysis['star_players'] - team2_analysis['star_players']
        
        return {
            'team1_avg_rating': team1_analysis['avg_rating'],
            'team2_avg_rating': team2_analysis['avg_rating'],
            'team1_form_factor': team1_analysis['form_factor'],
            'team2_form_factor': team2_analysis['form_factor'],
            'team1_star_players': team1_analysis['star_players'],
            'team2_star_players': team2_analysis['star_players'],
            'rating_advantage': rating_diff,
            'form_advantage': form_diff,
            'star_advantage': star_diff,
            'overall_player_edge': (rating_diff + form_diff + star_diff * 0.2) / 2.2
        }
    
    def _analyze_composition_synergy(self, team1: str, team2: str, league: str) -> Dict:
        """Analisa a sinergia das composições típicas dos times"""
        
        # Dados simulados de estilo de jogo e composições preferidas
        team_styles = {
            'T1': {
                'playstyle': 'aggressive_early',
                'preferred_comps': ['engage', 'pick', 'teamfight'],
                'adaptation_rating': 9.0,
                'draft_flexibility': 8.8
            },
            'Gen.G Esports': {
                'playstyle': 'controlled_scaling',
                'preferred_comps': ['scaling', 'teamfight', 'zone_control'],
                'adaptation_rating': 8.5,
                'draft_flexibility': 8.2
            },
            'G2 Esports': {
                'playstyle': 'creative_chaos',
                'preferred_comps': ['pick', 'split_push', 'skirmish'],
                'adaptation_rating': 8.7,
                'draft_flexibility': 9.2
            },
            'Fnatic': {
                'playstyle': 'teamfight_oriented',
                'preferred_comps': ['teamfight', 'engage', 'front_to_back'],
                'adaptation_rating': 7.8,
                'draft_flexibility': 7.5
            }
        }
        
        def get_team_style(team_name):
            return team_styles.get(team_name, {
                'playstyle': 'balanced',
                'preferred_comps': ['teamfight', 'scaling'],
                'adaptation_rating': 7.0,
                'draft_flexibility': 7.0
            })
        
        team1_style = get_team_style(team1)
        team2_style = get_team_style(team2)
        
        # Calcular compatibilidade de estilos
        style_matchups = {
            ('aggressive_early', 'controlled_scaling'): 0.6,  # Early vs Late
            ('aggressive_early', 'teamfight_oriented'): 0.7,
            ('controlled_scaling', 'creative_chaos'): 0.5,
            ('creative_chaos', 'teamfight_oriented'): 0.8
        }
        
        matchup_key = (team1_style['playstyle'], team2_style['playstyle'])
        reverse_key = (team2_style['playstyle'], team1_style['playstyle'])
        
        style_compatibility = style_matchups.get(matchup_key, 
                            style_matchups.get(reverse_key, 0.5))
        
        # Calcular vantagem de draft
        draft_advantage = (team1_style['draft_flexibility'] - team2_style['draft_flexibility']) / 10
        adaptation_advantage = (team1_style['adaptation_rating'] - team2_style['adaptation_rating']) / 10
        
        return {
            'team1_playstyle': team1_style['playstyle'],
            'team2_playstyle': team2_style['playstyle'],
            'style_compatibility': style_compatibility,
            'team1_draft_flex': team1_style['draft_flexibility'],
            'team2_draft_flex': team2_style['draft_flexibility'],
            'draft_advantage': draft_advantage,
            'adaptation_advantage': adaptation_advantage,
            'composition_edge': (draft_advantage + adaptation_advantage) / 2
        }
    
    def _analyze_meta_adaptation(self, team1: str, team2: str, league: str) -> Dict:
        """Analisa como os times se adaptam ao meta atual"""
        
        # Meta atual simulado (seria baseado em patches e estatísticas reais)
        current_meta = {
            'patch': '14.24',
            'dominant_roles': ['jungle', 'adc'],
            'key_champions': ['Graves', 'Jinx', 'Azir', 'Nautilus', 'Gnar'],
            'meta_shift_recent': True,
            'adaptation_difficulty': 0.7
        }
        
        # Dados de adaptação dos times ao meta
        meta_adaptation_data = {
            'T1': {'adaptation_speed': 9.2, 'meta_champion_pool': 8.8, 'innovation_rating': 9.0},
            'Gen.G Esports': {'adaptation_speed': 8.5, 'meta_champion_pool': 8.9, 'innovation_rating': 7.8},
            'G2 Esports': {'adaptation_speed': 8.9, 'meta_champion_pool': 8.2, 'innovation_rating': 9.5},
            'Fnatic': {'adaptation_speed': 7.8, 'meta_champion_pool': 8.0, 'innovation_rating': 7.2}
        }
        
        def get_meta_rating(team_name):
            return meta_adaptation_data.get(team_name, {
                'adaptation_speed': 7.0,
                'meta_champion_pool': 7.0,
                'innovation_rating': 7.0
            })
        
        team1_meta = get_meta_rating(team1)
        team2_meta = get_meta_rating(team2)
        
        # Calcular vantagem no meta
        adaptation_diff = team1_meta['adaptation_speed'] - team2_meta['adaptation_speed']
        pool_diff = team1_meta['meta_champion_pool'] - team2_meta['meta_champion_pool']
        innovation_diff = team1_meta['innovation_rating'] - team2_meta['innovation_rating']
        
        # Se houve mudança recente no meta, adaptação é mais importante
        meta_weight = 1.2 if current_meta['meta_shift_recent'] else 1.0
        
        meta_advantage = ((adaptation_diff + pool_diff + innovation_diff) / 3) * meta_weight / 10
        
        return {
            'current_patch': current_meta['patch'],
            'meta_shift_recent': current_meta['meta_shift_recent'],
            'team1_adaptation': team1_meta['adaptation_speed'],
            'team2_adaptation': team2_meta['adaptation_speed'],
            'team1_champion_pool': team1_meta['meta_champion_pool'],
            'team2_champion_pool': team2_meta['meta_champion_pool'],
            'meta_advantage': meta_advantage,
            'adaptation_importance': meta_weight
        }
    
    def _analyze_league_strength(self, league: str) -> Dict:
        """Analisa a força e competitividade da liga"""
        
        league_data = {
            'LCK': {'strength': 9.5, 'competitiveness': 9.2, 'international_success': 9.8},
            'LPL': {'strength': 9.3, 'competitiveness': 8.8, 'international_success': 9.0},
            'LEC': {'strength': 8.2, 'competitiveness': 8.5, 'international_success': 7.5},
            'LTA North': {'strength': 7.8, 'competitiveness': 8.0, 'international_success': 7.2},
            'LTA South': {'strength': 7.5, 'competitiveness': 7.8, 'international_success': 6.8},
            'VCS': {'strength': 7.0, 'competitiveness': 7.5, 'international_success': 6.5},
            'LJL': {'strength': 6.8, 'competitiveness': 7.2, 'international_success': 6.0}
        }
        
        data = league_data.get(league, {
            'strength': 7.0, 'competitiveness': 7.0, 'international_success': 6.5
        })
        
        # Calcular fator de confiabilidade baseado na força da liga
        reliability_factor = (data['strength'] + data['competitiveness']) / 20
        
        return {
            'league': league,
            'strength_rating': data['strength'],
            'competitiveness': data['competitiveness'],
            'international_success': data['international_success'],
            'reliability_factor': reliability_factor,
            'prediction_confidence': min(1.0, reliability_factor * 1.2)
        }
    
    def _combine_analysis_factors(self, team1_form, team2_form, h2h_analysis, 
                                 player_analysis, composition_analysis, 
                                 meta_analysis, league_analysis) -> Dict:
        """Combina todos os fatores de análise em uma probabilidade final"""
        
        # Calcular probabilidades baseadas em cada fator
        form_prob = self._form_to_probability(team1_form['form_score'], team2_form['form_score'])
        h2h_prob = h2h_analysis['team1_h2h_winrate']
        player_prob = self._player_edge_to_probability(player_analysis['overall_player_edge'])
        comp_prob = self._composition_edge_to_probability(composition_analysis['composition_edge'])
        meta_prob = self._meta_edge_to_probability(meta_analysis['meta_advantage'])
        
        # Aplicar pesos configurados
        weights = self.analysis_weights
        
        team1_probability = (
            form_prob * weights['team_form'] +
            h2h_prob * weights['head_to_head'] +
            player_prob * weights['player_performance'] +
            comp_prob * weights['composition_synergy'] +
            meta_prob * weights['meta_adaptation'] +
            0.5 * weights['league_strength']  # Liga não favorece nenhum time
        )
        
        team2_probability = 1 - team1_probability
        
        # Calcular confiança geral
        confidence_factors = [
            team1_form['form_score'],
            team2_form['form_score'],
            h2h_analysis['h2h_confidence'],
            league_analysis['prediction_confidence'],
            min(1.0, abs(team1_probability - 0.5) * 2)  # Mais confiança em predições menos equilibradas
        ]
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return {
            'team1_probability': team1_probability,
            'team2_probability': team2_probability,
            'overall_confidence': overall_confidence,
            'factor_breakdown': {
                'form_contribution': form_prob * weights['team_form'],
                'h2h_contribution': h2h_prob * weights['head_to_head'],
                'player_contribution': player_prob * weights['player_performance'],
                'composition_contribution': comp_prob * weights['composition_synergy'],
                'meta_contribution': meta_prob * weights['meta_adaptation']
            },
            'analysis_details': {
                'team1_form': team1_form,
                'team2_form': team2_form,
                'h2h_analysis': h2h_analysis,
                'player_analysis': player_analysis,
                'composition_analysis': composition_analysis,
                'meta_analysis': meta_analysis,
                'league_analysis': league_analysis
            }
        }
    
    def _form_to_probability(self, team1_form, team2_form):
        """Converte forma dos times em probabilidade"""
        total_form = team1_form + team2_form
        return team1_form / total_form if total_form > 0 else 0.5
    
    def _player_edge_to_probability(self, player_edge):
        """Converte vantagem de jogadores em probabilidade"""
        # Normalizar edge para probabilidade (edge varia de -2 a +2 aproximadamente)
        normalized_edge = max(-1, min(1, player_edge / 2))
        return 0.5 + (normalized_edge * 0.3)  # Máximo 30% de swing
    
    def _composition_edge_to_probability(self, comp_edge):
        """Converte vantagem de composição em probabilidade"""
        normalized_edge = max(-0.5, min(0.5, comp_edge))
        return 0.5 + (normalized_edge * 0.2)  # Máximo 20% de swing
    
    def _meta_edge_to_probability(self, meta_edge):
        """Converte vantagem de meta em probabilidade"""
        normalized_edge = max(-0.3, min(0.3, meta_edge))
        return 0.5 + (normalized_edge * 0.15)  # Máximo 15% de swing
    
    def _simulate_bookmaker_odds(self, team1_prob, team2_prob):
        """Simula odds das casas de apostas (seria substituído por API real)"""
        # Adicionar margem da casa (5-8%)
        margin = 0.06
        
        # Converter probabilidades em odds com margem
        team1_odds = (1 / team1_prob) * (1 + margin)
        team2_odds = (1 / team2_prob) * (1 + margin)
        
        # Adicionar variação aleatória pequena para simular diferentes casas
        import random
        variation = 0.05
        team1_odds *= (1 + random.uniform(-variation, variation))
        team2_odds *= (1 + random.uniform(-variation, variation))
        
        return {
            'team1_odds': round(team1_odds, 2),
            'team2_odds': round(team2_odds, 2),
            'margin': margin
        }
    
    def _analyze_value_opportunities(self, team1_prob, team2_prob, odds, analysis):
        """Analisa oportunidades de value betting"""
        
        # Calcular EV para cada time
        team1_ev = (team1_prob * (odds['team1_odds'] - 1)) - (1 - team1_prob)
        team2_ev = (team2_prob * (odds['team2_odds'] - 1)) - (1 - team2_prob)
        
        # Determinar melhor aposta
        best_bet = None
        if team1_ev > self.ev_threshold and team1_ev > team2_ev:
            best_bet = {
                'team': 'team1',
                'probability': team1_prob,
                'odds': odds['team1_odds'],
                'ev': team1_ev,
                'implied_prob': 1 / odds['team1_odds']
            }
        elif team2_ev > self.ev_threshold:
            best_bet = {
                'team': 'team2',
                'probability': team2_prob,
                'odds': odds['team2_odds'],
                'ev': team2_ev,
                'implied_prob': 1 / odds['team2_odds']
            }
        
        if best_bet:
            # Calcular unidades baseado em EV e confiança
            confidence = analysis['overall_confidence']
            units_analysis = self.calculate_bet_units(best_bet['ev'], confidence, 
                                                    best_bet['probability'] - best_bet['implied_prob'])
            
            return {
                'has_value': True,
                'best_bet': best_bet,
                'units_analysis': units_analysis,
                'confidence': confidence,
                'risk_assessment': self._assess_comprehensive_risk(best_bet, analysis)
            }
        
        return {
            'has_value': False,
            'team1_ev': team1_ev,
            'team2_ev': team2_ev,
            'reason': 'EV insuficiente em ambos os lados'
        }
    
    def _assess_comprehensive_risk(self, bet, analysis):
        """Avalia risco de forma abrangente"""
        
        risk_factors = {
            'ev_risk': 'LOW' if bet['ev'] > 0.08 else 'MEDIUM' if bet['ev'] > 0.05 else 'HIGH',
            'confidence_risk': 'LOW' if analysis['overall_confidence'] > 0.8 else 'MEDIUM' if analysis['overall_confidence'] > 0.65 else 'HIGH',
            'probability_risk': 'LOW' if abs(bet['probability'] - 0.5) > 0.2 else 'MEDIUM' if abs(bet['probability'] - 0.5) > 0.1 else 'HIGH',
            'league_risk': analysis['analysis_details']['league_analysis']['strength_rating'] > 8.5
        }
        
        # Calcular risco geral
        risk_scores = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        avg_risk = sum(risk_scores[risk] for risk in [risk_factors['ev_risk'], risk_factors['confidence_risk'], risk_factors['probability_risk']]) / 3
        
        if avg_risk <= 1.5:
            overall_risk = 'LOW'
        elif avg_risk <= 2.5:
            overall_risk = 'MEDIUM'
        else:
            overall_risk = 'HIGH'
        
        return {
            'overall_risk': overall_risk,
            'risk_factors': risk_factors,
            'risk_score': avg_risk
        }
    
    def calculate_bet_units(self, ev_percentage, confidence, probability_diff):
        """Calcula unidades baseado em EV e confiança (versão avançada)"""
        
        # Análise de EV mais granular
        if ev_percentage >= 0.12:  # 12%+ EV
            ev_units = 3
            ev_level = "EXCEPCIONAL"
        elif ev_percentage >= 0.08:  # 8-12% EV
            ev_units = 2.5
            ev_level = "MUITO ALTO"
        elif ev_percentage >= 0.06:  # 6-8% EV
            ev_units = 2
            ev_level = "ALTO"
        elif ev_percentage >= 0.04:  # 4-6% EV
            ev_units = 1.5
            ev_level = "MÉDIO-ALTO"
        elif ev_percentage >= 0.03:  # 3-4% EV
            ev_units = 1
            ev_level = "MÉDIO"
        else:
            ev_units = 0.5
            ev_level = "BAIXO"
        
        # Análise de Confiança mais granular
        if confidence >= 0.90:  # 90%+ confiança
            conf_units = 3
            conf_level = "EXCEPCIONAL"
        elif confidence >= 0.85:  # 85-90% confiança
            conf_units = 2.5
            conf_level = "MUITO ALTA"
        elif confidence >= 0.80:  # 80-85% confiança
            conf_units = 2
            conf_level = "ALTA"
        elif confidence >= 0.75:  # 75-80% confiança
            conf_units = 1.5
            conf_level = "MÉDIA-ALTA"
        elif confidence >= 0.70:  # 70-75% confiança
            conf_units = 1
            conf_level = "MÉDIA"
        else:
            conf_units = 0.5
            conf_level = "BAIXA"
        
        # Fator de diferença de probabilidade (maior diferença = mais confiança)
        prob_diff_factor = min(1.5, abs(probability_diff) * 5)
        
        # Cálculo final com fator de diferença
        final_units = min(self.max_units_per_bet, 
                         (ev_units + conf_units + prob_diff_factor) / 3)
        final_units = round(final_units * 4) / 4  # Arredondar para 0.25
        
        return {
            'units': final_units,
            'stake': final_units * self.base_unit,
            'ev_level': ev_level,
            'conf_level': conf_level,
            'ev_percentage': ev_percentage * 100,
            'confidence': confidence * 100,
            'probability_diff': probability_diff * 100,
            'recommendation': self._get_advanced_recommendation(final_units, ev_percentage, confidence),
            'kelly_criterion': self._calculate_kelly_criterion(ev_percentage, confidence)
        }
    
    def _get_advanced_recommendation(self, units, ev, confidence):
        """Gera recomendação avançada baseada na análise"""
        if units >= 2.75:
            return "🔥 APOSTA EXCEPCIONAL - Máxima prioridade, oportunidade rara"
        elif units >= 2.25:
            return "⭐ APOSTA PREMIUM - Muito forte, alta recomendação"
        elif units >= 1.75:
            return "✅ APOSTA FORTE - Boa oportunidade, recomendada"
        elif units >= 1.25:
            return "👍 APOSTA SÓLIDA - Oportunidade válida, considerar"
        elif units >= 1.0:
            return "⚠️ APOSTA CAUTELOSA - Valor marginal, avaliar risco"
        else:
            return "❌ APOSTA FRACA - Evitar, risco alto"
    
    def _calculate_kelly_criterion(self, ev, confidence):
        """Calcula critério de Kelly para gestão ótima de banca"""
        # Kelly = (bp - q) / b, onde b = odds-1, p = probabilidade, q = 1-p
        # Simplificado para EV: Kelly ≈ EV / variance
        
        # Estimar variância baseada na confiança
        variance = 1 - confidence  # Menor confiança = maior variância
        
        kelly_fraction = ev / variance if variance > 0 else 0
        kelly_units = min(self.max_units_per_bet, kelly_fraction * 10)  # Escalar para unidades
        
        return {
            'kelly_fraction': kelly_fraction,
            'kelly_units': kelly_units,
            'recommended_fraction': min(0.25, kelly_fraction)  # Nunca mais que 25% da banca
        }
    
    def _generate_recommendation(self, value_analysis):
        """Gera recomendação final detalhada"""
        if not value_analysis['has_value']:
            return {
                'action': 'SKIP',
                'reason': value_analysis['reason'],
                'confidence': 'N/A'
            }
        
        bet = value_analysis['best_bet']
        units = value_analysis['units_analysis']
        risk = value_analysis['risk_assessment']
        
        return {
            'action': 'BET',
            'team': bet['team'],
            'units': units['units'],
            'stake': units['stake'],
            'odds': bet['odds'],
            'ev': f"{bet['ev']*100:.2f}%",
            'confidence': f"{value_analysis['confidence']*100:.1f}%",
            'risk_level': risk['overall_risk'],
            'recommendation': units['recommendation'],
            'kelly_suggestion': units['kelly_criterion']['recommended_fraction'],
            'reasoning': self._generate_reasoning(value_analysis)
        }
    
    def _generate_reasoning(self, value_analysis):
        """Gera explicação detalhada da recomendação"""
        bet = value_analysis['best_bet']
        analysis = value_analysis.get('analysis_details', {})
        
        reasoning = []
        
        # EV reasoning
        if bet['ev'] > 0.08:
            reasoning.append(f"EV excepcional de {bet['ev']*100:.1f}%")
        elif bet['ev'] > 0.05:
            reasoning.append(f"EV alto de {bet['ev']*100:.1f}%")
        else:
            reasoning.append(f"EV positivo de {bet['ev']*100:.1f}%")
        
        # Confidence reasoning
        conf = value_analysis['confidence']
        if conf > 0.85:
            reasoning.append("Confiança muito alta na análise")
        elif conf > 0.75:
            reasoning.append("Boa confiança na análise")
        else:
            reasoning.append("Confiança moderada na análise")
        
        # Risk reasoning
        risk = value_analysis['risk_assessment']['overall_risk']
        if risk == 'LOW':
            reasoning.append("Risco baixo identificado")
        elif risk == 'MEDIUM':
            reasoning.append("Risco moderado, gestão adequada necessária")
        else:
            reasoning.append("Risco alto, considerar reduzir stake")
        
        return " | ".join(reasoning)

def main():
    """Função de teste do sistema avançado"""
    system = AdvancedValueBettingSystem()
    
    # Teste com partida real
    match_data = {
        'team1': 'T1',
        'team2': 'Gen.G Esports',
        'league': 'LCK',
        'tournament': 'LCK Spring 2025'
    }
    
    print("🧠 SISTEMA AVANÇADO DE VALUE BETTING")
    print("=" * 60)
    
    analysis = system.analyze_match_comprehensive(match_data)
    
    print(f"\n📊 ANÁLISE: {analysis['match']} ({analysis['league']})")
    print("-" * 50)
    
    comp_analysis = analysis['comprehensive_analysis']
    print(f"🎯 Probabilidade Team1: {comp_analysis['team1_probability']*100:.1f}%")
    print(f"🎯 Probabilidade Team2: {comp_analysis['team2_probability']*100:.1f}%")
    print(f"🔍 Confiança Geral: {comp_analysis['overall_confidence']*100:.1f}%")
    
    if analysis['value_analysis']['has_value']:
        rec = analysis['recommendation']
        print(f"\n💰 VALUE BETTING DETECTADO!")
        print(f"🎯 Ação: {rec['action']} - {rec['team']}")
        print(f"💵 Unidades: {rec['units']}")
        print(f"💰 Stake: R$ {rec['stake']}")
        print(f"📊 EV: {rec['ev']}")
        print(f"🔍 Confiança: {rec['confidence']}")
        print(f"⚠️ Risco: {rec['risk_level']}")
        print(f"💡 {rec['recommendation']}")
        print(f"🧠 Raciocínio: {rec['reasoning']}")
    else:
        print(f"\n❌ Nenhum value detectado")
        print(f"Motivo: {analysis['value_analysis']['reason']}")

if __name__ == "__main__":
    main() 