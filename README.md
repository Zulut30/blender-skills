# blender-skills

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill that lets Claude drive Blender via the [Blender MCP](https://github.com/lab-blender-org/mcp) addon: build scenes, set up materials and lighting, render stills and animations, and debug `bpy` errors.

[![Skill validation](https://github.com/Zulut30/blender-skills/actions/workflows/skill-validate.yml/badge.svg)](https://github.com/Zulut30/blender-skills/actions/workflows/skill-validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Blender](https://img.shields.io/badge/Blender-5.x-orange.svg)](https://www.blender.org/)

The skill ships:

- A library of locale-safe Blender helpers (primitives, procedural materials, lighting, cameras, animation, imports).
- A documented workflow contract for an LLM driving Blender through MCP — render after every meaningful change, read the PNG back, iterate.
- A pitfall log of real Blender / MCP failure modes with their fixes (`bpy` 5.x slotted-actions API, locale-translated datablock names, EEVEE volume blackouts, MCP timeouts, parent-doubling, and more).
- Stdlib-only validators and CI to keep the skill from drifting.

## What this is — and isn't

It **is** a skill that helps an LLM:

- assemble parametric scenes (architecture, products, landscapes, courtyards) without re-discovering Blender locale issues every time;
- render a still or a 1–10s flythrough animation, chunked so the MCP socket doesn't time out;
- debug a `bpy` traceback by routing through the pitfalls journal first;
- inspect an unfamiliar `.blend` file before editing it.

It **is not** a generic 3D pipeline. It does not (yet) cover rigging, UV unwrapping, texture baking, particle hair, physics simulation, or video editing. Adding those is welcome — see [Contributing](#contributing).

## Install

```bash
git clone https://github.com/Zulut30/blender-skills.git ~/.claude/skills/blender
```

On Windows: `C:\Users\<you>\.claude\skills\blender\`.

Claude Code auto-discovers skills under `~/.claude/skills/` via the `description` field in `SKILL.md`.

**Requires:**

- Blender 5.x with the [Blender MCP](https://github.com/lab-blender-org/mcp) addon enabled and the server started (N-panel → MCP → Start Server).
- (Animation only) `ffmpeg` on `PATH` for assembling rendered frame sequences into `.mp4`.
- Python 3.11+ on the host for validators (Blender ships its own Python).

For a 5-minute path from clone to first render, see [`docs/quickstart.md`](docs/quickstart.md).

## Repository layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Skill instructions Claude reads first (workflow, anti-patterns, recipes). |
| `CHANGELOG.md` | Version history. |
| `scripts/_helpers.py` | Blender Python helpers — see [`reference/helper-index.md`](reference/helper-index.md). |
| `reference/pitfalls.md` | Failure modes with symptom / cause / fix. Pull-request additions welcome. |
| `reference/api-cheatsheet.md` | Index linking to per-topic API reference under [`reference/api/`](reference/api/). |
| `reference/api/*.md` | bpy/bmesh recipes by topic (mesh, modifiers, materials, lighting, camera, render, animation, geometry-nodes, inspection, safe-operators). |
| `reference/helper-index.{json,md}` | Generated catalog of all public helpers with category, side effects, and notes. |
| `templates/` | Copy-paste-ready scenes (`basic_scene`, `product_shot`, `arch_building`, `interior_room`, `turntable`, `landscape`). |
| `docs/quickstart.md` | 5-minute getting started. |
| `docs/setup-blender-mcp.md` | Detailed setup and sanity check. |
| `docs/troubleshooting.md` | Symptom → fix routing. |
| `docs/security.md` | Agent safety rules. |
| `docs/repo-metadata.md` | GitHub description / topics / website fields. |
| `docs/releasing.md` | Release process. |
| `tools/validate_skill.py` | Stdlib-only repo validator. |
| `tests/test_helper_index.py` | Stdlib helper-index test (no `bpy`). |
| `tests/smoke_*.py` | Optional Blender-side smoke scripts. |
| `.github/workflows/skill-validate.yml` | CI: validator + tests on every push/PR. |

## The contract

Claude follows a strict loop on every Blender task:

1. **Inspect** the scene before editing (`get_objects_summary`, `get_blendfile_summary_*`).
2. **Execute** via `mcp__Blender__execute_blender_code`. Scripts:
   - load helpers via `importlib`,
   - cap creates at ≤200 objects per call (longer scripts time out the MCP),
   - end with `result = {...}` for handoff.
3. **Render** with `render_viewport_to_path`. The path argument is a hint — read the actual path returned in `result.filepath`.
4. **Read** the PNG back to verify framing, lighting, clipping.
5. **Iterate** up to 3 times; if still wrong, ask the user.

The full contract — including required-reading rules, decision policy, task recipes, and anti-patterns — is in [`SKILL.md`](SKILL.md).

## Use cases

- **Architectural visualization** — parametric buildings (`templates/arch_building.py`), interiors (`templates/interior_room.py`), exterior with vegetation (`templates/landscape.py`).
- **Product shots** — black studio cyclorama with three-point lighting (`templates/product_shot.py`), 360° turntable animation (`templates/turntable.py`).
- **Cinematic flythroughs** — keyframed camera paths with banking, rendered per-frame and assembled with ffmpeg.
- **Procedural-material scenes** — stone, slate tiles, wood, grass, dirt, water, aged metal, and canvas materials with bump and noise variation.
- **Debugging** — when an MCP-driven `bpy` script fails, the pitfall log routes most failure modes to a documented fix.

## Why pitfalls.md matters

Each entry is a real failure that surfaced during eval, with a concrete fix:

- `KeyError: 'Principled BSDF'` — node names get translated under non-English Blender locales. Find by `n.type` instead.
- `auto_frame` puts the camera 1500 m away — old `SkillCamera.001` frusta poison `bbox_of`. Helper now removes prior cameras.
- Black render after `add_volumetric_fog` — EEVEE world Volume at `density>0.005` swallows light beyond ~80 m.
- `AttributeError: 'Action' object has no attribute 'fcurves'` — Blender 5.x slotted actions; traverse `action.layers[0].strips[0].channelbag(slot).fcurves`.
- Composite-helper parenting doubles child world coords → build children at `(0,0,0)` and translate the root last.
- `bpy.ops.render.render(animation=True)` times out MCP → render per-frame in 16–24-frame chunks, then `ffmpeg`.

When a new failure mode appears, append symptom + cause + fix. The next session inherits the fix for free.

## Validation

```bash
python tools/validate_skill.py
python tests/test_helper_index.py
python -m py_compile tools/validate_skill.py tests/test_helper_index.py
```

The validator checks: SKILL.md frontmatter, name regex, description length, broken markdown links, helper-index ↔ helpers consistency, no hardcoded user-paths, all backticked helper references in SKILL.md/README.md exist, and all JSON files parse.

Optional Blender smoke tests (require Blender on `PATH`):

```bash
blender -b --factory-startup --python tests/smoke_basic_scene.py
blender -b --factory-startup --python tests/smoke_product_shot.py
blender -b --factory-startup --python tests/smoke_animation_chunk.py
```

CI runs the stdlib validators automatically on every push/PR.

## Tested with

- Blender 5.1.1 on Windows, ru_RU locale (`use_translate_new_dataname=True` — even datablock names get translated, which is why every helper sets `obj.name` and `obj.data.name` explicitly).
- Older 4.x: most helpers work; `set_hosek_sky` and the slotted-actions code paths assume 5.x.

## Contributing

Pull requests welcome — especially:

- New entries in `reference/pitfalls.md` (real failures, not theoretical).
- New helpers covering missing categories (rigging, UV, baking, particles, export).
- Fixes when CI catches a regression.

Before opening a PR:

```bash
python tools/validate_skill.py     # must pass
python tests/test_helper_index.py  # must pass
```

If you add a helper, regenerate the index:

```bash
python tools/_gen_helper_index.py
```

## License

MIT — see [`LICENSE`](LICENSE) once present in the repo. Use, modify, distribute freely; no warranty.

## Related

- [Blender MCP addon](https://github.com/lab-blender-org/mcp) — the Blender side of the bridge.
- [Claude Code docs](https://docs.claude.com/en/docs/claude-code) — installing and using skills.
