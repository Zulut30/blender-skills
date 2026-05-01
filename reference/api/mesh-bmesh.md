# Mesh editing (bmesh)

### subdivide cube faces
```python
import bpy, bmesh
obj = bpy.context.object
bm = bmesh.new()
bm.from_mesh(obj.data)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
bm.to_mesh(obj.data)
bm.free()
obj.data.update()
```

### inset face by index, then extrude inset on Z
```python
import bpy, bmesh
from mathutils import Vector
obj = bpy.context.object
bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
face = bm.faces[0]
res = bmesh.ops.inset_individual(bm, faces=[face], thickness=0.1, depth=0.0)
new_faces = [f for f in bm.faces if f.select] or [face]
ex = bmesh.ops.extrude_face_region(bm, geom=new_faces)
verts = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, vec=Vector((0, 0, 0.5)), verts=verts)
bm.to_mesh(obj.data); bm.free(); obj.data.update()
```

### bevel edges by angle threshold
```python
import bpy, bmesh, math
obj = bpy.context.object
bm = bmesh.new(); bm.from_mesh(obj.data)
threshold = math.radians(30)
edges = [e for e in bm.edges if len(e.link_faces) == 2
         and e.calc_face_angle(0.0) > threshold]
bmesh.ops.bevel(bm, geom=edges, offset=0.05, segments=3, profile=0.5, affect='EDGES')
bm.to_mesh(obj.data); bm.free(); obj.data.update()
```

### merge by distance
```python
import bpy, bmesh
obj = bpy.context.object
bm = bmesh.new(); bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.0001)
bm.to_mesh(obj.data); bm.free(); obj.data.update()
```

---
[Back to API cheatsheet index](../api-cheatsheet.md)
