# Profile Assets & Automation

Everything visual on this profile README is generated or automated. This
document explains the design system, how to regenerate the assets, and how
the GitHub Actions workflows work.

## Design system

| Token | Value | Used for |
| --- | --- | --- |
| Background (deep) | `#0A0E1A` | hero header, footer, 3D graph (dark) |
| Panel / charcoal | `#0D1117` | terminal body, analytics backgrounds |
| Border | `#263048` | terminal frame, subtle strokes |
| Electric blue | `#1F6FEB` / `#58A6FF` | accents, prompts, framework badges |
| Restrained violet | `#8B5CF6` / `#A371F7` | accents, data badges, highlights |
| Primary text | `#E6EDF3` | headings inside SVGs |
| Muted text | `#8B949E` / `#6E7681` | secondary labels |

Typography is a system monospace stack (`ui-monospace, SFMono-Regular, Menlo,
Consolas, monospace`) — GitHub renders `<img>` SVGs in an isolated document,
so external web fonts are not an option and system monospace keeps the
terminal aesthetic consistent across platforms.
