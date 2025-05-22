"""
Serviço de previsão para partidas de LoL.

Realiza cálculos de probabilidade e gera palpites para apostas usando
modelo treinado com dados históricos de 2023-2025.
"""

import logging
import sys
import os
import random
from datetime import datetime
import json

# Adicionar diretório raiz ao path para importar de config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_CONFIDENCE_THRESHOLD
from services.model_trainer import ModelTrainer

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PredictorService:
    """
    Serviço para predição de resultados de partidas de LoL.
    
    Implementa algoritmos para calcular probabilidades de vitória
    e gerar recomendações para apostas, usando modelo treinado
    com dados históricos.
    """
    
    def __init__(self):
        """Inicializa o serviço de predição"""
        self.confidence_threshold = MODEL_CONFIDENCE_THRESHOLD
        self.model_trainer = ModelTrainer()
        self.model_loaded = self.model_trainer.load_model()
        
        if not self.model_loaded:
            logger.warning("Modelo preditivo não pôde ser carregado. Usando heurísticas básicas.")
        else:
            logger.info("Modelo preditivo carregado com sucesso")
            
        # Carregar dados de times para fallback
        self.teams_data = self._load_teams_data()
        logger.info("Serviço de predição inicializado")
        
    def _load_teams_data(self):
        """
        Carrega dados históricos de times para uso em fallback
        
        Returns:
            Dicionário com dados dos times ou dados básicos se falhar
        """
        # Dados padrão para alguns times (fallback)
        default_data = {
            "T1": 0.65,         # T1 tem 65% de chance base
            "GenG": 0.63,       # GenG tem 63% de chance base
            "G2": 0.58,         # G2 tem 58% de chance base
            "JDG": 0.61,        # JDG tem 61% de chance base
            "Cloud9": 0.55,     # Cloud9 tem 55% de chance base
            "Fnatic": 0.53,     # Fnatic tem 53% de chance base
            "DRX": 0.54,        # DRX tem 54% de chance base
            "MAD Lions": 0.52,  # MAD Lions tem 52% de chance base
        }
        
        try:
            # Tentar carregar dados mais completos
            data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'teams_data.json')
            
            if os.path.exists(data_path):
                with open(data_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("Arquivo de dados de times não encontrado. Usando dados padrão.")
                return default_data
        except Exception as e:
            logger.error(f"Erro ao carregar dados de times: {str(e)}")
            return default_data
        
    def get_prediction(self, team_a, team_b, compositions=None, match_data=None):
        """
        Calcula previsão para uma partida com base nos times e composições
        
        Args:
            team_a: Nome do time A
            team_b: Nome do time B
            compositions: Dicionário com composições dos times (opcional)
            match_data: Dados adicionais da partida (opcional)
            
        Returns:
            Dicionário com previsão calculada
        """
        try:
            # Calcular probabilidades usando modelo treinado ou fallback
            if self.model_loaded:
                # Obter estatísticas ao vivo para melhorar a previsão
                live_stats = None
                if match_data and "current_game_stats" in match_data and match_data["current_game_stats"]:
                    live_stats = match_data["current_game_stats"]
                
                # Fazer previsão com o modelo treinado
                proba_a = self.model_trainer.predict_match(team_a, team_b, live_stats)
                proba_b = 1.0 - proba_a
            else:
                # Algoritmo de previsão básico baseado em dados disponíveis (fallback)
                proba_a, proba_b = self._calculate_win_probability(team_a, team_b, compositions, match_data)
            
            # Calcular odds
            odds_a = round(1 / proba_a, 2) if proba_a > 0 else 99.99
            odds_b = round(1 / proba_b, 2) if proba_b > 0 else 99.99
            
            # Determinar time favorito
            favorite_team = team_a if proba_a > proba_b else team_b
            underdog_team = team_b if proba_a > proba_b else team_a
            
            # Definir nível de confiança
            diff = abs(proba_a - proba_b)
            if diff > 0.3:
                confidence = "alta"
            elif diff > 0.15:
                confidence = "média"
            else:
                confidence = "baixa"
                
            # Gerar palpite baseado na situação atual
            bet_tip = self._generate_bet_tip(favorite_team, underdog_team, proba_a, proba_b, compositions, match_data)
            
            # Construir objeto de resposta
            prediction = {
                "probaA": round(proba_a, 4),
                "probaB": round(proba_b, 4),
                "win_probability": round(max(proba_a, proba_b) * 100, 1),
                "oddsA": odds_a,
                "oddsB": odds_b,
                "favorite_team": favorite_team,
                "confidence": confidence,
                "bet_tip": bet_tip,
                "timestamp": datetime.now().isoformat(),
                "model_used": "advanced" if self.model_loaded else "basic"
            }
            
            return prediction
        except Exception as e:
            logger.error(f"Erro ao gerar previsão para {team_a} vs {team_b}: {str(e)}")
            # Retornar previsão padrão em caso de erro
            return {
                "probaA": 0.5,
                "probaB": 0.5,
                "win_probability": 50.0,
                "oddsA": 2.0,
                "oddsB": 2.0,
                "favorite_team": team_a,
                "confidence": "baixa",
                "bet_tip": "Dados insuficientes para palpite confiável.",
                "is_fallback": True
            }
    
    def _calculate_win_probability(self, team_a, team_b, compositions=None, match_data=None):
        """
        Calcula probabilidade de vitória com base nos times e estado atual do jogo
        Método de fallback quando o modelo avançado não está disponível
        
        Args:
            team_a: Nome do time A
            team_b: Nome do time B
            compositions: Dicionário com composições dos times (opcional)
            match_data: Dados adicionais da partida (opcional)
            
        Returns:
            Tupla (proba_a, proba_b) com probabilidades de vitória
        """
        # Valores base - podem ser substituídos por um modelo treinado real
        base_a, base_b = 0.5, 0.5
        
        # Ajuste por dados históricos
        if team_a in self.teams_data:
            if isinstance(self.teams_data[team_a], dict) and 'win_rate' in self.teams_data[team_a]:
                base_a = self.teams_data[team_a]['win_rate']
            else:
                base_a = self.teams_data[team_a]  # Para o caso de dados simplificados
                
        if team_b in self.teams_data:
            if isinstance(self.teams_data[team_b], dict) and 'win_rate' in self.teams_data[team_b]:
                base_b = self.teams_data[team_b]['win_rate']
            else:
                base_b = self.teams_data[team_b]  # Para o caso de dados simplificados
            
        # Normalizar para soma = 1
        total = base_a + base_b
        base_a /= total
        base_b /= total
        
        # Ajustar por composição se disponível
        comp_a, comp_b = 0, 0
        if compositions and "composition_a" in compositions and "composition_b" in compositions:
            # Simulação de avaliação de composição - seria substituído por modelo real
            comp_a = random.uniform(-0.05, 0.05)  # Efeito aleatório entre -5% e +5%
            comp_b = random.uniform(-0.05, 0.05)  # Efeito aleatório entre -5% e +5%
        
        # Ajustar por estado atual da partida
        state_a, state_b = 0, 0
        if match_data and "current_game_stats" in match_data and match_data["current_game_stats"]:
            stats = match_data["current_game_stats"]
            
            # Obter estatísticas de cada time
            team_a_stats = stats.get("team_a", {})
            team_b_stats = stats.get("team_b", {})
            
            # Calcular vantagem baseada em ouro
            if "gold" in team_a_stats and "gold" in team_b_stats:
                gold_a = team_a_stats["gold"]
                gold_b = team_b_stats["gold"]
                total_gold = gold_a + gold_b
                
                if total_gold > 0:  # Evitar divisão por zero
                    gold_diff = (gold_a - gold_b) / total_gold
                    state_a += gold_diff * 0.15  # Diferença de ouro tem impacto de até 15%
                    state_b -= gold_diff * 0.15
            
            # Calcular vantagem baseada em kills
            if "kills" in team_a_stats and "kills" in team_b_stats:
                kills_a = team_a_stats["kills"]
                kills_b = team_b_stats["kills"]
                total_kills = kills_a + kills_b
                
                if total_kills > 0:  # Evitar divisão por zero
                    kill_diff = (kills_a - kills_b) / max(5, total_kills)  # Normalizar por pelo menos 5 kills
                    state_a += kill_diff * 0.1  # Diferença de kills tem impacto de até 10%
                    state_b -= kill_diff * 0.1
            
            # Calcular vantagem baseada em dragões
            if "dragons" in team_a_stats and "dragons" in team_b_stats:
                dragons_a = len(team_a_stats.get("dragons", []))
                dragons_b = len(team_b_stats.get("dragons", []))
                dragon_diff = dragons_a - dragons_b
                
                # Maior peso para situações de vantagem de alma
                if dragons_a >= 4 or dragons_b >= 4:
                    if dragons_a >= 4:
                        state_a += 0.2  # Vantagem significativa para o time com 4+ dragões
                    if dragons_b >= 4:
                        state_b += 0.2
                else:
                    # Cada dragão dá uma pequena vantagem
                    state_a += dragon_diff * 0.05
                    state_b -= dragon_diff * 0.05
            
            # Calcular vantagem baseada em barões
            if "barons" in team_a_stats and "barons" in team_b_stats:
                barons_a = team_a_stats.get("barons", 0)
                barons_b = team_b_stats.get("barons", 0)
                baron_diff = barons_a - barons_b
                
                # Barão é muito impactante
                state_a += baron_diff * 0.15
                state_b -= baron_diff * 0.15
            
            # Ajuste baseado na fase do jogo
            game_time = stats.get("game_time", "00:00")
            minutes = 0
            if ":" in game_time:
                minutes, _ = map(int, game_time.split(":"))
            
            # Aumentar peso das vantagens atuais com base no tempo de jogo
            # Early game: vantagens são menos decisivas
            # Late game: vantagens são mais decisivas
            if minutes < 15:
                state_weight = 0.5  # Early game - peso menor
            elif minutes < 25:
                state_weight = 0.8  # Mid game - peso moderado
            else:
                state_weight = 1.2  # Late game - peso maior
                
            state_a *= state_weight
            state_b *= state_weight
            
        # Combinar todos os fatores
        proba_a = base_a + comp_a + state_a
        proba_b = base_b + comp_b + state_b
        
        # Garantir que valores estão entre 0.01 e 0.99
        proba_a = max(0.01, min(0.99, proba_a))
        proba_b = max(0.01, min(0.99, proba_b))
        
        # Normalizar para soma = 1
        total = proba_a + proba_b
        proba_a /= total
        proba_b /= total
        
        return proba_a, proba_b
    
    def _generate_bet_tip(self, favorite_team, underdog_team, proba_a, proba_b, compositions=None, match_data=None):
        """
        Gera dica de aposta baseada na previsão atual
        
        Args:
            favorite_team: Time favorito
            underdog_team: Time azarão
            proba_a: Probabilidade do time A
            proba_b: Probabilidade do time B
            compositions: Dicionário com composições (opcional)
            match_data: Dados adicionais da partida (opcional)
            
        Returns:
            String com dica de aposta
        """
        # Probabilidade do favorito
        fav_prob = max(proba_a, proba_b)
        
        # Determinar odds teóricas justas
        fair_odds_fav = 1 / fav_prob
        
        # Calcular nível de confiança
        diff = abs(proba_a - proba_b)
        confidence_level = "baixa"
        if diff > 0.3:
            confidence_level = "alta"
        elif diff > 0.15:
            confidence_level = "média"
        
        # Verificar se temos dados da partida em andamento
        live_match = False
        early_game = True
        if match_data and "current_game_stats" in match_data and match_data["current_game_stats"]:
            live_match = True
            stats = match_data["current_game_stats"]
            game_time = stats.get("game_time", "00:00")
            
            minutes = 0
            if ":" in game_time:
                minutes, _ = map(int, game_time.split(":"))
            
            if minutes >= 15:
                early_game = False
            
            team_a = match_data.get("teamA")
            team_b = match_data.get("teamB")
            
            # Ajustar time favorito com dados ao vivo
            if team_a and team_b:
                team_a_stats = stats.get("team_a", {})
                team_b_stats = stats.get("team_b", {})
                
                # Calcular vantagem atual baseada em fatores-chave
                team_a_advantage = 0
                team_b_advantage = 0
                
                # Vantagem de ouro
                if "gold" in team_a_stats and "gold" in team_b_stats:
                    gold_a = team_a_stats["gold"]
                    gold_b = team_b_stats["gold"]
                    
                    if gold_a > gold_b * 1.15:  # 15% de vantagem de ouro
                        team_a_advantage += 1
                    elif gold_b > gold_a * 1.15:
                        team_b_advantage += 1
                
                # Vantagem de kills
                if "kills" in team_a_stats and "kills" in team_b_stats:
                    kills_a = team_a_stats["kills"]
                    kills_b = team_b_stats["kills"]
                    
                    if kills_a >= kills_b + 5:  # 5 kills de vantagem
                        team_a_advantage += 1
                    elif kills_b >= kills_a + 5:
                        team_b_advantage += 1
                
                # Vantagem de dragões
                if "dragons" in team_a_stats and "dragons" in team_b_stats:
                    dragons_a = len(team_a_stats.get("dragons", []))
                    dragons_b = len(team_b_stats.get("dragons", []))
                    
                    if dragons_a >= dragons_b + 2:  # 2 dragões de vantagem
                        team_a_advantage += 1
                    elif dragons_b >= dragons_a + 2:
                        team_b_advantage += 1
                    
                    # Alma do dragão
                    if dragons_a >= 4:
                        team_a_advantage += 2
                    if dragons_b >= 4:
                        team_b_advantage += 2
                
                # Vantagem de barão
                if "barons" in team_a_stats and "barons" in team_b_stats:
                    barons_a = team_a_stats.get("barons", 0)
                    barons_b = team_b_stats.get("barons", 0)
                    
                    if barons_a > barons_b:
                        team_a_advantage += 2
                    elif barons_b > barons_a:
                        team_b_advantage += 2
                
                # Determinar quem está na vantagem ao vivo
                live_favorite = None
                if team_a_advantage > team_b_advantage + 1:
                    live_favorite = team_a
                elif team_b_advantage > team_a_advantage + 1:
                    live_favorite = team_b
        
        # Gerar dica de aposta com base em todos os fatores analisados
        if live_match and not early_game:
            if live_favorite == favorite_team and fav_prob >= 0.65:
                return f"Aposta recomendada: Vitória do {favorite_team}. Dados ao vivo confirmam vantagem."
            elif live_favorite and live_favorite != favorite_team:
                return f"Oportunidade detectada: Aposta no {live_favorite}. Desempenho ao vivo superior à expectativa."
            elif diff < 0.1:  # Partida muito equilibrada
                return f"Partida equilibrada ao vivo. Considere apostas em objetivos ou duração do jogo."
            else:
                return f"Aguarde mais dados para fazer uma aposta informada. Situação ainda incerta."
        elif live_match and early_game:
            return "Jogo em fase inicial. Aguarde o mid-game para apostas mais precisas."
        else:
            # Sem dados ao vivo, baseado apenas nas probabilidades pré-jogo
            if fav_prob >= 0.7:
                return f"Aposta forte na vitória do {favorite_team}. Alta probabilidade de sucesso."
            elif fav_prob >= 0.6:
                return f"Aposta moderada na vitória do {favorite_team}. Bom valor."
            elif fav_prob < 0.55:
                return f"Partida muito equilibrada. Considere apostar no {underdog_team} com odds atrativas ou evite."
            else:
                return "Dados insuficientes para uma recomendação de aposta confiável."
    
    def get_match_analysis(self, match_data):
        """
        Gera análise detalhada de uma partida
        
        Args:
            match_data: Dados da partida
            
        Returns:
            Dicionário com análise detalhada
        """
        try:
            team_a = match_data.get("teamA", "Time A")
            team_b = match_data.get("teamB", "Time B")
            
            # Obter previsão básica
            prediction = self.get_prediction(team_a, team_b, None, match_data)
            
            # Analisar composições se disponíveis
            comp_analysis = "Dados de composição não disponíveis."
            if "composition_a" in match_data and "composition_b" in match_data:
                comp_a = match_data["composition_a"]
                comp_b = match_data["composition_b"]
                
                # Aqui seria integrado um modelo de análise de composição
                # Implementação simplificada para gerar texto básico
                
                if len(comp_a) == 5 and len(comp_b) == 5:
                    # Análise simplificada baseada em tipos de composição
                    comp_a_types = self._analyze_composition_type(comp_a)
                    comp_b_types = self._analyze_composition_type(comp_b)
                    
                    comp_analysis = f"Time {team_a} tem composição focada em {', '.join(comp_a_types[:2])}, "
                    comp_analysis += f"enquanto {team_b} prioriza {', '.join(comp_b_types[:2])}. "
                    
                    # Adicionar análise de choque de estilos
                    if "poke" in comp_a_types and "engage" in comp_b_types:
                        comp_analysis += f"Vantagem para {team_b} se conseguir forçar lutas."
                    elif "engage" in comp_a_types and "poke" in comp_b_types:
                        comp_analysis += f"Vantagem para {team_a} se conseguir forçar lutas."
                    elif "scaling" in comp_a_types and "early game" in comp_b_types:
                        comp_analysis += f"Vantagem para {team_b} no early game, mas {team_a} é mais forte no late."
                    elif "early game" in comp_a_types and "scaling" in comp_b_types:
                        comp_analysis += f"Vantagem para {team_a} no early game, mas {team_b} é mais forte no late."
                    else:
                        comp_analysis += "Composições equilibradas com forças em diferentes fases do jogo."
            
            # Analisar estado atual do jogo
            game_analysis = "Partida ainda não iniciada."
            key_factors = []
            advantage_team = None
            
            if "current_game_stats" in match_data and match_data["current_game_stats"]:
                stats = match_data["current_game_stats"]
                
                # Extrair estatísticas relevantes
                team_a_stats = stats.get("team_a", {})
                team_b_stats = stats.get("team_b", {})
                game_time = stats.get("game_time", "00:00")
                
                minutes = 0
                if ":" in game_time:
                    minutes, _ = map(int, game_time.split(":"))
                
                # Determinar fase do jogo
                game_phase = "early game"
                if minutes >= 25:
                    game_phase = "late game"
                elif minutes >= 15:
                    game_phase = "mid game"
                
                # Analisar vantagens
                advantages = []
                
                # Vantagem de ouro
                if "gold" in team_a_stats and "gold" in team_b_stats:
                    gold_a = team_a_stats["gold"]
                    gold_b = team_b_stats["gold"]
                    gold_diff = gold_a - gold_b
                    
                    if abs(gold_diff) > 3000:
                        if gold_diff > 0:
                            advantages.append(f"{team_a} tem vantagem de {abs(gold_diff)/1000:.1f}k de ouro")
                            key_factors.append("Vantagem de ouro")
                        else:
                            advantages.append(f"{team_b} tem vantagem de {abs(gold_diff)/1000:.1f}k de ouro")
                            key_factors.append("Vantagem de ouro")
                
                # Vantagem de kills
                if "kills" in team_a_stats and "kills" in team_b_stats:
                    kills_a = team_a_stats["kills"]
                    kills_b = team_b_stats["kills"]
                    kill_diff = kills_a - kills_b
                    
                    if abs(kill_diff) >= 3:
                        if kill_diff > 0:
                            advantages.append(f"{team_a} tem vantagem de {abs(kill_diff)} kills")
                            key_factors.append("Vantagem de kills")
                        else:
                            advantages.append(f"{team_b} tem vantagem de {abs(kill_diff)} kills")
                            key_factors.append("Vantagem de kills")
                
                # Vantagem de objetivos
                obj_advantages = []
                
                # Dragões
                if "dragons" in team_a_stats and "dragons" in team_b_stats:
                    dragons_a = len(team_a_stats.get("dragons", []))
                    dragons_b = len(team_b_stats.get("dragons", []))
                    dragon_diff = dragons_a - dragons_b
                    
                    if dragons_a >= 4:
                        obj_advantages.append(f"{team_a} tem alma do dragão")
                        key_factors.append("Alma do dragão")
                    elif dragons_b >= 4:
                        obj_advantages.append(f"{team_b} tem alma do dragão")
                        key_factors.append("Alma do dragão")
                    elif abs(dragon_diff) >= 2:
                        if dragon_diff > 0:
                            obj_advantages.append(f"{team_a} tem vantagem de {dragons_a}-{dragons_b} em dragões")
                            key_factors.append("Vantagem de dragões")
                        else:
                            obj_advantages.append(f"{team_b} tem vantagem de {dragons_b}-{dragons_a} em dragões")
                            key_factors.append("Vantagem de dragões")
                
                # Barões
                if "barons" in team_a_stats and "barons" in team_b_stats:
                    barons_a = team_a_stats.get("barons", 0)
                    barons_b = team_b_stats.get("barons", 0)
                    
                    if barons_a > 0 and barons_a > barons_b:
                        obj_advantages.append(f"{team_a} tem {barons_a} barão(ões)")
                        key_factors.append("Barão ativo")
                    elif barons_b > 0 and barons_b > barons_a:
                        obj_advantages.append(f"{team_b} tem {barons_b} barão(ões)")
                        key_factors.append("Barão ativo")
                
                # Torres
                if "towers" in team_a_stats and "towers" in team_b_stats:
                    towers_a = team_a_stats.get("towers", 0)
                    towers_b = team_b_stats.get("towers", 0)
                    tower_diff = towers_a - towers_b
                    
                    if abs(tower_diff) >= 2:
                        if tower_diff > 0:
                            obj_advantages.append(f"{team_a} destruiu {tower_diff} torres a mais")
                            key_factors.append("Vantagem de torres")
                        else:
                            obj_advantages.append(f"{team_b} destruiu {abs(tower_diff)} torres a mais")
                            key_factors.append("Vantagem de torres")
                
                # Determinar time com vantagem geral
                team_a_points = 0
                team_b_points = 0
                
                for adv in advantages + obj_advantages:
                    if team_a in adv:
                        team_a_points += 1
                    elif team_b in adv:
                        team_b_points += 1
                
                if team_a_points > team_b_points + 1:
                    advantage_team = team_a
                elif team_b_points > team_a_points + 1:
                    advantage_team = team_b
                
                # Construir análise textual
                if advantages or obj_advantages:
                    game_analysis = f"Partida em {game_phase}. "
                    
                    if advantages:
                        game_analysis += " ".join(advantages) + ". "
                    
                    if obj_advantages:
                        game_analysis += " ".join(obj_advantages) + ". "
                    
                    if advantage_team:
                        game_analysis += f"{advantage_team} tem vantagem significativa neste momento."
                    else:
                        game_analysis += "Partida ainda equilibrada apesar das diferenças."
                else:
                    game_analysis = f"Partida em {game_phase}, situação bastante equilibrada até o momento."
                
                # Adicionar mais fatores-chave gerais
                if not key_factors:
                    key_factors = ["Partida equilibrada"]
                    
                if game_phase == "late game":
                    key_factors.append("Fase tardia do jogo")
                elif game_phase == "early game":
                    key_factors.append("Início de jogo")
            
            # Construir objeto de resposta completo
            proba_a = prediction.get("probaA", 0.5)
            proba_b = prediction.get("probaB", 0.5)
            
            # Calcular odds justas
            odds_a = round(1 / proba_a, 2) if proba_a > 0 else 99.99
            odds_b = round(1 / proba_b, 2) if proba_b > 0 else 99.99
            
            # Determinar nível de confiança
            confidence = prediction.get("confidence", "baixa")
            
            # Determinar time favorito
            favorite_team = prediction.get("favorite_team", team_a)
            
            # Gerar análise final completa
            final_analysis = f"{game_analysis} "
            if comp_analysis != "Dados de composição não disponíveis.":
                final_analysis += f"{comp_analysis} "
                
            # Adicionar análise de valor de aposta
            if advantage_team and advantage_team != favorite_team:
                final_analysis += f"Possível valor em apostar em {advantage_team} como azarão."
            elif advantage_team and advantage_team == favorite_team and confidence == "alta":
                final_analysis += f"Dados confirmam favoritismo de {favorite_team}."
            
            # Extrair dica de aposta
            bet_tip = prediction.get("bet_tip", "Dados insuficientes para palpite confiável.")
            
            return {
                "favorite_team": favorite_team,
                "win_probability": {
                    "team_a": proba_a,
                    "team_b": proba_b
                },
                "current_odds": {
                    "team_a": odds_a,
                    "team_b": odds_b
                },
                "confidence": confidence,
                "composition_analysis": comp_analysis,
                "game_state_analysis": game_analysis,
                "analysis": final_analysis,
                "bet_tip": bet_tip,
                "key_factors": key_factors,
                "time_analyzed": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar análise da partida: {str(e)}")
            return {
                "favorite_team": match_data.get("teamA", "Time A"),
                "win_probability": {"team_a": 0.5, "team_b": 0.5},
                "current_odds": {"team_a": 2.0, "team_b": 2.0},
                "confidence": "baixa",
                "analysis": "Não foi possível gerar análise detalhada devido a um erro.",
                "bet_tip": "Aguarde mais dados para fazer uma aposta informada.",
                "is_fallback": True
            }
    
    def _analyze_composition_type(self, champions):
        """
        Analisa o tipo de composição baseado nos campeões
        
        Args:
            champions: Lista de campeões na composição
            
        Returns:
            Lista de tipos de composição identificados
        """
        # Categorias conhecidas de campeões (simplificado)
        poke_champs = ["Xerath", "Ziggs", "Jayce", "Zoe", "Ezreal", "Varus", "Velkoz", "Nidalee"]
        engage_champs = ["Malphite", "Leona", "Nautilus", "Amumu", "Rakan", "Alistar", "Ornn", "Sejuani"]
        early_champs = ["Lee Sin", "Elise", "Renekton", "Lucian", "Pantheon", "Olaf", "Xin Zhao"]
        scaling_champs = ["Kayle", "Kassadin", "Vayne", "Jinx", "Ryze", "Cassiopeia", "Azir", "Twitch"]
        split_push = ["Fiora", "Jax", "Tryndamere", "Camille", "Yorick", "Nasus"]
        teamfight = ["Orianna", "Gnar", "Wukong", "Kennen", "Diana", "Rumble", "Miss Fortune"]
        pick_champs = ["Thresh", "Blitzcrank", "Pyke", "Ahri", "LeBlanc", "Zed", "Fizz"]
        
        # Contar número de campeões em cada categoria
        comp_types = []
        
        # Verificar quantos campeões de cada tipo temos
        poke_count = sum(1 for c in champions if c in poke_champs)
        engage_count = sum(1 for c in champions if c in engage_champs)
        early_count = sum(1 for c in champions if c in early_champs)
        scaling_count = sum(1 for c in champions if c in scaling_champs)
        split_count = sum(1 for c in champions if c in split_push)
        teamfight_count = sum(1 for c in champions if c in teamfight)
        pick_count = sum(1 for c in champions if c in pick_champs)
        
        # Determinar tipos de composição baseado nos thresholds
        if poke_count >= 2:
            comp_types.append("poke")
        if engage_count >= 2:
            comp_types.append("engage")
        if early_count >= 2:
            comp_types.append("early game")
        if scaling_count >= 2:
            comp_types.append("scaling")
        if split_count >= 2:
            comp_types.append("split push")
        if teamfight_count >= 2:
            comp_types.append("team fight")
        if pick_count >= 2:
            comp_types.append("pick composition")
            
        # Se não identificou tipos específicos, adicionar "balanceada"
        if not comp_types:
            comp_types.append("balanceada")
            
        return comp_types


# Teste direto
if __name__ == "__main__":
    # Criar serviço
    predictor = PredictorService()
    
    # Testar previsão simples
    prediction = predictor.get_prediction("T1", "GenG")
    print("Previsão simples:", prediction)
    
    # Testar previsão com composições
    compositions = {
        "composition_a": ["Aatrox", "Viego", "Azir", "Jinx", "Thresh"],
        "composition_b": ["Jax", "Lee Sin", "Ahri", "Xayah", "Pyke"]
    }
    prediction_with_comp = predictor.get_prediction("T1", "GenG", compositions)
    print("\nPrevisão com composições:", prediction_with_comp)
    
    # Testar previsão com dados de partida
    match_data = {
        "teamA": "T1",
        "teamB": "GenG",
        "composition_a": ["Aatrox", "Viego", "Azir", "Jinx", "Thresh"],
        "composition_b": ["Jax", "Lee Sin", "Ahri", "Xayah", "Pyke"],
        "current_game_stats": {
            "team_a": {
                "gold": 25600,
                "kills": 8,
                "towers": 3,
                "dragons": ["ocean", "infernal"],
                "barons": 0
            },
            "team_b": {
                "gold": 23400,
                "kills": 5,
                "towers": 1,
                "dragons": [],
                "barons": 0
            },
            "game_time": "18:45"
        }
    }
    prediction_full = predictor.get_prediction("T1", "GenG", compositions, match_data)
    print("\nPrevisão com dados completos:", prediction_full)
    
    # Testar análise de partida
    analysis = predictor.get_match_analysis(match_data)
    print("\nAnálise da partida:", analysis) 