# Animation (basics)

Back to [API cheatsheet](../api-cheatsheet.md).

## Practical notes

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

## Common pitfalls

- `bpy.ops.render.render(animation=True)` times out the MCP — render per-frame in chunks of 20-30.
- Blender 5.x Slotted Actions: `action.fcurves` is gone; use `action.layers[0].strips[0].channelbag(slot).fcurves`.
- Bezier auto-clamped handles overshoot when orbit keys are >45° apart — distribute keys finely or use LINEAR.
