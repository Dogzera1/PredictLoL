#!/usr/bin/env python3
"""
FASE 3 - ENGENHARIA DE ATRIBUTOS AVANÇADA
Sistema de feature engineering avançado para melhorar precisão do modelo LoL
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.decomposition import PCA
import pickle
import json
from datetime import datetime
from dataclasses import dataclass


@dataclass
class FeatureConfig:
    """Configuração para geração de features"""
    enable_interactions: bool = True
    enable_temporal: bool = True
    enable_embedding: bool = True
    enable_meta_patch: bool = True
    max_features: int = 200
    interaction_depth: int = 2


class AdvancedFeatureEngineer:
    """Sistema avançado de engenharia de features para LoL"""
    
    def __init__(self, config: FeatureConfig = None):
        self.config = config or FeatureConfig()
        self.feature_importance = {}
        self.interaction_features = []
        self.temporal_features = []
        self.embedding_features = []
        self.meta_features = []
        
        # Base de conhecimento de counter-picks e matchups
        self.matchup_database = self._load_matchup_knowledge()
        self.champion_embeddings = self._load_champion_embeddings()
        
        # Scalers e encoders
        self.scalers = {}
        self.encoders = {}
        
    def _load_matchup_knowledge(self) -> Dict[str, Dict]:
        """Carrega base de conhecimento de matchups e counter-picks"""
        
        # Simulação de dados históricos de matchups
        # Em produção, isso viria de uma análise histórica real
        matchups = {
            # Top lane matchups
            'Aatrox': {
                'counters': ['Fiora', 'Camille', 'Jax'],
                'weak_against': ['Gnar', 'Kennen', 'Quinn'],
                'synergies': ['Sejuani', 'Graves', 'Orianna'],
                'win_rate_vs': {
                    'Gnar': 0.45, 'Fiora': 0.52, 'Camille': 0.48,
                    'Ornn': 0.54, 'Malphite': 0.58
                }
            },
            'Gnar': {
                'counters': ['Aatrox', 'Darius', 'Renekton'],
                'weak_against': ['Fiora', 'Irelia', 'Yasuo'],
                'synergies': ['Yasuo', 'Orianna', 'Malphite'],
                'win_rate_vs': {
                    'Aatrox': 0.55, 'Darius': 0.52, 'Fiora': 0.42,
                    'Camille': 0.47, 'Ornn': 0.51
                }
            },
            # Mid lane matchups
            'Azir': {
                'counters': ['Kassadin', 'Fizz', 'Zed'],
                'weak_against': ['Orianna', 'Syndra', 'Viktor'],
                'synergies': ['Sejuani', 'Leona', 'Nautilus'],
                'win_rate_vs': {
                    'Kassadin': 0.42, 'Orianna': 0.48, 'LeBlanc': 0.45,
                    'Syndra': 0.46, 'Viktor': 0.47
                }
            },
            'LeBlanc': {
                'counters': ['Azir', 'Orianna', 'Malzahar'],
                'weak_against': ['Kassadin', 'Galio', 'Lissandra'],
                'synergies': ['Graves', 'Elise', 'Thresh'],
                'win_rate_vs': {
                    'Azir': 0.55, 'Orianna': 0.52, 'Kassadin': 0.44,
                    'Syndra': 0.51, 'Viktor': 0.49
                }
            }
        }
        
        return matchups
    
    def _load_champion_embeddings(self) -> Dict[str, np.ndarray]:
        """Carrega embeddings de campeões baseados em características"""
        
        # Características dos campeões (0-10 scale)
        champion_stats = {
            'Aatrox': [7, 5, 3, 6, 8, 7],      # [damage, tank, mobility, cc, scaling, early]
            'Gnar': [6, 7, 6, 8, 7, 6],
            'Azir': [8, 3, 4, 5, 9, 4],
            'LeBlanc': [9, 2, 8, 4, 6, 8],
            'Jinx': [9, 1, 3, 3, 10, 3],
            'Lucian': [8, 2, 6, 2, 6, 9],
            'Thresh': [3, 6, 5, 9, 7, 7],
            'Lulu': [4, 3, 4, 6, 8, 6]
        }
        
        embeddings = {}
        for champion, stats in champion_stats.items():
            # Converter para embedding normalizado
            embedding = np.array(stats, dtype=float)
            embedding = embedding / np.linalg.norm(embedding)
            embeddings[champion] = embedding
        
        return embeddings
    
    def generate_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gera features de interações entre composições"""
        
        print("🔄 Gerando features de interações...")
        
        df_features = df.copy()
        
        # 1. Counter-pick features
        if 'team1_comp' in df.columns and 'team2_comp' in df.columns:
            df_features['counter_pick_advantage'] = df.apply(
                lambda row: self._calculate_counter_advantage(
                    row['team1_comp'], row['team2_comp']
                ), axis=1
            )
        
        # 2. Synergy features
        if 'team1_comp' in df.columns:
            df_features['team1_synergy_score'] = df['team1_comp'].apply(
                self._calculate_team_synergy
            )
        if 'team2_comp' in df.columns:
            df_features['team2_synergy_score'] = df['team2_comp'].apply(
                self._calculate_team_synergy
            )
        
        # 3. Embedding similarity features
        if 'team1_comp' in df.columns and 'team2_comp' in df.columns:
            df_features['comp_similarity'] = df.apply(
                lambda row: self._calculate_composition_similarity(
                    row['team1_comp'], row['team2_comp']
                ), axis=1
            )
        
        # 4. Role balance features
        for team in ['team1', 'team2']:
            if f'{team}_comp' in df.columns:
                balance_features = df[f'{team}_comp'].apply(self._calculate_role_balance)
                df_features[f'{team}_role_balance'] = balance_features
        
        # 5. Power spike timing features
        for team in ['team1', 'team2']:
            if f'{team}_comp' in df.columns:
                power_features = df[f'{team}_comp'].apply(self._calculate_power_spikes)
                df_features[f'{team}_early_power'] = power_features.apply(lambda x: x[0])
                df_features[f'{team}_mid_power'] = power_features.apply(lambda x: x[1])
                df_features[f'{team}_late_power'] = power_features.apply(lambda x: x[2])
        
        # 6. Draft advantage features
        if 'team1_comp' in df.columns and 'team2_comp' in df.columns:
            df_features['draft_advantage'] = df.apply(
                lambda row: self._calculate_draft_advantage(
                    row['team1_comp'], row['team2_comp']
                ), axis=1
            )
        
        print(f"✅ Geradas {len([c for c in df_features.columns if c not in df.columns])} features de interação")
        
        return df_features
    
    def generate_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gera features temporais refinadas"""
        
        print("🔄 Gerando features temporais...")
        
        df_features = df.copy()
        
        # 1. Janelas móveis para estatísticas
        window_sizes = [30, 60, 120, 300]  # segundos
        
        for window in window_sizes:
            if 'game_time' in df.columns:
                # Gold difference em janelas
                if 'gold_diff' in df.columns:
                    df_features[f'gold_diff_ma_{window}s'] = df['gold_diff'].rolling(
                        window=window, min_periods=1
                    ).mean()
                
                # Kill rate em janelas
                if 'total_kills' in df.columns and 'game_time' in df.columns:
                    df_features[f'kill_rate_{window}s'] = (
                        df['total_kills'] / (df['game_time'] / 60)
                    ).rolling(window=window, min_periods=1).mean()
        
        # 2. Features de ritmo de jogo
        if 'game_time' in df.columns:
            # Farm efficiency por tempo
            if 'team1_cs' in df.columns:
                df_features['team1_cs_per_min'] = df['team1_cs'] / (df['game_time'] / 60)
            if 'team2_cs' in df.columns:
                df_features['team2_cs_per_min'] = df['team2_cs'] / (df['game_time'] / 60)
            
            # Damage per minute
            if 'team1_damage' in df.columns:
                df_features['team1_dpm'] = df['team1_damage'] / (df['game_time'] / 60)
            if 'team2_damage' in df.columns:
                df_features['team2_dpm'] = df['team2_damage'] / (df['game_time'] / 60)
        
        # 3. Features de momentum
        if 'gold_diff' in df.columns:
            # Momentum baseado em mudanças de gold diff
            df_features['gold_momentum'] = df['gold_diff'].diff().fillna(0)
            df_features['gold_momentum_ma'] = df_features['gold_momentum'].rolling(
                window=5, min_periods=1
            ).mean()
        
        # 4. Features de fase do jogo
        if 'game_time' in df.columns:
            df_features['game_phase'] = df['game_time'].apply(self._classify_game_phase)
            df_features['early_game'] = (df['game_time'] <= 900).astype(int)  # 15 min
            df_features['mid_game'] = ((df['game_time'] > 900) & (df['game_time'] <= 2100)).astype(int)  # 15-35 min
            df_features['late_game'] = (df['game_time'] > 2100).astype(int)  # 35+ min
        
        print(f"✅ Geradas {len([c for c in df_features.columns if c not in df.columns])} features temporais")
        
        return df_features
    
    def generate_meta_patch_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gera features baseadas no meta e patch"""
        
        print("🔄 Gerando features de meta e patch...")
        
        df_features = df.copy()
        
        # 1. Encoding de patch com características
        if 'patch' in df.columns:
            # Extrair número major e minor do patch
            patch_info = df['patch'].str.extract(r'(\d+)\.(\d+)')
            df_features['patch_major'] = patch_info[0].astype(float)
            df_features['patch_minor'] = patch_info[1].astype(float)
            
            # Days since patch (simulado)
            df_features['days_since_patch'] = np.random.randint(1, 30, len(df))
        
        # 2. Meta strength features
        if 'team1_comp' in df.columns:
            df_features['team1_meta_strength'] = df['team1_comp'].apply(
                self._calculate_meta_strength
            )
        if 'team2_comp' in df.columns:
            df_features['team2_meta_strength'] = df['team2_comp'].apply(
                self._calculate_meta_strength
            )
        
        # 3. Pick/ban priority features
        if 'team1_comp' in df.columns:
            df_features['team1_pick_priority'] = df['team1_comp'].apply(
                self._calculate_pick_priority
            )
        if 'team2_comp' in df.columns:
            df_features['team2_pick_priority'] = df['team2_comp'].apply(
                self._calculate_pick_priority
            )
        
        # 4. Flex pick features
        if 'team1_comp' in df.columns and 'team2_comp' in df.columns:
            df_features['flex_advantage'] = df.apply(
                lambda row: self._calculate_flex_advantage(
                    row['team1_comp'], row['team2_comp']
                ), axis=1
            )
        
        print(f"✅ Geradas {len([c for c in df_features.columns if c not in df.columns])} features de meta")
        
        return df_features
    
    def generate_player_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gera features de performance recente dos jogadores"""
        
        print("🔄 Gerando features de performance de jogadores...")
        
        df_features = df.copy()
        
        # Simulação de dados de performance recente
        # Em produção, isso viria de APIs ou databases
        
        # 1. Form factors (últimas N partidas)
        for team in ['team1', 'team2']:
            # Win rate recente
            df_features[f'{team}_recent_winrate'] = np.random.uniform(0.3, 0.8, len(df))
            
            # Performance média recente
            df_features[f'{team}_recent_kda'] = np.random.uniform(1.0, 3.5, len(df))
            df_features[f'{team}_recent_gpm'] = np.random.uniform(300, 500, len(df))
            df_features[f'{team}_recent_dpm'] = np.random.uniform(400, 700, len(df))
        
        # 2. Matchup experience
        if 'team1_comp' in df.columns and 'team2_comp' in df.columns:
            df_features['matchup_experience'] = df.apply(
                lambda row: self._calculate_matchup_experience(
                    row['team1_comp'], row['team2_comp']
                ), axis=1
            )
        
        # 3. Champion mastery
        for team in ['team1', 'team2']:
            if f'{team}_comp' in df.columns:
                df_features[f'{team}_champion_mastery'] = df[f'{team}_comp'].apply(
                    self._calculate_champion_mastery
                )
        
        print(f"✅ Geradas {len([c for c in df_features.columns if c not in df.columns])} features de performance")
        
        return df_features
    
    # Métodos auxiliares para cálculos
    def _calculate_counter_advantage(self, team1_comp: List[str], team2_comp: List[str]) -> float:
        """Calcula vantagem de counter-picks"""
        if not isinstance(team1_comp, list) or not isinstance(team2_comp, list):
            return 0.0
        
        advantage = 0.0
        comparisons = 0
        
        for champ1 in team1_comp:
            for champ2 in team2_comp:
                if champ1 in self.matchup_database:
                    win_rate = self.matchup_database[champ1].get('win_rate_vs', {}).get(champ2, 0.5)
                    advantage += (win_rate - 0.5)
                    comparisons += 1
        
        return advantage / max(comparisons, 1)
    
    def _calculate_team_synergy(self, comp: List[str]) -> float:
        """Calcula synergy score do time"""
        if not isinstance(comp, list) or len(comp) < 2:
            return 0.5
        
        synergy_score = 0.0
        comparisons = 0
        
        for i, champ1 in enumerate(comp):
            for champ2 in comp[i+1:]:
                if champ1 in self.matchup_database:
                    synergies = self.matchup_database[champ1].get('synergies', [])
                    if champ2 in synergies:
                        synergy_score += 0.2
                comparisons += 1
        
        return min(1.0, synergy_score / max(comparisons, 1) + 0.5)
    
    def _calculate_composition_similarity(self, team1_comp: List[str], team2_comp: List[str]) -> float:
        """Calcula similaridade entre composições usando embeddings"""
        if not isinstance(team1_comp, list) or not isinstance(team2_comp, list):
            return 0.0
        
        # Calcular embedding médio de cada time
        team1_embedding = np.zeros(6)  # 6 características
        team2_embedding = np.zeros(6)
        
        team1_count = 0
        for champ in team1_comp:
            if champ in self.champion_embeddings:
                team1_embedding += self.champion_embeddings[champ]
                team1_count += 1
        
        team2_count = 0
        for champ in team2_comp:
            if champ in self.champion_embeddings:
                team2_embedding += self.champion_embeddings[champ]
                team2_count += 1
        
        if team1_count > 0:
            team1_embedding /= team1_count
        if team2_count > 0:
            team2_embedding /= team2_count
        
        # Calcular similaridade coseno
        if np.linalg.norm(team1_embedding) > 0 and np.linalg.norm(team2_embedding) > 0:
            similarity = np.dot(team1_embedding, team2_embedding) / (
                np.linalg.norm(team1_embedding) * np.linalg.norm(team2_embedding)
            )
            return float(similarity)
        
        return 0.0
    
    def _calculate_role_balance(self, comp: List[str]) -> float:
        """Calcula balance de roles na composição"""
        if not isinstance(comp, list):
            return 0.5
        
        # Simulação simples de balance
        # Em produção, seria baseado em dados reais de roles
        return np.random.uniform(0.3, 0.8)
    
    def _calculate_power_spikes(self, comp: List[str]) -> Tuple[float, float, float]:
        """Calcula power spikes (early, mid, late)"""
        if not isinstance(comp, list):
            return (0.5, 0.5, 0.5)
        
        # Simulação baseada em conhecimento de campeões
        early = np.random.uniform(0.3, 0.8)
        mid = np.random.uniform(0.4, 0.9)
        late = np.random.uniform(0.3, 0.9)
        
        return (early, mid, late)
    
    def _calculate_draft_advantage(self, team1_comp: List[str], team2_comp: List[str]) -> float:
        """Calcula vantagem geral de draft"""
        counter_adv = self._calculate_counter_advantage(team1_comp, team2_comp)
        synergy1 = self._calculate_team_synergy(team1_comp)
        synergy2 = self._calculate_team_synergy(team2_comp)
        
        return counter_adv + (synergy1 - synergy2) * 0.3
    
    def _classify_game_phase(self, game_time: float) -> str:
        """Classifica fase do jogo"""
        if game_time <= 900:  # 15 min
            return "early"
        elif game_time <= 2100:  # 35 min
            return "mid"
        else:
            return "late"
    
    def _calculate_meta_strength(self, comp: List[str]) -> float:
        """Calcula força no meta atual"""
        if not isinstance(comp, list):
            return 0.5
        
        # Simulação de meta strength
        return np.random.uniform(0.3, 0.8)
    
    def _calculate_pick_priority(self, comp: List[str]) -> float:
        """Calcula prioridade de pick"""
        if not isinstance(comp, list):
            return 0.5
        
        return np.random.uniform(0.2, 0.9)
    
    def _calculate_flex_advantage(self, team1_comp: List[str], team2_comp: List[str]) -> float:
        """Calcula vantagem de flex picks"""
        # Simulação de flex advantage
        return np.random.uniform(-0.2, 0.2)
    
    def _calculate_matchup_experience(self, team1_comp: List[str], team2_comp: List[str]) -> float:
        """Calcula experiência no matchup"""
        return np.random.uniform(0.0, 1.0)
    
    def _calculate_champion_mastery(self, comp: List[str]) -> float:
        """Calcula mastery médio dos campeões"""
        if not isinstance(comp, list):
            return 0.5
        
        return np.random.uniform(0.4, 0.9)
    
    def feature_selection(self, X: pd.DataFrame, y: pd.Series, method: str = 'mutual_info') -> pd.DataFrame:
        """Seleção automática de features mais importantes"""
        
        print(f"🔄 Selecionando features usando {method}...")
        
        # Preparar dados
        X_numeric = X.select_dtypes(include=[np.number])
        
        if method == 'mutual_info':
            selector = SelectKBest(score_func=mutual_info_classif, k=min(self.config.max_features, X_numeric.shape[1]))
        else:
            selector = SelectKBest(score_func=f_classif, k=min(self.config.max_features, X_numeric.shape[1]))
        
        X_selected = selector.fit_transform(X_numeric, y)
        selected_features = X_numeric.columns[selector.get_support()]
        
        print(f"✅ Selecionadas {len(selected_features)} features de {X_numeric.shape[1]} originais")
        
        # Salvar feature importance
        feature_scores = selector.scores_
        self.feature_importance = dict(zip(selected_features, feature_scores[selector.get_support()]))
        
        return pd.DataFrame(X_selected, columns=selected_features, index=X.index)
    
    def transform_dataset(self, df: pd.DataFrame, target_column: str = 'team1_win') -> Tuple[pd.DataFrame, pd.Series]:
        """Pipeline completo de transformação do dataset"""
        
        print("🚀 INICIANDO FEATURE ENGINEERING AVANÇADA")
        print("=" * 60)
        
        df_transformed = df.copy()
        
        # 1. Features de interação
        if self.config.enable_interactions:
            df_transformed = self.generate_interaction_features(df_transformed)
        
        # 2. Features temporais
        if self.config.enable_temporal:
            df_transformed = self.generate_temporal_features(df_transformed)
        
        # 3. Features de meta/patch
        if self.config.enable_meta_patch:
            df_transformed = self.generate_meta_patch_features(df_transformed)
        
        # 4. Features de performance de jogadores
        df_transformed = self.generate_player_performance_features(df_transformed)
        
        # 5. Separar X e y
        if target_column in df_transformed.columns:
            y = df_transformed[target_column]
            X = df_transformed.drop(columns=[target_column])
        else:
            y = pd.Series([1] * len(df_transformed))  # Dummy target
            X = df_transformed
        
        # 6. Seleção de features
        X_selected = self.feature_selection(X, y)
        
        print(f"\n✅ FEATURE ENGINEERING CONCLUÍDA!")
        print(f"📊 Dataset final: {X_selected.shape[0]} amostras, {X_selected.shape[1]} features")
        
        return X_selected, y
    
    def save_feature_config(self, filepath: str = "data/feature_config.json"):
        """Salva configuração de features"""
        config_data = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'enable_interactions': self.config.enable_interactions,
                'enable_temporal': self.config.enable_temporal,
                'enable_embedding': self.config.enable_embedding,
                'enable_meta_patch': self.config.enable_meta_patch,
                'max_features': self.config.max_features
            },
            'feature_importance': self.feature_importance,
            'total_features_generated': len(self.feature_importance)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Configuração salva em: {filepath}")


# Exemplo de uso
if __name__ == "__main__":
    # Configuração avançada
    config = FeatureConfig(
        enable_interactions=True,
        enable_temporal=True,
        enable_embedding=True,
        enable_meta_patch=True,
        max_features=150
    )
    
    # Criar feature engineer
    feature_engineer = AdvancedFeatureEngineer(config)
    
    # Carregar dados (simulado)
    try:
        df = pd.read_csv("data/processed_match_data.csv")
        print(f"✅ Dados carregados: {len(df)} registros")
        
        # Aplicar feature engineering
        X, y = feature_engineer.transform_dataset(df)
        
        # Salvar resultados
        X.to_csv("data/advanced_features.csv", index=False)
        feature_engineer.save_feature_config()
        
        print("\n🎯 FEATURE ENGINEERING AVANÇADA CONCLUÍDA!")
        print(f"📊 Features finais: {X.shape[1]}")
        print(f"📈 Top 10 features mais importantes:")
        
        sorted_features = sorted(
            feature_engineer.feature_importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for i, (feature, score) in enumerate(sorted_features[:10], 1):
            print(f"   {i}. {feature}: {score:.4f}")
    
    except FileNotFoundError:
        print("❌ Arquivo de dados não encontrado")
        print("💡 Execute primeiro o script de coleta de dados") 