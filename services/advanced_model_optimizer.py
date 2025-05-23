#!/usr/bin/env python3
"""
FASE 4 - OTIMIZAÇÃO DE MODELOS E ARQUITETURAS
Sistema avançado de otimização de hiperparâmetros e experimentação de arquiteturas
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import pickle
import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

# Imports de modelos
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score, classification_report
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler

# Otimização de hiperparâmetros
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

# Deep Learning (opcional)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, LSTM, Attention, LayerNormalization
    from tensorflow.keras.optimizers import Adam, AdamW
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# LightGBM/XGBoost
try:
    import lightgbm as lgb
    import xgboost as xgb
    BOOSTING_AVAILABLE = True
except ImportError:
    BOOSTING_AVAILABLE = False


@dataclass
class ModelConfig:
    """Configuração para otimização de modelos"""
    enable_traditional_ml: bool = True
    enable_deep_learning: bool = False
    enable_ensemble: bool = True
    enable_calibration: bool = True
    optimization_budget: int = 100  # Número de trials para otimização
    cv_folds: int = 5
    test_size: float = 0.2
    random_state: int = 42


class AdvancedModelOptimizer:
    """Sistema avançado de otimização de modelos para LoL"""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.models = {}
        self.best_models = {}
        self.optimization_results = {}
        self.ensemble_models = {}
        
        # Resultados de experimentos
        self.experiment_history = []
        
        print("🚀 INICIALIZANDO OTIMIZADOR AVANÇADO DE MODELOS")
        print(f"✅ Otuna disponível: {OPTUNA_AVAILABLE}")
        print(f"✅ TensorFlow disponível: {TF_AVAILABLE}")
        print(f"✅ LightGBM/XGBoost disponível: {BOOSTING_AVAILABLE}")
    
    def define_search_spaces(self) -> Dict[str, Dict]:
        """Define espaços de busca para hiperparâmetros"""
        
        search_spaces = {
            'RandomForest': {
                'n_estimators': [100, 200, 300, 500],
                'max_depth': [8, 12, 16, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2', 0.3, 0.5],
                'bootstrap': [True, False],
                'class_weight': ['balanced', None]
            },
            
            'GradientBoosting': {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'max_depth': [3, 5, 7, 9],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'subsample': [0.8, 0.9, 1.0],
                'max_features': ['sqrt', 'log2', None]
            },
            
            'LogisticRegression': {
                'C': [0.01, 0.1, 1.0, 10.0, 100.0],
                'penalty': ['l1', 'l2', 'elasticnet'],
                'solver': ['liblinear', 'saga'],
                'max_iter': [1000, 2000, 5000],
                'class_weight': ['balanced', None]
            },
            
            'SVC': {
                'C': [0.1, 1.0, 10.0, 100.0],
                'kernel': ['rbf', 'poly', 'sigmoid'],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1],
                'class_weight': ['balanced', None],
                'probability': [True]
            },
            
            'MLP': {
                'hidden_layer_sizes': [(100,), (200,), (100, 50), (200, 100), (300, 150, 75)],
                'activation': ['relu', 'tanh', 'logistic'],
                'alpha': [0.0001, 0.001, 0.01],
                'learning_rate': ['constant', 'adaptive'],
                'max_iter': [500, 1000, 2000],
                'early_stopping': [True],
                'validation_fraction': [0.1]
            }
        }
        
        # Adicionar LightGBM/XGBoost se disponível
        if BOOSTING_AVAILABLE:
            search_spaces['LightGBM'] = {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [-1, 5, 10, 15],
                'num_leaves': [31, 50, 100],
                'min_data_in_leaf': [10, 20, 30],
                'feature_fraction': [0.8, 0.9, 1.0],
                'bagging_fraction': [0.8, 0.9, 1.0],
                'objective': ['binary'],
                'metric': ['binary_logloss'],
                'boosting_type': ['gbdt']
            }
            
            search_spaces['XGBoost'] = {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [3, 6, 9],
                'min_child_weight': [1, 3, 5],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0],
                'objective': ['binary:logistic'],
                'eval_metric': ['logloss']
            }
        
        return search_spaces
    
    def optimize_traditional_models(self, X_train: np.ndarray, y_train: np.ndarray, 
                                  X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
        """Otimiza modelos tradicionais de ML"""
        
        print("🔄 OTIMIZANDO MODELOS TRADICIONAIS...")
        
        search_spaces = self.define_search_spaces()
        cv = StratifiedKFold(n_splits=self.config.cv_folds, shuffle=True, random_state=self.config.random_state)
        
        results = {}
        
        # 1. Random Forest
        print("🌲 Otimizando Random Forest...")
        rf_search = RandomizedSearchCV(
            RandomForestClassifier(random_state=self.config.random_state),
            search_spaces['RandomForest'],
            n_iter=50,
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1,
            random_state=self.config.random_state
        )
        rf_search.fit(X_train, y_train)
        results['RandomForest'] = self._evaluate_model(rf_search.best_estimator_, X_val, y_val, 'RandomForest')
        
        # 2. Gradient Boosting
        print("📈 Otimizando Gradient Boosting...")
        gb_search = RandomizedSearchCV(
            GradientBoostingClassifier(random_state=self.config.random_state),
            search_spaces['GradientBoosting'],
            n_iter=50,
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1,
            random_state=self.config.random_state
        )
        gb_search.fit(X_train, y_train)
        results['GradientBoosting'] = self._evaluate_model(gb_search.best_estimator_, X_val, y_val, 'GradientBoosting')
        
        # 3. Logistic Regression
        print("📊 Otimizando Logistic Regression...")
        # Normalizar dados para LR
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        lr_search = RandomizedSearchCV(
            LogisticRegression(random_state=self.config.random_state),
            search_spaces['LogisticRegression'],
            n_iter=30,
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1,
            random_state=self.config.random_state
        )
        lr_search.fit(X_train_scaled, y_train)
        results['LogisticRegression'] = self._evaluate_model(lr_search.best_estimator_, X_val_scaled, y_val, 'LogisticRegression')
        
        # 4. LightGBM (se disponível)
        if BOOSTING_AVAILABLE:
            print("🚀 Otimizando LightGBM...")
            lgb_search = RandomizedSearchCV(
                lgb.LGBMClassifier(random_state=self.config.random_state, verbose=-1),
                search_spaces['LightGBM'],
                n_iter=40,
                cv=cv,
                scoring='roc_auc',
                n_jobs=-1,
                random_state=self.config.random_state
            )
            lgb_search.fit(X_train, y_train)
            results['LightGBM'] = self._evaluate_model(lgb_search.best_estimator_, X_val, y_val, 'LightGBM')
        
        # 5. XGBoost (se disponível)
        if BOOSTING_AVAILABLE:
            print("⚡ Otimizando XGBoost...")
            xgb_search = RandomizedSearchCV(
                xgb.XGBClassifier(random_state=self.config.random_state, eval_metric='logloss'),
                search_spaces['XGBoost'],
                n_iter=40,
                cv=cv,
                scoring='roc_auc',
                n_jobs=-1,
                random_state=self.config.random_state
            )
            xgb_search.fit(X_train, y_train)
            results['XGBoost'] = self._evaluate_model(xgb_search.best_estimator_, X_val, y_val, 'XGBoost')
        
        print("✅ Otimização de modelos tradicionais concluída!")
        return results
    
    def optimize_with_optuna(self, X_train: np.ndarray, y_train: np.ndarray,
                           X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
        """Otimização avançada usando Optuna"""
        
        if not OPTUNA_AVAILABLE:
            print("⚠️ Optuna não disponível - usando otimização padrão")
            return self.optimize_traditional_models(X_train, y_train, X_val, y_val)
        
        print("🎯 OTIMIZAÇÃO AVANÇADA COM OPTUNA...")
        
        results = {}
        
        # 1. Otimizar LightGBM com Optuna
        if BOOSTING_AVAILABLE:
            print("🚀 Otimizando LightGBM com Optuna...")
            
            def objective_lgb(trial):
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'num_leaves': trial.suggest_int('num_leaves', 10, 100),
                    'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 5, 50),
                    'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
                    'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
                    'objective': 'binary',
                    'metric': 'binary_logloss',
                    'boosting_type': 'gbdt',
                    'random_state': self.config.random_state,
                    'verbose': -1
                }
                
                model = lgb.LGBMClassifier(**params)
                scores = cross_val_score(model, X_train, y_train, cv=3, scoring='roc_auc')
                return scores.mean()
            
            study_lgb = optuna.create_study(direction='maximize')
            study_lgb.optimize(objective_lgb, n_trials=self.config.optimization_budget)
            
            # Treinar melhor modelo
            best_lgb = lgb.LGBMClassifier(**study_lgb.best_params, random_state=self.config.random_state, verbose=-1)
            best_lgb.fit(X_train, y_train)
            results['LightGBM_Optuna'] = self._evaluate_model(best_lgb, X_val, y_val, 'LightGBM_Optuna')
        
        # 2. Otimizar Neural Network com Optuna
        print("🧠 Otimizando Neural Network com Optuna...")
        
        def objective_nn(trial):
            # Normalizar dados
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            
            params = {
                'hidden_layer_sizes': tuple([trial.suggest_int(f'n_units_l{i}', 50, 300) 
                                           for i in range(trial.suggest_int('n_layers', 1, 3))]),
                'activation': trial.suggest_categorical('activation', ['relu', 'tanh']),
                'alpha': trial.suggest_float('alpha', 1e-5, 1e-1, log=True),
                'learning_rate_init': trial.suggest_float('learning_rate_init', 1e-4, 1e-1, log=True),
                'max_iter': 1000,
                'early_stopping': True,
                'validation_fraction': 0.1,
                'random_state': self.config.random_state
            }
            
            model = MLPClassifier(**params)
            scores = cross_val_score(model, X_train_scaled, y_train, cv=3, scoring='roc_auc')
            return scores.mean()
        
        study_nn = optuna.create_study(direction='maximize')
        study_nn.optimize(objective_nn, n_trials=50)
        
        # Treinar melhor modelo
        scaler_nn = StandardScaler()
        X_train_scaled = scaler_nn.fit_transform(X_train)
        X_val_scaled = scaler_nn.transform(X_val)
        
        best_nn = MLPClassifier(**study_nn.best_params, random_state=self.config.random_state)
        best_nn.fit(X_train_scaled, y_train)
        results['NeuralNetwork_Optuna'] = self._evaluate_model(best_nn, X_val_scaled, y_val, 'NeuralNetwork_Optuna')
        
        print("✅ Otimização com Optuna concluída!")
        return results
    
    def create_deep_learning_models(self, X_train: np.ndarray, y_train: np.ndarray,
                                  X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
        """Cria modelos de deep learning avançados"""
        
        if not TF_AVAILABLE:
            print("⚠️ TensorFlow não disponível - pulando deep learning")
            return {}
        
        print("🧠 CRIANDO MODELOS DE DEEP LEARNING...")
        
        # Normalizar dados
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        results = {}
        input_dim = X_train_scaled.shape[1]
        
        # 1. Dense Neural Network
        print("🔹 Criando Dense Neural Network...")
        
        model_dense = Sequential([
            Dense(512, activation='relu', input_shape=(input_dim,)),
            Dropout(0.3),
            Dense(256, activation='relu'),
            Dropout(0.3),
            Dense(128, activation='relu'),
            Dropout(0.2),
            Dense(64, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        
        model_dense.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC']
        )
        
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(patience=5, factor=0.5)
        ]
        
        history_dense = model_dense.fit(
            X_train_scaled, y_train,
            epochs=100,
            batch_size=64,
            validation_data=(X_val_scaled, y_val),
            callbacks=callbacks,
            verbose=0
        )
        
        results['DenseNN'] = self._evaluate_tf_model(model_dense, X_val_scaled, y_val, 'DenseNN')
        
        # 2. Time-series inspired model (com features temporais)
        if X_train_scaled.shape[1] >= 50:  # Se temos features suficientes
            print("📈 Criando Time-series Transformer...")
            
            # Reshape para formato temporal (simular sequência)
            sequence_length = min(10, X_train_scaled.shape[1] // 5)
            features_per_step = X_train_scaled.shape[1] // sequence_length
            
            X_train_reshaped = X_train_scaled[:, :sequence_length * features_per_step].reshape(
                -1, sequence_length, features_per_step
            )
            X_val_reshaped = X_val_scaled[:, :sequence_length * features_per_step].reshape(
                -1, sequence_length, features_per_step
            )
            
            model_lstm = Sequential([
                LSTM(128, return_sequences=True, input_shape=(sequence_length, features_per_step)),
                Dropout(0.3),
                LSTM(64, return_sequences=False),
                Dropout(0.3),
                Dense(32, activation='relu'),
                Dense(1, activation='sigmoid')
            ])
            
            model_lstm.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='binary_crossentropy',
                metrics=['accuracy', 'AUC']
            )
            
            history_lstm = model_lstm.fit(
                X_train_reshaped, y_train,
                epochs=50,
                batch_size=32,
                validation_data=(X_val_reshaped, y_val),
                callbacks=callbacks,
                verbose=0
            )
            
            results['LSTM'] = self._evaluate_tf_model(model_lstm, X_val_reshaped, y_val, 'LSTM')
        
        print("✅ Modelos de deep learning criados!")
        return results
    
    def create_ensemble_models(self, models: Dict[str, Any], X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
        """Cria ensemble de modelos"""
        
        print("🎭 CRIANDO ENSEMBLE DE MODELOS...")
        
        if len(models) < 2:
            print("⚠️ Necessário pelo menos 2 modelos para ensemble")
            return {}
        
        results = {}
        
        # 1. Voting Ensemble (média simples)
        print("🗳️ Criando Voting Ensemble...")
        predictions = []
        model_names = []
        
        for name, model_data in models.items():
            if 'model' in model_data:
                model = model_data['model']
                if hasattr(model, 'predict_proba'):
                    pred = model.predict_proba(X_val)[:, 1]
                else:
                    pred = model.predict(X_val)
                predictions.append(pred)
                model_names.append(name)
        
        if predictions:
            # Ensemble por média
            ensemble_pred = np.mean(predictions, axis=0)
            
            auc = roc_auc_score(y_val, ensemble_pred)
            logloss = log_loss(y_val, ensemble_pred)
            accuracy = accuracy_score(y_val, (ensemble_pred > 0.5).astype(int))
            
            results['VotingEnsemble'] = {
                'auc_roc': auc,
                'log_loss': logloss,
                'accuracy': accuracy,
                'models_used': model_names,
                'predictions': ensemble_pred
            }
            
            print(f"   📊 Voting Ensemble AUC: {auc:.4f}")
        
        # 2. Weighted Ensemble (baseado na performance)
        print("⚖️ Criando Weighted Ensemble...")
        if len(models) >= 3:
            weights = []
            for name, model_data in models.items():
                if 'auc_roc' in model_data:
                    weights.append(model_data['auc_roc'])
                else:
                    weights.append(0.5)
            
            # Normalizar weights
            weights = np.array(weights)
            weights = weights / np.sum(weights)
            
            # Ensemble ponderado
            weighted_pred = np.average(predictions, axis=0, weights=weights[:len(predictions)])
            
            auc = roc_auc_score(y_val, weighted_pred)
            logloss = log_loss(y_val, weighted_pred)
            accuracy = accuracy_score(y_val, (weighted_pred > 0.5).astype(int))
            
            results['WeightedEnsemble'] = {
                'auc_roc': auc,
                'log_loss': logloss,
                'accuracy': accuracy,
                'weights': weights.tolist(),
                'models_used': model_names,
                'predictions': weighted_pred
            }
            
            print(f"   📊 Weighted Ensemble AUC: {auc:.4f}")
        
        # 3. Stacking Ensemble
        print("🏗️ Criando Stacking Ensemble...")
        if len(predictions) >= 2:
            # Usar predições como features para meta-modelo
            meta_features = np.column_stack(predictions)
            
            # Meta-modelo simples (Logistic Regression)
            meta_model = LogisticRegression(random_state=self.config.random_state)
            meta_model.fit(meta_features, y_val)  # Usando validação como treino para meta-modelo
            
            # Predição do stacking
            stacking_pred = meta_model.predict_proba(meta_features)[:, 1]
            
            auc = roc_auc_score(y_val, stacking_pred)
            logloss = log_loss(y_val, stacking_pred)
            accuracy = accuracy_score(y_val, (stacking_pred > 0.5).astype(int))
            
            results['StackingEnsemble'] = {
                'auc_roc': auc,
                'log_loss': logloss,
                'accuracy': accuracy,
                'meta_model': meta_model,
                'models_used': model_names,
                'predictions': stacking_pred
            }
            
            print(f"   📊 Stacking Ensemble AUC: {auc:.4f}")
        
        print("✅ Ensemble criado com sucesso!")
        return results
    
    def calibrate_models(self, models: Dict[str, Any], X_train: np.ndarray, y_train: np.ndarray,
                        X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
        """Calibra probabilidades dos modelos"""
        
        print("🎯 CALIBRANDO MODELOS...")
        
        calibrated_results = {}
        
        for name, model_data in models.items():
            if 'model' not in model_data:
                continue
                
            print(f"🔧 Calibrando {name}...")
            
            model = model_data['model']
            
            # Calibração usando CalibratedClassifierCV
            calibrated_clf = CalibratedClassifierCV(
                model, 
                method='isotonic',  # ou 'sigmoid'
                cv=3
            )
            
            calibrated_clf.fit(X_train, y_train)
            
            # Avaliar modelo calibrado
            calibrated_results[f'{name}_Calibrated'] = self._evaluate_model(
                calibrated_clf, X_val, y_val, f'{name}_Calibrated'
            )
        
        print("✅ Calibração concluída!")
        return calibrated_results
    
    def _evaluate_model(self, model, X_val: np.ndarray, y_val: np.ndarray, model_name: str) -> Dict[str, Any]:
        """Avalia um modelo sklearn"""
        
        start_time = time.time()
        
        if hasattr(model, 'predict_proba'):
            y_pred_proba = model.predict_proba(X_val)[:, 1]
        else:
            y_pred_proba = model.predict(X_val)
        
        inference_time = (time.time() - start_time) / len(X_val) * 1000  # ms por predição
        
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        auc = roc_auc_score(y_val, y_pred_proba)
        logloss = log_loss(y_val, y_pred_proba)
        accuracy = accuracy_score(y_val, y_pred)
        
        result = {
            'model': model,
            'model_name': model_name,
            'auc_roc': auc,
            'log_loss': logloss,
            'accuracy': accuracy,
            'inference_time_ms': inference_time,
            'predictions': y_pred_proba,
            'binary_predictions': y_pred
        }
        
        print(f"   📊 {model_name} - AUC: {auc:.4f}, Log-loss: {logloss:.4f}, Acc: {accuracy:.4f}")
        
        return result
    
    def _evaluate_tf_model(self, model, X_val: np.ndarray, y_val: np.ndarray, model_name: str) -> Dict[str, Any]:
        """Avalia um modelo TensorFlow"""
        
        start_time = time.time()
        y_pred_proba = model.predict(X_val, verbose=0).flatten()
        inference_time = (time.time() - start_time) / len(X_val) * 1000
        
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        auc = roc_auc_score(y_val, y_pred_proba)
        logloss = log_loss(y_val, y_pred_proba)
        accuracy = accuracy_score(y_val, y_pred)
        
        result = {
            'model': model,
            'model_name': model_name,
            'auc_roc': auc,
            'log_loss': logloss,
            'accuracy': accuracy,
            'inference_time_ms': inference_time,
            'predictions': y_pred_proba,
            'binary_predictions': y_pred
        }
        
        print(f"   📊 {model_name} - AUC: {auc:.4f}, Log-loss: {logloss:.4f}, Acc: {accuracy:.4f}")
        
        return result
    
    def run_optimization_pipeline(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Pipeline completo de otimização"""
        
        print("🚀 INICIANDO PIPELINE DE OTIMIZAÇÃO AVANÇADA")
        print("=" * 70)
        
        # Split treino/validação
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=self.config.test_size, 
            random_state=self.config.random_state, stratify=y
        )
        
        print(f"📊 Treino: {X_train.shape[0]} amostras")
        print(f"📊 Validação: {X_val.shape[0]} amostras")
        
        all_results = {}
        
        # 1. Modelos tradicionais
        if self.config.enable_traditional_ml:
            traditional_results = self.optimize_traditional_models(X_train, y_train, X_val, y_val)
            all_results.update(traditional_results)
        
        # 2. Otimização com Optuna
        if OPTUNA_AVAILABLE:
            optuna_results = self.optimize_with_optuna(X_train, y_train, X_val, y_val)
            all_results.update(optuna_results)
        
        # 3. Deep Learning
        if self.config.enable_deep_learning and TF_AVAILABLE:
            dl_results = self.create_deep_learning_models(X_train, y_train, X_val, y_val)
            all_results.update(dl_results)
        
        # 4. Ensemble
        if self.config.enable_ensemble and len(all_results) >= 2:
            ensemble_results = self.create_ensemble_models(all_results, X_val, y_val)
            all_results.update(ensemble_results)
        
        # 5. Calibração
        if self.config.enable_calibration:
            calibrated_results = self.calibrate_models(all_results, X_train, y_train, X_val, y_val)
            all_results.update(calibrated_results)
        
        # Identificar melhor modelo
        best_model = self._select_best_model(all_results)
        
        # Relatório final
        optimization_report = {
            'timestamp': datetime.now().isoformat(),
            'config': asdict(self.config),
            'models_tested': len(all_results),
            'best_model': best_model,
            'all_results': {name: {k: v for k, v in result.items() if k != 'model'} 
                           for name, result in all_results.items()},
            'dataset_info': {
                'train_samples': X_train.shape[0],
                'val_samples': X_val.shape[0],
                'features': X_train.shape[1],
                'positive_rate': float(np.mean(y))
            }
        }
        
        print("\n" + "="*70)
        print("✅ OTIMIZAÇÃO CONCLUÍDA!")
        print(f"🏆 MELHOR MODELO: {best_model['name']}")
        print(f"📊 AUC-ROC: {best_model['auc_roc']:.4f}")
        print(f"📉 Log-loss: {best_model['log_loss']:.4f}")
        print(f"✅ Acurácia: {best_model['accuracy']:.4f}")
        print(f"⚡ Tempo: {best_model['inference_time_ms']:.2f}ms")
        
        return optimization_report
    
    def _select_best_model(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Seleciona o melhor modelo baseado em múltiplas métricas"""
        
        # Score composto: AUC (60%) + (1 - Log-loss) (30%) + Acurácia (10%)
        best_score = -1
        best_model = None
        
        for name, result in results.items():
            if 'auc_roc' not in result:
                continue
                
            auc = result['auc_roc']
            logloss = result.get('log_loss', 1.0)
            accuracy = result.get('accuracy', 0.5)
            
            # Score normalizado
            score = 0.6 * auc + 0.3 * (1 - min(logloss, 1.0)) + 0.1 * accuracy
            
            if score > best_score:
                best_score = score
                best_model = {
                    'name': name,
                    'score': score,
                    'auc_roc': auc,
                    'log_loss': logloss,
                    'accuracy': accuracy,
                    'inference_time_ms': result.get('inference_time_ms', 0)
                }
        
        return best_model
    
    def save_optimization_results(self, results: Dict[str, Any], filepath: str = "data/optimization_results.json"):
        """Salva resultados da otimização"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultados salvos em: {filepath}")


