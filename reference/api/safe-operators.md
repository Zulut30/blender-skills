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
obj = bpy.data.objects['Cube']
for o in bpy.context.view_layer.objects:
    o.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
```

### delete object with full datablock cleanup
```python
import bpy
obj = bpy.data.objects['Cube']
mesh = obj.data if obj.type == 'MESH' else None
bpy.data.objects.remove(obj, do_unlink=True)
if mesh and mesh.users == 0:
    bpy.data.meshes.remove(mesh)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_recursive=True)
```

## Common pitfalls

- Many operators need an active object + Object mode; set `view_layer.objects.active` and `select_set(True)` first.
- Avoid `bpy.ops.object.select_all` (poll fails headless); iterate `scene.objects` and `o.select_set(...)` instead.
- Local Python vars do NOT survive across `execute_blender_code` calls — re-fetch via `bpy.data.objects['Name']`.
