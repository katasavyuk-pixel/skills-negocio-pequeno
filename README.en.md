# Skills for running a small business with Claude (in Spanish)

Six Agent Skills, written in Spanish for small businesses and freelancers in Spain. Each one does a piece of office work and leaves a file behind: what you are owed including the interest the law adds, the week your cash runs short, the quarter's invoices checked before they go to the accountant.

They start with a welcome that asks about the business once, saves the answers, and makes the other skills work with that business's data instead of a generic example.

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

Claude Code:

```
/plugin marketplace add katasavyuk-pixel/skills-negocio-pequeno
/plugin install negocio-pequeno@kata-ivanovych
```

Other agents that read Agent Skills:

```
npx skills add katasavyuk-pixel/skills-negocio-pequeno
```

The Claude app (claude.ai or desktop), no terminal: **Customize > Plugins > Add > Add marketplace**, choose to add from a repository, enter `katasavyuk-pixel/skills-negocio-pequeno`, sync, then add the plugin.

Python 3.9 or later is needed wherever the scripts run.

Every business, person, tax number and account in the worked examples is made up.

## Scope

`reclamar-facturas` and `cerrar-trimestre` apply Spanish law (common tax territory). Every rate and rule carries its article and was read in the consolidated text of the BOE on 13 October 2026. They are a calculation under the rules they quote, not legal or tax advice.

## Status

Version 2.0.1 (2.0 is new; 2.0.1 fixes installing from the Claude app). The scripts are tested on Python 3.9 and 3.13 on every change, each figure against a sum done by hand. Each skill was run end to end by a model that did not know it, on a made-up business. Installed from scratch in Claude Code, with `npx skills add`, and in the Claude app (Customize > Plugins > Add > Add marketplace), where the welcome skill ran in a chat. Not yet tested in real businesses or in Cowork, and the scripts of the other five have not been run inside the Claude app.

Kata Ivanovych, [kata.ianexora.com](https://kata.ianexora.com). [MIT](LICENSE).
