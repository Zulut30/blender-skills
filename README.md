# Blender Skill for Claude Code

A Claude Code skill that drives Blender via the [Blender MCP](https://github.com/lab-blender-org/mcp) addon to model, light, shade, and render 3D scenes — with battle-tested helpers, pitfalls, and templates.

Built and refined through iterative real-world evals (church → gothic castle → courtyard interior → cinematic flythrough). Every grabla encountered along the way is recorded in `reference/pitfalls.md` so the next session avoids it.

## Install

```bash
git clone https://github.com/Zulut30/blender-skills.git ~/.claude/skills/blender
```

(or on Windows: `C:\Users\<you>\.claude\skills\blender`)

Claude Code auto-discovers skills under `~/.claude/skills/` via the `description` field in `SKILL.md`.

Requires:
- Blender 5.x with the **Blender MCP** addon enabled and server started
- (For animation) `ffmpeg` on PATH for assembling rendered frames into `.mp4`

## What's in the box

| File | Purpose |
|---|---|
| `SKILL.md` | Workflow contract, helper index, anti-patterns. The doc Claude reads first. |
| `scripts/_helpers.py` | ~2200 lines, 44 helpers: primitives, procedural materials, gothic/courtyard geometry, atmosphere, animation. |
| `reference/pitfalls.md` | 28+ documented gotchas — Blender locale, slotted-actions API, EEVEE volume blackouts, `auto_frame` overshoot, MCP timeout, etc. |
| `reference/api-cheatsheet.md` | Compact bpy/bmesh recipes for what helpers don't cover. |
| `templates/` | Ready scenes: `basic_scene.py`, `product_shot.py`, `arch_building.py`. |

## The contract

Claude follows a strict loop on every Blender task:

1. **Inspect** the scene before editing (`get_objects_summary`, `get_blendfile_summary_*`).
2. **Execute** via `mcp__Blender__execute_blender_code`. Scripts must:
   - load helpers via `importlib`,
   - cap creates at ≤200 objects per call (longer scripts time out the MCP),
   - end with `result = {...}` for handoff.
3. **Render** with `render_viewport_to_path`. The path you pass is a hint — read the actual path returned in `result.filepath`.
4. **Read** the PNG to verify framing, lighting, clipping.
5. **Iterate** up to 3 times; if still wrong, ask the user.

## Helper categories

- **Primitives** with auto-naming and applied scale: `add_cube`, `add_cyl`, `add_cone`, `add_plane`, `add_torus`, `gable_roof`.
- **Procedural materials** (Principled BSDF + bump/voronoi): `procedural_stone`, `procedural_slate_tiles`, `procedural_wood`, `procedural_grass`, `procedural_dirt_path`, `procedural_water`, `procedural_metal_aged`, `procedural_canvas_flag`.
- **Gothic geometry**: `pointed_arch_window`, `crenellate_line`, `flying_buttress`, `chain_between`, `flag_banner`, `low_poly_tree`, `add_gargoyle`, `stone_block_band`, `tower_windows`.
- **Courtyard / props**: `paving_stones`, `add_well`, `add_barrel`, `add_haybale`, `add_torch`, `add_market_stall`.
- **Lighting / atmosphere**: `three_point_light`, `warm_key_light`, `studio_dark_world`, `set_hosek_sky`, `add_cloud_drifts`, `add_volumetric_fog` (use sparingly — see pitfall), `add_camera_dof`, `set_filmic_high_contrast`, `set_sunset_world`, `enable_eevee_quality`.
- **Animation / cinematic**: `set_animation_range`, `keyframe_camera_path`, `bird_flight_keyframes` (12-waypoint smooth path with banking), `bezier_orbit_keyframes`, `render_animation_frames` (per-frame, NOT `animation=True` — that times out the MCP), `set_object_origin`, `swing_door`.

## Why pitfalls.md is the most valuable file

Every entry is from a real failure I (Claude) ran into and recovered from. Examples:

- `KeyError 'Principled BSDF'` — node names get translated under non-English Blender locales. Find by `n.type` instead.
- `auto_frame` puts the camera 1500 m away — old `SkillCamera.001` frusta poison `bbox_of`. Helper now removes prior cameras.
- Black render after `add_volumetric_fog` — EEVEE world Volume at `density>0.005` swallows light beyond ~80 m.
- `AttributeError: 'Action' object has no attribute 'fcurves'` — Blender 5.x slotted actions; traverse `action.layers[0].strips[0].channelbag(slot).fcurves`.
- Composite-helper parenting doubles child world coords → build children at `(0,0,0)` and translate the root last.
- `bpy.ops.render.render(animation=True)` times out MCP → render per-frame in 16-24-frame chunks, then `ffmpeg`.

When a session hits a new failure mode, append the symptom + cause + fix here. The next session inherits the fix for free.

## Tested with

Blender 5.1.1, ru_RU locale (with `use_translate_new_dataname=True` — yes, even datablock names get translated, so every helper sets `obj.name` explicitly).

## License

MIT — use, modify, and improve. PRs welcome, especially new pitfalls and helper coverage for material categories the skill doesn't yet handle (cloth, particles, geometry nodes for blocks, etc.).
