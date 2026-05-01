# Render

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

---
[Back to API cheatsheet index](../api-cheatsheet.md)
