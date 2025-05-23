#!/usr/bin/env python3
"""
CONVERSÃO DE DADOS REAIS
Converte dados JSON reais para CSV compatível com o pipeline melhorado
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

def convert_real_data():
    """Converte dados reais do projeto para formato CSV"""
    
    print("🔄 Convertendo dados reais para o pipeline melhorado...")
    
    # Carregar dados JSON reais
    with open("data/processed_match_data.json", 'r') as f:
        data = json.load(f)
    
    print(f"✅ Carregados {len(data)} registros reais")
    
    # Converter para DataFrame
    df = pd.DataFrame(data)
    
    # Limpar e padronizar
    # Remover colunas que não são úteis para ML
    columns_to_remove = ['match_id', 'timestamp']
    df = df.drop(columns=[col for col in columns_to_remove if col in df.columns])
    
    # Garantir que team1_win é numérico
    df['team1_win'] = df['team1_win'].astype(int)
    
    # Converter categóricas para encoding
    if 'tournament' in df.columns:
        tournament_encoding = {
            'LCK': 1, 'LPL': 2, 'LEC': 3, 'LCS': 4, 
            'MSI': 5, 'Worlds': 6, 'Outros': 0
        }
        df['tournament_encoded'] = df['tournament'].map(tournament_encoding).fillna(0)
    
    if 'team1_side' in df.columns:
        df['team1_side_blue'] = (df['team1_side'] == 'blue').astype(int)
    
    if 'patch' in df.columns:
        # Extrair número do patch
        df['patch_major'] = df['patch'].str.extract(r'(\d+)\.').astype(float).fillna(14)
        df['patch_minor'] = df['patch'].str.extract(r'\.(\d+)').astype(float).fillna(1)
    
    # Remover colunas categóricas originais
    categorical_cols = ['tournament', 'team1_side', 'patch']
    df = df.drop(columns=[col for col in categorical_cols if col in df.columns])
    
    # Verificar e tratar valores faltantes
    df = df.fillna(0)
    
    # Garantir que todas as features são numéricas
    df = df.select_dtypes(include=[np.number])
    
    print(f"📊 Dataset final: {df.shape[0]} amostras, {df.shape[1]} features")
    print(f"🎯 Target distribution: {df['team1_win'].mean():.2%} vitórias team1")
    
    # Salvar como CSV
    df.to_csv("data/real_match_data.csv", index=False)
    
    print(f"💾 Dados salvos em: data/real_match_data.csv")
    
    # Mostrar informações do dataset
    print(f"\n📈 INFORMAÇÕES DO DATASET REAL:")
    print(f"   Amostras: {df.shape[0]}")
    print(f"   Features: {df.shape[1]}")
    print(f"   Target balance: {df['team1_win'].value_counts().to_dict()}")
    
    # Top features por correlação com target
    if df.shape[1] > 1:
        correlations = df.corr()['team1_win'].abs().sort_values(ascending=False)[1:11]
        print(f"\n🏆 Top 10 features mais correlacionadas:")
        for i, (feature, corr) in enumerate(correlations.items(), 1):
            print(f"   {i}. {feature}: {corr:.4f}")
    
    return df

if __name__ == "__main__":
    df = convert_real_data()
    print("\n✅ CONVERSÃO CONCLUÍDA! Dados reais prontos para o pipeline.") 