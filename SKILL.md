---
name: blender
description: Use this skill for Blender, .blend, bpy, bmesh, geometry nodes, materials, lighting, cameras, animation, rendering, imports/exports, and Blender MCP scene automation/debugging.
version: 1.7.0
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
- The user wants to import an external 3D model (.obj, .fbx, .glb) and prep it.
- The user wants a product/turntable render or a hero hard-surface presentation shot.
- The user wants a furnished interior room or architectural interior.
- The user wants a populated outdoor scene (vegetation: trees, grass, rocks).

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

## Required reading on activation

Before the **first** `execute_blender_code` call in a fresh session, read these
files into context. They contain the failure modes you do not want to
re-discover the hard way:

1. [`reference/pitfalls.md`](reference/pitfalls.md) — full failure log (locale,
   slotted-actions API, EEVEE volume blackouts, MCP timeouts, parent-doubling).
   Index every entry; you will need them when traceback comes back.
2. [`reference/helper-index.md`](reference/helper-index.md) — current public
   helper catalogue with signatures, side effects, idempotency.
3. [`reference/api-cheatsheet.md`](reference/api-cheatsheet.md) — index page
   that links to per-topic recipes under [`reference/api/`](reference/api/).

For specific tasks, also read:

| Task | Required reading |
|---|---|
| Modelling / mesh edits | [`reference/api/mesh-bmesh.md`](reference/api/mesh-bmesh.md), [`reference/api/modifiers.md`](reference/api/modifiers.md) |
| Materials / shaders | [`reference/api/materials.md`](reference/api/materials.md) |
| Lighting / world / sky | [`reference/api/lighting-world.md`](reference/api/lighting-world.md) |
| Camera placement / framing | [`reference/api/camera.md`](reference/api/camera.md) |
| Rendering | [`reference/api/render.md`](reference/api/render.md) |
| Animation / cinematics | [`reference/api/animation.md`](reference/api/animation.md) |
| Inspecting an unfamiliar `.blend` | [`reference/api/inspection.md`](reference/api/inspection.md) |
| Geometry Nodes | [`reference/api/geometry-nodes.md`](reference/api/geometry-nodes.md) |
| Operator-context errors | [`reference/api/safe-operators.md`](reference/api/safe-operators.md) |

For agent safety questions read [`docs/security.md`](docs/security.md).
For setup / install / sanity-check on a fresh machine, read
[`docs/setup-blender-mcp.md`](docs/setup-blender-mcp.md).
For symptom → fix routing read [`docs/troubleshooting.md`](docs/troubleshooting.md).

If you cannot read these files (sandboxed, no FS) you may proceed using only
this `SKILL.md` and the workflow below — but expect to hit pitfalls already
documented in `pitfalls.md`.

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

## Decision policy

When facing a choice — use this.

**Helper vs raw bpy.** Always prefer an existing helper. Only drop to raw `bpy.ops` if no helper covers the case AND `search_api_docs` confirms the call. Never guess API signatures.

**Estimate complexity before you write the script.** Count expected objects:
- ≤80 objects → single execute call is fine.
- 80–200 → one call, but do not also add atmosphere/particles in the same chunk.
- >200 → mandatory chunking. Build geometry → render preview → next chunk.

**When the render looks wrong on the first attempt, check in this order:**
1. Framing — is `auto_frame` called AFTER all geometry? Are composite roots at origin (children at local offsets)?
2. Lighting — world strength bleaching everything? Volume fog density >0.005 with long camera?
3. Materials — nodes found by `.type`? The procedural material applied to the right object?
4. After 3 full fix cycles still wrong → stop, show the last render to the user, ask for direction.

**Split into multiple turns vs do silently.**
- Routine scene building: silent, show result at end.
- Irreversible (overwriting .blend, deleting many objects): announce briefly first.
- Ambiguous intent ("make it look better"): make ONE concrete choice, state it in one sentence, execute.

**Engine.** Always `safe_engine()`. Never hardcode `BLENDER_EEVEE_NEXT` or `CYCLES`. For products / animations with reflections: prefer EEVEE + `enable_eevee_quality()`. For photorealism with no time pressure: Cycles is OK but mention render-time cost.

## Script contract

Every `execute_blender_code` payload follows this shape:

