from __future__ import annotations

import logging
import os
from difflib import SequenceMatcher
from typing import Iterable, Optional

from .config import normalize_text
from .models import Project

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 10
FUZZY_THRESHOLD = 0.55


def scan_projects(base_paths: Iterable[str], include_hidden: bool = True) -> tuple[Project, ...]:
    """Lista as pastas de primeiro nível de cada diretório-base."""
    projects: list[Project] = []
    seen: set[str] = set()

    for base_path in base_paths:
        expanded = os.path.expandvars(os.path.expanduser(base_path))
        if not os.path.exists(expanded):
            logger.warning("Project path does not exist: %s", expanded)
            continue
        if not os.path.isdir(expanded):
            logger.warning("Project path is not a directory: %s", expanded)
            continue

        base = os.path.abspath(expanded)
        try:
            entries = list(os.scandir(base))
        except PermissionError:
            logger.error("Permission denied accessing: %s", base)
            continue
        except OSError as exc:
            logger.error("Error scanning %s: %s", base, exc)
            continue

        for entry in entries:
            if not include_hidden and entry.name.startswith("."):
                continue
            try:
                if not entry.is_dir(follow_symlinks=True):
                    continue
            except OSError:
                continue

            path = os.path.abspath(entry.path)
            key = os.path.realpath(path)
            if key in seen:
                continue
            seen.add(key)
            projects.append(Project(name=entry.name, path=path, base=base))

    projects.sort(key=lambda project: (normalize_text(project.name), project.path))
    return tuple(projects)


def _is_subsequence(needle: str, haystack: str) -> bool:
    if not needle:
        return True
    index = 0
    for char in haystack:
        if char == needle[index]:
            index += 1
            if index == len(needle):
                return True
    return False


def _token_score(token: str, name: str) -> Optional[int]:
    if not token:
        return 0
    if token == name:
        return 0
    if name.startswith(token):
        return 10
    words = name.replace("_", " ").replace("-", " ").replace(".", " ").split()
    if any(word.startswith(token) for word in words):
        return 15
    if token in name:
        return 20
    if _is_subsequence(token, name):
        return 30
    ratio = SequenceMatcher(None, token, name).ratio()
    if ratio >= FUZZY_THRESHOLD:
        return 40
    return None


def score_project(project: Project, query: str) -> Optional[int]:
    """Retorna um score menor-melhor, ou None quando não há match."""
    name = normalize_text(project.name)
    tokens = [token for token in normalize_text(query).split() if token]
    if not tokens:
        return 0

    total = 0
    for token in tokens:
        token_score = _token_score(token, name)
        if token_score is None:
            return None
        total += token_score
    return total


def search_projects(
    projects: Iterable[Project],
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> tuple[Project, ...]:
    """Filtra e ordena projetos pela relevância em relação à busca."""
    query = (query or "").strip()
    projects = tuple(projects)
    if not query:
        return projects[:limit]

    scored: list[tuple[int, str, str, Project]] = []
    for project in projects:
        score = score_project(project, query)
        if score is None:
            continue
        scored.append((score, normalize_text(project.name), project.path, project))

    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return tuple(item[3] for item in scored[:limit])
