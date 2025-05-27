#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Machine Learning para Predições de LoL Esports
Implementação com scikit-learn para predições reais baseadas em dados históricos
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os

logger = logging.getLogger(__name__)

class MLPredictionSystem:
    """Sistema de Machine Learning para predições de partidas de LoL"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_columns = [
            'team1_rating', 'team2_rating', 'team1_recent_form', 'team2_recent_form',
            'team1_region_strength', 'team2_region_strength', 'rating_difference',
            'form_difference', 'team1_consistency', 'team2_consistency',
            'team1_meta_adaptation', 'team2_meta_adaptation', 'league_tier',
            'team1_h2h_winrate', 'team1_streak', 'team2_streak'
        ]
        
        # Dados históricos simulados (em produção seria de APIs reais)
        self.historical_data = self._generate_historical_data()
        
        # Treinar modelos
        self._train_models()
        
        logger.info("🤖 Sistema de ML para predições inicializado")
    
    def _generate_historical_data(self) -> pd.DataFrame:
        """Gera dados históricos simulados para treinamento"""
        np.random.seed(42)  # Para reprodutibilidade
        
        # Dados de times conhecidos
        teams_data = {
            'T1': {'rating': 95, 'region': 'LCK', 'tier': 1, 'consistency': 0.88},
            'GEN': {'rating': 90, 'region': 'LCK', 'tier': 1, 'consistency': 0.85},
            'JDG': {'rating': 92, 'region': 'LPL', 'tier': 1, 'consistency': 0.86},
            'BLG': {'rating': 88, 'region': 'LPL', 'tier': 1, 'consistency': 0.83},
            'G2': {'rating': 85, 'region': 'LEC', 'tier': 2, 'consistency': 0.80},
            'FNC': {'rating': 82, 'region': 'LEC', 'tier': 2, 'consistency': 0.78},
            'C9': {'rating': 78, 'region': 'LCS', 'tier': 2, 'consistency': 0.75},
            'TL': {'rating': 76, 'region': 'LCS', 'tier': 2, 'consistency': 0.73},
            'LOUD': {'rating': 72, 'region': 'CBLOL', 'tier': 3, 'consistency': 0.70},
            'FURIA': {'rating': 70, 'region': 'CBLOL', 'tier': 3, 'consistency': 0.68}
        }
        
        region_strength = {
            'LCK': 1.0, 'LPL': 0.95, 'LEC': 0.85, 'LCS': 0.80, 'CBLOL': 0.70
        }
        
        # Gerar 1000 partidas históricas
        data = []
        teams = list(teams_data.keys())
        
        for _ in range(1000):
            # Selecionar dois times aleatórios
            team1, team2 = np.random.choice(teams, 2, replace=False)
            
            # Dados do time 1
            t1_data = teams_data[team1]
            t1_rating = t1_data['rating'] + np.random.normal(0, 3)  # Variação
            t1_form = np.random.uniform(0.6, 1.0)
            t1_region_str = region_strength[t1_data['region']]
            t1_consistency = t1_data['consistency']
            t1_meta = np.random.uniform(0.7, 1.0)
            t1_streak = np.random.randint(-3, 6)
            
            # Dados do time 2
            t2_data = teams_data[team2]
            t2_rating = t2_data['rating'] + np.random.normal(0, 3)
            t2_form = np.random.uniform(0.6, 1.0)
            t2_region_str = region_strength[t2_data['region']]
            t2_consistency = t2_data['consistency']
            t2_meta = np.random.uniform(0.7, 1.0)
            t2_streak = np.random.randint(-3, 6)
            
            # Calcular features
            rating_diff = t1_rating - t2_rating
            form_diff = t1_form - t2_form
            league_tier = min(t1_data['tier'], t2_data['tier'])
            
            # H2H simulado
            h2h_winrate = 0.5 + (rating_diff / 100)  # Baseado na diferença de rating
            h2h_winrate = max(0.2, min(0.8, h2h_winrate))
            
            # Calcular probabilidade real de vitória (para label)
            win_prob = self._calculate_true_win_probability(
                t1_rating, t2_rating, t1_form, t2_form, 
                t1_region_str, t2_region_str, t1_consistency, t2_consistency
            )
            
            # Resultado (1 se team1 ganhou, 0 se team2 ganhou)
            result = 1 if np.random.random() < win_prob else 0
            
            data.append({
                'team1': team1,
                'team2': team2,
                'team1_rating': t1_rating,
                'team2_rating': t2_rating,
                'team1_recent_form': t1_form,
                'team2_recent_form': t2_form,
                'team1_region_strength': t1_region_str,
                'team2_region_strength': t2_region_str,
                'rating_difference': rating_diff,
                'form_difference': form_diff,
                'team1_consistency': t1_consistency,
                'team2_consistency': t2_consistency,
                'team1_meta_adaptation': t1_meta,
                'team2_meta_adaptation': t2_meta,
                'league_tier': league_tier,
                'team1_h2h_winrate': h2h_winrate,
                'team1_streak': t1_streak,
                'team2_streak': t2_streak,
                'team1_won': result
            })
        
        return pd.DataFrame(data)
    
    def _calculate_true_win_probability(self, t1_rating, t2_rating, t1_form, t2_form,
                                      t1_region, t2_region, t1_consistency, t2_consistency):
        """Calcula probabilidade real de vitória para gerar labels"""
        # Fórmula complexa que considera múltiplos fatores
        rating_factor = 1 / (1 + np.exp(-(t1_rating - t2_rating) / 15))
        form_factor = (t1_form - t2_form) * 0.2
        region_factor = (t1_region - t2_region) * 0.1
        consistency_factor = (t1_consistency - t2_consistency) * 0.15
        
        prob = rating_factor + form_factor + region_factor + consistency_factor
        return max(0.15, min(0.85, prob))
    
    def _train_models(self):
        """Treina múltiplos modelos de ML"""
        try:
            # Preparar dados
            X = self.historical_data[self.feature_columns]
            y = self.historical_data['team1_won']
            
            # Dividir dados
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Normalizar features
            self.scalers['standard'] = StandardScaler()
            X_train_scaled = self.scalers['standard'].fit_transform(X_train)
            X_test_scaled = self.scalers['standard'].transform(X_test)
            
            # Treinar múltiplos modelos
            models_to_train = {
                'random_forest': RandomForestClassifier(
                    n_estimators=100, max_depth=10, random_state=42
                ),
                'gradient_boosting': GradientBoostingClassifier(
                    n_estimators=100, max_depth=6, random_state=42
                ),
                'logistic_regression': LogisticRegression(
                    random_state=42, max_iter=1000
                )
            }
            
            best_model = None
            best_score = 0
            
            for name, model in models_to_train.items():
                if name == 'logistic_regression':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                accuracy = accuracy_score(y_test, y_pred)
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                
                logger.info(f"🤖 Modelo {name}: Acurácia = {accuracy:.3f}, CV = {cv_scores.mean():.3f}")
                
                self.models[name] = model
                
                if accuracy > best_score:
                    best_score = accuracy
                    best_model = name
            
            self.best_model = best_model
            logger.info(f"✅ Melhor modelo: {best_model} (Acurácia: {best_score:.3f})")
            
        except Exception as e:
            logger.error(f"❌ Erro no treinamento dos modelos: {e}")
    
    def predict_match(self, team1: str, team2: str, league: str) -> Dict:
        """Faz predição usando ML para uma partida"""
        try:
            # Obter dados dos times
            team1_data = self._get_team_data(team1, league)
            team2_data = self._get_team_data(team2, league)
            
            # Preparar features
            features = self._prepare_features(team1_data, team2_data)
            
            # Fazer predições com todos os modelos
            predictions = {}
            probabilities = {}
            
            for name, model in self.models.items():
                if name == 'logistic_regression':
                    features_scaled = self.scalers['standard'].transform([features])
                    prob = model.predict_proba(features_scaled)[0]
                    pred = model.predict(features_scaled)[0]
                else:
                    prob = model.predict_proba([features])[0]
                    pred = model.predict([features])[0]
                
                predictions[name] = pred
                probabilities[name] = prob[1]  # Probabilidade do team1 ganhar
            
            # Usar ensemble (média ponderada)
            weights = {'random_forest': 0.4, 'gradient_boosting': 0.4, 'logistic_regression': 0.2}
            
            team1_win_prob = sum(
                probabilities[model] * weights[model] 
                for model in probabilities.keys()
            )
            
            team2_win_prob = 1 - team1_win_prob
            
            # Calcular confiança
            confidence = self._calculate_prediction_confidence(
                team1_data, team2_data, team1_win_prob
            )
            
            # Gerar análise
            analysis = self._generate_ml_analysis(
                team1, team2, team1_data, team2_data, team1_win_prob
            )
            
            return {
                'team1': team1,
                'team2': team2,
                'team1_win_probability': team1_win_prob,
                'team2_win_probability': team2_win_prob,
                'predicted_winner': team1 if team1_win_prob > 0.5 else team2,
                'confidence': confidence,
                'ml_analysis': analysis,
                'model_predictions': probabilities,
                'best_model_used': self.best_model,
                'league': league,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na predição ML: {e}")
            return self._get_fallback_prediction(team1, team2, league)
    
    def _get_team_data(self, team: str, league: str) -> Dict:
        """Obtém dados de um time"""
        # Base de dados atualizada
        teams_database = {
            'T1': {'rating': 95, 'region': 'LCK', 'tier': 1, 'consistency': 0.88},
            'GEN': {'rating': 90, 'region': 'LCK', 'tier': 1, 'consistency': 0.85},
            'DK': {'rating': 87, 'region': 'LCK', 'tier': 1, 'consistency': 0.82},
            'KT': {'rating': 84, 'region': 'LCK', 'tier': 1, 'consistency': 0.80},
            'JDG': {'rating': 92, 'region': 'LPL', 'tier': 1, 'consistency': 0.86},
            'BLG': {'rating': 88, 'region': 'LPL', 'tier': 1, 'consistency': 0.83},
            'WBG': {'rating': 85, 'region': 'LPL', 'tier': 1, 'consistency': 0.81},
            'TES': {'rating': 83, 'region': 'LPL', 'tier': 1, 'consistency': 0.79},
            'G2': {'rating': 85, 'region': 'LEC', 'tier': 2, 'consistency': 0.80},
            'FNC': {'rating': 82, 'region': 'LEC', 'tier': 2, 'consistency': 0.78},
            'MAD': {'rating': 79, 'region': 'LEC', 'tier': 2, 'consistency': 0.75},
            'VIT': {'rating': 77, 'region': 'LEC', 'tier': 2, 'consistency': 0.73},
            'C9': {'rating': 78, 'region': 'LCS', 'tier': 2, 'consistency': 0.75},
            'TL': {'rating': 76, 'region': 'LCS', 'tier': 2, 'consistency': 0.73},
            'TSM': {'rating': 72, 'region': 'LCS', 'tier': 2, 'consistency': 0.68},
            '100T': {'rating': 74, 'region': 'LCS', 'tier': 2, 'consistency': 0.70},
            'LOUD': {'rating': 72, 'region': 'CBLOL', 'tier': 3, 'consistency': 0.70},
            'FURIA': {'rating': 70, 'region': 'CBLOL', 'tier': 3, 'consistency': 0.68},
            'RED': {'rating': 67, 'region': 'CBLOL', 'tier': 3, 'consistency': 0.65},
            'KBM': {'rating': 65, 'region': 'CBLOL', 'tier': 3, 'consistency': 0.63}
        }
        
        # Buscar dados do time
        for known_team, data in teams_database.items():
            if known_team.lower() in team.lower() or team.lower() in known_team.lower():
                # Adicionar variação temporal
                data = data.copy()
                data['recent_form'] = np.random.uniform(0.7, 1.0)
                data['meta_adaptation'] = np.random.uniform(0.8, 1.0)
                data['streak'] = np.random.randint(-2, 4)
                return data
        
        # Time desconhecido
        region_strength = {
            'LCK': 1.0, 'LPL': 0.95, 'LEC': 0.85, 'LCS': 0.80, 'CBLOL': 0.70
        }
        
        return {
            'rating': 65,
            'region': league,
            'tier': 3,
            'consistency': 0.65,
            'recent_form': 0.7,
            'meta_adaptation': 0.8,
            'streak': 0
        }
    
    def _prepare_features(self, team1_data: Dict, team2_data: Dict) -> List[float]:
        """Prepara features para o modelo"""
        region_strength = {
            'LCK': 1.0, 'LPL': 0.95, 'LEC': 0.85, 'LCS': 0.80, 'CBLOL': 0.70
        }
        
        t1_region_str = region_strength.get(team1_data['region'], 0.6)
        t2_region_str = region_strength.get(team2_data['region'], 0.6)
        
        # H2H simulado baseado em ratings
        rating_diff = team1_data['rating'] - team2_data['rating']
        h2h_winrate = 0.5 + (rating_diff / 100)
        h2h_winrate = max(0.2, min(0.8, h2h_winrate))
        
        features = [
            team1_data['rating'],
            team2_data['rating'],
            team1_data['recent_form'],
            team2_data['recent_form'],
            t1_region_str,
            t2_region_str,
            rating_diff,
            team1_data['recent_form'] - team2_data['recent_form'],
            team1_data['consistency'],
            team2_data['consistency'],
            team1_data['meta_adaptation'],
            team2_data['meta_adaptation'],
            min(team1_data['tier'], team2_data['tier']),
            h2h_winrate,
            team1_data['streak'],
            team2_data['streak']
        ]
        
        return features
    
    def _calculate_prediction_confidence(self, team1_data: Dict, team2_data: Dict, 
                                       win_prob: float) -> str:
        """Calcula confiança da predição"""
        # Fatores que aumentam confiança
        consistency_avg = (team1_data['consistency'] + team2_data['consistency']) / 2
        rating_diff = abs(team1_data['rating'] - team2_data['rating'])
        prob_certainty = abs(win_prob - 0.5) * 2  # Quão longe de 50/50
        
        confidence_score = (consistency_avg + (rating_diff / 100) + prob_certainty) / 3
        
        if confidence_score > 0.7:
            return "Alta"
        elif confidence_score > 0.5:
            return "Média"
        else:
            return "Baixa"
    
    def _generate_ml_analysis(self, team1: str, team2: str, team1_data: Dict, 
                            team2_data: Dict, win_prob: float) -> str:
        """Gera análise baseada em ML"""
        stronger_team = team1 if win_prob > 0.5 else team2
        stronger_data = team1_data if win_prob > 0.5 else team2_data
        
        analysis_points = []
        
        # Análise de rating
        rating_diff = abs(team1_data['rating'] - team2_data['rating'])
        if rating_diff > 15:
            analysis_points.append(f"ML detecta vantagem significativa de rating para {stronger_team}")
        elif rating_diff > 8:
            analysis_points.append(f"Ligeira vantagem de rating para {stronger_team}")
        
        # Análise de forma
        if stronger_data['recent_form'] > 0.85:
            analysis_points.append(f"{stronger_team} em excelente forma segundo algoritmos")
        
        # Análise de consistência
        if stronger_data['consistency'] > 0.8:
            analysis_points.append(f"Alta consistência detectada em {stronger_team}")
        
        # Análise de meta
        if stronger_data['meta_adaptation'] > 0.9:
            analysis_points.append(f"{stronger_team} bem adaptado ao meta atual")
        
        if not analysis_points:
            analysis_points.append("Partida equilibrada segundo modelos de ML")
        
        return " • ".join(analysis_points)
    
    def _get_fallback_prediction(self, team1: str, team2: str, league: str) -> Dict:
        """Predição de fallback"""
        return {
            'team1': team1,
            'team2': team2,
            'team1_win_probability': 0.5,
            'team2_win_probability': 0.5,
            'predicted_winner': 'Indefinido',
            'confidence': 'Baixa',
            'ml_analysis': 'Predição ML não disponível',
            'model_predictions': {},
            'best_model_used': 'none',
            'league': league,
            'timestamp': datetime.now()
        }
    
    def get_model_info(self) -> Dict:
        """Retorna informações sobre os modelos"""
        return {
            'models_trained': list(self.models.keys()),
            'best_model': self.best_model,
            'training_samples': len(self.historical_data),
            'features_used': len(self.feature_columns),
            'last_training': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        } 