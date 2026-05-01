# Camera

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

---
[Back to API cheatsheet index](../api-cheatsheet.md)
