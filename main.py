from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import ItemEnterEvent, KeywordQueryEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from project_launcher.actions import open_project
from project_launcher.config import build_settings
from project_launcher.detect import IdeDetector
from project_launcher.ide_service import default_option, find_option, order_options
from project_launcher.models import IdeOption, Settings
from project_launcher.selector import ICON, build_picker_items
from project_launcher.search import scan_projects, search_projects
from project_launcher.terminal import TerminalInfo, detect_terminal

logger = logging.getLogger(__name__)

DETECTION_TTL = 60.0


class ProjectsExtension(Extension):
    def __init__(self) -> None:
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())

        self.settings: Optional[Settings] = None
        self.pending_project: Optional[str] = None
        self._raw_options: Optional[tuple[IdeOption, ...]] = None
        self._terminal_info: Optional[TerminalInfo] = None
        self._detection_key: Optional[tuple[object, ...]] = None
        self._detection_time = 0.0

    def get_settings(self) -> Settings:
        if self.settings is None:
            self.settings = build_settings(self.preferences)
        return self.settings

    def invalidate(self) -> None:
        self.settings = None
        self._raw_options = None
        self._terminal_info = None
        self._detection_key = None
        self._detection_time = 0.0

    def _detect(self) -> tuple[tuple[IdeOption, ...], Optional[TerminalInfo]]:
        settings = self.get_settings()
        key: tuple[object, ...] = (settings.custom_ides, settings.terminal_command)
        now = time.monotonic()

        if (
            self._raw_options is not None
            and self._detection_key == key
            and now - self._detection_time < DETECTION_TTL
        ):
            return self._raw_options, self._terminal_info

        terminal_info = detect_terminal(settings.terminal_command)
        try:
            raw_options = IdeDetector().detect(settings.custom_ides, terminal_info)
        except Exception:
            logger.exception("Unexpected error detecting IDEs")
            raw_options = ()

        self._raw_options = raw_options
        self._terminal_info = terminal_info
        self._detection_key = key
        self._detection_time = now
        return raw_options, terminal_info

    def get_options(self) -> tuple[IdeOption, ...]:
        raw_options, _terminal = self._detect()
        return order_options(raw_options, self.get_settings().preferred_ides)

    def get_terminal_info(self) -> Optional[TerminalInfo]:
        _options, terminal_info = self._detect()
        return terminal_info

    def _message_item(self, name: str, description: str) -> ExtensionResultItem:
        action = HideWindowAction()
        return ExtensionResultItem(
            icon=ICON,
            name=name,
            description=description,
            on_enter=action,
            on_alt_enter=action,
        )

    def render_project_list(self, query: str) -> RenderResultListAction:
        settings = self.get_settings()
        if not settings.project_paths:
            return RenderResultListAction(
                [
                    self._message_item(
                        "Configure as pastas de projetos",
                        "Preferências → Extensões → Open With IDE → Pastas de projetos",
                    )
                ]
            )

        projects = scan_projects(settings.project_paths)
        if not projects:
            return RenderResultListAction(
                [
                    self._message_item(
                        "Nenhum projeto encontrado",
                        f"Verifique os caminhos configurados: {', '.join(settings.project_paths)}",
                    )
                ]
            )

        options = self.get_options()
        default = default_option(options)
        results = search_projects(projects, query)

        if not results:
            return RenderResultListAction(
                [
                    self._message_item(
                        "Nenhum projeto correspondente",
                        f'Nenhum projeto encontrado para "{query}"',
                    )
                ]
            )

        items: list[ExtensionResultItem] = []
        for project in results:
            description = project.path
            if default is not None:
                description += (
                    f"  ·  Enter: {default.name}  ·  Alt+Enter: escolher IDE/agente"
                )
                on_enter = ExtensionCustomAction(
                    {"action": "open", "path": project.path, "ide_id": default.id},
                    keep_app_open=False,
                )
            else:
                description += "  ·  Nenhuma IDE/agente instalado"
                on_enter = HideWindowAction()

            items.append(
                ExtensionResultItem(
                    icon=ICON,
                    name=project.name,
                    description=description,
                    on_enter=on_enter,
                    on_alt_enter=ExtensionCustomAction(
                        {"action": "pick", "path": project.path},
                        keep_app_open=True,
                    ),
                )
            )

        return RenderResultListAction(items)

    def render_picker(self, project_path: str) -> RenderResultListAction:
        picker_items = build_picker_items(self.get_options())
        if not picker_items:
            return RenderResultListAction(
                [self._message_item("Nenhuma IDE configurada", "Configure custom_ides nas preferências")]
            )

        items: list[ExtensionResultItem] = []
        for item in picker_items:
            if item.enabled and item.ide_id:
                action = ExtensionCustomAction(
                    {"action": "open", "path": project_path, "ide_id": item.ide_id},
                    keep_app_open=False,
                )
                items.append(
                    ExtensionResultItem(
                        icon=item.icon,
                        name=item.name,
                        description=item.description,
                        on_enter=action,
                        on_alt_enter=action,
                    )
                )
            else:
                items.append(
                    ExtensionResultItem(
                        icon=item.icon,
                        name=item.name,
                        description=item.description,
                        on_enter=None,
                        on_alt_enter=None,
                        highlightable=False,
                    )
                )

        return RenderResultListAction(items)


class KeywordQueryEventListener(EventListener):
    def on_event(self, event: KeywordQueryEvent, extension: ProjectsExtension) -> RenderResultListAction:
        extension.pending_project = None
        return extension.render_project_list(event.get_argument() or "")


class ItemEnterEventListener(EventListener):
    def on_event(self, event: ItemEnterEvent, extension: ProjectsExtension) -> Any:
        data = event.get_data() or {}
        action = data.get("action")
        project_path = data.get("path")

        if action == "pick":
            if not project_path or not os.path.isdir(project_path):
                logger.warning("Project path is not a directory: %s", project_path)
                return HideWindowAction()
            extension.pending_project = project_path
            return extension.render_picker(project_path)

        if action == "open":
            if not project_path or not os.path.isdir(project_path):
                logger.warning("Project path is not a directory: %s", project_path)
                return HideWindowAction()

            option = find_option(extension.get_options(), data.get("ide_id"))
            if option is None or not option.available:
                logger.warning("Invalid or unavailable IDE selection: %s", data.get("ide_id"))
                return HideWindowAction()

            open_project(option, project_path, extension.get_terminal_info())
            extension.pending_project = None
            return HideWindowAction()

        return HideWindowAction()


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event: PreferencesUpdateEvent, extension: ProjectsExtension) -> None:
        extension.invalidate()


if __name__ == "__main__":
    ProjectsExtension().run()
