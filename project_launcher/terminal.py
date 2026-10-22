from __future__ import annotations

import logging
import os
import shlex
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Optional

from .paths import find_executable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TerminalSpec:
    id: str
    names: tuple[str, ...]
    args: tuple[str, ...]


# Templates dos terminais mais comuns. {path} é substituído pela pasta do projeto.
TERMINAL_SPECS: tuple[TerminalSpec, ...] = (
    TerminalSpec("gnome-terminal", ("gnome-terminal",), ("--working-directory={path}", "--")),
    TerminalSpec("konsole", ("konsole",), ("--workdir", "{path}", "-e")),
    TerminalSpec("kitty", ("kitty",), ("--directory", "{path}")),
    TerminalSpec("alacritty", ("alacritty",), ("--working-directory", "{path}", "-e")),
    TerminalSpec("wezterm", ("wezterm",), ("start", "--cwd", "{path}", "--")),
    TerminalSpec("xfce4-terminal", ("xfce4-terminal",), ("--working-directory={path}", "-x")),
    TerminalSpec("foot", ("foot",), ("--working-directory={path}",)),
    TerminalSpec("tilix", ("tilix",), ("--working-directory={path}", "-e")),
    TerminalSpec("xterm", ("xterm",), ("-e",)),
    TerminalSpec("x-terminal-emulator", ("x-terminal-emulator",), ("-e",)),
)


@dataclass(frozen=True)
class TerminalLaunch:
    command: tuple[str, ...]
    cwd: Optional[str]


@dataclass(frozen=True)
class TerminalInfo:
    available: bool
    name: Optional[str]
    base_command: Optional[tuple[str, ...]]
    source: str = "auto"

    def build(self, project_path: str, agent_command: tuple[str, ...]) -> Optional[TerminalLaunch]:
        """Monta o comando do terminal + agente para a pasta do projeto."""
        if not self.available or not self.base_command:
            return None

        base = list(self.base_command)
        has_path_placeholder = any("{path}" in part for part in base)
        base = [part.replace("{path}", project_path) for part in base]
        agent = [part.replace("{path}", project_path) for part in agent_command]
        cwd = None if has_path_placeholder else project_path
        return TerminalLaunch(command=tuple(base + agent), cwd=cwd)


def _spec_for(name: str) -> Optional[TerminalSpec]:
    base = os.path.basename(name)
    for spec in TERMINAL_SPECS:
        if base == spec.id or base in spec.names:
            return spec
    return None


def detect_terminal(
    configured: Optional[tuple[str, ...]] = None,
    which: Optional[Callable[[str], Optional[str]]] = None,
    extra_dirs: Optional[Iterable[str]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> TerminalInfo:
    """Resolve o terminal preferido/configurado ou detecta um instalado."""
    finder = lambda name: find_executable(name, which=which, extra_dirs=extra_dirs)  # noqa: E731

    if configured:
        path = finder(configured[0])
        if path:
            base = (path,) + tuple(configured[1:])
            return TerminalInfo(True, name=os.path.basename(path), base_command=base, source="configured")
        logger.warning(
            "terminal_command configured but not executable: %s; falling back to auto-detection",
            configured[0],
        )

    environment = env if env is not None else os.environ
    raw_terminal = (environment.get("TERMINAL") or "").strip()
    if raw_terminal:
        try:
            parts = shlex.split(raw_terminal)
        except ValueError:
            parts = []
        if parts:
            path = finder(parts[0])
            if path:
                spec = _spec_for(parts[0])
                base = (path,) + ((spec.args if spec else ("-e",)))
                name = spec.id if spec else os.path.basename(path)
                return TerminalInfo(True, name=name, base_command=base, source="env")

    for spec in TERMINAL_SPECS:
        for name in spec.names:
            path = finder(name)
            if path:
                base = (path,) + spec.args
                return TerminalInfo(True, name=spec.id, base_command=base, source="auto")

    return TerminalInfo(False, name=None, base_command=None)
