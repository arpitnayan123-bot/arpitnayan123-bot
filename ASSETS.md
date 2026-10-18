# Profile Assets & Automation

Everything visual on this profile README is generated or automated. This
document explains the design system, how to regenerate the assets, and how
the GitHub Actions workflows work.

## Design system

| Token | Value | Used for |
| --- | --- | --- |
| Background (deep) | `#110D1A` / `#110E19` | hero, footer, glass panels, 3D graph (dark) |
| Panel border | `#2E2740` | terminal frame, glass card borders, analytics card borders |
| Signature gold | `#FFC93C` / `#FFE29A` | accents, typing strip (dark), glass titles, snake, 3D ramp |
| Amber / warm orange | `#FFB454` / `#FF8C42` | wave ribbons, secondary accents, email badge |
| Restrained violet | `#8B5CF6` / `#A78BFA` | contrast accents, IIT Madras badge, Medulla glow |
| Primary text | `#F2E9D8` / `#F5EDDC` | headings inside SVGs, GIF title band |
| Warm muted | `#E8DCC4` / `#9A8C74` | secondary labels, faint text |

Typography is a system monospace stack (`ui-monospace, SFMono-Regular, Menlo,
Consolas, monospace`) — GitHub renders `<img>` SVGs in an isolated document,
so external web fonts are not an option and system monospace keeps the
terminal aesthetic consistent across platforms.

### Glassmorphism recipe

The flagship project cards are frosted-glass panels built entirely in SVG:
a baked aubergine panel, two blurred accent blobs drifting behind it on SMIL
`translate` loops, a white top sheen, a slow diagonal shimmer sweep, a
corner-lit gradient border, a gold gradient title and a translucent status
pill. Each card carries exactly one line of copy — name, category, brief,
tech — so the section reads at a glance and the details stay in the repos.

## Assets

| File | Role |
| --- | --- |
| `assets/hero-aurora.gif` | live gilded aurora hero — gold waves, warm particles, pulsing glow (desktop, 896×260) |
| `assets/hero-aurora-mobile.gif` | compact aurora hero served on narrow screens |
| `assets/typing.svg` | rotating typewriter phrases (SMIL clip reveal, amber in both themes) |
| `assets/terminal.svg` | decorative developer terminal with blinking gold cursor |
| `assets/mantra.svg` | frosted mantra strip — breathing gold gradient text |
| `assets/activity-header.svg` | frosted contribution banner — breathing ramp cells, gold gradient title |
| `assets/project-nexura.svg` | glassmorphism card — Nexura OS (healthcare operating system) |
| `assets/project-rea.svg` | glassmorphism card — REA (AI coding agent, private) |
| `assets/project-medulla.svg` | glassmorphism card — Medulla (medical learning OS) |
| `assets/project-aarogya.svg` | glassmorphism card — Aarogya AI (AI health-intelligence platform) |
| `assets/project-sanket.svg` | glassmorphism card — Sanket (voice to FHIR clinical notes) |
| `assets/project-healthtwin.svg` | glassmorphism card — Personal Health Twin (concept) |
| `assets/project-conclave.svg` | glassmorphism card — Conclave (IIT founder network) |
| `assets/footer-nebula.gif` | closing golden nebula banner — twinkling stars — "Learn. Build. Iterate." |
| `assets/footer-nebula-mobile.gif` | compact nebula footer for narrow screens |
| `assets/divider.svg` | section separator with a slow traveling gold glint |
| `profile-3d-settings.json` | custom gold palette for the 3D contribution graph (`profile-gilded.svg`) |

All custom visuals are self-hosted (no third-party generators), script-free,
and use SMIL animations that render inside GitHub's `<img>` pipeline. Every
animated element keeps full-content initial attributes, so the SVGs degrade
to complete static images if a renderer ignores SMIL.

The header and footer ship in two sizes and are switched with a standard
`<picture>` + `max-width` media query so text stays readable on phones.

The profile deliberately mixes two motion systems: the ambient full-width
visuals (aurora hero, nebula footer) are rendered GIFs — richer layered
motion than SMIL allows — while the text-critical animations (typing,
terminal, divider) stay as vector SMIL SVGs so the words remain pixel-crisp
at any scale.

## Regenerating the assets

```bash
python3 scripts/generate_assets.py   # vector animations + glass cards (requires nothing)
python3 scripts/generate_gifs.py     # rendered GIFs (hero, footer) - requires Pillow
```

The vector generator writes its three animated SVGs, the mantra strip, the activity
banner and the seven glass project cards from the tokens and content lists at the top of
the script — edit `PHRASES` for the typing strip, `TERMINAL_LINES` for the
terminal session and the `PROJECTS` list for the glass cards. The GIF
generator renders at 2x and writes four looping GIFs; edit `NAME`,
`TAGLINE_SEGMENTS` or the `FOOTER_*` lines there. Both scripts share the
same design tokens — keep them in sync, then commit the regenerated files.

## GitHub Actions workflows

| Workflow | What it does | Schedule |
| --- | --- | --- |
| `snake.yml` | renders the gold contribution snake (light + dark) and pushes it to the `output` branch | daily 00:00 UTC |
| `profile-3d.yml` | generates the 3D contribution calendar — standard palettes plus the custom `profile-gilded.svg` from `profile-3d-settings.json` | weekly, Sunday 18:00 UTC |

Both workflows use least-privilege `contents: write` permissions, a
`concurrency` group (so overlapping runs cannot clobber each other), and only
the built-in `GITHUB_TOKEN` — no personal tokens or secrets are required or
stored.

### One-time manual step

The README's 3D section references `profile-gilded.svg`, which appears
after the first workflow run. Trigger it once:

> **Actions → Generate 3D Contribution Graph → Run workflow**

Until then, the section falls back to the standard `profile-season-animate`
render, so the profile never shows a broken image.

## Maintenance notes

- The account **profile bio** is set in GitHub settings (not in this repo);
  keep it aligned with the positioning in this README.
- Third-party analytics (GitHub stats, top languages, streak stats, gruvbox
  summary cards, profile views) are optional enhancements — if any of them
  go down, the rest of the profile is unaffected because every custom visual
  is self-hosted. The trophy service was returning 402 during the gilded
  redesign, so it is deliberately not used.
- Project badges only list technologies that are actually used in the linked
  repositories; update them if the projects change.
