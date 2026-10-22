from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, Iterable, Optional

# Diretórios comuns onde IDEs e agentes CLI costumam ser instalados.
COMMON_BIN_DIRS = (
    "~/.local/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/snap/bin",
    "~/.npm-global/bin",
    "~/.bun/bin",
    "~/.local/share/pnpm",
    "~/.linuxbrew/bin",
    "/home/linuxbrew/.linuxbrew/bin",
    "~/.local/share/JetBrains/Toolbox/scripts",
)


def _is_executable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def candidate_dirs(extra_dirs: Optional[Iterable[str]] = None) -> tuple[str, ...]:
    """Retorna os diretórios de busca, sem duplicatas e na ordem de prioridade."""
    dirs: list[str] = []
    for directory in list(COMMON_BIN_DIRS) + list(extra_dirs or ()):
        expanded = os.path.expandvars(os.path.expanduser(directory))
        if expanded and expanded not in dirs:
            dirs.append(expanded)
    return tuple(dirs)


def find_executable(
    name: str,
    which: Optional[Callable[[str], Optional[str]]] = None,
    extra_dirs: Optional[Iterable[str]] = None,
) -> Optional[str]:
    """Resolve um comando para um caminho executável.

    Aceita tanto nomes simples (``cursor``) quanto caminhos absolutos ou com
    ``~``. O ``which`` é injetável para facilitar os testes.
    """
    if not name:
        return None

    expanded = os.path.expandvars(os.path.expanduser(name))
    if os.sep in expanded:
        return expanded if _is_executable(expanded) else None

    finder = which or shutil.which
    try:
        found = finder(expanded)
    except (OSError, TypeError):
        found = None
    if found and _is_executable(found):
        return found

    for directory in candidate_dirs(extra_dirs):
        candidate = os.path.join(directory, expanded)
        if _is_executable(candidate):
            return candidate
    return None


def home_path(value: str) -> str:
    """Expande ``~`` e variáveis de ambiente."""
    return os.path.expandvars(os.path.expanduser(value))


def real_path(value: str) -> str:
    """Resolve o caminho real, sem exigir que o arquivo exista."""
    return os.path.realpath(home_path(value))


def basename(value: str) -> str:
    """Retorna o basename de um caminho/comando."""
    return Path(home_path(value)).name
