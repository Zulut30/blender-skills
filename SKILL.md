---
name: blender
description: Use this skill whenever the user wants to model, light, shade, or render
  anything in Blender via the Blender MCP (tools named `mcp__Blender__*`). Triggers
  on mentions of Blender, .blend, bpy, bmesh, geometry nodes, or Russian/English
  verbs like "смоделируй / отрендери / сделай сцену / материал / шейдер / model /
  render / scene". Also use for debugging bpy errors, adjusting render settings,
  or inspecting an existing .blend file.
version: 1.4.0
---

# Blender skill

You drive Blender through `mcp__Blender__execute_blender_code` and a few read-only
inspection tools. Hold to the workflow below — most failures come from skipping
steps, not from missing knowledge.

## When to use

Use this skill when:
- The user asks for any 3D modelling, scene assembly, materials, lights, or rendering work in Blender.
- The user opens a `.blend` and wants to inspect, modify, or render it.
- A `bpy` error needs debugging.

Do not use it for:
- General 3D / rendering theory questions with no Blender code involved.
- Other DCCs (Maya, Houdini, 3ds Max).

## Available MCP tools (cheat sheet)

| Tool | When |
|---|---|
| `execute_blender_code` | Any change to the scene. Returns whatever you assign to `result`. |
| `render_viewport_to_path` | After every meaningful change. The `output_path` you pass is a HINT — the MCP writes to a temp dir and returns the real path in `result.filepath`. Always `Read` that returned path, not your hint. |
| `get_objects_summary` / `get_object_detail_summary` | Inspect what is in the scene before editing. |
| `get_blendfile_summary_*` | When opening an unfamiliar `.blend` (datablocks, missing files, libraries, paths). |
| `search_api_docs` / `get_python_api_docs` | When you are not sure about a `bpy` symbol. Use it instead of guessing. |
| `search_manual_docs` | For workflow / operator usage explanations. |
| `get_screenshot_of_window_as_image` | When the user asks "what does it look like in the editor" rather than render output. |
| `jump_to_*` | When the user wants to be brought to a specific tab/object in the UI. |

## Mandatory workflow

For every task, follow these steps in order. Do not collapse them.

1. **Inspect** unless the scene is known empty. Call `get_objects_summary` (cheap)
   so you know what already exists. Never assume — locale, prior edits, or linked
   libraries can surprise you.
2. **Plan in one or two sentences** to the user (what you will build/change), then
   execute. Do not ask for confirmation on routine modelling work.
3. **Execute** via `execute_blender_code`. The script must:
   - load helpers (see "Script contract" below);
   - be idempotent — safe to re-run after a fix;
   - end with `result = {...}` containing names of created/modified objects and
     anything you will need next turn (the namespace is gone after the call);
   - **stay under ~150–200 created objects per call**. Bigger sets time out the
     MCP and stall Blender. For a complex scene, build in chunks: exterior →
     render preview → interior → render preview → atmosphere. Large grids
     (paving, fences) split by quadrant.
4. **Render** with `render_viewport_to_path` to a path under the project working
   directory. The MCP returns the *actual* filepath; remember it.
5. **Read** the returned PNG with the `Read` tool to see the result. This is not
   optional — it is your only way to verify framing, lighting, and clipping.
6. **Self-critique the frame.** Ask: is everything in shot? does anything clip?
   does the lighting read? are the materials correct? If no, fix and loop.
7. **Iteration cap: 3.** If after three render+fix loops the image is still wrong,
   stop and ask the user instead of grinding.

## Script contract

Every `execute_blender_code` payload follows this shape:

```python
import importlib.util, bpy, math
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    r"C:\Users\zulut\.claude\skills\blender\scripts\_helpers.py")
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)

# ... your scene code, using H.add_cube / H.mat / H.auto_frame / etc.

result = {"objects": [...], "bbox": [...]}
```

Hard rules:

- **Apply scale on every primitive you set yourself.** Helpers do this. If you
  call raw `bpy.ops.mesh.primitive_*_add` directly and set `obj.scale = ...`,
  follow with `bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)`
  while the object is active and selected. Otherwise modifiers, bbox, and
  `auto_frame` will lie to you.
