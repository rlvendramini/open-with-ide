# Open With IDE

Extensão para o [Ulauncher](https://ulauncher.io/) que lista e pesquisa pastas de projetos e as abre na IDE ou agente de sua preferência.

## Funcionalidades

- Busca projetos em um ou mais diretórios, com correspondência sem acentos.
- `Enter` abre o projeto na IDE/agente padrão.
- `Alt+Enter` abre o seletor de IDEs e agentes.
- Detecta IDEs GUI e agentes CLI instalados.
- Mostra opções não instaladas como itens bloqueados.
- Ordena as opções pelas IDEs preferidas configuradas.
- Permite adicionar IDEs e agentes personalizados.
- Abre agentes CLI no terminal, na pasta do projeto.

## Requisitos

- Linux.
- Ulauncher 5.16.2 ou superior (API `^2.0.0`).
- Ulauncher 6 beta é suportado em modo de compatibilidade.
- Python 3.10+ (a extensão usa o Python do Ulauncher).
- Nenhuma dependência Python externa.

## Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/rlvendramini/open-with-ide.git
   cd open-with-ide
   ```

2. Crie o link da extensão:

   ```bash
   ln -sfn "$(pwd)" ~/.local/share/ulauncher/extensions/open-with-ide
   ```

3. Reinicie o Ulauncher.

4. Abra **Preferências → Extensões → Open With IDE** e configure as preferências.

## Configuração

### Pastas de projetos

Caminhos separados por vírgula. `~` e variáveis de ambiente são expandidos.

```txt
/home/user/projects,/home/user/work
```

### IDEs preferidas

Lista ordenada separada por vírgula. A primeira opção instalada é a padrão.

```txt
cursor, zed, code
```

### IDEs e agentes personalizados

Separe as entradas por ponto e vírgula no formato `Nome=comando [argumentos]`.

- IDE GUI:

  ```txt
  MeuIDE=/opt/meuide/meuide --new-window
  ```

- Agente CLI que abre no terminal:

  ```txt
  MeuAgente=terminal:meuagente --flag
  ```

- Placeholder opcional para a pasta do projeto:

  ```txt
  MinhaIDE=/opt/minhaide/minhaide --folder={path}
  ```

### Terminal dos agentes CLI

Opcional. Use `{path}` para a pasta do projeto; o comando do agente é anexado ao final.

```txt
gnome-terminal --working-directory={path} --
```

Se ficar vazio, a extensão detecta automaticamente um terminal instalado.

### Palavra-chave

Padrão: `projects`.

## Uso

1. Abra o Ulauncher.
2. Digite `projects` e o nome do projeto.
3. Selecione o projeto e pressione:
   - `Enter` para abrir na IDE/agente padrão;
   - `Alt+Enter` para abrir o seletor.

Itens bloqueados aparecem com cadeado e não podem ser ativados.

### Limitação do Ulauncher

O Ulauncher 5.16.2 trata `Ctrl+Enter` como `Enter` e `Ctrl+Alt+Enter` como `Alt+Enter`. Por isso esta extensão usa:

| Atalho | Ação |
|---|---|
| `Enter` / `Ctrl+Enter` | IDE/agente padrão |
| `Alt+Enter` / `Ctrl+Alt+Enter` | seletor de IDEs/agentes |

## IDEs e agentes detectados

**IDEs GUI:** Cursor, Visual Studio Code, Zed, VSCodium, Windsurf, IntelliJ IDEA, PyCharm, WebStorm, GoLand, CLion, Rider, PhpStorm, RubyMine, DataGrip, RustRover, Fleet, Android Studio, Sublime Text, Kate, KDevelop, Geany, Emacs e GNOME Builder.

**Agentes CLI:** Codex CLI, Claude Code, OpenCode, Gemini CLI, Cursor Agent, Aider, Qwen Code, Goose, Amp e GitHub Copilot CLI.

## Desenvolvimento

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m py_compile main.py project_launcher/*.py
```

## Licença

[MIT](LICENSE)
