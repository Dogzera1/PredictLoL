#!/usr/bin/env python3
"""
Sistema de Avaliação e Diagnóstico de Modelos LoL
Fase 1: Diagnóstico e Definição de Metas
"""

import numpy as np
import pandas as pd
import pickle
import json
import time
from datetime import datetime, timedelta
from sklearn.metrics import (
    roc_auc_score, log_loss, accuracy_score, precision_recall_curve,
    confusion_matrix, classification_report, roc_curve
)
from sklearn.calibration import calibration_curve
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

class ModelEvaluator:
    """Sistema avançado de avaliação de modelos LoL"""
    
    def __init__(self, model_path: str = "data/model.pkl", 
                 scaler_path: str = "data/scaler.pkl"):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.evaluation_results = {}
        
        self._load_model()
    
    def _load_model(self):
        """Carrega modelo e scaler"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            # Carregar informações do modelo
            try:
                with open("data/model_info.json", 'r') as f:
                    self.model_info = json.load(f)
                    self.feature_names = self.model_info['feature_names']
            except FileNotFoundError:
                self.model_info = None
                self.feature_names = None
                
            print("✅ Modelo e scaler carregados com sucesso")
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
    
    def _encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Codifica features categóricas"""
        df_encoded = df.copy()
        
        # Features categóricas conhecidas
        categorical_features = ['tournament', 'team1_side', 'patch']
        
        for feature in categorical_features:
            if feature in df_encoded.columns:
                if feature not in self.label_encoders:
                    self.label_encoders[feature] = LabelEncoder()
                    df_encoded[feature] = self.label_encoders[feature].fit_transform(df_encoded[feature].astype(str))
                else:
                    # Para novos valores, usar transformação existente
                    try:
                        df_encoded[feature] = self.label_encoders[feature].transform(df_encoded[feature].astype(str))
                    except ValueError:
                        # Se houver valores novos, usar valor padrão
                        df_encoded[feature] = 0
        
        return df_encoded
    
    def load_test_data(self, data_path: str = "data/processed_match_data.json") -> pd.DataFrame:
        """Carrega dados de teste"""
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            print(f"✅ Dados carregados: {len(df)} registros")
            return df
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return pd.DataFrame()
    
    def evaluate_performance(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Avaliação completa de performance"""
        
        # Tempo de inferência
        start_time = time.time()
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        inference_time = (time.time() - start_time) / len(X_test) * 1000  # ms por predição
        
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Métricas principais
        metrics = {
            'auc_roc': float(roc_auc_score(y_test, y_pred_proba)),
            'log_loss': float(log_loss(y_test, y_pred_proba)),
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'inference_time_ms': float(inference_time),
            'total_samples': int(len(y_test)),
            'positive_rate': float(np.mean(y_test)),
            'prediction_mean': float(np.mean(y_pred_proba)),
            'prediction_std': float(np.std(y_pred_proba))
        }
        
        # Precisão por confiança (top-k)
        for threshold in [0.6, 0.7, 0.8, 0.9]:
            confident_mask = (y_pred_proba >= threshold) | (y_pred_proba <= 1-threshold)
            if np.sum(confident_mask) > 0:
                confident_acc = accuracy_score(y_test[confident_mask], y_pred[confident_mask])
                metrics[f'confident_accuracy_{threshold}'] = float(confident_acc)
                metrics[f'confident_samples_{threshold}'] = int(np.sum(confident_mask))
        
        self.evaluation_results.update(metrics)
        return metrics
    
    def analyze_by_context(self, df: pd.DataFrame, predictions: np.ndarray) -> Dict[str, Dict]:
        """Análise por contexto (patches, comps, etc.)"""
        
        results = {}
        
        # Por patch (se disponível)
        if 'patch' in df.columns:
            patch_analysis = {}
            for patch in df['patch'].unique():
                mask = df['patch'] == patch
                if np.sum(mask) > 10:  # Mínimo de amostras reduzido
                    patch_metrics = self._calculate_subset_metrics(
                        df.loc[mask, 'team1_win'].values,
                        predictions[mask]
                    )
                    patch_analysis[str(patch)] = patch_metrics
            results['by_patch'] = patch_analysis
        
        # Por duração do jogo
        if 'game_duration' in df.columns:
            duration_bins = [(0, 25), (25, 35), (35, 999)]  # Mudando para 999 em vez de ∞
            duration_analysis = {}
            
            for min_dur, max_dur in duration_bins:
                mask = (df['game_duration'] >= min_dur) & (df['game_duration'] < max_dur)
                if np.sum(mask) > 10:
                    bin_name = f"{min_dur}-{max_dur if max_dur != 999 else '999+'}min"
                    duration_analysis[bin_name] = self._calculate_subset_metrics(
                        df.loc[mask, 'team1_win'].values,
                        predictions[mask]
                    )
            results['by_duration'] = duration_analysis
        
        # Por lado do mapa
        if 'team1_side' in df.columns:
            side_analysis = {}
            for side in df['team1_side'].unique():
                mask = df['team1_side'] == side
                if np.sum(mask) > 10:
                    side_analysis[str(side)] = self._calculate_subset_metrics(
                        df.loc[mask, 'team1_win'].values,
                        predictions[mask]
                    )
            results['by_side'] = side_analysis
        
        return results
    
    def _calculate_subset_metrics(self, y_true: np.ndarray, y_pred_proba: np.ndarray) -> Dict[str, float]:
        """Calcula métricas para um subset específico"""
        if len(y_true) == 0:
            return {}
        
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        return {
            'auc_roc': float(roc_auc_score(y_true, y_pred_proba)) if len(np.unique(y_true)) > 1 else 0.5,
            'log_loss': float(log_loss(y_true, y_pred_proba)),
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'samples': int(len(y_true)),
            'positive_rate': float(np.mean(y_true)),
            'prediction_mean': float(np.mean(y_pred_proba))
        }
    
    def identify_worst_scenarios(self, df: pd.DataFrame, predictions: np.ndarray, y_true: np.ndarray) -> Dict[str, Any]:
        """Identifica cenários de pior performance"""
        
        # Calcular erro absoluto
        errors = np.abs(predictions - y_true)
        
        # Top piores predições
        worst_indices = np.argsort(errors)[-20:]  # 20 piores
        
        worst_scenarios = {
            'worst_predictions': [],
            'common_patterns': {}
        }
        
        # Analisar piores casos
        for idx in worst_indices:
            scenario = {
                'index': int(idx),
                'true_label': int(y_true[idx]),
                'prediction': float(predictions[idx]),
                'error': float(errors[idx])
            }
            
            # Adicionar contexto se disponível
            if 'patch' in df.columns:
                scenario['patch'] = str(df.iloc[idx]['patch'])
            if 'game_duration' in df.columns:
                scenario['duration'] = float(df.iloc[idx]['game_duration'])
            
            worst_scenarios['worst_predictions'].append(scenario)
        
        # Padrões comuns nos piores casos
        if len(worst_indices) > 0:
            worst_df = df.iloc[worst_indices]
            
            # Patches mais problemáticos
            if 'patch' in worst_df.columns:
                patch_counts = worst_df['patch'].value_counts()
                worst_scenarios['common_patterns']['problematic_patches'] = patch_counts.head().to_dict()
            
            # Durações problemáticas
            if 'game_duration' in worst_df.columns:
                duration_stats = worst_df['game_duration'].describe()
                worst_scenarios['common_patterns']['duration_stats'] = duration_stats.to_dict()
        
        return worst_scenarios
    
    def calibration_analysis(self, y_true: np.ndarray, y_pred_proba: np.ndarray) -> Dict[str, Any]:
        """Análise de calibração do modelo"""
        
        # Curva de calibração
        fraction_positives, mean_predicted_value = calibration_curve(
            y_true, y_pred_proba, n_bins=10, strategy='uniform'
        )
        
        # Brier Score
        brier_score = np.mean((y_pred_proba - y_true) ** 2)
        
        # Expected Calibration Error (ECE)
        bin_boundaries = np.linspace(0, 1, 11)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (y_pred_proba > bin_lower) & (y_pred_proba <= bin_upper)
            prop_in_bin = np.mean(in_bin)
            
            if prop_in_bin > 0:
                accuracy_in_bin = np.mean(y_true[in_bin])
                avg_confidence_in_bin = np.mean(y_pred_proba[in_bin])
                ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
        
        return {
            'brier_score': float(brier_score),
            'ece': float(ece),
            'calibration_slope': float(np.corrcoef(mean_predicted_value, fraction_positives)[0, 1]) if len(mean_predicted_value) > 1 else 0.0,
            'reliability_data': {
                'fraction_positives': fraction_positives.tolist(),
                'mean_predicted_value': mean_predicted_value.tolist()
            }
        }
    
    def generate_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera relatório completo de diagnóstico"""
        
        if self.model is None:
            return {"error": "Modelo não carregado"}
        
        print("🔍 Iniciando diagnóstico completo...")
        
        # Codificar features categóricas
        df_encoded = self._encode_categorical_features(df)
        
        # Usar features do modelo salvo se disponível
        if self.feature_names:
            feature_columns = self.feature_names
            print(f"🎯 Usando {len(feature_columns)} features do modelo salvo")
        else:
            feature_columns = [col for col in df_encoded.columns if col not in ['team1_win', 'match_id', 'timestamp']]
            print(f"⚠️ Usando todas as features disponíveis: {len(feature_columns)}")
        
        # Verificar se todas as features necessárias estão disponíveis
        missing_features = [col for col in feature_columns if col not in df_encoded.columns]
        if missing_features:
            print(f"❌ Features ausentes: {missing_features}")
            return {"error": f"Features ausentes: {missing_features}"}
        
        X = df_encoded[feature_columns].values
        y = df_encoded['team1_win'].values
        
        # Verificar se há valores não numéricos restantes
        non_numeric_cols = []
        for i, col in enumerate(feature_columns):
            try:
                X[:, i].astype(float)
            except (ValueError, TypeError):
                non_numeric_cols.append(col)
        
        if non_numeric_cols:
            print(f"⚠️ Removendo colunas não numéricas: {non_numeric_cols}")
            numeric_cols = [col for col in feature_columns if col not in non_numeric_cols]
            X = df_encoded[numeric_cols].values
            feature_columns = numeric_cols
        
        # Normalizar se necessário
        if self.scaler:
            try:
                X = self.scaler.transform(X)
                print(f"✅ Dados normalizados usando scaler salvo")
            except ValueError as e:
                print(f"⚠️ Erro no scaler, usando dados brutos: {e}")
        
        # Predições
        y_pred_proba = self.model.predict_proba(X)[:, 1]
        
        # Avaliação principal
        print("📊 Calculando métricas principais...")
        performance = self.evaluate_performance(X, y)
        
        # Análise contextual
        print("🔍 Analisando por contexto...")
        context_analysis = self.analyze_by_context(df, y_pred_proba)
        
        # Cenários problemáticos
        print("⚠️ Identificando cenários problemáticos...")
        worst_scenarios = self.identify_worst_scenarios(df, y_pred_proba, y)
        
        # Análise de calibração
        print("📐 Analisando calibração...")
        calibration = self.calibration_analysis(y, y_pred_proba)
        
        # Relatório final
        report = {
            'timestamp': datetime.now().isoformat(),
            'model_info': {
                'model_type': type(self.model).__name__,
                'features_count': X.shape[1],
                'training_samples': X.shape[0],
                'feature_names': feature_columns
            },
            'performance_metrics': performance,
            'context_analysis': context_analysis,
            'worst_scenarios': worst_scenarios,
            'calibration_analysis': calibration,
            'recommendations': self._generate_recommendations(performance, context_analysis, worst_scenarios)
        }
        
        print("✅ Diagnóstico completo!")
        return report
    
    def _generate_recommendations(self, performance: Dict, context: Dict, worst: Dict) -> List[str]:
        """Gera recomendações baseadas no diagnóstico"""
        
        recommendations = []
        
        # Performance geral
        if performance['auc_roc'] < 0.75:
            recommendations.append("🔴 AUC baixo (<0.75) - considere features adicionais ou modelo mais complexo")
        elif performance['auc_roc'] < 0.85:
            recommendations.append("🟡 AUC moderado - oportunidade de melhoria com feature engineering")
        
        if performance['log_loss'] > 0.6:
            recommendations.append("🔴 Log-loss alto - modelo mal calibrado, considere calibração")
        
        if performance['inference_time_ms'] > 100:
            recommendations.append("⚡ Tempo de inferência alto - otimize para produção")
        
        # Análise contextual
        if 'by_patch' in context:
            patch_aucs = [metrics['auc_roc'] for metrics in context['by_patch'].values()]
            if len(patch_aucs) > 1 and (max(patch_aucs) - min(patch_aucs)) > 0.1:
                recommendations.append("📊 Performance inconsistente entre patches - considere features específicas de meta")
        
        if 'by_duration' in context:
            duration_aucs = [metrics['auc_roc'] for metrics in context['by_duration'].values()]
            if len(duration_aucs) > 1 and (max(duration_aucs) - min(duration_aucs)) > 0.15:
                recommendations.append("⏱️ Performance varia muito por duração - adicione features temporais")
        
        # Cenários problemáticos
        if len(worst.get('worst_predictions', [])) > 0:
            recommendations.append("🎯 Analise cenários de pior performance para feature engineering direcionada")
        
        if not recommendations:
            recommendations.append("✅ Modelo está performando bem - foque em otimizações incrementais")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filepath: str = "evaluation_report.json"):
        """Salva relatório em arquivo"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📄 Relatório salvo em: {filepath}")

# Exemplo de uso
if __name__ == "__main__":
    evaluator = ModelEvaluator()
    
    # Carregar dados de teste
    df = evaluator.load_test_data()
    
    if not df.empty:
        # Gerar relatório completo
        report = evaluator.generate_report(df)
        
        # Salvar relatório
        evaluator.save_report(report, "data/model_evaluation_report.json")
        
        # Exibir resumo
        print("\n" + "="*60)
        print("📊 RESUMO DO DIAGNÓSTICO")
        print("="*60)
        print(f"AUC-ROC: {report['performance_metrics']['auc_roc']:.4f}")
        print(f"Log-Loss: {report['performance_metrics']['log_loss']:.4f}")
        print(f"Acurácia: {report['performance_metrics']['accuracy']:.4f}")
        print(f"Tempo de inferência: {report['performance_metrics']['inference_time_ms']:.2f}ms")
        print("\n🎯 RECOMENDAÇÕES:")
        for rec in report['recommendations']:
            print(f"  • {rec}") 