```python
import importlib.util, bpy, math
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    os.path.expanduser("~/.claude/skills/blender/scripts/_helpers.py"))
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

### v1.5.0 additions

- **Asset import:** `import_obj(filepath)`, `import_fbx(filepath)`, `import_glb(filepath)`,
  `normalize_imported(obj, target_size)` (centers + rescales to unit-ish size),
  `cleanup_materials(obj)` (purges duplicate slots, fixes broken texture paths).
- **Geometry nodes (data API):** `gn_scatter_on_surface(target, instance, count, seed)`,
  `gn_array_along_curve(curve, instance, count)`, `gn_random_transform(obj, scale_jitter, rot_jitter)`.
- **Vegetation:** `add_tree_cluster(center, radius, count, seed)`, `scatter_grass_tufts(area_bounds, count≤300, seed)`,
  `scatter_rocks(area_bounds, count, size_range, seed)`.
- **Cloth / soft-surface (sim-free):** `add_curtain(location, w, h, folds)` (shape-key sine wave, no bake),
  `add_rug(location, size_x, size_y, color)` (subdivided plane with vertex jitter for fabric feel).
- **Interior / room:** `build_room_box(w, d, h, wall_color)`, `add_window_cutout(wall, x, z, w, h)`,
  `add_door_frame(wall, x, w, h)`, `add_emissive_plane(location, size, color, strength)`.
- **Lighting presets (extended):** `add_area_light(location, size, energy, color)`,
  `hdri_world(filepath, strength)` (validates `image.has_data`, normalises Windows paths).
- **Turntable / product:** `cyclorama_backdrop(color, size)`, `setup_turntable(subject, frames=120, turns=1)`.
- **Render output:** `decimate_mesh(obj, ratio≥0.1)`, `auto_bevel(obj, width, segments)`,
  `place_on_floor(obj)` (uses evaluated bbox).

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

## Task recipes

Pick the matching recipe as your starting plan.

| Task | Recipe steps |
|---|---|
| Product turntable | `reset_scene()` → `cyclorama_backdrop()` → import / create subject → `setup_turntable()` → `enable_eevee_quality()` → preview frame 1 → `render_animation_frames()` |
| Interior room | `reset_scene()` → `build_room_box()` → `add_window_cutout()` / `add_door_frame()` → furnish → `add_area_light()` + `add_emissive_plane()` → `auto_frame()` → render |
| Exterior building + environment | `reset_scene()` → arch_building template → `scatter_rocks()` → `add_tree_cluster()` → `scatter_grass_tufts()` → `set_hosek_sky()` → `add_volumetric_fog(density≤0.003)` → `auto_frame()` → render |
| Hero prop / hard-surface | `reset_scene()` → `import_obj()` or `import_fbx()` → `normalize_imported()` → `cleanup_materials()` → `auto_bevel()` → `three_point_light()` → `studio_dark_world()` → `add_camera_dof()` → render |
| Cinematic flythrough | `reset_scene()` → build scene in chunks (exterior → preview → interior → preview) → `bird_flight_keyframes()` (≥12 waypoints) → `render_animation_frames()` in 16-frame chunks → assemble with ffmpeg |
| Vegetation landscape | `reset_scene()` → ground plane with `procedural_grass`/`procedural_dirt_path` → `scatter_rocks()` → `add_tree_cluster()` → `scatter_grass_tufts()` → `set_hosek_sky()` → `add_volumetric_fog(density≤0.003)` → render |

**Always render a preview after the first structural chunk.** Do not build the entire scene then discover framing is wrong.

## Templates

When you need a starting scene, load a template instead of building from scratch:

| File | Use case | Tweak knobs |
|---|---|---|
| [templates/basic_scene.py](templates/basic_scene.py) | Empty staging — floor, sky, three-point light. Add subjects, then `auto_frame`. | floor size in `add_plane`, sky color in `set_world_sky`. |
| [templates/product_shot.py](templates/product_shot.py) | Single subject on a black studio cyclorama. | `SUBJECT_LOCATION`; replace the gold cube with your own subject; `key_energy`. |
| [templates/arch_building.py](templates/arch_building.py) | Parametric small building (nave + tower + spire + apse). | Constants at the top: `NAVE_W/L/H`, `ROOF_H`, `TOWER_S/H`, `SPIRE_H`. Pass only the building parts to `auto_frame`, not the ground. |
| [templates/interior_room.py](templates/interior_room.py) | Furnished interior with window, door, table, 2 chairs, rug, area light. | `ROOM_W/D/H`, `WALL_COLOR`. |
| [templates/turntable.py](templates/turntable.py) | Studio cyclorama + placeholder hero subject + 360° camera over 120 frames. | `SUBJECT_LOCATION`, `TURNS`, `FRAME_END`; replace placeholder with your model. |
| [templates/landscape.py](templates/landscape.py) | Outdoor landscape: grass terrain, dirt path, tree clusters, scattered rocks, grass tufts, golden-hour Hosek sky. | `TERRAIN_SIZE`, `TREE_CLUSTERS`, `ROCK_COUNT`, `GRASS_TUFTS` (≤300/call). |

Each template imports helpers via the same `importlib` prelude — copy the file
contents into `execute_blender_code` as-is, then extend.

## When something breaks

1. Read the traceback returned by `execute_blender_code`. Do not retry blindly.
2. Check [reference/pitfalls.md](reference/pitfalls.md) — it indexes the common
   failures (locale, scale, EEVEE samples path, `select_all` in wrong context, etc.).
3. If the symptom is not there, call `search_api_docs` for the API you used.
4. Fix the root cause and re-run. If you find a new failure mode, append it to
   `pitfalls.md` so the next session benefits.

### Quick symptom → fix

| Symptom | First check | Fix |
|---|---|---|
| `KeyError: 'Camera'` or `KeyError: 'Куб'` | Locale translation | Use `bpy.context.scene.camera`; rename every primitive after creation. |
| Black render | World + fog | `add_volumetric_fog` density >0.005 with long camera → reduce density. World strength = 0? |
| Objects at wrong position | Parent doubling | Composite root Empty at origin, children at LOCAL offsets only. |
| `auto_frame` clips | Stale `SkillCamera.001` frusta | Already fixed in helper; if scene is dirty call `reset_scene()` first. |
| MCP timeout mid-script | >200 objects or `animation=True` | Chunk; use `render_animation_frames()` in 16-frame batches. |
| `AttributeError: 'NoneType'` on light/camera | Object not active/selected | `bpy.context.view_layer.objects.active = obj; obj.select_set(True)`. |
| Bezier camera orbit overshoots | Keyframes >60° apart | Add intermediate waypoints; `bird_flight_keyframes` with ≥12 pts. |
| `ShaderNodeTexSky` Nishita error in 5.1 | NISHITA missing | `set_hosek_sky()` (uses HOSEK_WILKIE). |
| `'Action' object has no attribute 'fcurves'` | Blender 5.x slotted actions | Use `keyframe_camera_path()` — handles both legacy + slotted. |
| HDRI silently black on Windows | Backslash path | Use raw-string or forward slashes. `hdri_world()` validates `image.has_data`. |

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

See [CHANGELOG.md](CHANGELOG.md) for version history.
