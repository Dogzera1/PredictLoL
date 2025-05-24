#!/usr/bin/env python3
"""
Sistema de Value Betting Automático
Detecta apostas de valor em tempo real durante partidas ao vivo
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
import json
import random
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ValueBet:
    """Representa uma aposta de valor detectada"""
    match_id: str
    team: str
    opponent: str
    league: str
    predicted_probability: float
    current_odds: float
    value_percentage: float
    confidence: str
    reasoning: str
    timestamp: datetime
    match_time: str  # "15:30" por exemplo
    urgency: str  # "alta", "media", "baixa"

class OddsSimulator:
    """Simula odds dinâmicas durante a partida"""
    
    def __init__(self):
        # Odds base para cada time (seriam obtidas de casas de apostas reais)
        self.base_odds = {}
        self.match_states = {}  # Estado atual de cada partida
        
    def get_live_odds(self, match_id: str, teams: List[str]) -> Dict[str, float]:
        """Simula odds ao vivo que mudam durante a partida"""
        if match_id not in self.base_odds:
            # Inicializar odds base
            self.base_odds[match_id] = {
                teams[0]: round(random.uniform(1.4, 3.5), 2),
                teams[1]: round(random.uniform(1.4, 3.5), 2)
            }
            
        # Simular mudanças baseadas no "momentum" da partida
        current_odds = self.base_odds[match_id].copy()
        
        # Fatores que afetam odds durante partida
        time_factor = random.uniform(0.9, 1.1)  # Mudanças temporais
        momentum_factor = random.uniform(0.8, 1.2)  # Momentum do jogo
        
        for team in teams:
            # Simular flutuação das odds
            current_odds[team] *= time_factor * momentum_factor
            current_odds[team] = max(1.1, min(5.0, current_odds[team]))  # Limitar range
            current_odds[team] = round(current_odds[team], 2)
            
        return current_odds

class ValueBetDetector:
    """Detecta apostas de valor comparando probabilidades vs odds"""
    
    def __init__(self, prediction_system, odds_simulator):
        self.prediction_system = prediction_system
        self.odds_simulator = odds_simulator
        self.value_threshold = 0.15  # 15% de edge mínimo
        self.min_probability = 0.55  # Probabilidade mínima de 55%
        self.max_odds_threshold = 1.5  # Odds máximas aceitáveis
        
    async def analyze_match_for_value(self, match_data: Dict) -> List[ValueBet]:
        """Analisa uma partida em busca de apostas de valor"""
        value_bets = []
        
        try:
            # Obter predição atual
            prediction = await self.prediction_system.predict_live_match(match_data)
            
            teams = match_data.get('teams', [])
            if len(teams) < 2:
                return value_bets
                
            team1_name = teams[0].get('name', teams[0].get('code', 'Team1'))
            team2_name = teams[1].get('name', teams[1].get('code', 'Team2'))
            team_names = [team1_name, team2_name]
            
            # Obter odds atuais (simuladas)
            live_odds = self.odds_simulator.get_live_odds(match_data['id'], team_names)
            
            # Verificar apostas de valor para cada time
            probabilities = [
                prediction['team1_win_probability'],
                prediction['team2_win_probability']
            ]
            
            for i, (team, prob) in enumerate(zip(team_names, probabilities)):
                opponent = team_names[1-i]
                current_odds = live_odds.get(team, 2.0)
                
                # Calcular value
                implied_probability = 1 / current_odds
                value_percentage = (prob - implied_probability) / implied_probability
                
                # Verificar se é uma aposta de valor
                if (prob >= self.min_probability and 
                    current_odds >= self.max_odds_threshold and 
                    value_percentage >= self.value_threshold):
                    
                    value_bet = ValueBet(
                        match_id=match_data['id'],
                        team=team,
                        opponent=opponent,
                        league=match_data.get('league', 'Unknown'),
                        predicted_probability=prob,
                        current_odds=current_odds,
                        value_percentage=value_percentage,
                        confidence=prediction['confidence'],
                        reasoning=self._generate_reasoning(prob, current_odds, value_percentage),
                        timestamp=datetime.now(),
                        match_time=self._get_match_time(match_data),
                        urgency=self._calculate_urgency(value_percentage, prob)
                    )
                    value_bets.append(value_bet)
                    
        except Exception as e:
            logger.error(f"❌ Erro ao analisar value bet: {e}")
            
        return value_bets
    
    def _generate_reasoning(self, probability: float, odds: float, value: float) -> str:
        """Gera explicação para a aposta de valor"""
        implied_prob = 1 / odds
        return (f"Probabilidade real: {probability:.1%} vs "
                f"Odds implicam: {implied_prob:.1%} "
                f"(Edge: {value:.1%})")
    
    def _get_match_time(self, match_data: Dict) -> str:
        """Estima tempo de partida"""
        # Simular tempo de jogo (seria obtido da API real)
        minutes = random.randint(5, 45)
        seconds = random.randint(0, 59)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _calculate_urgency(self, value_percentage: float, probability: float) -> str:
        """Calcula urgência da aposta"""
        if value_percentage >= 0.25 and probability >= 0.70:
            return "alta"
        elif value_percentage >= 0.20 and probability >= 0.60:
            return "media"
        else:
            return "baixa"

class ValueBetNotificationSystem:
    """Sistema de notificação automática de apostas de valor"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.subscribers = set()  # IDs de usuários inscritos
        self.sent_notifications = set()  # Para evitar spam
        self.last_cleanup = datetime.now()
        
    def subscribe_user(self, user_id: int):
        """Inscreve usuário nas notificações"""
        self.subscribers.add(user_id)
        logger.info(f"✅ Usuário {user_id} inscrito nas notificações de value betting")
    
    def unsubscribe_user(self, user_id: int):
        """Remove usuário das notificações"""
        self.subscribers.discard(user_id)
        logger.info(f"❌ Usuário {user_id} removido das notificações")
    
    async def send_value_bet_alert(self, value_bet: ValueBet):
        """Envia alerta de aposta de valor para todos os inscritos"""
        if not self.subscribers:
            return
            
        # Evitar spam - só enviar uma vez por value bet
        alert_key = f"{value_bet.match_id}_{value_bet.team}_{value_bet.current_odds}"
        if alert_key in self.sent_notifications:
            return
            
        self.sent_notifications.add(alert_key)
        
        # Formatar mensagem
        message = self._format_value_bet_message(value_bet)
        
        # Enviar para todos os inscritos
        for user_id in self.subscribers.copy():
            try:
                await self.bot.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"📱 Value bet enviada para usuário {user_id}")
            except Exception as e:
                logger.error(f"❌ Erro ao enviar para {user_id}: {e}")
                # Remove usuários que bloquearam o bot
                self.subscribers.discard(user_id)
    
    def _format_value_bet_message(self, value_bet: ValueBet) -> str:
        """Formata mensagem de value bet"""
        urgency_emoji = {
            "alta": "🔥",
            "media": "⚡",
            "baixa": "💡"
        }
        
        emoji = urgency_emoji.get(value_bet.urgency, "💡")
        
        message = f"""
{emoji} **VALUE BET DETECTADA!**

🎯 **{value_bet.team}** vs {value_bet.opponent}
🏆 **Liga:** {value_bet.league}
⏱️ **Tempo:** {value_bet.match_time}

📊 **ANÁLISE:**
• **Probabilidade:** {value_bet.predicted_probability:.1%}
• **Odds Atuais:** {value_bet.current_odds}x
• **Edge:** +{value_bet.value_percentage:.1%}
• **Confiança:** {value_bet.confidence}

💰 **REASONING:**
{value_bet.reasoning}

🚨 **URGÊNCIA:** {value_bet.urgency.upper()}

⚠️ *Aposte com responsabilidade*
🔄 *Odds podem mudar rapidamente*
        """.strip()
        
        return message
    
    def cleanup_old_notifications(self):
        """Remove notificações antigas para evitar acúmulo"""
        now = datetime.now()
        if now - self.last_cleanup > timedelta(hours=1):
            self.sent_notifications.clear()
            self.last_cleanup = now
            logger.info("🧹 Cache de notificações limpo")

