# Animation (basics)

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

---
[Back to API cheatsheet index](../api-cheatsheet.md)
