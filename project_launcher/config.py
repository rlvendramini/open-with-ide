from __future__ import annotations

import logging
import os
import re
import shlex
import unicodedata
from typing import Mapping, Optional

from .models import CustomIde, Settings

logger = logging.getLogger(__name__)

SEPARATOR_PROJECT_PATHS = ","
SEPARATOR_CUSTOM_IDES = ";"
PREFERRED_SEPARATOR = ","
TERMINAL_PREFIX = "terminal:"


def normalize_text(value: str) -> str:
    """Normaliza texto para comparações sem acentos e sem caixa."""
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_accents.casefold().strip()


def slugify(value: str) -> str:
    normalized = normalize_text(value)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "ide"


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""


def parse_project_paths(raw: str) -> tuple[str, ...]:
    """Divide os caminhos por vírgula, expandindo ``~`` e variáveis."""
    paths: list[str] = []
    seen: set[str] = set()
    for item in _string(raw).split(SEPARATOR_PROJECT_PATHS):
        expanded = os.path.expandvars(os.path.expanduser(item.strip()))
        if not expanded:
            continue
        key = os.path.realpath(expanded)
        if key in seen:
            continue
        seen.add(key)
        paths.append(expanded)
    return tuple(paths)


def parse_preferred_ides(raw: str) -> tuple[str, ...]:
    """Lê a ordem das IDEs preferidas, preservando a ordem configurada."""
    tokens: list[str] = []
    seen: set[str] = set()
    for item in _string(raw).split(PREFERRED_SEPARATOR):
        token = item.strip()
        if not token:
            continue
        key = normalize_text(token)
        if key in seen:
            continue
        seen.add(key)
        tokens.append(token)
    return tuple(tokens)


def parse_custom_ides(raw: str) -> tuple[CustomIde, ...]:
    """Lê definições ``Nome=comando`` separadas por ponto e vírgula.

    O prefixo ``terminal:`` marca um agente que deve ser aberto no terminal.
    Entradas inválidas são registradas no log e ignoradas.
    """
    custom: list[CustomIde] = []
    used_ids: set[str] = set()

    for entry in _string(raw).split(SEPARATOR_CUSTOM_IDES):
        entry = entry.strip()
        if not entry:
            continue

        if "=" in entry:
            name, command = entry.split("=", 1)
            name = name.strip()
            command = command.strip()
        else:
            name = ""
            command = entry

        kind = "gui"
        if command.casefold().startswith(TERMINAL_PREFIX):
            kind = "cli"
            command = command[len(TERMINAL_PREFIX) :].strip()

        if not command:
            logger.warning("Custom IDE without command ignored: %s", entry)
            continue

        try:
            parts = shlex.split(command)
        except ValueError as exc:
            logger.warning("Invalid custom IDE %r: %s", entry, exc)
            continue

        if not parts:
            logger.warning("Custom IDE without command ignored: %s", entry)
            continue

        if not name:
            name = os.path.basename(parts[0]) or parts[0]

        base_id = f"custom-{slugify(name)}"
        ide_id = base_id
        suffix = 2
        while ide_id in used_ids:
            ide_id = f"{base_id}-{suffix}"
            suffix += 1
        used_ids.add(ide_id)

        custom.append(
            CustomIde(
                id=ide_id,
                name=name,
                kind=kind,
                command=tuple(parts),
            )
        )

    return tuple(custom)


def parse_terminal_command(raw: str) -> Optional[tuple[str, ...]]:
    """Lê o template opcional do terminal."""
    value = _string(raw).strip()
    if not value:
        return None
    try:
        parts = shlex.split(value)
    except ValueError as exc:
        logger.warning("Invalid terminal_command %r: %s", value, exc)
        return None
    return tuple(parts) if parts else None


def build_settings(preferences: Mapping[str, object]) -> Settings:
    """Converte as preferências cruas do Ulauncher em ``Settings``."""
    return Settings(
        project_paths=parse_project_paths(_string(preferences.get("project_paths", ""))),
        preferred_ides=parse_preferred_ides(_string(preferences.get("preferred_ides", ""))),
        custom_ides=parse_custom_ides(_string(preferences.get("custom_ides", ""))),
        terminal_command=parse_terminal_command(_string(preferences.get("terminal_command", ""))),
    )
