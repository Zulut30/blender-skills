# Common operators safely

Back to [API cheatsheet](../api-cheatsheet.md).

## Practical notes

### exit to OBJECT mode safely
```python
import bpy
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
```

### make object active and selected (without select_all)
```python
import bpy
# Use the currently-active object, OR look up by a name YOU assigned explicitly.
# Blender's default 'Cube' becomes 'Куб' under ru_RU — never hard-code default names.
obj = bpy.context.active_object
# Alternative: obj = bpy.data.objects['MyCube']  # only if you did obj.name = 'MyCube' yourself
for o in bpy.context.view_layer.objects:
    o.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
```

### delete object with full datablock cleanup
```python
import bpy
# obj must have been created with obj.name = 'MyCube' explicitly,
# OR fetched via bpy.context.active_object — Blender's default 'Cube' becomes 'Куб' under ru_RU.
obj = bpy.context.active_object
mesh = obj.data if obj.type == 'MESH' else None
bpy.data.objects.remove(obj, do_unlink=True)
if mesh and mesh.users == 0:
    bpy.data.meshes.remove(mesh)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True)
```

## Common pitfalls

- Many operators need an active object + Object mode; set `view_layer.objects.active` and `select_set(True)` first.
- Avoid `bpy.ops.object.select_all` (poll fails headless); iterate `scene.objects` and `o.select_set(...)` instead.
- Local Python vars do NOT survive across `execute_blender_code` calls — re-fetch via `bpy.data.objects['Name']` ONLY if you assigned `Name` yourself (e.g. `obj.name = 'MyCube'`); default names like `'Cube'` are locale-translated and unreliable. Prefer `bpy.context.active_object` or `bpy.context.scene.camera` when applicable.
