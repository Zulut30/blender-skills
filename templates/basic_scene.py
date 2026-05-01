"""Empty staging scene: ground, three-point light, sky, render settings; no subject."""
import importlib.util, bpy, os
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    os.path.expanduser("~/.claude/skills/blender/scripts/_helpers.py"))
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)

H.reset_scene()

floor_mat = H.mat('Floor', (0.45, 0.45, 0.45), roughness=0.85, metallic=0.0)
floor = H.add_plane('Floor', (0, 0, 0), 20, floor_mat)

H.set_world_sky(top=(0.55, 0.75, 0.95), strength=1.2)
key, fill, back = H.three_point_light(target=(0, 0, 1), key_energy=4.0)
H.set_render(engine=H.safe_engine(), resolution=(1280, 800), samples=64)

bb_min, bb_max = H.bbox_of([floor])

result = {
    'objects': {'floor': floor.name},
    'lights': {'key': key.name, 'fill': fill.name, 'back': back.name},
    'bbox_min': tuple(bb_min),
    'bbox_max': tuple(bb_max),
}
