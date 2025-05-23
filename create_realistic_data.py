#!/usr/bin/env python3
"""
Script para criar dados realistas de League of Legends
baseado nos padrões encontrados nos repositórios pesquisados
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

class RealisticLoLDataGenerator:
    def __init__(self):
        self.champions = [
            'Aatrox', 'Ahri', 'Akali', 'Alistar', 'Amumu', 'Anivia', 'Annie', 'Aphelios',
            'Ashe', 'Azir', 'Bard', 'Blitzcrank', 'Brand', 'Braum', 'Caitlyn', 'Camille',
            'Cassiopeia', 'Cho\'Gath', 'Corki', 'Darius', 'Diana', 'Dr. Mundo', 'Draven',
            'Ekko', 'Elise', 'Evelynn', 'Ezreal', 'Fiddlesticks', 'Fiora', 'Fizz',
            'Galio', 'Gangplank', 'Garen', 'Gnar', 'Gragas', 'Graves', 'Gwen', 'Hecarim',
            'Heimerdinger', 'Illaoi', 'Irelia', 'Ivern', 'Janna', 'Jarvan IV', 'Jax',
            'Jayce', 'Jhin', 'Jinx', 'Kai\'Sa', 'Kalista', 'Karma', 'Karthus', 'Kassadin',
            'Katarina', 'Kayle', 'Kayn', 'Kennen', 'Kha\'Zix', 'Kindred', 'Kled', 'Kog\'Maw',
            'LeBlanc', 'Lee Sin', 'Leona', 'Lillia', 'Lissandra', 'Lucian', 'Lulu', 'Lux',
            'Malphite', 'Malzahar', 'Maokai', 'Master Yi', 'Miss Fortune', 'Mordekaiser',
            'Morgana', 'Nami', 'Nasus', 'Nautilus', 'Nidalee', 'Nocturne', 'Nunu', 'Olaf',
            'Orianna', 'Ornn', 'Pantheon', 'Poppy', 'Pyke', 'Qiyana', 'Quinn', 'Rakan',
            'Rammus', 'Rek\'Sai', 'Rell', 'Renekton', 'Rengar', 'Riven', 'Rumble', 'Ryze',
            'Samira', 'Sejuani', 'Senna', 'Seraphine', 'Sett', 'Shaco', 'Shen', 'Shyvana',
            'Singed', 'Sion', 'Sivir', 'Skarner', 'Sona', 'Soraka', 'Swain', 'Sylas',
            'Syndra', 'Tahm Kench', 'Taliyah', 'Talon', 'Taric', 'Teemo', 'Thresh', 'Tristana',
            'Trundle', 'Tryndamere', 'Twisted Fate', 'Twitch', 'Udyr', 'Urgot', 'Varus',
            'Vayne', 'Veigar', 'Vel\'Koz', 'Vi', 'Viego', 'Viktor', 'Vladimir', 'Volibear',
            'Warwick', 'Wukong', 'Xayah', 'Xerath', 'Xin Zhao', 'Yasuo', 'Yone', 'Yorick',
            'Yuumi', 'Zac', 'Zed', 'Ziggs', 'Zilean', 'Zoe', 'Zyra'
        ]
        
        self.teams = [
            'T1', 'Gen.G', 'DRX', 'KT Rolster', 'Hanwha Life', 'DWG KIA', 'Liiv SANDBOX',
            'Fredit BRION', 'Nongshim RedForce', 'Kwangdong Freecs',  # LCK
            'JD Gaming', 'Top Esports', 'Oh My God', 'FunPlus Phoenix', 'EDward Gaming',
            'Royal Never Give Up', 'Weibo Gaming', 'LNG Esports', 'Team WE', 'Invictus Gaming',  # LPL
            'G2 Esports', 'Fnatic', 'Rogue', 'MAD Lions', 'Misfits Gaming', 'Team Vitality',
            'Excel Esports', 'Astralis', 'SK Gaming', 'Team BDS',  # LEC
            'Cloud9', 'Team Liquid', 'Evil Geniuses', '100 Thieves', 'FlyQuest', 'TSM',
            'Immortals', 'CLG', 'Golden Guardians', 'Dignitas'  # LCS
        ]
        
        self.leagues = ['LCK', 'LPL', 'LEC', 'LCS', 'LCK CL', 'LPL Academy', 'LEC Regional', 'LCS Academy']
        self.positions = ['top', 'jng', 'mid', 'bot', 'sup']
        
    def generate_game_data(self, num_games: int = 2000) -> pd.DataFrame:
        """Gera dados realistas de partidas"""
        
        print(f"🎮 Gerando {num_games} partidas realistas...")
        
        games = []
        game_id = 1
        
        for _ in range(num_games):
            # Escolher times
            team1, team2 = random.sample(self.teams, 2)
            league = random.choice(self.leagues)
            
            # Data aleatória nos últimos 2 anos
            start_date = datetime.now() - timedelta(days=730)
            end_date = datetime.now()
            random_date = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )
            
            # Duração do jogo (15-45 minutos, média ~25)
            game_length = np.random.normal(25, 5)
            game_length = max(15, min(45, game_length))
            
            # Resultado (um time vence)
            team1_wins = random.choice([True, False])
            
            # Gerar dados para cada posição de cada time
            for team_idx, (team, wins) in enumerate([(team1, team1_wins), (team2, not team1_wins)]):
                for position in self.positions:
                    # Estatísticas baseadas na posição e resultado
                    stats = self._generate_position_stats(position, wins, game_length)
                    
                    game = {
                        'gameid': f"GAME_{game_id:05d}",
                        'league': league,
                        'teamname': team,
                        'position': position,
                        'champion': random.choice(self.champions),
                        'side': 'Blue' if team_idx == 0 else 'Red',
                        'result': wins,
                        'gamelength': round(game_length, 2),
                        'date': random_date.strftime('%Y-%m-%d'),
                        'patch': f"13.{random.randint(1, 24)}",
                        **stats
                    }
                    
                    games.append(game)
            
            game_id += 1
            
            if game_id % 500 == 0:
                print(f"   📊 {game_id} partidas geradas...")
        
        print(f"✅ Geração concluída: {len(games)} registros criados")
        return pd.DataFrame(games)
    
    def _generate_position_stats(self, position: str, wins: bool, game_length: float) -> dict:
        """Gera estatísticas realistas baseadas na posição"""
        
        # Multiplicadores baseados em vitória/derrota
        win_mult = 1.3 if wins else 0.8
        
        # Bases por posição
        base_stats = {
            'top': {'kills': 3, 'deaths': 3, 'assists': 4, 'cs': 8, 'gold': 550, 'damage': 900},
            'jng': {'kills': 4, 'deaths': 3, 'assists': 8, 'cs': 5, 'gold': 450, 'damage': 800},
            'mid': {'kills': 5, 'deaths': 3, 'assists': 6, 'cs': 8.5, 'gold': 580, 'damage': 1100},
            'bot': {'kills': 4, 'deaths': 3, 'assists': 5, 'cs': 9, 'gold': 600, 'damage': 1200},
            'sup': {'kills': 1, 'deaths': 4, 'assists': 12, 'cs': 1.5, 'gold': 300, 'damage': 400}
        }
        
        base = base_stats[position]
        
        # Gerar estatísticas com variação realista
        kills = max(0, int(np.random.poisson(base['kills'] * win_mult)))
        deaths = max(1, int(np.random.poisson(base['deaths'] / win_mult)))
        assists = max(0, int(np.random.poisson(base['assists'] * win_mult)))
        
        # CS e Gold por minuto
        cspm = base['cs'] * np.random.normal(1, 0.2) * win_mult
        gpm = base['gold'] * np.random.normal(1, 0.15) * win_mult
        dpm = base['damage'] * np.random.normal(1, 0.25) * win_mult
        
        # Estatísticas totais
        total_cs = max(0, int(cspm * game_length))
        total_gold = max(500, int(gpm * game_length))
        total_damage = max(100, int(dpm * game_length))
        
        # Objetivos (apenas para algumas posições)
        firstblood = random.random() < 0.1 if position in ['jng', 'mid'] else False
        firstdragon = random.random() < 0.5 if position == 'jng' else False
        firstbaron = random.random() < 0.5 if position == 'jng' else False
        
        # KDA
        kda = (kills + assists) / max(deaths, 1)
        
        # Wards (supports colocam mais)
        ward_mult = 3 if position == 'sup' else 1
        wards_placed = int(np.random.poisson(2 * ward_mult) * game_length / 10)
        wards_killed = int(np.random.poisson(1 * ward_mult) * game_length / 10)
        
        return {
            'kills': kills,
            'deaths': deaths,
            'assists': assists,
            'kda': round(kda, 2),
            'cs': total_cs,
            'cspm': round(cspm, 1),
            'gold': total_gold,
            'gpm': round(gpm, 1),
            'damagetochampions': total_damage,
            'dpm': round(dpm, 1),
            'wardsplaced': wards_placed,
            'wardskilled': wards_killed,
            'firstblood': firstblood,
            'firstdragon': firstdragon,
            'firstbaron': firstbaron,
            'doublekills': int(np.random.poisson(0.3)) if wins else int(np.random.poisson(0.1)),
            'triplekills': int(np.random.poisson(0.05)) if wins else int(np.random.poisson(0.01)),
            'quadrakills': int(np.random.poisson(0.005)) if wins else 0,
            'pentakills': 1 if random.random() < 0.001 and wins else 0,
        }
    
    def save_data(self, df: pd.DataFrame, filename: str = None):
        """Salva os dados gerados"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/processed/realistic_lol_data_{timestamp}.csv"
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Salvar
        df.to_csv(filename, index=False)
        print(f"💾 Dados salvos em: {filename}")
        
        # Estatísticas resumidas
        print(f"\n📊 RESUMO DOS DADOS:")
        print(f"   🎮 Total de partidas: {df['gameid'].nunique()}")
        print(f"   👥 Total de registros: {len(df)}")
        print(f"   🏆 Times únicos: {df['teamname'].nunique()}")
        print(f"   🎯 Champions únicos: {df['champion'].nunique()}")
        print(f"   🏟️ Ligas: {', '.join(df['league'].unique())}")
        print(f"   📅 Período: {df['date'].min()} até {df['date'].max()}")
        
        return filename

def main():
    """Função principal"""
    
    print("🎲 GERADOR DE DADOS REALISTAS DE LOL")
    print("=" * 50)
    print("📝 Criando dataset com padrões realistas baseados em pesquisa")
    print("🔬 Estatísticas por posição, vitória/derrota, duração do jogo")
    print()
    
    generator = RealisticLoLDataGenerator()
    
    # Gerar dados
    df = generator.generate_game_data(num_games=3000)  # 3000 partidas = 30k registros
    
    # Salvar
    filename = generator.save_data(df)
    
    print("\n✅ GERAÇÃO CONCLUÍDA!")
    print("🚀 Agora você pode usar estes dados para treinar o modelo")
    print(f"📋 Execute: python train_model.py {filename}")

if __name__ == "__main__":
    main() 