- **Names always explicit.** UI names get translated under `ru_RU` and friends.
  Never write `bpy.data.objects['Camera']`. Use the python references returned by
  helpers, or look up by the explicit English name you assigned.
- **Find nodes by `type`, not by display name.** `n.type == 'BSDF_PRINCIPLED'`,
  not `nodes['Principled BSDF']`. Helpers do this for you — prefer `H.mat(...)`
  over hand-rolling materials.
- **Apply scale.** After `obj.scale = (...)`, call `bpy.ops.object.transform_apply(scale=True)`
  (helpers do this). Otherwise modifiers and bbox lie to you.
- **Pick the engine via enum.** Use `H.safe_engine()` — `BLENDER_EEVEE_NEXT` does
  not exist on every version (e.g. it is missing on 5.1).
- **No state across calls.** Each `execute_blender_code` is a fresh exec namespace.
  Persist nothing in python — only `bpy.data` survives. Look objects up by name
  in the next call.

When in doubt about an API, call `search_api_docs` rather than guessing.

## Building blocks

Prefer composition of helpers over hand-writing primitives every time. The full
list and signatures live in [scripts/_helpers.py](scripts/_helpers.py). Quick
index:

- Setup: `reset_scene()`, `set_render(...)`, `set_world_sky(...)`, `safe_engine()`.
- Primitives (auto-named, scale-applied, optional material): `add_cube`,
  `add_cyl`, `add_cone`, `add_plane`, `add_torus`, `gable_roof`.
- Materials (flat): `mat(name, color, roughness, metallic, emission=...)`.
- Materials (procedural, with bump/noise — much better visual quality):
  `procedural_stone`, `procedural_slate_tiles`, `procedural_wood`,
  `procedural_grass`, `procedural_dirt_path`, `procedural_water`,
  `procedural_metal_aged`, `procedural_canvas_flag`. Prefer these for hero
  surfaces (stone walls, roofs, ground); flat `mat()` for tiny accent objects.
- Boolean ops: `boolean_difference(target, cutter, apply=True, delete_cutter=True)`.
- Gothic geometry: `pointed_arch_window(name, location, w, h, depth, material, facing, frame_thickness, frame_material)` (real arched mesh + frame),
  `crenellate_line(name_prefix, p0, p1, z_top, ...)` (battlements along arbitrary 2D segment),
  `flying_buttress(name, anchor_low, anchor_high, thickness, material, segments)`,
  `chain_between(name_prefix, p_start, p_end, link_count, ...)`,
  `flag_banner(name, location, width, height, color, pole_height)` → `(pole, banner)`,
  `low_poly_tree(name, location, height, ...)` → root Empty,
  `add_gargoyle(name, location, facing, material, scale)` → root Empty.
- Lighting: `three_point_light(target, key_energy)`, `warm_key_light(target, energy, color)`,
  `studio_dark_world(strength, color)`.
- Animation / cinematic: `set_animation_range(start, end, fps)`,
  `keyframe_camera_path(camera, keyframes, look_at_per_key, lens_per_key, interpolation)`
  (handles Blender 5.x slotted-actions API),
  `bird_flight_keyframes(camera, plan)` — `plan` is `[(frame, loc, look_at, roll_deg), ...]`,
  preferred for cinematic flythroughs (12+ waypoints, automatic banking),
  `bezier_orbit_keyframes(center, radius, height, n_samples, frame_start, frame_end)`,
  `render_animation_frames(output_dir, frame_start, frame_end, ...)` — per-frame
  loop, NOT `animation=True` (times out the MCP). Render in chunks of
  16–24 frames per call (more if scene is light), then assemble with ffmpeg
  on host.
- Sky / clouds: `set_hosek_sky(sun_elev_deg, sun_azim_deg, turbidity, ground_albedo, strength)`
  (Hosek-Wilkie since Nishita is missing in 5.1), `add_cloud_drifts(positions, plane_size, tilt_deg)`
  — scattered emissive+transparent cloud planes for cinematic backdrops.
