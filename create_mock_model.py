#!/usr/bin/env python3
"""
Cria um modelo mock para demonstrar o sistema de diagnóstico da Fase 1
"""

import json
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

def create_mock_model():
    """Cria modelo mock usando dados processados"""
    
    print("🔧 Criando modelo mock para demonstração...")
    
    # Carregar dados processados
    with open('data/processed_match_data.json', 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # Selecionar features numéricas principais
    numeric_features = [
        'team1_kills', 'team1_gold', 'team1_towers', 'team1_dragons', 'team1_barons',
        'team2_kills', 'team2_gold', 'team2_towers', 'team2_dragons', 'team2_barons',
        'kill_diff', 'gold_diff', 'tower_diff', 'dragon_diff', 'baron_diff',
        'gold_ratio', 'kill_ratio', 'objective_score_diff',
        'games_count', 'game_duration', 'total_kills', 'total_gold',
        'first_blood', 'first_tower', 'first_dragon', 'elder_dragons', 'herald_kills',
        'avg_kills_per_min', 'gold_per_min_diff', 'vision_score_diff', 'cs_diff_15', 'gold_diff_15',
        'team1_ad_count', 'team1_ap_count', 'team1_tank_count',
        'team2_ad_count', 'team2_ap_count', 'team2_tank_count',
        'early_game_lead', 'mid_game_lead', 'late_game_scaling'
    ]
    
    # Codificar features categóricas
    categorical_features = ['tournament', 'team1_side', 'patch']
    label_encoders = {}
    
    df_model = df.copy()
    for feature in categorical_features:
        if feature in df_model.columns:
            le = LabelEncoder()
            df_model[feature] = le.fit_transform(df_model[feature].astype(str))
            label_encoders[feature] = le
            numeric_features.append(feature)
    
    # Preparar dados
    X = df_model[numeric_features].values
    y = df_model['team1_win'].values
    
    print(f"📊 Dados preparados: {X.shape[0]} amostras, {X.shape[1]} features")
    
    # Split treino/teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Treinar modelo
    print("🤖 Treinando RandomForestClassifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Avaliar
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"✅ Modelo treinado:")
    print(f"   📊 Acurácia: {accuracy:.4f}")
    print(f"   📊 AUC-ROC: {auc:.4f}")
    
    # Salvar modelo e scaler
    with open('data/model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    with open('data/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    # Salvar feature names para referência
    model_info = {
        'feature_names': numeric_features,
        'n_features': len(numeric_features),
        'categorical_encoders': {name: list(le.classes_) for name, le in label_encoders.items()},
        'model_type': 'RandomForestClassifier',
        'training_accuracy': float(accuracy),
        'training_auc': float(auc),
        'training_samples': len(X_train)
    }
    
    with open('data/model_info.json', 'w') as f:
        json.dump(model_info, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Modelo salvo em: data/model.pkl")
    print(f"💾 Scaler salvo em: data/scaler.pkl")
    print(f"💾 Info do modelo salvo em: data/model_info.json")
    
    return model, scaler, numeric_features

if __name__ == "__main__":
    create_mock_model()
    print("\n✅ Modelo mock criado com sucesso!")
    print("🚀 Agora você pode executar: python phase_1_diagnostic.py") 