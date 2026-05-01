"""Landscape template — wide exterior with terrain, dirt path, trees, rocks, grass.

REPLACE / TWEAK:
- TERRAIN_SIZE: side length of the ground plane (metres).
- TREE_CLUSTERS: list of (x, y) cluster centres — add or remove entries to populate.
- ROCK_COUNT / GRASS_TUFTS: density of scatter. Keep GRASS_TUFTS modest (<= ~500)
  per Pitfall 31 in the skill notes — instancing cost grows quickly.
- Sky: tweak sun_elevation_deg (lower = more golden) and sun_azimuth_deg in
  H.set_hosek_sky for time-of-day mood.
- Fog density controls atmospheric depth — raise for misty, lower for crisp.
- Camera height: pulled to z=8 manually after auto_frame for a wide vista.
"""
import importlib.util, bpy, os, math
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    os.path.expanduser("~/.claude/skills/blender/scripts/_helpers.py"))
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)

# PARAMETERS
TERRAIN_SIZE = 40.0
TREE_CLUSTERS = [(8, -5), (-12, 4)]
ROCK_COUNT = 40
GRASS_TUFTS = 300  # cap per Pitfall 31

H.reset_scene()

# --- Ground plane -----------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=TERRAIN_SIZE, location=(0.0, 0.0, 0.0))
ground = bpy.context.active_object
ground.name = 'Terrain'
grass_mat = H.procedural_grass('Terrain', base=(0.18, 0.36, 0.14), variation=0.10)
ground.data.materials.append(grass_mat)

# --- Dirt path crossing the terrain -----------------------------------------
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.01))
path = bpy.context.active_object
path.name = 'Path'
path.scale = (TERRAIN_SIZE * 0.95, 1.4, 0.02)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
path_mat = H.procedural_dirt_path('Path')
path.data.materials.append(path_mat)

# --- Tree clusters ----------------------------------------------------------
tree_cluster_objs = []
for i, (x, y) in enumerate(TREE_CLUSTERS):
    cluster = H.add_tree_cluster(center=(x, y, 0.0), count=5, radius=4.0)
    if hasattr(cluster, 'name'):
        tree_cluster_objs.append(cluster.name)
    elif isinstance(cluster, (list, tuple)):
        tree_cluster_objs.extend([(c.name if hasattr(c, 'name') else str(c)) for c in cluster])
    else:
        tree_cluster_objs.append(str(cluster))

# --- Scatter rocks + grass --------------------------------------------------
rocks = H.scatter_rocks(ground, count=ROCK_COUNT, size_range=(0.15, 0.6), seed=11)
tufts = H.scatter_grass_tufts(ground, count=GRASS_TUFTS, seed=7)

# --- Sky + fog --------------------------------------------------------------
H.set_hosek_sky(
    sun_elevation_deg=20,
    sun_azimuth_deg=235,
    turbidity=2.5,
    ground_albedo=0.30,
    strength=1.4,
)
H.add_volumetric_fog(density=0.002, color=(0.95, 0.85, 0.75))

# --- Camera (wide vista) ----------------------------------------------------
cam = H.auto_frame([ground], padding=1.05, elevation_deg=8, azimuth_deg=40, lens=28)
# Pull camera up for a wider, slightly more elevated vista.
if cam is not None and hasattr(cam, 'location'):
    cam.location.z = 8.0

H.set_render(resolution=(1800, 1100), samples=96)

def _name(o):
    return o.name if hasattr(o, 'name') else str(o)

result = {
    "ground": ground.name,
    "path": path.name,
    "tree_clusters": tree_cluster_objs,
    "rocks": _name(rocks),
    "grass_tufts": _name(tufts),
    "camera": _name(cam),
    "sky": "HosekSky",
    "fog": "VolumetricFog",
}
