# Troubleshooting

Each entry: symptom -> first thing to check -> fix.

## 1. MCP tool unavailable

Symptom: `Cannot connect to Blender at localhost:9876`.
Check: is Blender running with the MCP addon loaded?
Fix: start the MCP server inside Blender (N-panel in 3D Viewport -> MCP tab -> Start Server). If it still fails, verify the addon is enabled in Preferences -> Add-ons and that port 9876 is not blocked by a firewall or another process.

## 2. MCP timeout mid-script

Symptom: `MCP error -32001: Request timed out`.
Check: how many objects are touched in one call, and is `bpy.ops.render.render(animation=True)` involved?
Fix: chunk scripts to <= 150 objects per `execute_blender_code` call. Never animate-render through MCP; use `render_animation_frames()` per-frame in 16-24 frame batches.

## 3. Render path doesn't match hint

Symptom: file isn't where you asked it to go.
Check: `render_viewport_to_path` writes to a temp dir.
Fix: always read `result.filepath` from the tool response, not the hint you passed in. Copy elsewhere if you need persistence.

## 4. Black render

Symptom: render is fully black or near-black.
Check, in order: (a) volumetric fog density > 0.005 with long camera distance; (b) world strength = 0; (c) camera inside an opaque object; (d) AgX color management on a low-light scene reads near-black.
Fix: disable volume -> check `world.background.strength` -> reposition camera -> try Standard view transform.

## 5. Missing materials/textures after import

Symptom: pink/black surfaces after importing an `.fbx` or `.obj`.
Check: `bpy.data.images` -- any `image.has_data == False`?
Fix: call `cleanup_materials(obj)` to consolidate, then re-link missing image paths. For HDRI specifically: see pitfall #33 (Windows backslash paths).

## 6. Localised object names

Symptom: `KeyError: 'Camera'` on `bpy.data.objects['Camera']`.
Check: locale (e.g. `ru_RU`) renames default datablocks at creation.
Fix: use `bpy.context.scene.camera`, or rename explicitly after creation. The skill's helpers already handle this.

## 7. EEVEE vs Cycles surprises

Symptom: `RuntimeError` setting `scene.render.engine`.
Check: `'BLENDER_EEVEE_NEXT'` does not exist on Blender 5.1; `'CYCLES'` may be unavailable without the addon.
Fix: always use the `safe_engine()` helper. Never hardcode engine identifiers.

## 8. `bpy.ops.import_scene.obj` not found

Symptom: `AttributeError` on `bpy.ops.import_scene.obj`.
Check: Blender version (3.3+).
Fix: replaced by `bpy.ops.wm.obj_import`. Use the `import_obj` helper, which dispatches per-version.

## 9. `auto_frame` puts the camera 1500m away

Symptom: framing zooms out absurdly far.
Check: stale cameras or helpers from a prior call inflated the bbox.
Fix: current helpers ignore non-mesh objects in framing. If the scene is dirty from earlier failed runs, call `reset_scene()` first.

## 10. `'Action' object has no attribute 'fcurves'`

Symptom: AttributeError when keyframing on Blender 5.x.
Check: slotted actions are the new default.
Fix: use `keyframe_camera_path()`, which handles both legacy `action.fcurves` and the slotted layer/strip path.

## 11. Composite-object children at doubled positions

Symptom: child meshes appear at 2x the intended offset.
Check: are children built at world coords AND parented to a root that's also at world coords?
Fix: build children at LOCAL offsets relative to `(0,0,0)`, parent to a root at origin, then translate the root last.

## 12. HDRI silently shows black world

Symptom: world environment renders black despite an HDRI being assigned.
Check: Windows backslash paths or `image.has_data == False`.
Fix: pass paths as raw strings or with forward slashes. The `hdri_world` helper validates `image.has_data` and warns on failure.

---
For more rare cases, see [reference/pitfalls.md](../reference/pitfalls.md) -- 34 documented gotchas.
