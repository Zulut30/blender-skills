# Quickstart — first render in 5 minutes

This guide takes you from a clean machine to a rendered image driven by Claude through Blender MCP. Pure happy path; deeper docs are linked at the end.

## 0. Prerequisites

| Tool | Why |
|---|---|
| [Blender 5.x](https://www.blender.org/download/) | The 3D engine. |
| [Blender MCP addon](https://github.com/lab-blender-org/mcp) | Bridges Blender's Python API to Claude. |
| [Claude Code](https://docs.claude.com/en/docs/claude-code) | The skill is loaded by Claude Code. |
| Python 3.11+ | For the stdlib validator (Blender ships its own Python). |
| (Optional) `ffmpeg` on `PATH` | Only needed for animation render assembly. |

## 1. Clone the skill

```bash
git clone https://github.com/Zulut30/blender-skills.git ~/.claude/skills/blender
```

Windows:

```powershell
git clone https://github.com/Zulut30/blender-skills.git "$env:USERPROFILE\.claude\skills\blender"
```

Claude Code auto-discovers the skill on next launch via the `description` field in `SKILL.md`.

## 2. Sanity check — no Blender yet

From the repo root:

```bash
python tools/validate_skill.py
python tests/test_helper_index.py
```

Both should print `OK` / `passed`. If they don't, your clone is incomplete or your Python is older than 3.11.

## 3. Start Blender + MCP server

1. Open Blender 5.x.
2. Edit → Preferences → Add-ons → enable **Blender MCP**.
3. In a 3D Viewport, press `N` to open the side panel → **MCP** tab → **Start Server**.
4. The status line should say *Running on port 9876*.

Verify the bridge from Claude Code:

```
Use the blender skill. Run a sanity check that returns the Blender version.
```

Claude should call `mcp__Blender__execute_blender_code` with something like:

```python
import bpy
result = {"version": list(bpy.app.version)}
```

and return `[5, 1, 1]` (or your version).

If Claude reports `Cannot connect to Blender at localhost:9876`, the server is not actually listening — see [troubleshooting.md](troubleshooting.md).

## 4. First scene — primitives + render

Ask Claude:

> Build a basic_scene template, add a single cube, render it.

Claude will copy [`templates/basic_scene.py`](../templates/basic_scene.py) into `execute_blender_code`, place a primitive, call `auto_frame` and `render_viewport_to_path`, then read the returned PNG back to verify framing.

Expected outcome: an image saved under your OS temp directory (the path is in the tool result), visible in Claude's chat once read.

## 5. First procedural-material scene

> Use `procedural_stone` and `procedural_slate_tiles` to make a small wall + roof scene. Sunset lighting. Render at 1280x720.

Claude routes through the helper index, picks the right materials, sets up `set_hosek_sky` with a low-elevation sun, frames on the geometry only (not the ground), renders, reads back.

## 6. Optional — first animation

> 3-second turntable around the previous scene, 24 fps.

Claude uses `bird_flight_keyframes` (or `bezier_orbit_keyframes`) for keyframing, renders frames per-call in 16–24-frame chunks, and tells you the output directory. Run `ffmpeg` on the host:

```bash
ffmpeg -framerate 24 -i frame_%04d.png -pix_fmt yuv420p -c:v libx264 -crf 18 out.mp4
```

## What to read next

- [`SKILL.md`](../SKILL.md) — full skill contract Claude follows.
- [`reference/pitfalls.md`](../reference/pitfalls.md) — real failure modes and fixes.
- [`reference/helper-index.md`](../reference/helper-index.md) — every public helper with category, side effects, idempotency.
- [`docs/troubleshooting.md`](troubleshooting.md) — symptom → fix routing.
- [`docs/security.md`](security.md) — what agents are not allowed to do.

## When something breaks

The first thing Claude reads on a failure is `reference/pitfalls.md`. If your symptom is not there and you find a fix, please [open a PR](https://github.com/Zulut30/blender-skills/pulls) — every entry there is a session that didn't fail.
