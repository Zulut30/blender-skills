# Lighting / world

Back to [API cheatsheet](../api-cheatsheet.md).

## Practical notes

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

## Common pitfalls

- World Volume Scatter density >0.005 with long camera distance produces black render in EEVEE.
- HDRI on Windows: pass forward slashes or raw strings; `bpy.data.images.load` can return image with no data otherwise.
- Set `world.use_nodes = True` before touching `world.node_tree` — it's `None` by default on fresh worlds.
