from __future__ import annotations

import configparser
import logging
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional

from .catalog import CATALOG
from .config import normalize_text
from .models import CatalogIde, CustomIde, IdeOption
from .paths import basename, find_executable, real_path
from .terminal import TerminalInfo

logger = logging.getLogger(__name__)

FIELD_CODE_RE = re.compile(r"%[a-zA-Z]")
TRUTHY = {"1", "true", "yes", "on"}

DEFAULT_DESKTOP_DIRS = (
    "~/.local/share/applications",
    "/usr/local/share/applications",
    "/usr/share/applications",
    "/var/lib/snapd/desktop/applications",
    "~/.local/share/flatpak/exports/share/applications",
    "/var/lib/flatpak/exports/share/applications",
)


@dataclass(frozen=True)
class DesktopEntry:
    desktop_id: str
    name: str
    command: tuple[str, ...]


def _truthy(value: Optional[str]) -> bool:
    return (value or "").strip().casefold() in TRUTHY


def parse_exec_line(
    exec_line: str,
    which: Optional[Callable[[str], Optional[str]]] = None,
    extra_dirs: Optional[Iterable[str]] = None,
) -> Optional[tuple[str, ...]]:
    """Converte a linha ``Exec=`` de um .desktop em uma lista de argumentos."""
    if not exec_line:
        return None

    cleaned = exec_line.replace("%%", "\x00PERCENT\x00")
    cleaned = FIELD_CODE_RE.sub("", cleaned).replace("\x00PERCENT\x00", "%")

    try:
        parts = shlex.split(cleaned)
    except ValueError as exc:
        logger.debug("Invalid Exec line %r: %s", exec_line, exc)
        return None

    if not parts:
        return None

    # Exec=env VAR=valor comando ...
    if os.path.basename(parts[0]) == "env":
        parts = parts[1:]
        while parts and "=" in parts[0] and not parts[0].startswith("/"):
            variable, _, _value = parts[0].partition("=")
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", variable):
                break
            parts = parts[1:]

    if not parts:
        return None

    resolved = find_executable(parts[0], which=which, extra_dirs=extra_dirs)
    if not resolved:
        return None

    parts[0] = resolved
    return tuple(parts)


