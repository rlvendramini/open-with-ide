import logging
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction

# Tentar importar fuzzywuzzy
try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

logger = logging.getLogger(__name__)


class CursorProjectsExtension(Extension):
    def __init__(self):
        super(CursorProjectsExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.projects: List[Dict[str, str]] = []
        
    def load_projects(self):
        """Carrega todos os projetos das pastas configuradas"""
        self.projects = []
        project_paths = self.preferences.get('project_paths', '').strip()
        
        if not project_paths:
            logger.warning("No project paths configured")
            return
        
        # Separar múltiplos caminhos por vírgula
        paths = [p.strip() for p in project_paths.split(',') if p.strip()]
        
        for base_path in paths:
            base_path = os.path.expanduser(base_path)
            if not os.path.exists(base_path):
                logger.warning(f"Path does not exist: {base_path}")
                continue
            
            if not os.path.isdir(base_path):
                logger.warning(f"Path is not a directory: {base_path}")
                continue
            
            try:
                # Listar todas as pastas no diretório base
                for item in os.listdir(base_path):
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path):
                        self.projects.append({
                            'name': item,
                            'path': os.path.abspath(item_path),
                            'base': base_path
                        })
            except PermissionError:
                logger.error(f"Permission denied accessing: {base_path}")
            except Exception as e:
                logger.error(f"Error loading projects from {base_path}: {e}")
        
        logger.info(f"Loaded {len(self.projects)} projects")
    
    def search_projects(self, query: str) -> List[Dict[str, str]]:
        """Busca projetos usando fuzzywuzzy se disponível, senão usa busca simples"""
        if not query:
            return self.projects[:10]  # Retorna os primeiros 10 se não houver query
        
        query_lower = query.lower()
        
        if FUZZYWUZZY_AVAILABLE:
            # Usar fuzzywuzzy para busca fuzzy
            project_names = [p['name'] for p in self.projects]
            matches = process.extract(query, project_names, limit=10, scorer=fuzz.WRatio)
            
            # Filtrar matches com score muito baixo
            filtered_matches = [m for m in matches if m[1] > 40]
            
            # Criar lista de projetos ordenada por relevância
            result = []
            for match_name, score in filtered_matches:
                for project in self.projects:
                    if project['name'] == match_name:
                        result.append(project)
                        break
            
            return result
        else:
            # Busca simples: case-insensitive substring match
            matches = []
            for project in self.projects:
                if query_lower in project['name'].lower():
                    matches.append(project)
            
            # Ordenar: exatas matches primeiro, depois por nome
            matches.sort(key=lambda p: (
                not p['name'].lower().startswith(query_lower),
                p['name'].lower()
            ))
            
            return matches[:10]


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        # Recarregar projetos a cada query (para pegar mudanças no filesystem)
        extension.load_projects()
        
        query = event.get_argument() or ''
        
        if not extension.projects:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='No projects found',
                    description='Configure project paths in extension preferences',
                    on_enter=HideWindowAction()
                )
            ])
        
        projects = extension.search_projects(query)
        
        if not projects:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='No matching projects',
                    description=f'No projects found matching "{query}"',
                    on_enter=HideWindowAction()
                )
            ])
        
        items = []
        for project in projects:
            items.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=project['name'],
                    description=project['path'],
                    on_enter=ExtensionCustomAction(
                        {'action': 'open_project', 'path': project['path']},
                        keep_app_open=False
                    )
                )
            )
        
        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()
        
        if data['action'] == 'open_project':
            project_path = data['path']
            cursor_cmd = extension.preferences.get('cursor_command', '/usr/bin/cursor')
            
            try:
                # Abrir o projeto com o Cursor
                subprocess.Popen(
                    [cursor_cmd, project_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logger.info(f"Opening project: {project_path}")
            except FileNotFoundError:
                logger.error(f"Cursor command not found: {cursor_cmd}")
            except Exception as e:
                logger.error(f"Error opening project: {e}")
        
        return HideWindowAction()


if __name__ == '__main__':
    CursorProjectsExtension().run()
