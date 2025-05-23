#!/usr/bin/env python3
"""
Script para treinar modelo real de predição de vitórias em LoL
Usando os dados realistas gerados
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class LoLPredictionModel:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.model = None
        self.scaler = None
        self.encoders = {}
        self.feature_importance = None
        self.performance_metrics = {}
        
    def load_and_preprocess_data(self):
        """Carrega e preprocessa os dados"""
        
        print("📊 CARREGANDO DADOS...")
        
        # Carregar dados
        self.df = pd.read_csv(self.data_file)
        print(f"   ✅ {len(self.df)} registros carregados")
        
        # Remover linhas com dados faltantes críticos
        initial_size = len(self.df)
        self.df = self.df.dropna(subset=['result', 'kills', 'deaths', 'assists'])
        print(f"   🧹 {initial_size - len(self.df)} linhas removidas por dados faltantes")
        
        # Criar features derivadas
        self.df['kill_participation'] = (self.df['kills'] + self.df['assists']) / self.df['deaths'].clip(lower=1)
        self.df['efficiency'] = self.df['gold'] / self.df['gamelength']
        self.df['combat_score'] = self.df['kills'] * 3 + self.df['assists'] - self.df['deaths'] * 2
        self.df['farm_efficiency'] = self.df['cs'] / self.df['gamelength']
        
        print(f"   🔧 Features derivadas criadas")
        print(f"   📈 Dataset final: {len(self.df)} registros")
        
    def prepare_features(self):
        """Prepara features para o modelo"""
        
        print("\n🔧 PREPARANDO FEATURES...")
        
        # Features categóricas para encoding
        categorical_features = ['position', 'champion', 'league', 'side']
        
        # Features numéricas
        numeric_features = [
            'kills', 'deaths', 'assists', 'kda', 'cs', 'cspm', 'gold', 'gpm',
            'damagetochampions', 'dpm', 'wardsplaced', 'wardskilled',
            'doublekills', 'triplekills', 'quadrakills', 'pentakills',
            'gamelength', 'kill_participation', 'efficiency', 'combat_score', 'farm_efficiency'
        ]
        
        # Features booleanas
        boolean_features = ['firstblood', 'firstdragon', 'firstbaron']
        
        # Preparar dataset
        X = self.df.copy()
        y = self.df['result'].astype(int)
        
        # Encoding de variáveis categóricas
        for feature in categorical_features:
            if feature in X.columns:
                le = LabelEncoder()
                X[feature] = le.fit_transform(X[feature].astype(str))
                self.encoders[feature] = le
                print(f"   🏷️ {feature}: {len(le.classes_)} categorias únicas")
        
        # Converter booleanas para int
        for feature in boolean_features:
            if feature in X.columns:
                X[feature] = X[feature].astype(int)
        
        # Selecionar features finais
        all_features = categorical_features + numeric_features + boolean_features
        available_features = [f for f in all_features if f in X.columns]
        
        X = X[available_features]
        
        print(f"   ✅ {len(available_features)} features selecionadas")
        print(f"   🎯 Target balance: {y.value_counts().to_dict()}")
        
        return X, y, available_features
    
    def train_models(self, X, y):
        """Treina múltiplos modelos e seleciona o melhor"""
        
        print("\n🤖 TREINANDO MODELOS...")
        
        # Split dos dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Normalizar features numéricas
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Modelos para testar
        models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100, 
                max_depth=10, 
                random_state=42, 
                class_weight='balanced'
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=100, 
                max_depth=6, 
                random_state=42
            ),
            'LogisticRegression': LogisticRegression(
                random_state=42, 
                class_weight='balanced',
                max_iter=1000
            )
        }
        
        best_score = 0
        best_model_name = None
        
        # Testar cada modelo
        for name, model in models.items():
            print(f"\n   🔄 Testando {name}...")
            
            # Usar dados normalizados para LogisticRegression
            if name == 'LogisticRegression':
                X_train_model = X_train_scaled
                X_test_model = X_test_scaled
            else:
                X_train_model = X_train
                X_test_model = X_test
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_model, y_train, cv=5, scoring='roc_auc')
            mean_cv_score = cv_scores.mean()
            
            # Treinar modelo
            model.fit(X_train_model, y_train)
            
            # Avaliação
            train_score = model.score(X_train_model, y_train)
            test_score = model.score(X_test_model, y_test)
            
            # Predições para AUC
            y_pred_proba = model.predict_proba(X_test_model)[:, 1]
            auc_score = roc_auc_score(y_test, y_pred_proba)
            
            print(f"      📈 CV Score: {mean_cv_score:.4f} (±{cv_scores.std()*2:.4f})")
            print(f"      🎯 Train Score: {train_score:.4f}")
            print(f"      🎯 Test Score: {test_score:.4f}")
            print(f"      🎯 AUC Score: {auc_score:.4f}")
            
            # Salvar métricas
            self.performance_metrics[name] = {
                'cv_score': mean_cv_score,
                'cv_std': cv_scores.std(),
                'train_score': train_score,
                'test_score': test_score,
                'auc_score': auc_score
            }
            
            # Verificar se é o melhor modelo
            if auc_score > best_score:
                best_score = auc_score
                best_model_name = name
                self.model = model
                
                # Para RandomForest, salvar importância das features
                if hasattr(model, 'feature_importances_'):
                    self.feature_importance = dict(zip(X.columns, model.feature_importances_))
        
        print(f"\n🏆 MELHOR MODELO: {best_model_name} (AUC: {best_score:.4f})")
        
        # Avaliação detalhada do melhor modelo
        if best_model_name == 'LogisticRegression':
            X_test_final = X_test_scaled
        else:
            X_test_final = X_test
            
        y_pred = self.model.predict(X_test_final)
        y_pred_proba = self.model.predict_proba(X_test_final)[:, 1]
        
        print(f"\n📊 RELATÓRIO DETALHADO:")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        # Feature importance (se disponível)
        if self.feature_importance:
            print(f"\n🎯 TOP 10 FEATURES MAIS IMPORTANTES:")
            sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
            for feature, importance in sorted_features[:10]:
                print(f"   {feature}: {importance:.4f}")
        
        return X_test, y_test, best_model_name
    
    def save_model(self, model_name: str):
        """Salva o modelo treinado"""
        
        print(f"\n💾 SALVANDO MODELO...")
        
        # Criar diretório
        model_dir = "models/trained"
        os.makedirs(model_dir, exist_ok=True)
        
        # Timestamp para o arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salvar modelo
        model_path = f"{model_dir}/lol_predictor_{model_name.lower()}_{timestamp}.joblib"
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'encoders': self.encoders,
            'feature_importance': self.feature_importance,
            'performance_metrics': self.performance_metrics,
            'model_type': model_name
        }, model_path)
        
        print(f"   ✅ Modelo salvo em: {model_path}")
        
        # Salvar relatório
        report_path = f"{model_dir}/training_report_{timestamp}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"RELATÓRIO DE TREINAMENTO - {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Arquivo de dados: {self.data_file}\n")
            f.write(f"Registros utilizados: {len(self.df)}\n")
            f.write(f"Melhor modelo: {model_name}\n\n")
            
            f.write("PERFORMANCE DOS MODELOS:\n")
            for name, metrics in self.performance_metrics.items():
                f.write(f"\n{name}:\n")
                for metric, value in metrics.items():
                    f.write(f"  {metric}: {value:.4f}\n")
            
            if self.feature_importance:
                f.write(f"\nFEATURE IMPORTANCE (TOP 15):\n")
                sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
                for feature, importance in sorted_features[:15]:
                    f.write(f"  {feature}: {importance:.4f}\n")
        
        print(f"   📋 Relatório salvo em: {report_path}")
        
        return model_path
    
    def run_training_pipeline(self):
        """Executa o pipeline completo de treinamento"""
        
        print("🚀 INICIANDO TREINAMENTO DO MODELO LOL PREDICTOR")
        print("=" * 60)
        
        # 1. Carregar e preprocessar dados
        self.load_and_preprocess_data()
        
        # 2. Preparar features
        X, y, feature_names = self.prepare_features()
        
        # 3. Treinar modelos
        X_test, y_test, best_model_name = self.train_models(X, y)
        
        # 4. Salvar modelo
        model_path = self.save_model(best_model_name)
        
        print(f"\n✅ TREINAMENTO CONCLUÍDO COM SUCESSO!")
        print(f"🎯 Melhor modelo: {best_model_name}")
        print(f"📊 AUC Score: {self.performance_metrics[best_model_name]['auc_score']:.4f}")
        print(f"💾 Modelo salvo em: {model_path}")
        
        return model_path

def main():
    """Função principal"""
    
    # Usar o arquivo mais recente se não especificado
    data_file = "data/processed/realistic_lol_data_20250522_224457.csv"
    
    if not os.path.exists(data_file):
        print(f"❌ Arquivo não encontrado: {data_file}")
        print("💡 Execute primeiro: python create_realistic_data.py")
        return
    
    # Treinar modelo
    trainer = LoLPredictionModel(data_file)
    model_path = trainer.run_training_pipeline()
    
    print(f"\n🎮 PRÓXIMOS PASSOS:")
    print(f"   1. 🧪 Teste o modelo: python test_model.py {model_path}")
    print(f"   2. 🔄 Integre com o bot: python integrate_model.py")
    print(f"   3. 📊 Execute Phase 2: python phase_2_data_enrichment.py")

if __name__ == "__main__":
    main() 