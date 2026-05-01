# Geometry Nodes

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

---
[Back to API cheatsheet index](../api-cheatsheet.md)
