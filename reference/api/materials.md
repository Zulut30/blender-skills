# Materials beyond Principled

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

---
[Back to API cheatsheet index](../api-cheatsheet.md)
