"""
Serviço de treinamento do modelo preditivo para LoL.

Coleta dados históricos de partidas e treina o modelo de machine learning
para previsão de resultados de partidas.
"""

import logging
import sys
import os
import requests
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RIOT_API_KEY, RIOT_API_BASE_URL

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    Classe responsável por treinar o modelo preditivo para apostas em LoL.
    
    Implementa funções para coletar dados históricos de partidas,
    processar esses dados e treinar um modelo de machine learning
    para prever resultados de partidas futuras.
    """
    
    def __init__(self):
        """Inicializa o treinador de modelo"""
        self.model = None
        self.scaler = StandardScaler()
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        
        # Criar diretório de dados se não existir
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            
        self.model_path = os.path.join(self.data_path, 'prediction_model.pkl')
        self.scaler_path = os.path.join(self.data_path, 'scaler.pkl')
        self.teams_data_path = os.path.join(self.data_path, 'teams_data.json')
        
        logger.info("Treinador de modelo inicializado")
    
    def _make_request(self, endpoint, params=None):
        """
        Faz requisição à API Lolesports
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            
        Returns:
            Dados da resposta ou None em caso de erro
        """
        headers = {
            "x-api-key": RIOT_API_KEY,
            "Content-Type": "application/json"
        }
        
        url = f"{RIOT_API_BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao fazer requisição para {endpoint}: {str(e)}")
            return None
    
    def collect_historical_data(self):
        """
        Coleta dados históricos de partidas de 2023, 2024 e 2025
        
        Returns:
            Boolean indicando sucesso ou falha
        """
        logger.info("Iniciando coleta de dados históricos de 2023-2025...")
        
        try:
            # Dados para armazenar
            historical_matches = []
            teams_data = {}
            
            # Coletar dados de cada ano
            for year in [2023, 2024, 2025]:
                logger.info(f"Coletando dados do ano {year}...")
                
                # Definir período de busca (ano completo)
                start_date = f"{year}-01-01T00:00:00Z"
                end_date = f"{year}-12-31T23:59:59Z"
                
                # Se estivermos no ano atual, ajustar a data final para hoje
                if year == datetime.now().year:
                    end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # Buscar torneios do período
                tournaments = self._get_tournaments(start_date, end_date)
                
                if not tournaments:
                    logger.warning(f"Nenhum torneio encontrado para o ano {year}")
                    continue
                
                # Para cada torneio, coletar partidas
                for tournament in tournaments:
                    tournament_id = tournament.get('id')
                    tournament_name = tournament.get('name', 'Torneio desconhecido')
                    
                    logger.info(f"Coletando partidas do torneio: {tournament_name}")
                    
                    # Buscar partidas do torneio
                    matches = self._get_tournament_matches(tournament_id)
                    
                    if not matches:
                        logger.warning(f"Nenhuma partida encontrada para o torneio {tournament_name}")
                        continue
                    
                    # Filtrar apenas partidas completas
                    completed_matches = [m for m in matches if m.get('state') == 'completed']
                    logger.info(f"Encontradas {len(completed_matches)} partidas completas em {tournament_name}")
                    
                    # Processar cada partida
                    for match in completed_matches:
                        match_data = self._process_match_data(match)
                        if match_data:
                            historical_matches.append(match_data)
                            
                            # Atualizar dados dos times
                            self._update_teams_data(teams_data, match_data)
            
            # Salvar dados coletados
            logger.info(f"Total de partidas coletadas: {len(historical_matches)}")
            
            if historical_matches:
                # Salvar dados de partidas
                matches_path = os.path.join(self.data_path, 'historical_matches.json')
                with open(matches_path, 'w') as f:
                    json.dump(historical_matches, f)
                
                # Salvar dados de times
                with open(self.teams_data_path, 'w') as f:
                    json.dump(teams_data, f)
                
                logger.info(f"Dados históricos salvos em {matches_path}")
                return True
            else:
                logger.error("Nenhuma partida histórica foi coletada")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao coletar dados históricos: {str(e)}")
            return False
    
    def _get_tournaments(self, start_date, end_date):
        """
        Busca torneios dentro de um período
        
        Args:
            start_date: Data inicial (formato ISO)
            end_date: Data final (formato ISO)
            
        Returns:
            Lista de torneios ou None em caso de erro
        """
        try:
            # Buscar por torneios no período
            # Como a API não tem um endpoint direto para isso, vamos simular isso
            # buscando torneios ativos dentro do período
            
            # Na API real, seria algo como:
            # result = self._make_request("getTournaments", {
            #     "startDate": start_date,
            #     "endDate": end_date
            # })
            
            # Para fins de simulação (dados mockados):
            leagues = ["LEC", "LCS", "LCK", "LPL", "Worlds", "MSI"]
            tournaments = []
            
            for i, league in enumerate(leagues):
                tournament_id = f"tournament_{i}_{start_date[:4]}"  # Usar o ano como parte do ID
                tournaments.append({
                    "id": tournament_id,
                    "name": f"{league} {start_date[:4]}",
                    "league": league,
                    "startDate": start_date,
                    "endDate": end_date
                })
            
            return tournaments
            
        except Exception as e:
            logger.error(f"Erro ao buscar torneios: {str(e)}")
            return None
    
    def _get_tournament_matches(self, tournament_id):
        """
        Busca partidas de um torneio específico
        
        Args:
            tournament_id: ID do torneio
            
        Returns:
            Lista de partidas ou None em caso de erro
        """
        try:
            # Na API real, seria algo como:
            # result = self._make_request("getTournamentMatches", {
            #     "tournamentId": tournament_id
            # })
            
            # Para fins de simulação (dados mockados):
            # Vamos gerar entre 10-30 partidas mockadas para cada torneio
            num_matches = np.random.randint(10, 30)
            matches = []
            
            # Alguns times comuns
            teams = [
                {"id": "t1", "name": "T1", "code": "T1"},
                {"id": "geng", "name": "GenG", "code": "GEN"},
                {"id": "drx", "name": "DRX", "code": "DRX"},
                {"id": "jdg", "name": "JD Gaming", "code": "JDG"},
                {"id": "blg", "name": "Bilibili Gaming", "code": "BLG"},
                {"id": "g2", "name": "G2 Esports", "code": "G2"},
                {"id": "fnc", "name": "Fnatic", "code": "FNC"},
                {"id": "c9", "name": "Cloud9", "code": "C9"},
                {"id": "tl", "name": "Team Liquid", "code": "TL"},
                {"id": "mad", "name": "MAD Lions", "code": "MAD"}
            ]
            
            year = int(tournament_id.split('_')[-1])  # Extrair ano do ID do torneio
            
            for i in range(num_matches):
                # Escolher dois times aleatórios
                team_indices = np.random.choice(len(teams), 2, replace=False)
                team_a = teams[team_indices[0]]
                team_b = teams[team_indices[1]]
                
                # Gerar resultado aleatório
                team_a_wins = np.random.randint(0, 3)
                team_b_wins = np.random.randint(0, 3)
                
                # Garantir que sempre há um vencedor claro
                while team_a_wins == team_b_wins:
                    team_a_wins = np.random.randint(0, 3)
                    team_b_wins = np.random.randint(0, 3)
                
                # Gerar data aleatória dentro do ano
                match_date = datetime(year, np.random.randint(1, 13), np.random.randint(1, 28))
                match_date_str = match_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                match = {
                    "id": f"match_{tournament_id}_{i}",
                    "state": "completed",
                    "startTime": match_date_str,
                    "tournament": {"id": tournament_id},
                    "match": {
                        "teams": [
                            {
                                "id": team_a["id"],
                                "name": team_a["name"],
                                "code": team_a["code"],
                                "result": {"gameWins": team_a_wins}
                            },
                            {
                                "id": team_b["id"],
                                "name": team_b["name"],
                                "code": team_b["code"],
                                "result": {"gameWins": team_b_wins}
                            }
                        ]
                    }
                }
                
                matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Erro ao buscar partidas do torneio {tournament_id}: {str(e)}")
            return None
    
    def _process_match_data(self, match):
        """
        Processa dados de uma partida para formato adequado ao treinamento
        
        Args:
            match: Dados da partida da API
            
        Returns:
            Dicionário com dados processados ou None em caso de erro
        """
        try:
            # Extrair informações básicas
            match_id = match.get('id')
            state = match.get('state')
            
            # Verificar se é uma partida completa
            if state != 'completed':
                return None
            
            # Extrair informações dos times
            teams = match.get('match', {}).get('teams', [])
            
            if len(teams) != 2:
                logger.warning(f"Partida {match_id} não tem exatamente 2 times")
                return None
            
            team_a = teams[0]
            team_b = teams[1]
            
            team_a_name = team_a.get('name', 'Time A')
            team_b_name = team_b.get('name', 'Time B')
            
            team_a_wins = team_a.get('result', {}).get('gameWins', 0)
            team_b_wins = team_b.get('result', {}).get('gameWins', 0)
            
            # Determinar o vencedor (1 = time A venceu, 0 = time B venceu)
            winner = 1 if team_a_wins > team_b_wins else 0
            
            # Dados básicos da partida
            match_data = {
                "match_id": match_id,
                "team_a": team_a_name,
                "team_b": team_b_name,
                "team_a_wins": team_a_wins,
                "team_b_wins": team_b_wins,
                "winner": winner,
                "tournament_id": match.get('tournament', {}).get('id', 'unknown'),
                "date": match.get('startTime')
            }
            
            return match_data
            
        except Exception as e:
            logger.error(f"Erro ao processar dados da partida: {str(e)}")
            return None
    
    def _update_teams_data(self, teams_data, match_data):
        """
        Atualiza dados de times com base no resultado da partida
        
        Args:
            teams_data: Dicionário de dados dos times
            match_data: Dados da partida processada
        """
        team_a = match_data["team_a"]
        team_b = match_data["team_b"]
        winner = match_data["winner"]
        
        # Inicializar dados do time A se não existir
        if team_a not in teams_data:
            teams_data[team_a] = {
                "matches_played": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "recent_matches": []
            }
        
        # Inicializar dados do time B se não existir
        if team_b not in teams_data:
            teams_data[team_b] = {
                "matches_played": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "recent_matches": []
            }
        
        # Atualizar estatísticas do time A
        teams_data[team_a]["matches_played"] += 1
        if winner == 1:
            teams_data[team_a]["wins"] += 1
        else:
            teams_data[team_a]["losses"] += 1
        
        teams_data[team_a]["win_rate"] = teams_data[team_a]["wins"] / teams_data[team_a]["matches_played"]
        
        # Atualizar estatísticas do time B
        teams_data[team_b]["matches_played"] += 1
        if winner == 0:
            teams_data[team_b]["wins"] += 1
        else:
            teams_data[team_b]["losses"] += 1
        
        teams_data[team_b]["win_rate"] = teams_data[team_b]["wins"] / teams_data[team_b]["matches_played"]
        
        # Adicionar partida recente para o time A
        match_record_a = {
            "opponent": team_b,
            "result": "win" if winner == 1 else "loss",
            "score": f"{match_data['team_a_wins']}-{match_data['team_b_wins']}",
            "date": match_data["date"]
        }
        
        teams_data[team_a]["recent_matches"].append(match_record_a)
        teams_data[team_a]["recent_matches"] = teams_data[team_a]["recent_matches"][-10:]  # Manter apenas 10 mais recentes
        
        # Adicionar partida recente para o time B
        match_record_b = {
            "opponent": team_a,
            "result": "win" if winner == 0 else "loss",
            "score": f"{match_data['team_b_wins']}-{match_data['team_a_wins']}",
            "date": match_data["date"]
        }
        
        teams_data[team_b]["recent_matches"].append(match_record_b)
        teams_data[team_b]["recent_matches"] = teams_data[team_b]["recent_matches"][-10:]  # Manter apenas 10 mais recentes
    
    def train_model(self):
        """
        Treina o modelo de previsão usando dados históricos de 2023-2025
        
        Returns:
            Boolean indicando sucesso ou falha
        """
        logger.info("Iniciando treinamento do modelo com dados de 2023-2025...")
        
        try:
            # Carregar dados históricos
            matches_path = os.path.join(self.data_path, 'historical_matches.json')
            
            if not os.path.exists(matches_path):
                logger.error(f"Arquivo de dados históricos não encontrado: {matches_path}")
                return False
            
            with open(matches_path, 'r') as f:
                historical_matches = json.load(f)
            
            if not historical_matches:
                logger.error("Nenhum dado histórico disponível para treinamento")
                return False
            
            logger.info(f"Carregados {len(historical_matches)} registros de partidas para treinamento")
            
            # Carregar dados de times
            with open(self.teams_data_path, 'r') as f:
                teams_data = json.load(f)
            
            # Preparar dados para treinamento
            X, y = self._prepare_training_data(historical_matches, teams_data)
            
            if X.shape[0] == 0:
                logger.error("Nenhum dado válido para treinamento")
                return False
            
            # Normalizar features
            X_scaled = self.scaler.fit_transform(X)
            
            # Dividir dados em treino (80%) e validação (20%)
            from sklearn.model_selection import train_test_split
            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Treinar modelo avançado (Random Forest com hyperparâmetros otimizados)
            logger.info("Treinando modelo RandomForest otimizado...")
            self.model = RandomForestClassifier(
                n_estimators=200,  # Mais árvores para melhor generalização
                max_depth=12,      # Profundidade um pouco maior para capturar padrões mais complexos
                min_samples_split=6, # Ajuda a evitar overfitting
                min_samples_leaf=4,  # Ajuda a evitar overfitting
                max_features='sqrt', # Usa raiz quadrada do número de features
                bootstrap=True,    # Usa bootstrap para criar subamostras
                class_weight='balanced', # Trata desbalanceamento de classes
                random_state=42
            )
            
            # Avaliar modelo com validação cruzada
            logger.info("Avaliando modelo com validação cruzada...")
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
            logger.info(f"Acurácia média na validação cruzada: {cv_scores.mean():.4f}")
            
            # Treinar o modelo final com todos os dados
            self.model.fit(X_train, y_train)
            
            # Avaliar modelo no conjunto de validação
            y_pred_val = self.model.predict(X_val)
            accuracy_val = accuracy_score(y_val, y_pred_val)
            precision_val = precision_score(y_val, y_pred_val)
            recall_val = recall_score(y_val, y_pred_val)
            f1_val = f1_score(y_val, y_pred_val)
            
            logger.info(f"Métricas de validação:")
            logger.info(f"Acurácia: {accuracy_val:.4f}")
            logger.info(f"Precisão: {precision_val:.4f}")
            logger.info(f"Recall: {recall_val:.4f}")
            logger.info(f"F1-Score: {f1_val:.4f}")
            
            # Treinar modelo final com todos os dados
            self.model.fit(X_scaled, y)
            
            # Avaliar modelo no conjunto de treinamento
            y_pred = self.model.predict(X_scaled)
            accuracy = accuracy_score(y, y_pred)
            precision = precision_score(y, y_pred)
            recall = recall_score(y, y_pred)
            f1 = f1_score(y, y_pred)
            
            logger.info(f"Métricas de treinamento final:")
            logger.info(f"Acurácia: {accuracy:.4f}")
            logger.info(f"Precisão: {precision:.4f}")
            logger.info(f"Recall: {recall:.4f}")
            logger.info(f"F1-Score: {f1:.4f}")
            
            # Identificar características mais importantes
            feature_importances = self.model.feature_importances_
            logger.info("Características mais importantes para o modelo:")
            for i, importance in enumerate(feature_importances):
                logger.info(f"Feature {i+1}: {importance:.4f}")
            
            # Salvar o modelo treinado
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Salvar o scaler
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            logger.info(f"Modelo treinado com dados 2023-2025 e salvo em {self.model_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro durante treinamento do modelo: {str(e)}")
            return False
    
    def _prepare_training_data(self, historical_matches, teams_data):
        """
        Prepara dados históricos para treinamento
        
        Args:
            historical_matches: Lista de partidas históricas
            teams_data: Dicionário com dados dos times
            
        Returns:
            X: Features para treinamento
            y: Labels (vencedores)
        """
        features = []
        labels = []
        
        for match in historical_matches:
            team_a = match["team_a"]
            team_b = match["team_b"]
            winner = match["winner"]
            
            # Verificar se temos dados de ambos os times
            if team_a not in teams_data or team_b not in teams_data:
                continue
            
            # Extrair features dos times
            team_a_data = teams_data[team_a]
            team_b_data = teams_data[team_b]
            
            # Features básicas
            match_features = [
                team_a_data["win_rate"],                       # Taxa de vitória do time A
                team_b_data["win_rate"],                       # Taxa de vitória do time B
                team_a_data["matches_played"],                 # Experiência do time A
                team_b_data["matches_played"],                 # Experiência do time B
                team_a_data["wins"] / max(1, team_a_data["matches_played"]),  # Taxa de vitória normalizada do time A
                team_b_data["wins"] / max(1, team_b_data["matches_played"]),  # Taxa de vitória normalizada do time B
                team_a_data["wins"],                           # Total de vitórias do time A
                team_b_data["wins"],                           # Total de vitórias do time B
                team_a_data["losses"],                         # Total de derrotas do time A
                team_b_data["losses"],                         # Total de derrotas do time B
            ]
            
            # Calcular desempenho recente (últimas 5 partidas)
            recent_a = team_a_data["recent_matches"][-5:] if len(team_a_data["recent_matches"]) >= 5 else team_a_data["recent_matches"]
            recent_b = team_b_data["recent_matches"][-5:] if len(team_b_data["recent_matches"]) >= 5 else team_b_data["recent_matches"]
            
            recent_wins_a = sum(1 for m in recent_a if m["result"] == "win")
            recent_wins_b = sum(1 for m in recent_b if m["result"] == "win")
            
            match_features.extend([
                recent_wins_a / max(1, len(recent_a)),  # Taxa de vitória recente do time A
                recent_wins_b / max(1, len(recent_b))   # Taxa de vitória recente do time B
            ])
            
            # Adicionar característica de confronto direto
            head_to_head_a = sum(1 for m in team_a_data["recent_matches"] if m["opponent"] == team_b and m["result"] == "win")
            head_to_head_b = sum(1 for m in team_b_data["recent_matches"] if m["opponent"] == team_a and m["result"] == "win")
            total_matches = head_to_head_a + head_to_head_b
            
            if total_matches > 0:
                match_features.append(head_to_head_a / total_matches)
            else:
                match_features.append(0.5)  # Valor neutro se não há histórico
            
            features.append(match_features)
            labels.append(winner)
        
        return np.array(features), np.array(labels)
    
    def load_model(self):
        """
        Carrega modelo treinado do disco
        
        Returns:
            Boolean indicando sucesso ou falha
        """
        try:
            if not os.path.exists(self.model_path) or not os.path.exists(self.scaler_path):
                logger.warning("Modelo treinado ou scaler não encontrados")
                return False
            
            # Carregar modelo
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Carregar scaler
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            logger.info("Modelo e scaler carregados com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            return False
    
    def predict_match(self, team_a, team_b, live_stats=None):
        """
        Prediz resultado de uma partida com dados ao vivo
        
        Args:
            team_a: Nome do time A
            team_b: Nome do time B
            live_stats: Estatísticas ao vivo (opcional)
            
        Returns:
            Probabilidade do time A vencer (float entre 0 e 1)
        """
        if not self.model:
            logger.warning("Modelo não carregado")
            return 0.5
        
        try:
            # Carregar dados dos times
            if not os.path.exists(self.teams_data_path):
                logger.warning("Dados de times não encontrados")
                return 0.5
            
            with open(self.teams_data_path, 'r') as f:
                teams_data = json.load(f)
            
            # Verificar se temos dados dos times
            if team_a not in teams_data or team_b not in teams_data:
                logger.warning(f"Dados insuficientes para os times {team_a} e/ou {team_b}")
                return 0.5
            
            # Extrair features dos times
            team_a_data = teams_data[team_a]
            team_b_data = teams_data[team_b]
            
            # Features básicas
            features = [
                team_a_data["win_rate"],                       # Taxa de vitória do time A
                team_b_data["win_rate"],                       # Taxa de vitória do time B
                team_a_data["matches_played"],                 # Experiência do time A
                team_b_data["matches_played"],                 # Experiência do time B
                team_a_data["wins"] / max(1, team_a_data["matches_played"]),  # Taxa de vitória normalizada do time A
                team_b_data["wins"] / max(1, team_b_data["matches_played"]),  # Taxa de vitória normalizada do time B
                team_a_data["wins"],                           # Total de vitórias do time A
                team_b_data["wins"],                           # Total de vitórias do time B
                team_a_data["losses"],                         # Total de derrotas do time A
                team_b_data["losses"],                         # Total de derrotas do time B
            ]
            
            # Calcular desempenho recente (últimas 5 partidas)
            recent_a = team_a_data["recent_matches"][-5:] if len(team_a_data["recent_matches"]) >= 5 else team_a_data["recent_matches"]
            recent_b = team_b_data["recent_matches"][-5:] if len(team_b_data["recent_matches"]) >= 5 else team_b_data["recent_matches"]
            
            recent_wins_a = sum(1 for m in recent_a if m["result"] == "win")
            recent_wins_b = sum(1 for m in recent_b if m["result"] == "win")
            
            features.extend([
                recent_wins_a / max(1, len(recent_a)),  # Taxa de vitória recente do time A
                recent_wins_b / max(1, len(recent_b))   # Taxa de vitória recente do time B
            ])
            
            # Adicionar característica de confronto direto
            head_to_head_a = sum(1 for m in team_a_data["recent_matches"] if m["opponent"] == team_b and m["result"] == "win")
            head_to_head_b = sum(1 for m in team_b_data["recent_matches"] if m["opponent"] == team_a and m["result"] == "win")
            total_matches = head_to_head_a + head_to_head_b
            
            if total_matches > 0:
                features.append(head_to_head_a / total_matches)
            else:
                features.append(0.5)  # Valor neutro se não há histórico
            
            # Adicionar features de estatísticas ao vivo (peso maior para partidas em andamento)
            live_game_weight = 0.0  # Peso padrão quando não há estatísticas ao vivo
            
            if live_stats:
                # Extrair estatísticas de cada time
                team_a_stats = live_stats.get("team_a", {})
                team_b_stats = live_stats.get("team_b", {})
                
                # Verificar fase do jogo pelo tempo
                game_time = "00:00"
                if "game_time" in live_stats:
                    game_time = live_stats["game_time"]
                
                minutes = 0
                if ":" in game_time:
                    minutes, _ = map(int, game_time.split(":"))
                
                # Ajustar peso das estatísticas ao vivo com base na fase do jogo
                # Early game (0-15 min): menos confiável
                # Mid game (15-25 min): mais confiável
                # Late game (25+ min): muito confiável
                if minutes < 15:
                    live_game_weight = 0.3  # Early game - peso menor
                elif minutes < 25:
                    live_game_weight = 0.6  # Mid game - peso moderado
                else:
                    live_game_weight = 0.8  # Late game - peso alto
                
                # Calcular vantagem baseada em ouro (importante para previsão)
                if "gold" in team_a_stats and "gold" in team_b_stats:
                    gold_a = team_a_stats["gold"]
                    gold_b = team_b_stats["gold"]
                    total_gold = gold_a + gold_b
                    
                    if total_gold > 0:
                        gold_diff = (gold_a - gold_b) / total_gold
                        features.append(gold_diff)
                    else:
                        features.append(0.0)
                else:
                    features.append(0.0)
                
                # Calcular vantagem baseada em kills
                if "kills" in team_a_stats and "kills" in team_b_stats:
                    kills_a = team_a_stats["kills"]
                    kills_b = team_b_stats["kills"]
                    total_kills = kills_a + kills_b
                    
                    if total_kills > 0:
                        kill_diff = (kills_a - kills_b) / max(5, total_kills)
                        features.append(kill_diff)
                    else:
                        features.append(0.0)
                else:
                    features.append(0.0)
                
                # Calcular vantagem baseada em dragões (importante no meta atual)
                if "dragons" in team_a_stats and "dragons" in team_b_stats:
                    dragons_a = len(team_a_stats["dragons"])
                    dragons_b = len(team_b_stats["dragons"])
                    dragon_diff = dragons_a - dragons_b
                    
                    # Se há vantagem de alma (4 dragões)
                    if dragons_a >= 4 or dragons_b >= 4:
                        dragon_factor = 2.0 * (dragon_diff / 4.0)  # Maior peso para vantagem de alma
                    else:
                        dragon_factor = dragon_diff / 4.0
                    
                    features.append(dragon_factor)
                else:
                    features.append(0.0)
                
                # Calcular vantagem baseada em barões (muito importante no late game)
                if "barons" in team_a_stats and "barons" in team_b_stats:
                    barons_a = team_a_stats["barons"]
                    barons_b = team_b_stats["barons"]
                    baron_diff = barons_a - barons_b
                    
                    # Barão tem peso maior no late game
                    if minutes >= 25:
                        baron_factor = baron_diff * 1.5
                    else:
                        baron_factor = baron_diff
                    
                    features.append(baron_factor)
                else:
                    features.append(0.0)
                
                # Adicionar vantagem de torres
                if "towers" in team_a_stats and "towers" in team_b_stats:
                    towers_a = team_a_stats["towers"]
                    towers_b = team_b_stats["towers"]
                    tower_diff = (towers_a - towers_b) / 11.0  # Normalizar pelo total de torres (11)
                    
                    features.append(tower_diff)
                else:
                    features.append(0.0)
            else:
                # Se não temos dados ao vivo, adicionar valores neutros
                features.extend([0.0, 0.0, 0.0, 0.0, 0.0])
            
            # Verificar e ajustar o número de features para 13
            expected_features = 13
            if len(features) != expected_features:
                if len(features) > expected_features:
                    logger.warning(f"Número de features maior que o esperado: {len(features)}. Ajustando para {expected_features}.")
                    features = features[:expected_features]
                else:
                    logger.warning(f"Número de features menor que o esperado: {len(features)}. Preenchendo até {expected_features}.")
                    # Preencher com zeros até alcançar o número esperado
                    features.extend([0.0] * (expected_features - len(features)))
            
            # Normalizar features
            features_scaled = self.scaler.transform([features])
            
            # Fazer previsão com o modelo
            base_proba = self.model.predict_proba(features_scaled)[0][1]
            
            # Ajustar previsão com base nas estatísticas ao vivo (se disponíveis)
            if live_stats and live_game_weight > 0:
                # Calcular vantagem ao vivo baseada em fatores críticos
                live_advantage = 0.0
                
                # Vantagem de ouro é um forte indicador
                if "gold" in team_a_stats and "gold" in team_b_stats:
                    gold_a = team_a_stats.get("gold", 0)
                    gold_b = team_b_stats.get("gold", 0)
                    
                    if gold_a + gold_b > 0:
                        gold_ratio = gold_a / (gold_a + gold_b)
                        # Converter para vantagem centralizada em 0.5 (-0.5 a +0.5)
                        gold_advantage = (gold_ratio - 0.5) * 2
                        live_advantage += gold_advantage * 0.4  # Peso de 40% para ouro
                
                # Vantagem de dragões (importante para objetivos)
                if "dragons" in team_a_stats and "dragons" in team_b_stats:
                    dragons_a = len(team_a_stats.get("dragons", []))
                    dragons_b = len(team_b_stats.get("dragons", []))
                    
                    # Diferença normalizada de dragões
                    if dragons_a + dragons_b > 0:
                        dragon_advantage = (dragons_a - dragons_b) / max(4, dragons_a + dragons_b)
                        live_advantage += dragon_advantage * 0.3  # Peso de 30% para dragões
                
                # Vantagem de barão (crítico para fechar jogos)
                if "barons" in team_a_stats and "barons" in team_b_stats:
                    barons_a = team_a_stats.get("barons", 0)
                    barons_b = team_b_stats.get("barons", 0)
                    
                    if barons_a > barons_b:
                        live_advantage += 0.25  # Vantagem significativa para o time com Barão
                    elif barons_b > barons_a:
                        live_advantage -= 0.25  # Desvantagem significativa
                
                # Ajustar probabilidade base com a vantagem ao vivo
                # Fórmula: (1-w) * prob_base + w * (prob_base + live_advantage)
                adjusted_proba = (1 - live_game_weight) * base_proba + live_game_weight * (base_proba + live_advantage)
                
                # Garantir que o resultado está entre 0.01 e 0.99
                adjusted_proba = max(0.01, min(0.99, adjusted_proba))
                
                logger.info(f"Previsão para {team_a} vs {team_b}: base={base_proba:.4f}, ajustada={adjusted_proba:.4f}")
                return adjusted_proba
            else:
                # Sem dados ao vivo, usar apenas a previsão do modelo
                logger.info(f"Previsão para {team_a} vs {team_b}: {base_proba:.4f}")
                return base_proba
            
        except Exception as e:
            logger.error(f"Erro ao prever resultado da partida: {str(e)}")
            return 0.5

# Teste direto
if __name__ == "__main__":
    trainer = ModelTrainer()
    
    # Coletar dados históricos
    print("Coletando dados históricos...")
    trainer.collect_historical_data()
    
    # Treinar modelo
    print("Treinando modelo...")
    trainer.train_model()
    
    # Testar previsão
    print("Testando previsão...")
    proba = trainer.predict_match("T1", "GenG")
    print(f"Probabilidade de T1 vencer GenG: {proba:.4f}") 