class LiveValueBetMonitor:
    """Monitor de value bets em tempo real"""
    
    def __init__(self, bot_instance, riot_api, prediction_system):
        self.bot = bot_instance
        self.riot_api = riot_api
        self.prediction_system = prediction_system
        
        # Inicializar componentes
        self.odds_simulator = OddsSimulator()
        self.value_detector = ValueBetDetector(prediction_system, self.odds_simulator)
        self.notification_system = ValueBetNotificationSystem(bot_instance)
        
        # Estado do monitor
        self.is_running = False
        self.monitor_task = None
        self.stats = {
            'total_bets_detected': 0,
            'total_notifications_sent': 0,
            'uptime_start': None
        }
        
    async def start_monitoring(self):
        """Inicia monitoramento de value bets"""
        if self.is_running:
            logger.warning("⚠️ Monitor já está rodando")
            return
            
        self.is_running = True
        self.stats['uptime_start'] = datetime.now()
        
        logger.info("🔍 Iniciando monitoramento de value bets...")
        
        # Inicializar sistema automaticamente
        try:
            await initialize_value_bet_system(self.bot, self.riot_api, self.prediction_system)
            logger.info("✅ Sistema de Value Betting inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar sistema: {e}")
        
        # Criar task do monitor
        self.monitor_task = asyncio.create_task(self._monitor_cycle())
        
    async def stop_monitoring(self):
        """Para monitoramento"""
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            
    async def _monitor_cycle(self):
        """Ciclo principal de monitoramento"""
        logger.info("🔄 Ciclo de monitoramento iniciado")
        
        while self.is_running:
            try:
                # Buscar partidas ao vivo
                live_matches = await self.riot_api.get_all_live_matches()
                
                if not live_matches:
                    logger.info("📭 Nenhuma partida ao vivo encontrada")
                    await asyncio.sleep(30)
                    continue
                
                logger.info(f"🎮 Analisando {len(live_matches)} partidas ao vivo...")
                
                # Analisar cada partida para value bets
                for match in live_matches:
                    try:
                        value_bets = await self.value_detector.analyze_match_for_value(match)
                        
                        for value_bet in value_bets:
                            await self._process_value_bet(value_bet)
                            
                    except Exception as e:
                        logger.error(f"❌ Erro ao analisar partida {match.get('id', 'unknown')}: {e}")
                
                # Aguardar antes do próximo ciclo
                await asyncio.sleep(120)  # 2 minutos entre verificações
                
            except asyncio.CancelledError:
                logger.info("🛑 Monitor cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Erro no ciclo de monitoramento: {e}")
                await asyncio.sleep(60)  # Aguardar 1 minuto em caso de erro
    
    async def _process_value_bet(self, value_bet: ValueBet):
        """Processa uma value bet detectada"""
        self.stats['total_bets_detected'] += 1
        
        # Log da detecção
        await self._log_value_bet(value_bet)
        
        # Enviar notificação automática
        try:
            await self.notification_system.send_value_bet_alert(value_bet)
            self.stats['total_notifications_sent'] += 1
            logger.info(f"📱 Notificação enviada para value bet: {value_bet.team}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação: {e}")
    
    async def _log_value_bet(self, value_bet: ValueBet):
        """Registra value bet nos logs"""
        log_entry = {
            'timestamp': value_bet.timestamp.isoformat(),
            'match_id': value_bet.match_id,
            'team': value_bet.team,
            'opponent': value_bet.opponent,
            'league': value_bet.league,
            'predicted_probability': value_bet.predicted_probability,
            'current_odds': value_bet.current_odds,
            'value_percentage': value_bet.value_percentage,
            'confidence': value_bet.confidence,
            'reasoning': value_bet.reasoning,
            'match_time': value_bet.match_time,
            'urgency': value_bet.urgency
        }
        
        # Salvar em arquivo de log
        log_file = Path('logs/value_bets.jsonl')
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do monitor"""
        uptime = None
        if self.stats['uptime_start']:
            uptime = (datetime.now() - self.stats['uptime_start']).total_seconds()
            
        return {
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'total_bets_detected': self.stats['total_bets_detected'],
            'total_notifications_sent': self.stats['total_notifications_sent'],
            'subscribers_count': len(self.notification_system.subscribers)
        }

def add_value_bet_commands(bot_instance):
    """Adiciona comandos de value betting ao bot"""
    
    async def subscribe_command(update, context):
        """Comando para se inscrever nas notificações"""
        user_id = update.effective_user.id
        
        # Verificar autorização
        if not bot_instance.is_user_authorized(user_id):
            await update.message.reply_text("🔐 Você não está autorizado a usar este bot.")
            return
            
        # Inscrever usuário
        bot_instance.value_bet_monitor.notification_system.subscribe_user(user_id)
        
        await update.message.reply_text(
            "✅ **Inscrito em Value Betting!**\n\n"
            "Você receberá notificações automáticas quando apostas de valor forem detectadas.\n\n"
            "📊 **Critérios:**\n"
            "• Probabilidade mínima: 55%\n"
            "• Edge mínimo: 15%\n"
            "• Odds mínimas: 1.50\n\n"
            "Use /unsubscribe_vb para cancelar.",
            parse_mode='Markdown'
        )
    
    async def unsubscribe_command(update, context):
        """Comando para cancelar inscrição"""
        user_id = update.effective_user.id
        
        bot_instance.value_bet_monitor.notification_system.unsubscribe_user(user_id)
        
        await update.message.reply_text(
            "❌ **Inscrição cancelada**\n\n"
            "Você não receberá mais notificações de value betting.\n"
            "Use /subscribe_vb para se inscrever novamente.",
            parse_mode='Markdown'
        )
    
    async def value_stats_command(update, context):
        """Comando para ver estatísticas do value betting"""
        user_id = update.effective_user.id
        
        if not bot_instance.is_user_authorized(user_id):
            await update.message.reply_text("🔐 Você não está autorizado a usar este bot.")
            return
            
        stats = bot_instance.value_bet_monitor.get_stats()
        
        uptime_str = "N/A"
        if stats['uptime_seconds']:
            hours = int(stats['uptime_seconds'] // 3600)
            minutes = int((stats['uptime_seconds'] % 3600) // 60)
            uptime_str = f"{hours}h {minutes}m"
        
        text = f"""💰 **Estatísticas Value Betting**

