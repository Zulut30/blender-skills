# Changelog

All notable changes to the Blender skill.

## 1.5.1 — Maintenance / structure pass

- Frontmatter normalised; description tightened for accurate skill activation.
- Changelog extracted from `SKILL.md` to `CHANGELOG.md`.
- Added `tools/validate_skill.py`, `tests/test_helper_index.py`, three Blender smoke scripts.
- Added `reference/helper-index.json` and `reference/helper-index.md` auto-derived from `scripts/_helpers.py`.
- Split `reference/api-cheatsheet.md` into per-topic files under `reference/api/`; original file becomes the index.
- Added `docs/setup-blender-mcp.md`, `docs/troubleshooting.md`, `docs/security.md`.
- GitHub Actions workflow for skill validation on every push/PR.
- No public helper signatures changed; no recipes or pitfalls removed.

## 1.5.0 — General-purpose expansion

- Added 22 helpers across 8 new categories (asset import, geometry nodes, vegetation scattering, cloth/soft-surface, interior/room, extended lighting, turntable/product, render output).
- Added three templates (`interior_room`, `turntable`, `landscape`).
- Added "Decision policy" and "Task recipes" sections.
- Added quick symptom→fix table to "When something breaks".
- Added 6 pitfalls (GN via data API, obj importer rename in 3.3+, cloth/scatter timeouts, decimate <0.1 manifold, HDRI Windows path, stale bbox after ops).

## 1.4.0 — Cinematic castle flythrough eval

- 8s mp4, 192 frames, animated gate.
- Added 4 helpers: `set_hosek_sky`, `add_cloud_drifts`, `set_object_origin`, `swing_door`, `bird_flight_keyframes`.
- 5 new pitfalls: (1) ShaderNodeTexSky has no `NISHITA` in 5.1 — use `HOSEK_WILKIE`; (2) Cloud planes need careful positioning to be in FOV; (3) Hinged objects (doors, drawbridges) need `origin_set` to the hinge before keyframing rotation; (4) Sky `sun_direction` + SUN-light `location` must match for visual coherence; (5) Bird-like flight needs ≥12 waypoints with AUTO_CLAMPED handles + roll banking on orbits.

## 1.3.0 — Castle flythrough eval

- 6s mp4, 144 frames @ 24fps.
- Added 4 animation helpers: `set_animation_range`, `keyframe_camera_path`, `render_animation_frames`, `bezier_orbit_keyframes`.
- Three new pitfalls: (1) Blender 5.x slotted-actions API removed `action.fcurves` — must traverse `action.layers[0].strips[0].channelbag(slot).fcurves`; helper now handles both legacy and slotted paths; (2) Bezier overshoot when orbit keyframes are >60° apart — render preview at midpoints to catch this before full render; (3) `bpy.ops.render.render(animation=True)` times out MCP — render per-frame in 20–30-frame chunks via `render_animation_frames`, then ffmpeg.

## 1.2.0 — Courtyard interior eval

- Added 8 helpers: `stone_block_band`, `tower_windows`, `paving_stones`, `add_well`, `add_barrel`, `add_haybale`, `add_torch`, `add_market_stall`.
- Two new pitfalls: (1) huge single scripts (>200 obj) time out the MCP — must chunk by exterior/interior/atmosphere with render preview between; (2) `paving_stones` with `color_jitter>0` creates per-tile material copies → for areas >10×10 m, prefer one big `add_plane` with `procedural_stone(bumpiness=0.6)`.

## 1.1.0 — Gothic-castle eval

- Added 28 helpers: 8 procedural materials (stone, slate tiles, wood, grass, dirt, water, aged metal, canvas flag), 7 gothic geometry primitives (pointed_arch_window, crenellate_line, flying_buttress, chain_between, flag_banner, low_poly_tree, add_gargoyle), 5 atmosphere utilities (filmic, volumetric_fog, camera_dof, sunset_world, eevee_quality).
- Fixed `add_gargoyle` parent-doubling bug.
- Added 3 pitfalls (composite parenting, EEVEE world volume blackout, view_transform 5.x quirk).
- SKILL.md helper index reorganised by category.

## 1.0.1 — Bugfix from gothic-castle eval

- Repeated `auto_frame` calls accumulated `SkillCamera.001/.002/...` whose frusta polluted later `bbox_of` calls.
- Fixed in `frame_camera` (removes prior `SkillCamera*` before creating) and `bbox_of` (mesh-types only).
- New pitfall recorded.

## 1.0.0 — Eval baseline

- 3/3 first-iteration pass.
- Added `add_torus`, `warm_key_light`, `studio_dark_world`, `boolean_difference`.
- Lighting recipes table.
- Strengthened render-path-is-a-hint and apply-scale rules.
- Templates table now lists tweak knobs.
- New pitfall: raw `primitive_*_add` without helpers.

## 0.1.0 — Initial skill

- Helpers, three templates, pitfalls reference, workflow.
