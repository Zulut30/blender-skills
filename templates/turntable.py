"""Turntable template — a clean studio turntable for a hero subject.

REPLACE / TWEAK:
- The objects under SubjectRoot (gold sphere + aged-brass cube) are PLACEHOLDERS.
  To swap in your own model:
    1. Delete the placeholder children of SubjectRoot.
    2. Import / build your model and parent it to the SubjectRoot Empty.
    3. Re-run H.setup_turntable(subject_root, ...) to refresh the camera radius.
- TURNS / FRAME_END: control rotation speed (TURNS rotations across FRAME_END frames).
- Studio darkness: H.studio_dark_world strength controls ambient fill.
- Key/rim energy: tune via three_point_light(key_energy=...) and rim_light(energy=...).
"""
import importlib.util, bpy, os, math
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    os.path.expanduser("~/.claude/skills/blender/scripts/_helpers.py"))
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)

# PARAMETERS
SUBJECT_LOCATION = (0.0, 0.0, 1.0)
TURNS = 1.0  # number of full rotations across the animation
FRAME_END = 120

H.reset_scene()

# --- Backdrop ---------------------------------------------------------------
cyc = H.cyclorama_backdrop('Cyc', size=8.0, color=(0.04, 0.04, 0.05))

# --- Subject (PLACEHOLDER — replace with your own model) --------------------
# REPLACE the SubjectRoot children with your own model.
# To replace: delete the placeholder objects under SubjectRoot, parent your
# imported model to SubjectRoot, then run setup_turntable again.
subject_root = bpy.data.objects.new('SubjectRoot', None)
bpy.context.collection.objects.link(subject_root)
subject_root.location = SUBJECT_LOCATION

# Gold metallic sphere (PLACEHOLDER)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(0.0, 0.0, 0.0))
sphere = bpy.context.active_object
sphere.name = 'PlaceholderSphere'
bpy.ops.object.shade_smooth()
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
sphere_mat = H.mat('GoldSphere', (1.0, 0.78, 0.18), roughness=0.18, metallic=1.0)
sphere.data.materials.append(sphere_mat)
sphere.parent = subject_root
sphere.matrix_parent_inverse.identity()
sphere.location = (0.0, 0.0, 0.0)

# Aged brass companion cube (PLACEHOLDER)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.9, 0.0, -0.2))
cube = bpy.context.active_object
cube.name = 'PlaceholderCube'
cube.scale = (0.4, 0.4, 0.6)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
brass_mat = H.procedural_metal_aged('AgedBrass')
cube.data.materials.append(brass_mat)
cube.parent = subject_root
cube.matrix_parent_inverse.identity()
cube.location = (0.9, 0.0, -0.2)

# --- World + lights ---------------------------------------------------------
H.studio_dark_world(strength=0.2, color=(0.02, 0.02, 0.02))
key_lights = H.three_point_light(target=SUBJECT_LOCATION, key_energy=8.0)
rim = H.rim_light(target_obj=subject_root, energy=4.0, color=(0.7, 0.85, 1.0))

# --- Animation + camera -----------------------------------------------------
H.set_animation_range(start=1, end=FRAME_END, fps=24)
cam = H.setup_turntable(
    subject_root,
    frame_start=1,
    frame_end=FRAME_END,
    radius=None,
    height_offset=0.4,
    lens=85,
)

# --- Render -----------------------------------------------------------------
H.enable_eevee_quality()
H.set_render_resolution(1920, 1080)

def _name(obj):
    return obj.name if hasattr(obj, 'name') else str(obj)

result = {
    "subject_root": subject_root.name,
    "subject_children": [sphere.name, cube.name],
    "backdrop": _name(cyc),
    "lights": {
        "key_set": [_name(o) for o in (key_lights if isinstance(key_lights, (list, tuple)) else [key_lights])],
        "rim": _name(rim),
    },
    "camera": _name(cam),
    "frames": (1, FRAME_END),
    "turns": TURNS,
}