def parse_desktop_entry(
    path: str,
    which: Optional[Callable[[str], Optional[str]]] = None,
    extra_dirs: Optional[Iterable[str]] = None,
) -> Optional[DesktopEntry]:
    """Lê um arquivo .desktop e retorna os dados úteis, ou None."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str  # type: ignore[assignment]
    try:
        read_files = parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error):
        return None
    if not read_files or "Desktop Entry" not in parser:
        return None

    section = parser["Desktop Entry"]
    if _truthy(section.get("NoDisplay")) or _truthy(section.get("Hidden")):
        return None
    if _truthy(section.get("Terminal")):
        return None

    try_exec = (section.get("TryExec") or "").strip()
    if try_exec:
        try_exec_command = try_exec.split()[0]
        if not find_executable(try_exec_command, which=which, extra_dirs=extra_dirs):
            return None

    command = parse_exec_line(section.get("Exec") or "", which=which, extra_dirs=extra_dirs)
    if not command:
        return None

    return DesktopEntry(
        desktop_id=Path(path).stem,
        name=(section.get("Name") or "").strip(),
        command=command,
    )


class IdeDetector:
    """Detecta quais IDEs/agentes do catálogo estão instalados."""

    def __init__(
        self,
        catalog: tuple[CatalogIde, ...] = CATALOG,
        home: Optional[str] = None,
        desktop_dirs: Optional[Iterable[str]] = None,
        which: Optional[Callable[[str], Optional[str]]] = None,
        extra_dirs: Optional[Iterable[str]] = None,
    ) -> None:
        self.catalog = catalog
        self.home = Path(home).expanduser() if home else Path.home()
        self.desktop_dirs = tuple(
            Path(d).expanduser() for d in (desktop_dirs if desktop_dirs is not None else DEFAULT_DESKTOP_DIRS)
        )
        self.which = which
        self.extra_dirs = tuple(extra_dirs or ())

    def _find(self, name: str) -> Optional[str]:
        if not name:
            return None
        if name.startswith("~/"):
            name = str(self.home / name[2:])
        return find_executable(name, which=self.which, extra_dirs=self.extra_dirs)

    def _desktop_commands(self) -> dict[str, DesktopEntry]:
        by_stem: dict[str, CatalogIde] = {}
        by_name: dict[str, CatalogIde] = {}
        for entry in self.catalog:
            # Agentes CLI não têm entrada .desktop própria; evita casar com
            # aplicativos gráficos de mesmo nome (ex.: OpenCode Desktop).
            if entry.kind != "gui":
                continue
            for desktop_id in entry.desktop_ids:
                by_stem[desktop_id.casefold()] = entry
            by_name[normalize_text(entry.name)] = entry

        found: dict[str, DesktopEntry] = {}
        for directory in self.desktop_dirs:
            if not directory.is_dir():
                continue
            try:
                files = sorted(directory.glob("*.desktop"))
            except OSError:
                continue
            for path in files:
                entry = parse_desktop_entry(
                    str(path),
                    which=self.which,
                    extra_dirs=self.extra_dirs,
                )
                if not entry:
                    continue
                matched = by_stem.get(entry.desktop_id.casefold()) or by_name.get(normalize_text(entry.name))
                if not matched or matched.id in found:
                    continue
                found[matched.id] = entry
        return found

    def _resolve_catalog(
        self,
        entry: CatalogIde,
        desktop_commands: Mapping[str, DesktopEntry],
    ) -> Optional[tuple[tuple[str, ...], str]]:
        for command in entry.commands:
            resolved = self._find(command)
            if resolved:
                return (resolved,) + entry.args, "path"

        for known_path in entry.known_paths:
            resolved = self._find(known_path)
            if resolved:
                return (resolved,) + entry.args, "path"

        desktop_entry = desktop_commands.get(entry.id)
        if desktop_entry:
            return desktop_entry.command + entry.args, "desktop"

        return None

    @staticmethod
    def _identity(command: tuple[str, ...]) -> str:
        return real_path(command[0]) + "\x00" + "\x00".join(command[1:])

    def detect(
        self,
        custom_ides: tuple[CustomIde, ...] = (),
        terminal_info: Optional[TerminalInfo] = None,
    ) -> tuple[IdeOption, ...]:
        desktop_commands = self._desktop_commands()
        terminal_available = bool(terminal_info and terminal_info.available)

        custom_keys: set[str] = set()
        for custom in custom_ides:
            custom_keys.add(custom.id.casefold())
            custom_keys.add(normalize_text(custom.name))
            if custom.command:
                custom_keys.add(basename(custom.command[0]).casefold())

        options: list[IdeOption] = []
        seen: set[str] = set()

        for entry in self.catalog:
            if (
                entry.id.casefold() in custom_keys
                or normalize_text(entry.name) in custom_keys
                or any(basename(command).casefold() in custom_keys for command in entry.commands)
            ):
                continue

            resolved = self._resolve_catalog(entry, desktop_commands)
            if resolved:
                command, source = resolved
                identity = self._identity(command)
                if identity in seen:
                    continue
                seen.add(identity)
                blocked_reason = "no_terminal" if entry.kind == "cli" and not terminal_available else None
                options.append(
                    IdeOption(
                        id=entry.id,
                        name=entry.name,
                        kind=entry.kind,
                        command=command,
                        installed=True,
                        blocked_reason=blocked_reason,
                        source=source,
                        popularity=entry.popularity,
                    )
                )
            else:
                options.append(
                    IdeOption(
                        id=entry.id,
                        name=entry.name,
                        kind=entry.kind,
                        command=None,
                        installed=False,
                        blocked_reason="not_installed",
                        source="catalog",
                        popularity=entry.popularity,
                    )
                )

        for index, custom in enumerate(custom_ides, start=1):
            resolved = self._find(custom.command[0]) if custom.command else None
            if resolved:
                command = (resolved,) + custom.command[1:]
                identity = self._identity(command)
                if identity in seen:
                    continue
                seen.add(identity)
                blocked_reason = "no_terminal" if custom.kind == "cli" and not terminal_available else None
                options.append(
                    IdeOption(
                        id=custom.id,
                        name=custom.name,
                        kind=custom.kind,
                        command=command,
                        installed=True,
                        blocked_reason=blocked_reason,
                        source="custom",
                        popularity=1000 + index,
                    )
                )
            else:
                options.append(
                    IdeOption(
                        id=custom.id,
                        name=custom.name,
                        kind=custom.kind,
                        command=None,
                        installed=False,
                        blocked_reason="not_installed",
                        source="custom",
                        popularity=1000 + index,
                    )
                )

        return tuple(options)
