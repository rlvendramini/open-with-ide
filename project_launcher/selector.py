from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Iterable, Optional

from .models import IdeOption

ICON = "images/icon.png"
ICON_DISABLED = "images/icon-disabled.png"
LOCK_PREFIX = "🔒 "


@dataclass(frozen=True)
class PickerItem:
    name: str
    description: str
    icon: str
    enabled: bool
    ide_id: Optional[str] = None
    kind: str = ""
    is_default: bool = False


def has_available(options: Iterable[IdeOption]) -> bool:
    return any(option.available for option in options)


def _command_text(option: IdeOption) -> str:
    if not option.command:
        return ""
    try:
        return shlex.join(option.command)
    except (TypeError, ValueError):
        return " ".join(option.command)


def _kind_text(option: IdeOption) -> str:
    return "CLI · abre no terminal" if option.kind == "cli" else "GUI"


def _blocked_description(option: IdeOption) -> str:
    if option.blocked_reason == "no_terminal":
        return "Instalado, mas nenhum terminal compatível foi encontrado"
    return "Não instalado · instale para habilitar"


def build_picker_items(options: Iterable[IdeOption]) -> list[PickerItem]:
    """Monta os itens do seletor, incluindo opções bloqueadas."""
    options = tuple(options)
    items: list[PickerItem] = []

    if not has_available(options):
        items.append(
            PickerItem(
                name="Nenhuma IDE/agente instalado",
                description="Instale uma IDE/agente ou configure custom_ides nas preferências",
                icon=ICON,
                enabled=False,
            )
        )

    for option in options:
        if option.available:
            command = _command_text(option)
            description = f"{command} · {_kind_text(option)}" if command else _kind_text(option)
            if option.is_default:
                description = f"IDE padrão · {description}"
            items.append(
                PickerItem(
                    name=option.name,
                    description=description,
                    icon=ICON,
                    enabled=True,
                    ide_id=option.id,
                    kind=option.kind,
                    is_default=option.is_default,
                )
            )
        else:
            items.append(
                PickerItem(
                    name=f"{LOCK_PREFIX}{option.name}",
                    description=_blocked_description(option),
                    icon=ICON_DISABLED,
                    enabled=False,
                    ide_id=None,
                    kind=option.kind,
                    is_default=False,
                )
            )

    return items
