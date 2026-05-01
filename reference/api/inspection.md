# Scene inspection

### count tris in scene
```python
import bpy
total = 0
deps = bpy.context.evaluated_depsgraph_get()
for obj in bpy.context.scene.objects:
    if obj.type != 'MESH': continue
    me = obj.evaluated_get(deps).to_mesh()
    me.calc_loop_triangles()
    total += len(me.loop_triangles)
    obj.evaluated_get(deps).to_mesh_clear()
print('tris:', total)
```

### find all objects using a specific material
```python
import bpy
mat = bpy.data.materials['Glass']
users = [o for o in bpy.data.objects
         if any(s.material == mat for s in o.material_slots)]
print([o.name for o in users])
```

### world-space bbox of a set of objects
```python
import mathutils
objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
mn = mathutils.Vector(( 1e18,  1e18,  1e18))
mx = mathutils.Vector((-1e18, -1e18, -1e18))
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mn = mathutils.Vector(map(min, mn, w))
        mx = mathutils.Vector(map(max, mx, w))
center = (mn + mx) * 0.5
size   = (mx - mn)
```

---
[Back to API cheatsheet index](../api-cheatsheet.md)
