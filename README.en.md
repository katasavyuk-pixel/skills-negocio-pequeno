# Skills for running a small business with AI (in Spanish)

Six Agent Skills, written in Spanish for small businesses and freelancers in Spain. Each one does a piece of office work and leaves a file behind: what you are owed including the interest the law adds, the week your cash runs short, the quarter's invoices checked before they go to the accountant.

They start with a welcome that asks about the business once, saves the answers, and makes the other skills work with that business's data instead of a generic example.

They work in the Claude app, Claude Code, Codex, OpenCode and any agent that reads the Agent Skills format: see [Install](#install).

[Versión en español](README.md)

## What is here

| Skill | What it delivers |
| --- | --- |
| `empezar` | The business profile, saved to a file, and which skill to use first. |
| `reclamar-facturas` | A workbook with every overdue invoice, its late-payment interest and the 40 euros per invoice Spanish law adds, plus the draft claim that fits each customer. |
| `prever-caja` | A thirteen-week cash forecast with three scenarios: the week you fall short and the customer you depend on. |
| `cerrar-trimestre` | A workbook with the errors in the quarter's invoices, VAT by rate and the filing dates. |
| `visibilidad-en-ia` | Nine checks of whether an AI assistant can find and read your website, and who has to fix each one. |
| `datos-de-documentos` | A table with the data from your invoices, orders or emails, each value with the fragment of the document it comes from. |

## How they work

1. They read the business profile (`perfil-negocio.md`) that `empezar` creates.
2. The model gathers and explains; a short script does what must not be guessed: sums, interest, validation.
3. They leave a file: an `.xlsx` workbook and a short summary that starts with the answer.
4. They send nothing and file nothing. They leave drafts.

The scripts use the Python standard library only, open no connection (except `visibilidad-en-ia`, which fetches the public pages of the site it is asked to audit) and are checked on every change by `.github/validar.py`.

## Install

The skills are folders in the open Agent Skills format (`SKILL.md`, references, scripts), so any agent that reads that format can use them. Each section below says whether I tested it or follow the agent's documentation.

Python 3.9 or later is needed wherever the scripts run. The `npx` commands also need Node.js.

### The Claude app (claude.ai or desktop), no terminal

**Customize > Plugins > Add > Add marketplace**, choose to add from a repository, enter `katasavyuk-pixel/skills-negocio-pequeno`, sync, then add the plugin. Tested on 13 October 2026.

### Claude Code

```
/plugin marketplace add katasavyuk-pixel/skills-negocio-pequeno
/plugin install negocio-pequeno@kata-ivanovych
```

Tested on 13 October 2026.

### Codex

Codex reads the same marketplace as Claude Code; no extra files:

```
codex plugin marketplace add katasavyuk-pixel/skills-negocio-pequeno
codex plugin add negocio-pequeno@kata-ivanovych
```

Start a new session after installing. Without the marketplace, with the Agent Skills installer (project `.agents/skills/`; with `-g`, `~/.agents/skills/`):

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a codex
```

`visibilidad-en-ia` has to reach the website it audits, and Codex's sandbox has no network by default: for that audit, start Codex with `-c sandbox_workspace_write.network_access=true`.

Tested on 15 October 2026 with Codex CLI 0.162.1: both ways, Codex sees the six skills; with the `npx skills` install, `prever-caja` wrote its workbook from the sample data and `empezar` ran the welcome, wrote the profile and validated it with its script.

### OpenCode

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a opencode
```

Project `.agents/skills/`; with `-g`, `~/.config/opencode/skills/`. Tested on 15 October 2026 with OpenCode 1.18.35: it sees the six skills, and `prever-caja` wrote its workbook from the sample data.

### Antigravity

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a antigravity
```

Project `.agents/skills/`, read by the Antigravity app, IDE and CLI according to its documentation. For all projects, the CLI reads `~/.gemini/antigravity-cli/skills/` (`-a antigravity-cli -g`) and the app and IDE read `~/.gemini/config/skills/` (copy them there). Not tested.

### Gemini CLI

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a gemini-cli
```

Project `.agents/skills/`; with `-g`, `~/.gemini/skills/`. Paths from its documentation; not tested.

### Cursor

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a cursor
```

Project `.agents/skills/`; with `-g`, `~/.cursor/skills/`. Paths from its documentation; not tested.

### GitHub Copilot

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a github-copilot
```

Repository `.agents/skills/`; with `-g`, `~/.copilot/skills/`. According to its documentation, Copilot's cloud agent, the Copilot CLI and agent mode in VS Code and JetBrains read them. Not tested.

### Any other agent that reads Agent Skills

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno -a AGENT-NAME
```

The names `-a` accepts are in the installer's [supported agents](https://github.com/vercel-labs/skills#supported-agents). Or copy each skill's whole folder (for example `skills/prever-caja/`, with everything in it) into your agent's skills folder: each folder is self-contained.

Every business, person, tax number and account in the worked examples is made up.

## Scope

`reclamar-facturas` and `cerrar-trimestre` apply Spanish law (common tax territory). Every rate and rule carries its article and was read in the consolidated text of the BOE on 13 October 2026. They are a calculation under the rules they quote, not legal or tax advice.

## Status

Version 2.1.0 (2.0 is new; 2.0.1 fixes installing from the Claude app; 2.1 documents installing in Codex, OpenCode and other agents that read Agent Skills). The scripts are tested on Python 3.9 and 3.13 on every change, each figure against a sum done by hand. Each skill was run end to end by a model that did not know it, on a made-up business. Installed from scratch in Claude Code, with `npx skills add`, and in the Claude app (Customize > Plugins > Add > Add marketplace), where the welcome skill ran in a chat, on 13 October 2026; and in Codex and OpenCode on 15 October, where `prever-caja` wrote its workbook and, in Codex, `empezar` wrote and validated a profile. Not yet tested in real businesses or in Cowork, the scripts of the other five have not been run inside the Claude app, and Antigravity, Gemini CLI, Cursor and GitHub Copilot are documented, not tested.

Kata Ivanovych, [kata.ianexora.com](https://kata.ianexora.com). [MIT](LICENSE).
