# Render

Back to [API cheatsheet](../api-cheatsheet.md).

## Practical notes

### switch to CYCLES if available, else EEVEE
```python
import bpy
scene = bpy.context.scene
avail = {it.identifier for it in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items}
for cand in ('CYCLES', 'BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    if cand in avail:
        scene.render.engine = cand
        break
if scene.render.engine == 'CYCLES':
    scene.cycles.device = 'GPU'
```

### enable denoise (eevee + cycles)
```python
import bpy
scene = bpy.context.scene
if scene.render.engine == 'CYCLES':
    scene.cycles.use_denoising = True
    scene.cycles.samples = 128
else:
    # EEVEE Next
    if hasattr(scene.eevee, 'use_raytracing'):
        scene.eevee.use_raytracing = True
```

### render to PNG
```python
import bpy
scene = bpy.context.scene
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = 'C:/tmp/out.png'
bpy.ops.render.render(write_still=True)
```

## Common pitfalls

- Hardcoding `'BLENDER_EEVEE_NEXT'` breaks on Blender 5.1; probe enum_items and use `safe_engine()`.
- EEVEE samples may live under `scene.eevee` or `scene.eevee_next` depending on build — `getattr` both.
- `render_viewport_to_path` may write to a temp dir; trust the `filepath` field in the response, not the input path.
