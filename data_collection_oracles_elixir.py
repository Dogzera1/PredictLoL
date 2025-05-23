#!/usr/bin/env python3
"""
Sistema de Coleta de Dados Reais do Oracle's Elixir
Coleta dados de partidas profissionais de League of Legends (2023-2025)
"""

import requests
import pandas as pd
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pickle

class OraclesElixirCollector:
    """Coletor de dados do Oracle's Elixir"""
    
    def __init__(self):
        self.base_url = "https://oracleselixir.com/tools/downloads"
        self.data_dir = "data/raw"
        self.processed_dir = "data/processed"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def download_match_data(self, year: int = 2024) -> str:
        """Baixa dados de partidas de um ano específico"""
        
        print(f"📥 Baixando dados de {year}...")
        
        # URLs conhecidas do Oracle's Elixir (formato padrão)
        urls = {
            2023: f"https://oracleselixir.com/tools/downloads/{year}_LoL_esports_match_data_from_OraclesElixir.csv",
            2024: f"https://oracleselixir.com/tools/downloads/{year}_LoL_esports_match_data_from_OraclesElixir.csv",
            2025: f"https://oracleselixir.com/tools/downloads/{year}_LoL_esports_match_data_from_OraclesElixir.csv"
        }
        
        if year not in urls:
            print(f"❌ Ano {year} não suportado")
            return None
            
        url = urls[year]
        filename = f"{self.data_dir}/matches_{year}.csv"
        
        try:
            print(f"   🌐 Fazendo download de: {url}")
            response = requests.get(url, timeout=300)  # 5 minutos timeout
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"   ✅ Dados de {year} salvos em: {filename}")
                
                # Verificar se o arquivo é válido
                try:
                    df = pd.read_csv(filename)
                    print(f"   📊 {len(df)} registros carregados")
                    return filename
                except Exception as e:
                    print(f"   ❌ Erro ao validar arquivo: {e}")
                    return None
            else:
                print(f"   ❌ Erro HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro no download: {e}")
            return None
    
    def process_match_data(self, csv_file: str) -> pd.DataFrame:
        """Processa dados brutos de partidas"""
        
        print(f"🔧 Processando dados de: {csv_file}")
        
        try:
            # Carregar dados
            df = pd.read_csv(csv_file)
            print(f"   📊 Dados brutos: {len(df)} registros")
            
            # Filtrar apenas partidas completas de ligas principais
            major_leagues = [
                'LCK', 'LPL', 'LEC', 'LCS', 'MSI', 'Worlds', 
                'CBLOL', 'LJL', 'PCS', 'VCS', 'LLA'
            ]
            
            # Filtros básicos
            df_filtered = df[
                (df['league'].isin(major_leagues)) &
                (df['position'] == 'team') &  # Apenas dados de time
                (df['result'] == 1)  # Apenas vencedores (para cada partida)
            ].copy()
            
            print(f"   📊 Após filtros: {len(df_filtered)} partidas")
            
            # Criar features básicas
            processed_matches = []
            
            # Agrupar por gameid para ter dados de ambos os times
            for game_id in df_filtered['gameid'].unique():
                game_data = df[df['gameid'] == game_id]
                
                if len(game_data) >= 2:  # Precisa ter dados de ambos os times
                    match_data = self._extract_match_features(game_data)
                    if match_data:
                        processed_matches.append(match_data)
            
            processed_df = pd.DataFrame(processed_matches)
            print(f"   ✅ Processamento concluído: {len(processed_df)} partidas válidas")
            
            return processed_df
            
        except Exception as e:
            print(f"   ❌ Erro no processamento: {e}")
            return pd.DataFrame()
    
    def _extract_match_features(self, game_data: pd.DataFrame) -> Dict[str, Any]:
        """Extrai features de uma partida específica"""
        
        try:
            # Separar dados por time
            team_data = game_data[game_data['position'] == 'team']
            
            if len(team_data) != 2:
                return None
            
            # Ordenar por resultado (vencedor primeiro)
            team_data = team_data.sort_values('result', ascending=False)
            winner = team_data.iloc[0]
            loser = team_data.iloc[1]
            
            # Features básicas da partida
            match_features = {
                # Informações da partida
                'match_id': str(winner['gameid']),
                'date': winner['date'],
                'league': winner['league'],
                'patch': winner['patch'],
                'game_duration': winner.get('gamelength', 0),
                
                # Time vencedor (team1)
                'team1_name': winner['teamname'],
                'team1_side': winner.get('side', 'unknown'),
                'team1_kills': winner.get('kills', 0),
                'team1_deaths': winner.get('deaths', 0),
                'team1_assists': winner.get('assists', 0),
                'team1_gold': winner.get('earnedgold', 0),
                'team1_towers': winner.get('towers', 0),
                'team1_dragons': winner.get('dragons', 0),
                'team1_barons': winner.get('barons', 0),
                'team1_heralds': winner.get('heralds', 0),
                
                # Time perdedor (team2) 
                'team2_name': loser['teamname'],
                'team2_side': loser.get('side', 'unknown'),
                'team2_kills': loser.get('kills', 0),
                'team2_deaths': loser.get('deaths', 0),
                'team2_assists': loser.get('assists', 0),
                'team2_gold': loser.get('earnedgold', 0),
                'team2_towers': loser.get('towers', 0),
                'team2_dragons': loser.get('dragons', 0),
                'team2_barons': loser.get('barons', 0),
                'team2_heralds': loser.get('heralds', 0),
                
                # Label (team1 sempre venceu)
                'team1_win': 1
            }
            
            # Features derivadas
            match_features.update({
                'kill_diff': match_features['team1_kills'] - match_features['team2_kills'],
                'gold_diff': match_features['team1_gold'] - match_features['team2_gold'],
                'tower_diff': match_features['team1_towers'] - match_features['team2_towers'],
                'dragon_diff': match_features['team1_dragons'] - match_features['team2_dragons'],
                'baron_diff': match_features['team1_barons'] - match_features['team2_barons'],
                
                'total_kills': match_features['team1_kills'] + match_features['team2_kills'],
                'total_gold': match_features['team1_gold'] + match_features['team2_gold'],
                
                'gold_ratio': match_features['team1_gold'] / max(match_features['team2_gold'], 1),
                'kill_ratio': match_features['team1_kills'] / max(match_features['team2_kills'], 1),
            })
            
            return match_features
            
        except Exception as e:
            print(f"   ⚠️ Erro ao extrair features: {e}")
            return None
    
    def collect_multi_year_data(self, years: List[int] = [2023, 2024, 2025]) -> pd.DataFrame:
        """Coleta dados de múltiplos anos"""
        
        print("🚀 INICIANDO COLETA DE DADOS ORACLE'S ELIXIR")
        print("=" * 60)
        
        all_matches = []
        
        for year in years:
            print(f"\n📅 PROCESSANDO ANO {year}")
            print("-" * 40)
            
            # Download dos dados
            csv_file = self.download_match_data(year)
            
            if csv_file:
                # Processar dados
                processed_data = self.process_match_data(csv_file)
                
                if not processed_data.empty:
                    all_matches.append(processed_data)
                    print(f"   ✅ {len(processed_data)} partidas adicionadas")
                else:
                    print(f"   ❌ Nenhuma partida válida encontrada")
            else:
                print(f"   ❌ Falha no download para {year}")
        
        # Combinar todos os dados
        if all_matches:
            combined_df = pd.concat(all_matches, ignore_index=True)
            print(f"\n🎯 TOTAL: {len(combined_df)} partidas coletadas")
            
            # Salvar dados processados
            output_file = f"{self.processed_dir}/oracle_elixir_matches_2023_2025.csv"
            combined_df.to_csv(output_file, index=False)
            print(f"💾 Dados salvos em: {output_file}")
            
            # Salvar estatísticas
            self._save_collection_stats(combined_df)
            
            return combined_df
        else:
            print("❌ Nenhum dado foi coletado com sucesso")
            return pd.DataFrame()
    
    def _save_collection_stats(self, df: pd.DataFrame):
        """Salva estatísticas da coleta"""
        
        stats = {
            'collection_date': datetime.now().isoformat(),
            'total_matches': len(df),
            'unique_teams': df['team1_name'].nunique() + df['team2_name'].nunique(),
            'leagues': df['league'].unique().tolist(),
            'patches': df['patch'].unique().tolist(),
            'date_range': {
                'start': df['date'].min(),
                'end': df['date'].max()
            },
            'avg_game_duration': float(df['game_duration'].mean()),
            'features_count': len(df.columns)
        }
        
        stats_file = f"{self.processed_dir}/collection_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 ESTATÍSTICAS DA COLETA:")
        print(f"   • Partidas: {stats['total_matches']:,}")
        print(f"   • Ligas: {len(stats['leagues'])}")
        print(f"   • Patches: {len(stats['patches'])}")
        print(f"   • Período: {stats['date_range']['start']} a {stats['date_range']['end']}")
        print(f"   • Duração média: {stats['avg_game_duration']:.1f} min")

def main():
    """Função principal para coleta de dados"""
    
    print("🎮 COLETOR DE DADOS ORACLE'S ELIXIR")
    print("=" * 50)
    print("📝 Coletando dados reais de partidas profissionais de LoL")
    print("📅 Período: 2023-2025")
    print()
    
    collector = OraclesElixirCollector()
    
    # Coletar dados dos últimos anos
    df = collector.collect_multi_year_data([2023, 2024])  # 2025 pode não estar disponível ainda
    
    if not df.empty:
        print("\n✅ COLETA CONCLUÍDA COM SUCESSO!")
        print("🚀 Agora você pode treinar o modelo com dados reais")
        print("📋 Execute: python train_real_model.py")
    else:
        print("\n❌ FALHA NA COLETA DE DADOS")
        print("💡 Verifique sua conexão e tente novamente")

if __name__ == "__main__":
    main() 