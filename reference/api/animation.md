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
Render per-frame inside the MCP — `animation=True` blocks the MCP socket past its timeout.
```python
import bpy, os
out_dir = os.path.expanduser("~/blender_renders")
os.makedirs(out_dir, exist_ok=True)
scn = bpy.context.scene
for i in range(scn.frame_start, scn.frame_end + 1):
    scn.frame_set(i)
    scn.render.filepath = os.path.join(out_dir, f"frame_{i:04d}.png")
    bpy.ops.render.render(write_still=True)
# Then assemble with ffmpeg on the host:
# ffmpeg -framerate 24 -i frame_%04d.png -pix_fmt yuv420p out.mp4
```

## Common pitfalls

- `bpy.ops.render.render(animation=True)` times out the MCP — render per-frame in chunks of 20-30.
- Blender 5.x Slotted Actions: `action.fcurves` is gone; use `action.layers[0].strips[0].channelbag(slot).fcurves`.
- Bezier auto-clamped handles overshoot when orbit keys are >45° apart — distribute keys finely or use LINEAR.
