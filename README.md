# hermes-plugin-project-initials

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that starts the automatic title of
every session with the initials of the project it belongs to, so sessions are recognisable at a glance in
the sidebar and in `hermes sessions`:

| Project | Session title Hermes generates | Stored title |
|---|---|---|
| `Billing Service (bs)` | `Fix invoice rounding` | `BS: Fix invoice rounding` |
| `Mobile App (ma)` | `Crash on login` | `MA: Crash on login` |
| *(no project)* | `Explain this stack trace` | unchanged |

The initials are the trailing `(xx)` of the project's name. Nothing else stores them, so renaming a project
in the sidebar changes the prefix of every title written after that.

## Requirements

- Hermes with the `transform_session_title` hook (a value-returning hook fired just before an automatic
  title is stored; proposed in NousResearch/hermes-agent#137481). Without it the plugin loads, registers a
  hook name nothing fires, and does nothing.

## Install

```bash
hermes plugins install https://github.com/bmcfiv/hermes-plugin-project-initials
hermes plugins enable project-initials
```

The plugin is inert until you enable it.

## Settings

Under `plugins.entries.project-initials.settings` in `config.yaml` (or Settings -> Plugins in the desktop app):

| Key | Default | Meaning |
|---|---|---|
| `uppercase` | `true` | Write the prefix as `BS:` instead of `bs:`. |
| `max_words` | `0` | Cut each topic to its first clause and this many words. `0` keeps the title as generated. |
| `drop_project_words` | `false` | Drop the project's own name words from the topic (the prefix says them already). |
| `derive_missing` | `false` | Derive initials for projects whose name has no `(xx)`: first letters of the first two words, or the first two letters of a one-word name, plus a third letter only when two are taken. Never renames the project. |

Defaults leave the generated topic untouched and only add the prefix. Settings are read on every title, so
changes apply without a restart.

## Behaviour

- Only **automatic** titles pass through the hook (instant title, model title, subagent title). A name you
  type with `/title` or in the sidebar is never touched.
- A session outside any project, or in a project with no initials (and `derive_missing` off), keeps its title.
- A prefix that belongs to another known project is replaced, not stacked; running the rule twice is a no-op.
- The session store's `#N` duplicate suffix is dropped before the prefix is applied, and the result is capped
  to the store's title length.
- Any failure is logged at debug level and the title is stored unchanged.

## What it touches (disclosure)

- Hook: `transform_session_title` only. No tools, middleware, environment variables, network access or
  files written. It patches nothing in Hermes.
- Reads the project list and the project that owns the session's working directory through
  `hermes_cli.projects_db` (read-only: `connect_closing`, `list_projects`, `project_for_path`). That module
  is not a documented plugin API yet, so `hermes plugins validate` reports it as a warning. If you rename it
  upstream, the plugin leaves titles unchanged.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License

MIT
