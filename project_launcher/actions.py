from __future__ import annotations

import logging
import subprocess
from typing import Any, Callable, Optional

from .models import IdeOption
from .terminal import TerminalInfo

logger = logging.getLogger(__name__)

PopenLike = Callable[..., Any]


def build_gui_command(option: IdeOption, project_path: str) -> list[str]:
    """Monta o comando de uma IDE GUI, respeitando o placeholder {path}."""
    if not option.command:
        raise ValueError("IDE sem comando configurado")
    parts = list(option.command)
    if any("{path}" in part for part in parts):
        return [part.replace("{path}", project_path) for part in parts]
    return parts + [project_path]


def open_project(
    option: IdeOption,
    project_path: str,
    terminal_info: Optional[TerminalInfo] = None,
    popen: Optional[PopenLike] = None,
) -> bool:
    """Abre o projeto; retorna True quando o processo foi iniciado."""
    if not option.available:
        logger.warning("Refusing to open unavailable option: %s", option.name)
        return False

    command: list[str]
    cwd: Optional[str] = None

    try:
        if option.kind == "cli":
            if terminal_info is None:
                logger.error("No terminal information for CLI agent: %s", option.name)
                return False
            if not option.command:
                logger.error("CLI agent without command: %s", option.name)
                return False
            launch = terminal_info.build(project_path, option.command)
            if launch is None:
                logger.error("No terminal available to launch %s", option.name)
                return False
            command = list(launch.command)
            cwd = launch.cwd
        else:
            command = build_gui_command(option, project_path)

        kwargs: dict[str, Any] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "start_new_session": True,
        }
        if cwd:
            kwargs["cwd"] = cwd

        launcher = popen or subprocess.Popen
        launcher(command, **kwargs)
        logger.info("Opening %s with %s", project_path, option.name)
        return True
    except FileNotFoundError:
        logger.error("Executable not found for %s", option.name)
        return False
    except OSError as exc:
        logger.error("OS error opening %s with %s: %s", project_path, option.name, exc)
        return False
    except Exception as exc:  # pragma: no cover - salvaguarda contra erros inesperados
        logger.exception("Unexpected error opening %s with %s: %s", project_path, option.name, exc)
        return False
