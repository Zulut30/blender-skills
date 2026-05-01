# Camera

Back to [API cheatsheet](../api-cheatsheet.md).

## Practical notes

### DOF with focus_object and fstop
```python
import bpy
cam = bpy.context.scene.camera.data
target = next(o for o in bpy.data.objects if o.type == 'MESH')
cam.dof.use_dof = True
cam.dof.focus_object = target
cam.dof.aperture_fstop = 2.8
```

### orthographic camera
```python
import bpy
cam = bpy.context.scene.camera.data
cam.type = 'ORTHO'
cam.ortho_scale = 6.0
```

### track-to constraint on target
```python
import bpy
cam_obj = bpy.context.scene.camera
target  = next(o for o in bpy.data.objects if o.type == 'MESH')
c = cam_obj.constraints.new(type='TRACK_TO')
c.target = target
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
```

## Common pitfalls

- `bpy.data.objects['Camera']` is locale-fragile (becomes "Камера" in ru_RU); prefer `bpy.context.scene.camera`.
- Repeated `frame_camera` calls leave behind `SkillCamera.001/.002` and inflate bbox — clean up old cameras first.
- Pass only hero meshes to `auto_frame`; ground planes and skyboxes blow up the bbox and shrink the subject.