- Hinged objects: `set_object_origin(obj, world_pos)` (place pivot for hinges),
  `swing_door(obj, hinge_pos, axis, closed_deg, open_deg, swing_in_frame, swing_out_frame, ...)`.

**When animating sun-lit scenes**, set `sky.sun_direction` AND the SUN-light
`location` from the same `(sun_dir × distance)` so highlights and sky align.
See [pitfalls.md](reference/pitfalls.md) for the recipe.
- Atmosphere & color: `set_filmic_high_contrast()` (AgX in 5.x is fine),
  `add_volumetric_fog(density, color, anisotropy)` — keep density ≤ 0.005 with
  cameras farther than 50 m or you'll get a black render,
  `add_camera_dof(target_obj, focus_distance, fstop)`,
  `set_sunset_world(top, bottom, strength)`,
  `enable_eevee_quality()` (SSR / raytracing / 128 samples).

**When you build composite objects with a root Empty parent**, place all child
meshes at LOCAL offsets from (0,0,0) and translate the root at the end. Setting
both child world location AND parent world location doubles the position via
the parent transform — see [pitfalls.md](reference/pitfalls.md).
- Camera: `frame_camera(...)` for explicit placement, `auto_frame(objects, ...)`
  to fit a list of objects to the render aspect — use this last, after geometry.
- Math: `bbox_of(objects)`.

## Lighting recipes

Defaults that read well without fiddling. Pass `color` to a freshly created light's
`color` property, or use `H.warm_key_light` / `H.studio_dark_world`.

| Mood | Key color (RGB) | World | Energy |
|---|---|---|---|
| Neutral daylight | `(1.0, 1.0, 1.0)` | sky `(0.55, 0.75, 0.95)`, strength 1.2 | 4.0 |
| Warm / golden hour | `(1.0, 0.78, 0.55)` | sky `(0.95, 0.7, 0.45)`, strength 1.0 | 5.0 |
| Cool / overcast | `(0.85, 0.9, 1.0)` | sky `(0.6, 0.7, 0.8)`, strength 1.5 | 3.5 |
| Studio dark | `(1.0, 0.95, 0.9)` | dark `(0.02, 0.02, 0.02)`, strength 0.3 | 6.0 |
| Moonlight | `(0.7, 0.8, 1.0)` | sky `(0.05, 0.07, 0.12)`, strength 0.4 | 2.0 |

For metals/jewellery prefer the studio-dark mood — specular highlight reads cleanly
against the dark backdrop.

## Templates

When you need a starting scene, load a template instead of building from scratch:

| File | Use case | Tweak knobs |
|---|---|---|
| [templates/basic_scene.py](templates/basic_scene.py) | Empty staging — floor, sky, three-point light. Add subjects, then `auto_frame`. | floor size in `add_plane`, sky color in `set_world_sky`. |
| [templates/product_shot.py](templates/product_shot.py) | Single subject on a black studio cyclorama. | `SUBJECT_LOCATION`; replace the gold cube with your own subject; `key_energy`. |
| [templates/arch_building.py](templates/arch_building.py) | Parametric small building (nave + tower + spire + apse). | Constants at the top: `NAVE_W/L/H`, `ROOF_H`, `TOWER_S/H`, `SPIRE_H`. Pass only the building parts to `auto_frame`, not the ground. |

Each template imports helpers via the same `importlib` prelude — copy the file
contents into `execute_blender_code` as-is, then extend.

## When something breaks

1. Read the traceback returned by `execute_blender_code`. Do not retry blindly.
2. Check [reference/pitfalls.md](reference/pitfalls.md) — it indexes the common
   failures (locale, scale, EEVEE samples path, `select_all` in wrong context, etc.).
3. If the symptom is not there, call `search_api_docs` for the API you used.
4. Fix the root cause and re-run. If you find a new failure mode, append it to
   `pitfalls.md` so the next session benefits.

## Anti-patterns

- ✗ Calling `render_viewport_to_path` and then telling the user "done" without
  reading the resulting PNG. You did not verify; you guessed.
