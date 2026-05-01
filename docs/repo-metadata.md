# Repository metadata for the GitHub UI

This file documents the exact strings to set in the GitHub UI for `Zulut30/blender-skills`. Apply via the gear icon next to **About** on the repo home page.

## Description (Settings → About → Description)

> Claude Code skill that drives Blender via MCP — locale-safe helpers, procedural materials, animation, validators, and a real-failure pitfall log.

(196 chars; GitHub limit is 350. Keep this single-line.)

## Website (Settings → About → Website)

Recommended:

```
https://github.com/Zulut30/blender-skills/blob/main/docs/quickstart.md
```

If the repo later gets a dedicated landing page (GitHub Pages, blog post, demo video), point Website there instead.

## Topics (Settings → About → Topics)

Set 8–15 topics. GitHub topic format: lowercase, hyphen-separated, ≤ 50 chars each.

Recommended set (12):

```
claude-code
claude-skill
blender
blender-mcp
mcp-server
bpy
3d-rendering
3d-modeling
procedural-materials
ai-tools
python
automation
```

Optional additions (if any of these become a focus):

- `agentic-tools` — if positioning the repo broadly as agent infra
- `geometry-nodes` — if adding meaningful GN coverage
- `cinematics` — if camera-animation features become a flagship use case
- `eevee` / `cycles` — if the lighting/rendering helpers grow
- `russian-locale` — niche but accurate; describes one specific pain point the skill solves

Remove any topic that no longer reflects current scope (e.g. drop `automation` if you decide the repo isn't general automation).

## Repository feature flags (Settings → General → Features)

| Setting | Value | Why |
|---|---|---|
| Wikis | Off | Docs live in `docs/`, single source of truth. |
| Issues | On | Needed for pitfall additions and bug reports. |
| Sponsorships | Off (until ready) | — |
| Discussions | Off (until ready) | Reopen if Q&A volume justifies it. |
| Projects | Off | — |

## Branch protection (Settings → Branches → Add rule)

For `main`:

- Require a pull request before merging.
- Require status checks to pass: `validate` (the workflow under `.github/workflows/skill-validate.yml`).
- Require linear history.
- Restrict who can push (only repo admins) — optional.

## Releases

See [`releasing.md`](releasing.md). Each public release should:

- match a `vX.Y.Z` git tag,
- include the relevant `CHANGELOG.md` slice in the release notes body,
- be marked **Latest** by default for the most recent stable.

## Social preview image

Skip until ready. If/when a hero render exists (e.g. the gothic-castle flythrough thumbnail), upload via Settings → Social preview. Recommended size 1280×640.

## License

Set to **MIT** in the GitHub UI (Settings → General → License). Add a `LICENSE` file at the repo root with the MIT text — the README already references it.
