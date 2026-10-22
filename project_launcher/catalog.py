from __future__ import annotations

from dataclasses import replace

from .models import CatalogIde

# Catálogo em ordem de popularidade. Ajuste/estenda esta lista para incluir
# novas IDEs ou agentes; a detecção encontra os comandos correspondentes.
_RAW_CATALOG: tuple[CatalogIde, ...] = (
    CatalogIde(
        id="cursor",
        name="Cursor",
        kind="gui",
        commands=("cursor",),
        desktop_ids=("cursor",),
        known_paths=("~/.local/bin/cursor", "/usr/share/cursor/cursor"),
    ),
    CatalogIde(
        id="vscode",
        name="Visual Studio Code",
        kind="gui",
        commands=("code", "code-insiders"),
        desktop_ids=("code", "code-insiders", "visual-studio-code"),
    ),
    CatalogIde(
        id="zed",
        name="Zed",
        kind="gui",
        commands=("zed",),
        desktop_ids=("dev.zed.Zed", "zed"),
        known_paths=("~/.local/bin/zed", "~/.local/zed.app/bin/zed"),
    ),
    CatalogIde(
        id="vscodium",
        name="VSCodium",
        kind="gui",
        commands=("codium",),
        desktop_ids=("codium", "com.vscodium.codium"),
    ),
    CatalogIde(
        id="windsurf",
        name="Windsurf",
        kind="gui",
        commands=("windsurf",),
        desktop_ids=("windsurf",),
    ),
    CatalogIde(
        id="idea",
        name="IntelliJ IDEA",
        kind="gui",
        commands=("idea", "idea-ultimate", "intellij-idea-ultimate", "intellij-idea-community"),
        desktop_ids=("jetbrains-idea", "jetbrains-idea-ce", "intellij-idea-ultimate", "intellij-idea-community"),
    ),
    CatalogIde(
        id="pycharm",
        name="PyCharm",
        kind="gui",
        commands=("pycharm", "pycharm-professional", "pycharm-community"),
        desktop_ids=("jetbrains-pycharm", "jetbrains-pycharm-ce"),
    ),
    CatalogIde(
        id="webstorm",
        name="WebStorm",
        kind="gui",
        commands=("webstorm",),
        desktop_ids=("jetbrains-webstorm",),
    ),
    CatalogIde(
        id="goland",
        name="GoLand",
        kind="gui",
        commands=("goland",),
        desktop_ids=("jetbrains-goland",),
    ),
    CatalogIde(
        id="clion",
        name="CLion",
        kind="gui",
        commands=("clion",),
        desktop_ids=("jetbrains-clion",),
    ),
    CatalogIde(
        id="rider",
        name="Rider",
        kind="gui",
        commands=("rider",),
        desktop_ids=("jetbrains-rider",),
    ),
    CatalogIde(
        id="phpstorm",
        name="PhpStorm",
        kind="gui",
        commands=("phpstorm",),
        desktop_ids=("jetbrains-phpstorm",),
    ),
    CatalogIde(
        id="rubymine",
        name="RubyMine",
        kind="gui",
        commands=("rubymine",),
        desktop_ids=("jetbrains-rubymine",),
    ),
    CatalogIde(
        id="datagrip",
        name="DataGrip",
        kind="gui",
        commands=("datagrip",),
        desktop_ids=("jetbrains-datagrip",),
    ),
    CatalogIde(
        id="rustrover",
        name="RustRover",
        kind="gui",
        commands=("rustrover",),
        desktop_ids=("jetbrains-rustrover",),
    ),
    CatalogIde(
        id="fleet",
        name="Fleet",
        kind="gui",
        commands=("fleet",),
        desktop_ids=("jetbrains-fleet",),
    ),
    CatalogIde(
        id="android-studio",
        name="Android Studio",
        kind="gui",
        commands=("studio.sh", "android-studio"),
        desktop_ids=("android-studio", "com.google.AndroidStudio"),
        known_paths=("~/android-studio/bin/studio.sh", "/opt/android-studio/bin/studio.sh"),
    ),
    CatalogIde(
        id="sublime",
        name="Sublime Text",
        kind="gui",
        commands=("subl", "sublime_text"),
        desktop_ids=("sublime_text", "sublime-text"),
    ),
    CatalogIde(
        id="kate",
        name="Kate",
        kind="gui",
        commands=("kate",),
        desktop_ids=("org.kde.kate",),
    ),
    CatalogIde(
        id="kdevelop",
        name="KDevelop",
        kind="gui",
        commands=("kdevelop",),
        desktop_ids=("org.kde.kdevelop",),
    ),
    CatalogIde(
        id="geany",
        name="Geany",
        kind="gui",
        commands=("geany",),
        desktop_ids=("geany",),
    ),
    CatalogIde(
        id="emacs",
        name="Emacs",
        kind="gui",
        commands=("emacs",),
        desktop_ids=("emacs",),
    ),
    CatalogIde(
        id="gnome-builder",
        name="GNOME Builder",
        kind="gui",
        commands=("gnome-builder",),
        desktop_ids=("org.gnome.Builder",),
    ),
    CatalogIde(
        id="codex",
        name="Codex CLI",
        kind="cli",
        commands=("codex",),
    ),
    CatalogIde(
        id="claude-code",
        name="Claude Code",
        kind="cli",
        commands=("claude", "claude-code"),
    ),
    CatalogIde(
        id="opencode",
        name="OpenCode",
        kind="cli",
        commands=("opencode",),
    ),
    CatalogIde(
        id="gemini-cli",
        name="Gemini CLI",
        kind="cli",
        commands=("gemini",),
    ),
    CatalogIde(
        id="cursor-agent",
        name="Cursor Agent",
        kind="cli",
        commands=("cursor-agent",),
    ),
    CatalogIde(
        id="aider",
        name="Aider",
        kind="cli",
        commands=("aider",),
    ),
    CatalogIde(
        id="qwen-code",
        name="Qwen Code",
        kind="cli",
        commands=("qwen",),
    ),
    CatalogIde(
        id="goose",
        name="Goose",
        kind="cli",
        commands=("goose",),
    ),
    CatalogIde(
        id="amp",
        name="Amp",
        kind="cli",
        commands=("amp",),
    ),
    CatalogIde(
        id="copilot-cli",
        name="GitHub Copilot CLI",
        kind="cli",
        commands=("copilot",),
    ),
)

CATALOG: tuple[CatalogIde, ...] = tuple(
    replace(entry, popularity=index) for index, entry in enumerate(_RAW_CATALOG, start=1)
)
CATALOG_BY_ID: dict[str, CatalogIde] = {entry.id: entry for entry in CATALOG}
JETBRAINS_IDS = frozenset(
    {
        "idea",
        "pycharm",
        "webstorm",
        "goland",
        "clion",
        "rider",
        "phpstorm",
        "rubymine",
        "datagrip",
        "rustrover",
        "fleet",
    }
)