- ✗ `bpy.data.objects['Camera']` / `nodes['Principled BSDF']`. Locale-fragile.
- ✗ Hardcoding `'BLENDER_EEVEE_NEXT'`. Use `safe_engine()`.
- ✗ Editing geometry with operators that need a specific context (`select_all`,
  `transform_apply`) without ensuring object mode and an active object.
- ✗ Holding python references across `execute_blender_code` calls.
- ✗ Adding emoji or chatty comments inside generated bpy scripts. Keep them
  terse — they are tools, not blog posts.

## Changelog

- 1.4.0 — Cinematic castle flythrough eval (8s mp4, 192 frames, animated gate).
  Added 4 helpers: `set_hosek_sky`, `add_cloud_drifts`, `set_object_origin`,
  `swing_door`, `bird_flight_keyframes`. 5 new pitfalls: (1) ShaderNodeTexSky
  has no `NISHITA` in 5.1 — use `HOSEK_WILKIE`; (2) Cloud planes need careful
  positioning to be in FOV; (3) Hinged objects (doors, drawbridges) need
  `origin_set` to the hinge before keyframing rotation; (4) Sky `sun_direction`
  + SUN-light `location` must match for visual coherence; (5) Bird-like flight
  needs ≥12 waypoints with AUTO_CLAMPED handles + roll banking on orbits.
- 1.3.0 — Castle flythrough eval (6s mp4, 144 frames @ 24fps). Added 4
  animation helpers: `set_animation_range`, `keyframe_camera_path`,
  `render_animation_frames`, `bezier_orbit_keyframes`. Three new pitfalls:
  (1) Blender 5.x slotted-actions API removed `action.fcurves` — must traverse
  `action.layers[0].strips[0].channelbag(slot).fcurves`; helper now handles
  both legacy and slotted paths; (2) Bezier overshoot when orbit keyframes
  are >60° apart — render preview at midpoints to catch this before full
  render; (3) `bpy.ops.render.render(animation=True)` times out MCP — render
  per-frame in 20–30-frame chunks via `render_animation_frames`, then ffmpeg.
- 1.2.0 — Courtyard interior eval. Added 8 helpers: `stone_block_band`,
  `tower_windows`, `paving_stones`, `add_well`, `add_barrel`, `add_haybale`,
  `add_torch`, `add_market_stall`. Two new pitfalls: (1) huge single scripts
  (>200 obj) time out the MCP — must chunk by exterior/interior/atmosphere with
  render preview between; (2) `paving_stones` with `color_jitter>0` creates
  per-tile material copies → for areas >10×10 m, prefer one big `add_plane`
  with `procedural_stone(bumpiness=0.6)`.
- 1.1.0 — Gothic-castle eval. Added 28 helpers: 8 procedural materials (stone,
  slate tiles, wood, grass, dirt, water, aged metal, canvas flag), 7 gothic
  geometry primitives (pointed_arch_window, crenellate_line, flying_buttress,
  chain_between, flag_banner, low_poly_tree, add_gargoyle), 5 atmosphere
  utilities (filmic, volumetric_fog, camera_dof, sunset_world, eevee_quality).
  Fixed `add_gargoyle` parent-doubling bug. Added 3 pitfalls (composite parenting,
  EEVEE world volume blackout, view_transform 5.x quirk). SKILL.md helper index
  reorganised by category.
- 1.0.1 — Bugfix from gothic-castle eval: repeated `auto_frame` calls accumulated
  `SkillCamera.001/.002/...` whose frusta polluted later `bbox_of` calls. Fixed
  in `frame_camera` (removes prior `SkillCamera*` before creating) and `bbox_of`
  (mesh-types only). New pitfall recorded.
- 1.0.0 — eval baseline 3/3 first-iteration pass. Added `add_torus`,
  `warm_key_light`, `studio_dark_world`, `boolean_difference`. Lighting recipes
  table. Strengthened render-path-is-a-hint and apply-scale rules. Templates
  table now lists tweak knobs. New pitfall: raw `primitive_*_add` without helpers.
- 0.1.0 — initial skill: helpers, three templates, pitfalls reference, workflow.