🔄 **Status:** {'🟢 Ativo' if stats['is_running'] else '🔴 Inativo'}
⏰ **Uptime:** {uptime_str}
📊 **Bets detectados:** {stats['total_bets_detected']}
📱 **Notificações enviadas:** {stats['total_notifications_sent']}
👥 **Inscritos:** {stats['subscribers_count']}

⚙️ **Configurações atuais:**
• Verificação a cada 2 minutos
• Probabilidade mínima: 55%
• Edge mínimo: 15%
• Odds mínimas: 1.50"""

        await update.message.reply_text(text, parse_mode='Markdown')
    
    # Registrar comandos no bot
    from telegram.ext import CommandHandler
    
    bot_instance.application.add_handler(CommandHandler("subscribe_vb", subscribe_command))
    bot_instance.application.add_handler(CommandHandler("unsubscribe_vb", unsubscribe_command))
    bot_instance.application.add_handler(CommandHandler("value_stats", value_stats_command))
    
    logger.info("✅ Comandos de value betting adicionados")

async def initialize_value_bet_system(bot_instance, riot_api, prediction_system):
    """Inicializa sistema completo de value betting"""
    try:
        logger.info("🚀 Inicializando sistema de Value Betting...")
        
        # Criar monitor se não existir
        if not hasattr(bot_instance, 'value_bet_monitor'):
            bot_instance.value_bet_monitor = LiveValueBetMonitor(
                bot_instance, riot_api, prediction_system
            )
        
        # Adicionar comandos
        add_value_bet_commands(bot_instance)
        
        # Iniciar monitoramento automático
        await bot_instance.value_bet_monitor.start_monitoring()
        
        logger.info("✅ Sistema de Value Betting inicializado com sucesso!")
        
        # Enviar notificação de inicialização (se houver inscritos)
        if hasattr(bot_instance, 'value_bet_monitor'):
            notification_system = bot_instance.value_bet_monitor.notification_system
            if notification_system.subscribers:
                for user_id in notification_system.subscribers:
                    try:
                        await bot_instance.application.bot.send_message(
                            chat_id=user_id,
                            text="🟢 **Sistema de Value Betting ativado!**\n\nMonitoramento automático iniciado. Você receberá alertas quando apostas de valor forem detectadas.",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"❌ Erro ao notificar usuário {user_id}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar sistema de Value Betting: {e}")
        return False 