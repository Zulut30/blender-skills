"""Studio product shot: glossy dark ground, cyclorama backdrop, dark world, gold subject."""
import importlib.util, bpy, math
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    r"C:\Users\zulut\.claude\skills\blender\scripts\_helpers.py")
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)

H.reset_scene()

SUBJECT_LOCATION = (0, 0, 1)

ground_mat = H.mat('Ground', (0.02, 0.02, 0.02), roughness=0.05, metallic=0.0)
ground = H.add_plane('Ground', (0, 0, 0), 20, ground_mat)

backdrop_mat = H.mat('Backdrop', (0.08, 0.08, 0.09), roughness=0.6, metallic=0.0)
backdrop = H.add_plane('Backdrop', (0, 8, 6), 20, backdrop_mat)
backdrop.rotation_euler = (math.radians(90), 0, 0)

sweep_mat = H.mat('Sweep', (0.05, 0.05, 0.06), roughness=0.4, metallic=0.0)
sweep = H.add_plane('Sweep', (0, 5, 1.5), 12, sweep_mat)
sweep.rotation_euler = (math.radians(55), 0, 0)

gold = H.mat('Gold', (1.0, 0.78, 0.2), roughness=0.25, metallic=1.0)
subject = H.add_cube('Subject', SUBJECT_LOCATION, (0.6, 0.6, 0.6), gold)

H.set_world_sky(top=(0.02, 0.02, 0.02), strength=0.3)
key, fill, back = H.three_point_light(target=SUBJECT_LOCATION, key_energy=6.0)
H.set_render(engine='BLENDER_EEVEE', resolution=(1280, 800), samples=64)

cam = H.auto_frame([subject], padding=1.4, elevation_deg=18, azimuth_deg=35, lens=50)

bb_min, bb_max = H.bbox_of([subject])

result = {
    'objects': {
        'ground': ground.name,
        'backdrop': backdrop.name,
        'sweep': sweep.name,
        'subject': subject.name,
    },
    'camera': cam.name,
    'lights': {'key': key.name, 'fill': fill.name, 'back': back.name},
    'bbox_min': tuple(bb_min),
    'bbox_max': tuple(bb_max),
}
