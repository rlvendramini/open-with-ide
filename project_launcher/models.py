from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Project:
    """Uma pasta de projeto encontrada em um dos diretórios-base."""

    name: str
    path: str
    base: str


@dataclass(frozen=True)
class CatalogIde:
    """Definição estática de uma IDE ou agente no catálogo."""

    id: str
    name: str
    kind: str  # "gui" ou "cli"
    commands: tuple[str, ...]
    desktop_ids: tuple[str, ...] = ()
    known_paths: tuple[str, ...] = ()
    args: tuple[str, ...] = ()
    popularity: int = 100


@dataclass(frozen=True)
class CustomIde:
    """IDE/agente configurado pelo usuário."""

    id: str
    name: str
    kind: str  # "gui" ou "cli"
    command: tuple[str, ...]
    source: str = "custom"


@dataclass(frozen=True)
class IdeOption:
    """Uma opção concreta exibida no seletor."""

    id: str
    name: str
    kind: str
    command: Optional[tuple[str, ...]]
    installed: bool
    blocked_reason: Optional[str]  # "not_installed" ou "no_terminal"
    source: str
    popularity: int
    is_default: bool = False

    @property
    def available(self) -> bool:
        """True quando a opção pode ser realmente usada."""
        return self.installed and self.blocked_reason is None


@dataclass(frozen=True)
class Settings:
    """Preferências já normalizadas."""

    project_paths: tuple[str, ...]
    preferred_ides: tuple[str, ...]
    custom_ides: tuple[CustomIde, ...]
    terminal_command: Optional[tuple[str, ...]]