# Exemplo de uso
if __name__ == "__main__":
    # Configuração
    config = ModelConfig(
        enable_traditional_ml=True,
        enable_deep_learning=False,  # Desabilitar por padrão
        enable_ensemble=True,
        enable_calibration=True,
        optimization_budget=50
    )
    
    optimizer = AdvancedModelOptimizer(config)
    
    # Carregar dados (simulado)
    try:
        import pandas as pd
        
        # Tentar carregar dados avançados primeiro
        try:
            df = pd.read_csv("data/advanced_features.csv")
            print(f"✅ Features avançadas carregadas: {len(df)} registros")
        except FileNotFoundError:
            df = pd.read_csv("data/processed_match_data.csv")
            print(f"✅ Dados básicos carregados: {len(df)} registros")
        
        # Preparar dados
        if 'team1_win' in df.columns:
            y = df['team1_win'].values
            X = df.drop(columns=['team1_win']).select_dtypes(include=[np.number]).values
        else:
            # Dados simulados
            X = np.random.randn(1000, 50)
            y = np.random.binomial(1, 0.5, 1000)
        
        print(f"📊 Dataset: {X.shape[0]} amostras, {X.shape[1]} features")
        
        # Executar otimização
        results = optimizer.run_optimization_pipeline(X, y)
        
        # Salvar resultados
        optimizer.save_optimization_results(results)
        
        print("\n🎯 OTIMIZAÇÃO AVANÇADA CONCLUÍDA!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("💡 Certifique-se de ter dados disponíveis para otimização") 