from __future__ import annotations

import logging
import os
from dataclasses import replace
from typing import Callable, Iterable, Optional

from .config import normalize_text, slugify
from .models import IdeOption
from .paths import basename, find_executable, real_path

logger = logging.getLogger(__name__)


def _command_basenames(option: IdeOption) -> set[str]:
    if not option.command:
        return set()
    return {normalize_text(basename(part)) for part in option.command}


def _matches_token(option: IdeOption, token: str) -> bool:
    normalized = normalize_text(token)
    if not normalized:
        return False
    if normalized in {normalize_text(option.id), normalize_text(option.name)}:
        return True
    if normalized in _command_basenames(option):
        return True
    if os.sep in token and option.command:
        return real_path(token) == real_path(option.command[0])
    return False


def _preferred_id(token: str, used: set[str]) -> str:
    base = f"preferred-{slugify(token)}"
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def resolve_preferred(
    options: tuple[IdeOption, ...],
    tokens: Iterable[str],
    which: Optional[Callable[[str], Optional[str]]] = None,
) -> tuple[list[IdeOption], tuple[IdeOption, ...]]:
    """Resolve a lista de preferidas, criando opções ad-hoc para caminhos.

    Retorna ``(preferidas, opções)``; as opções incluem eventuais entradas
    ad-hoc criadas a partir de caminhos/comandos configurados.
    """
    all_options = list(options)
    preferred: list[IdeOption] = []
    used_ids: set[str] = {option.id for option in all_options}

    for token in tokens:
        token = token.strip()
        if not token:
            continue

        matches = [option for option in all_options if _matches_token(option, token)]
        chosen: Optional[IdeOption] = None
        if matches:
            available = [option for option in matches if option.available]
            chosen = available[0] if available else matches[0]
            if not chosen.available:
                logger.warning("Preferred IDE is not available: %s", token)
        else:
            resolved = find_executable(token, which=which)
            if resolved:
                chosen = IdeOption(
                    id=_preferred_id(token, used_ids),
                    name=basename(resolved),
                    kind="gui",
                    command=(resolved,),
                    installed=True,
                    blocked_reason=None,
                    source="preferred",
                    popularity=999,
                )
                all_options.append(chosen)
            else:
                logger.warning("Preferred IDE not found: %s", token)

        if chosen and chosen.id not in {option.id for option in preferred}:
            preferred.append(chosen)

    return preferred, tuple(all_options)


def order_options(
    options: tuple[IdeOption, ...],
    preferred_tokens: Iterable[str] = (),
    which: Optional[Callable[[str], Optional[str]]] = None,
) -> tuple[IdeOption, ...]:
    """Ordena instaladas primeiro, preferidas no topo e bloqueadas no fim."""
    preferred, all_options = resolve_preferred(options, preferred_tokens, which=which)
    preferred_ids = {option.id for option in preferred}

    available_preferred = [option for option in preferred if option.available]
    available_rest = [
        option
        for option in all_options
        if option.available and option.id not in preferred_ids
    ]
    blocked = [option for option in all_options if not option.available]

    def sort_key(option: IdeOption) -> tuple[int, str, str]:
        return (option.popularity, normalize_text(option.name), option.id)

    ordered = (
        available_preferred
        + sorted(available_rest, key=sort_key)
        + sorted(blocked, key=sort_key)
    )

    default_id = ordered[0].id if ordered and ordered[0].available else None
    return tuple(
        replace(option, is_default=(default_id is not None and option.id == default_id))
        for option in ordered
    )


def default_option(options: Iterable[IdeOption]) -> Optional[IdeOption]:
    """Retorna a opção padrão (ou a primeira disponível)."""
    for option in options:
        if option.is_default and option.available:
            return option
    for option in options:
        if option.available:
            return option
    return None


def find_option(options: Iterable[IdeOption], ide_id: Optional[str]) -> Optional[IdeOption]:
    if not ide_id:
        return None
    for option in options:
        if option.id == ide_id:
            return option
    return None
