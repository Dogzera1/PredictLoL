"""
Sistema de Análise de Patch Notes - Fase 2
Analisa mudanças de patch e impacto no meta para ajustar predições

Funcionalidades:
- Análise automática de patch notes
- Cálculo de impacto nas forças dos campeões
- Detecção de mudanças no meta
- Ajuste dinâmico do CompositionAnalyzer
"""

from __future__ import annotations

import re
import json
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dataclasses import dataclass

from ..utils.logger_config import get_logger
from ..utils.helpers import get_current_timestamp

logger = get_logger(__name__)


@dataclass
class ChampionChange:
    """Representa uma mudança específica de campeão"""
    champion: str
    ability: str
    description: str
    change_type: str  # buff, nerf, adjustment
    impact_score: float  # 0-10
    patch_version: str


@dataclass
class PatchAnalysis:
    """Resultado da análise de um patch"""
    version: str
    date: str
    champion_changes: Dict[str, Any]
    item_changes: Dict[str, Any]
    meta_impact: Dict[str, float]
    overall_impact: float


class PatchAnalyzer:
    """
    Analisador de Patch Notes com capacidades de:
    - Web scraping de patch notes oficiais
    - Parsing inteligente de mudanças
    - Cálculo de impacto no meta
    - Ajuste de força dos campeões
    """

    def __init__(self):
        """Inicializa o analisador de patches"""
        self.patch_history: Dict[str, Dict] = {}
        self.current_patch: Optional[str] = None
        self.base_url = "https://www.leagueoflegends.com/en-us/news/game-updates/patch-"
        
        # Cache de análises
        self.analysis_cache: Dict[str, PatchAnalysis] = {}
        
        # Pesos para cálculo de impacto
        self.ability_weights = {
            "passive": 1.2,
            "q": 1.0,
            "w": 1.0, 
            "e": 1.0,
            "r": 1.5,  # Ultimate tem mais impacto
            "attack damage": 1.1,
            "health": 0.8,
            "armor": 0.7,
            "magic resist": 0.7,
            "movement speed": 0.6,
            "mana": 0.5
        }
        
        # Padrões de mudanças comuns
        self.change_patterns = [
            r'(Q|W|E|R|Passive).*?(\d+(?:\.\d+)?.*?→.*?\d+(?:\.\d+)?)',
            r'(Attack Damage|Health|Armor|Magic Resist|Movement Speed).*?(\d+(?:\.\d+)?.*?→.*?\d+(?:\.\d+)?)',
            r'(Cooldown|Mana Cost|Duration|Range).*?(\d+(?:\.\d+)?.*?→.*?\d+(?:\.\d+)?)',
            r'(Base|Bonus|Per Level).*?(\d+(?:\.\d+)?.*?→.*?\d+(?:\.\d+)?)'
        ]
        
        logger.info("PatchAnalyzer inicializado com sucesso")

    async def initialize(self) -> bool:
        """Inicializa o analisador carregando dados históricos"""
        try:
            # Carrega histórico de patches
            await self._load_patch_history()
            
            # Detecta patch atual
            await self._detect_current_patch()
            
            logger.info(f"PatchAnalyzer inicializado - Patch atual: {self.current_patch}")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do PatchAnalyzer: {e}")
            return False

    async def analyze_patch(self, patch_version: str, force_refresh: bool = False) -> PatchAnalysis:
        """
        Analisa um patch específico
        
        Args:
            patch_version: Versão do patch (ex: "14.10")
            force_refresh: Força nova análise mesmo se já existe
            
        Returns:
            Análise completa do patch
        """
        try:
            # Verifica cache primeiro
            if not force_refresh and patch_version in self.analysis_cache:
                logger.debug(f"Análise do patch {patch_version} recuperada do cache")
                return self.analysis_cache[patch_version]
            
            logger.info(f"Analisando patch {patch_version}...")
            
            # Download das patch notes
            patch_notes_html = await self._download_patch_notes(patch_version)
            
            if not patch_notes_html:
                raise Exception(f"Não foi possível baixar patch notes para {patch_version}")
            
            # Parse do HTML
            soup = BeautifulSoup(patch_notes_html, 'html.parser')
            
            # Extrai mudanças de campeões
            champion_changes = self._extract_champion_changes(soup)
            
            # Extrai mudanças de itens
            item_changes = self._extract_item_changes(soup)
            
            # Analisa impacto no meta
            meta_impact = self._analyze_meta_impact(champion_changes, item_changes)
            
            # Calcula impacto geral
            overall_impact = self._calculate_overall_impact(champion_changes, item_changes)
            
            # Cria resultado da análise
            analysis = PatchAnalysis(
                version=patch_version,
                date=datetime.now().isoformat(),
                champion_changes=champion_changes,
                item_changes=item_changes,
                meta_impact=meta_impact,
                overall_impact=overall_impact
            )
            
            # Salva no cache e histórico
            self.analysis_cache[patch_version] = analysis
            self.patch_history[patch_version] = {
                "version": patch_version,
                "date": analysis.date,
                "champion_changes": champion_changes,
                "item_changes": item_changes,
                "meta_impact": meta_impact,
                "overall_impact": overall_impact
            }
            
            await self._save_patch_history()
            
            logger.info(f"Patch {patch_version} analisado: {len(champion_changes)} campeões alterados")
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar patch {patch_version}: {e}")
            # Retorna análise vazia em caso de erro
            return PatchAnalysis(
                version=patch_version,
                date=datetime.now().isoformat(),
                champion_changes={},
                item_changes={},
                meta_impact={},
                overall_impact=0.0
            )

    async def _download_patch_notes(self, patch_version: str) -> Optional[str]:
        """Download das patch notes oficiais"""
        try:
            # Formata URL (ex: patch-14-10-notes)
            formatted_version = patch_version.replace(".", "-")
            url = f"{self.base_url}{formatted_version}-notes"
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        logger.debug(f"Patch notes baixadas para {patch_version}")
                        return html
                    else:
                        logger.warning(f"Status {response.status} para patch {patch_version}")
                        return None
                        
        except Exception as e:
            logger.error(f"Erro ao baixar patch notes para {patch_version}: {e}")
            return None

    def _extract_champion_changes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai mudanças específicas de campeões"""
        changes = {}
        
        try:
            # Procura por seções de campeões (múltiplos padrões)
            champion_sections = []
            
            # Padrão 1: Headers com nomes de campeões
            champion_sections.extend(soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'^[A-Z][a-z]+$')))
            
            # Padrão 2: Divs com classes de campeão
            champion_sections.extend(soup.find_all('div', class_=re.compile(r'champion')))
            
            # Padrão 3: Procura por nomes conhecidos de campeões
            known_champions = [
                "Aatrox", "Ahri", "Akali", "Azir", "Caitlyn", "Camille", "Draven", 
                "Fiora", "Gnar", "Graves", "Irelia", "Jax", "Jayce", "Jinx", 
                "Kindred", "LeBlanc", "Leona", "Lucian", "Lulu", "Malphite",
                "Nidalee", "Orianna", "Riven", "Sejuani", "Sett", "Thresh",
                "Tristana", "Vayne", "Viktor", "Yasuo", "Zed", "Aphelios"
            ]
            
            for champion in known_champions:
                champion_elements = soup.find_all(string=re.compile(champion, re.IGNORECASE))
                for element in champion_elements:
                    if hasattr(element, 'parent'):
                        champion_sections.append(element.parent)
            
            # Processa cada seção encontrada
            for section in champion_sections:
                if section and hasattr(section, 'get_text'):
                    section_text = section.get_text().strip()
                    
                    # Extrai nome do campeão
                    champion_match = re.match(r'^([A-Z][a-z]+)', section_text)
                    if champion_match:
                        champion_name = champion_match.group(1).lower()
                        
                        # Encontra mudanças após o nome do campeão
                        changes_section = section.find_next_sibling() or section
                        
                        if changes_section:
                            champion_changes = self._parse_champion_section(changes_section)
                            
                            if champion_changes:
                                changes[champion_name] = {
                                    "changes": champion_changes,
                                    "overall_impact": self._classify_overall_impact(champion_changes),
                                    "strength_change": self._calculate_strength_change(champion_changes),
                                    "change_summary": self._summarize_changes(champion_changes)
                                }
            
            logger.debug(f"Extraídas mudanças de {len(changes)} campeões")
            return changes
            
        except Exception as e:
            logger.error(f"Erro ao extrair mudanças de campeões: {e}")
            return {}

    def _parse_champion_section(self, section) -> List[Dict[str, Any]]:
        """Faz parse de uma seção específica de campeão"""
        changes = []
        
        try:
            if not section or not hasattr(section, 'get_text'):
                return changes
            
            text = section.get_text()
            
            # Procura por padrões de mudanças
            for pattern in self.change_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if len(match) >= 2:
                        ability, change_text = match[0], match[1]
                        
                        change_type = self._classify_change_type(change_text)
                        impact_score = self._calculate_change_impact(ability, change_text, change_type)
                        
                        changes.append({
                            "ability": ability,
                            "description": change_text,
                            "type": change_type,
                            "impact_score": impact_score,
                            "raw_text": f"{ability}: {change_text}"
                        })
            
            # Se não encontrou mudanças específicas, procura por mudanças textuais
            if not changes:
                # Procura por palavras-chave de mudanças
                buff_keywords = ["increased", "improved", "enhanced", "added", "buffed", "stronger"]
                nerf_keywords = ["reduced", "decreased", "removed", "nerfed", "weaker", "lowered"]
                
                text_lower = text.lower()
                
                for keyword in buff_keywords:
                    if keyword in text_lower:
                        changes.append({
                            "ability": "general",
                            "description": f"General buff detected: {keyword}",
                            "type": "buff",
                            "impact_score": 5.0,
                            "raw_text": text[:100] + "..."
                        })
                        break
                
                for keyword in nerf_keywords:
                    if keyword in text_lower:
                        changes.append({
                            "ability": "general",
                            "description": f"General nerf detected: {keyword}",
                            "type": "nerf", 
                            "impact_score": 5.0,
                            "raw_text": text[:100] + "..."
                        })
                        break
            
            return changes
            
        except Exception as e:
            logger.error(f"Erro ao fazer parse da seção: {e}")
            return []

    def _classify_change_type(self, change_text: str) -> str:
        """Classifica se é buff, nerf ou ajuste"""
        try:
            # Extrai números antes e depois da seta
            numbers = re.findall(r'\d+(?:\.\d+)?', change_text)
            
            if len(numbers) >= 2:
                before = float(numbers[0])
                after = float(numbers[-1])
                
                # Tolerância para micro-ajustes
                if abs(after - before) / max(before, 1) < 0.05:
                    return "adjustment"
                elif after > before:
                    return "buff"
                elif after < before:
                    return "nerf"
            
            # Fallback para análise textual
            buff_keywords = ["increased", "improved", "enhanced", "added", "buffed", "higher", "more"]
            nerf_keywords = ["reduced", "decreased", "removed", "nerfed", "lower", "less", "weaker"]
            
            text_lower = change_text.lower()
            
            buff_count = sum(1 for keyword in buff_keywords if keyword in text_lower)
            nerf_count = sum(1 for keyword in nerf_keywords if keyword in text_lower)
            
            if buff_count > nerf_count:
                return "buff"
            elif nerf_count > buff_count:
                return "nerf"
            
            return "adjustment"
            
        except Exception as e:
            logger.error(f"Erro ao classificar mudança: {e}")
            return "adjustment"

    def _calculate_change_impact(self, ability: str, change_text: str, change_type: str) -> float:
        """Calcula impacto numérico da mudança (0-10)"""
        try:
            weight = self.ability_weights.get(ability.lower(), 1.0)
            
            # Extrai magnitude da mudança
            numbers = re.findall(r'\d+(?:\.\d+)?', change_text)
            
            if len(numbers) >= 2:
                before = float(numbers[0])
                after = float(numbers[-1])
                
                if before > 0:
                    percentage_change = abs((after - before) / before)
                    
                    # Converte para impacto (0-10)
                    base_impact = min(10.0, percentage_change * 15)  # 66% change = 10 impact
                    
                    # Aplica peso da habilidade
                    final_impact = base_impact * weight
                    
                    return min(10.0, final_impact)
            
            # Fallback baseado no tipo e contexto
            fallback_impacts = {
                "buff": 6.0,
                "nerf": 6.0,
                "adjustment": 3.0
            }
            
            base_impact = fallback_impacts.get(change_type, 5.0)
            
            # Ajuste baseado em palavras-chave
            high_impact_keywords = ["ultimate", "passive", "major", "significant", "substantial"]
            low_impact_keywords = ["minor", "slight", "small", "negligible"]
            
            text_lower = change_text.lower()
            
            if any(keyword in text_lower for keyword in high_impact_keywords):
                base_impact *= 1.3
            elif any(keyword in text_lower for keyword in low_impact_keywords):
                base_impact *= 0.7
            
            return min(10.0, base_impact * weight)
            
        except Exception as e:
            logger.error(f"Erro ao calcular impacto da mudança: {e}")
            return 5.0

    def _extract_item_changes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai mudanças de itens"""
        changes = {}
        
        try:
            # Procura por seções de itens
            item_sections = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'item', re.IGNORECASE))
            
            for section in item_sections:
                if section:
                    # Processa seção de itens (implementação simplificada)
                    items_text = section.find_next_sibling()
                    if items_text:
                        text = items_text.get_text()
                        
                        # Procura por nomes de itens conhecidos
                        known_items = [
                            "Blade of the Ruined King", "Infinity Edge", "Guardian Angel",
                            "Zhonya's Hourglass", "Rabadon's Deathcap", "Void Staff",
                            "Trinity Force", "Sterak's Gage", "Dead Man's Plate"
                        ]
                        
                        for item in known_items:
                            if item.lower() in text.lower():
                                changes[item.lower().replace(" ", "_").replace("'", "")] = {
                                    "name": item,
                                    "description": "Item change detected",
                                    "impact_score": 4.0
                                }
            
            logger.debug(f"Extraídas mudanças de {len(changes)} itens")
            return changes
            
        except Exception as e:
            logger.error(f"Erro ao extrair mudanças de itens: {e}")
            return {}

    def _analyze_meta_impact(self, champion_changes: Dict, item_changes: Dict) -> Dict[str, float]:
        """Analisa impacto geral no meta"""
        try:
            meta_impact = {
                "assassins": 0.0,
                "mages": 0.0,
                "marksmen": 0.0,
                "tanks": 0.0,
                "fighters": 0.0,
                "supports": 0.0
            }
            
            # Mapeamento de campeões para classes (simplificado)
            champion_classes = {
                "akali": "assassins", "zed": "assassins", "leblanc": "assassins",
                "azir": "mages", "viktor": "mages", "orianna": "mages",
                "jinx": "marksmen", "caitlyn": "marksmen", "vayne": "marksmen",
                "malphite": "tanks", "leona": "tanks", "sejuani": "tanks",
                "irelia": "fighters", "jax": "fighters", "fiora": "fighters",
                "thresh": "supports", "lulu": "supports"
            }
            
            # Calcula impacto por classe
            for champion, changes in champion_changes.items():
                champion_class = champion_classes.get(champion)
                if champion_class:
                    strength_change = changes.get("strength_change", 0.0)
                    meta_impact[champion_class] += strength_change
            
            # Normaliza impactos
            for class_name in meta_impact:
                meta_impact[class_name] = max(-10.0, min(10.0, meta_impact[class_name]))
            
            return meta_impact
            
        except Exception as e:
            logger.error(f"Erro ao analisar impacto no meta: {e}")
            return {"assassins": 0.0, "mages": 0.0, "marksmen": 0.0, "tanks": 0.0, "fighters": 0.0, "supports": 0.0}

    def _classify_overall_impact(self, changes: List[Dict]) -> str:
        """Classifica impacto geral (buff, nerf, neutral)"""
        if not changes:
            return "neutral"
        
        total_impact = sum(
            change["impact_score"] * (1 if change["type"] == "buff" else -1 if change["type"] == "nerf" else 0)
            for change in changes
        )
        
        if total_impact > 2:
            return "buff"
        elif total_impact < -2:
            return "nerf"
        else:
            return "neutral"

    def _calculate_strength_change(self, changes: List[Dict]) -> float:
        """Calcula mudança de força total (-10 a +10)"""
        if not changes:
            return 0.0
        
        total_change = 0.0
        
        for change in changes:
            impact = change["impact_score"]
            
            if change["type"] == "buff":
                total_change += impact
            elif change["type"] == "nerf":
                total_change -= impact
            # ajustes não contam
        
        # Normaliza para -10 a +10
        return max(-10.0, min(10.0, total_change))

    def _summarize_changes(self, changes: List[Dict]) -> str:
        """Cria resumo das mudanças"""
        if not changes:
            return "No changes"
        
        buffs = [c for c in changes if c["type"] == "buff"]
        nerfs = [c for c in changes if c["type"] == "nerf"]
        adjustments = [c for c in changes if c["type"] == "adjustment"]
        
        summary_parts = []
        
        if buffs:
            summary_parts.append(f"{len(buffs)} buffs")
        if nerfs:
            summary_parts.append(f"{len(nerfs)} nerfs")
        if adjustments:
            summary_parts.append(f"{len(adjustments)} adjustments")
        
        return ", ".join(summary_parts)

    def _calculate_overall_impact(self, champion_changes: Dict, item_changes: Dict) -> float:
        """Calcula impacto geral do patch (0-10)"""
        try:
            champion_impact = len(champion_changes) * 0.5  # Cada campeão alterado = 0.5 impact
            item_impact = len(item_changes) * 0.3         # Cada item alterado = 0.3 impact
            
            total_impact = champion_impact + item_impact
            
            return min(10.0, total_impact)
            
        except Exception as e:
            logger.error(f"Erro ao calcular impacto geral: {e}")
            return 0.0

    async def _detect_current_patch(self) -> None:
        """Detecta patch atual da Riot Games"""
        try:
            # Tenta detectar via API ou website da Riot
            # Por agora, usa versão padrão
            self.current_patch = "14.10"
            
            logger.info(f"Patch atual detectado: {self.current_patch}")
            
        except Exception as e:
            logger.error(f"Erro ao detectar patch atual: {e}")
            self.current_patch = "14.10"  # Fallback

    async def _load_patch_history(self) -> None:
        """Carrega histórico de patches do arquivo"""
        try:
            with open("bot/data/patch_history.json", "r", encoding="utf-8") as f:
                self.patch_history = json.load(f)
            
            logger.info(f"Histórico de {len(self.patch_history)} patches carregado")
            
        except FileNotFoundError:
            logger.info("Arquivo de histórico não encontrado, criando novo")
            self.patch_history = {}
        except Exception as e:
            logger.error(f"Erro ao carregar histórico de patches: {e}")
            self.patch_history = {}

    async def _save_patch_history(self) -> None:
        """Salva histórico de patches no arquivo"""
        try:
            import os
            os.makedirs("bot/data", exist_ok=True)
            
            with open("bot/data/patch_history.json", "w", encoding="utf-8") as f:
                json.dump(self.patch_history, f, indent=2, ensure_ascii=False)
            
            logger.debug("Histórico de patches salvo")
            
        except Exception as e:
            logger.error(f"Erro ao salvar histórico de patches: {e}")

    def get_champion_strength_adjustment(self, champion: str, patch_version: str = None) -> float:
        """
        Retorna ajuste de força do campeão baseado no patch
        
        Args:
            champion: Nome do campeão
            patch_version: Versão do patch (usar atual se None)
            
        Returns:
            Ajuste de força (-10.0 a +10.0)
        """
        if not patch_version:
            patch_version = self.current_patch
        
        if not patch_version or patch_version not in self.patch_history:
            return 0.0
        
        patch_data = self.patch_history[patch_version]
        champion_data = patch_data.get("champion_changes", {}).get(champion.lower(), {})
        
        return champion_data.get("strength_change", 0.0)

    def get_meta_strength(self, champion_class: str, patch_version: str = None) -> float:
        """
        Retorna força da classe no meta atual
        
        Args:
            champion_class: Classe do campeão (assassins, mages, etc.)
            patch_version: Versão do patch
            
        Returns:
            Força da classe no meta (-10.0 a +10.0)
        """
        if not patch_version:
            patch_version = self.current_patch
        
        if not patch_version or patch_version not in self.patch_history:
            return 0.0
        
        patch_data = self.patch_history[patch_version]
        meta_impact = patch_data.get("meta_impact", {})
        
        return meta_impact.get(champion_class, 0.0)

    async def update_champion_database_with_patch(self, patch_version: str = None) -> Dict[str, float]:
        """
        Atualiza database de campeões com mudanças do patch
        
        Args:
            patch_version: Versão do patch a aplicar
            
        Returns:
            Dict com ajustes aplicados {champion: adjustment}
        """
        try:
            if not patch_version:
                patch_version = self.current_patch
            
            if not patch_version or patch_version not in self.patch_history:
                logger.warning(f"Patch {patch_version} não encontrado no histórico")
                return {}
            
            patch_data = self.patch_history[patch_version]
            champion_changes = patch_data.get("champion_changes", {})
            
            adjustments = {}
            
            for champion, changes in champion_changes.items():
                strength_change = changes.get("strength_change", 0.0)
                if abs(strength_change) > 0.1:  # Só aplica mudanças significativas
                    adjustments[champion] = strength_change
            
            logger.info(f"Aplicados ajustes de patch para {len(adjustments)} campeões")
            return adjustments
            
        except Exception as e:
            logger.error(f"Erro ao atualizar database com patch: {e}")
            return {}

    def get_analysis_stats(self) -> Dict:
        """Retorna estatísticas do analisador"""
        return {
            "patches_analyzed": len(self.patch_history),
            "current_patch": self.current_patch,
            "cached_analyses": len(self.analysis_cache),
            "last_analysis": max(
                [data.get("date", "") for data in self.patch_history.values()],
                default="Never"
            )
        } 