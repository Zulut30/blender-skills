# Blender API cheatsheet
Compact recipes for things helpers don't cover. Each block is self-contained and copy-pasteable.

## Mesh editing (bmesh)

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

## Modifiers

### add Subdivision Surface
```python
obj = bpy.context.object
m = obj.modifiers.new(name='Subsurf', type='SUBSURF')
m.levels = 1           # viewport
m.render_levels = 2
```

### add Bevel
```python
obj = bpy.context.object
m = obj.modifiers.new(name='Bevel', type='BEVEL')
m.width = 0.02
m.segments = 3
m.limit_method = 'ANGLE'
```

### Boolean difference with another object, then apply
```python
import bpy
a = bpy.data.objects['Cube']; a.name = 'Cube'
b = bpy.data.objects['Sphere']; b.name = 'Sphere'
m = a.modifiers.new(name='Bool', type='BOOLEAN')
m.operation = 'DIFFERENCE'
m.object = b
m.solver = 'EXACT'
bpy.context.view_layer.objects.active = a
bpy.ops.object.modifier_apply(modifier=m.name)
b.hide_set(True)
```

### Array + Curve modifier
```python
obj = bpy.context.object
curve = bpy.data.objects['BezierCurve']; curve.name = 'BezierCurve'
arr = obj.modifiers.new(name='Array', type='ARRAY')
arr.fit_type = 'FIT_CURVE'
arr.curve = curve
crv = obj.modifiers.new(name='Curve', type='CURVE')
crv.object = curve
crv.deform_axis = 'POS_X'
```

### apply all modifiers safely
```python
import bpy
obj = bpy.context.object
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = obj
override = {'object': obj, 'active_object': obj, 'selected_objects': [obj]}
for mod in list(obj.modifiers):
    with bpy.context.temp_override(**override):
        bpy.ops.object.modifier_apply(modifier=mod.name)
```

## Geometry Nodes

### create empty geometry node group and assign via Nodes modifier
```python
import bpy
ng = bpy.data.node_groups.new(name='GN', type='GeometryNodeTree'); ng.name = 'GN'
ng.interface.new_socket(name='Geometry', in_out='INPUT',  socket_type='NodeSocketGeometry')
ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
n_in  = ng.nodes.new('NodeGroupInput')
n_out = ng.nodes.new('NodeGroupOutput'); n_out.location = (300, 0)
ng.links.new(n_in.outputs[0], n_out.inputs[0])
obj = bpy.context.object
mod = obj.modifiers.new(name='GN', type='NODES')
mod.node_group = ng
```

### add distribute_points_on_faces node
```python
# assumes ng exists with Group Input/Output already wired
dp = ng.nodes.new('GeometryNodeDistributePointsOnFaces')
dp.location = (150, 0)
dp.inputs['Density'].default_value = 50.0
ng.links.new(n_in.outputs['Geometry'], dp.inputs['Mesh'])
ng.links.new(dp.outputs['Points'], n_out.inputs['Geometry'])
```

## Materials beyond Principled

### emissive area light material (for plane-light)
```python
import bpy
mat = bpy.data.materials.new(name='Emit'); mat.name = 'Emit'
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
emit = nt.nodes.new('ShaderNodeEmission')
emit.inputs['Color'].default_value = (1, 0.9, 0.7, 1)
emit.inputs['Strength'].default_value = 50.0
out = nt.nodes.new('ShaderNodeOutputMaterial')
out.location = (300, 0)
nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
```

### glass via Principled (transmission=1, roughness=0)
```python
import bpy
mat = bpy.data.materials.new(name='Glass'); mat.name = 'Glass'
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Transmission Weight'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.0
bsdf.inputs['IOR'].default_value = 1.45
bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
```

### procedural noise into Base Color via ColorRamp
```python
import bpy
mat = bpy.data.materials.new(name='Noise'); mat.name = 'Noise'
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
noise = nt.nodes.new('ShaderNodeTexNoise'); noise.location = (-600, 0)
ramp  = nt.nodes.new('ShaderNodeValToRGB');  ramp.location  = (-300, 0)
ramp.color_ramp.elements[0].color = (0.05, 0.05, 0.1, 1)
ramp.color_ramp.elements[1].color = (0.9, 0.7, 0.4, 1)
nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
```

## Lighting / world

### HDRI environment from file
```python
import bpy
world = bpy.context.scene.world
world.use_nodes = True
nt = world.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
coord = nt.nodes.new('ShaderNodeTexCoord');     coord.location = (-800, 0)
mapn  = nt.nodes.new('ShaderNodeMapping');      mapn.location  = (-600, 0)
env   = nt.nodes.new('ShaderNodeTexEnvironment'); env.location = (-300, 0)
bg    = nt.nodes.new('ShaderNodeBackground')
out   = nt.nodes.new('ShaderNodeOutputWorld');  out.location = (300, 0)
env.image = bpy.data.images.load('C:/path/to/env.exr', check_existing=True)
nt.links.new(coord.outputs['Generated'], mapn.inputs['Vector'])
nt.links.new(mapn.outputs['Vector'], env.inputs['Vector'])
nt.links.new(env.outputs['Color'], bg.inputs['Color'])
nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
```

### SUN with direction from a vector
```python
import bpy, math, mathutils
data = bpy.data.lights.new(name='Sun', type='SUN'); data.name = 'Sun'
data.energy = 5.0
sun = bpy.data.objects.new('Sun', data); sun.name = 'Sun'
bpy.context.collection.objects.link(sun)
direction = mathutils.Vector((-0.3, -0.5, -1.0)).normalized()
# sun shines along its local -Z; rotate -Z to match `direction`
sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
```

### Area light pointed at a target
```python
import bpy, mathutils
target = bpy.data.objects['Cube']
data = bpy.data.lights.new(name='AreaKey', type='AREA'); data.name = 'AreaKey'
data.size = 2.0; data.energy = 500.0
light = bpy.data.objects.new('AreaKey', data); light.name = 'AreaKey'
bpy.context.collection.objects.link(light)
light.location = (4, -4, 4)
v = (mathutils.Vector(target.matrix_world.translation) - light.location)
light.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
```

## Camera

### DOF with focus_object and fstop
```python
cam = bpy.data.objects['Camera'].data
cam.dof.use_dof = True
cam.dof.focus_object = bpy.data.objects['Cube']
cam.dof.aperture_fstop = 2.8
```

### orthographic camera
```python
cam = bpy.data.objects['Camera'].data
cam.type = 'ORTHO'
cam.ortho_scale = 6.0
```

### track-to constraint on target
```python
import bpy
cam_obj = bpy.data.objects['Camera']
target  = bpy.data.objects['Cube']
c = cam_obj.constraints.new(type='TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
```

## Render

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

## Animation (basics)

### keyframe location/rotation on frames 1 and 50
```python
import bpy, math
obj = bpy.context.object
scene = bpy.context.scene
scene.frame_set(1)
obj.location = (0, 0, 0); obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert('location'); obj.keyframe_insert('rotation_euler')
scene.frame_set(50)
obj.location = (0, 0, 3); obj.rotation_euler = (0, 0, math.radians(180))
obj.keyframe_insert('location'); obj.keyframe_insert('rotation_euler')
```

### set frame range and render animation
```python
import bpy
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 50
scene.render.fps = 24
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = 'C:/tmp/anim_'
bpy.ops.render.render(animation=True)
```

## Scene inspection

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

## Common operators safely

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
