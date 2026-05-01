# Modifiers

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

---
[Back to API cheatsheet index](../api-cheatsheet.md)
