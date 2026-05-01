"""Parametric building: nave, gable roof, tower with belvedere and spire, cross, apse, windows."""
import importlib.util, bpy, math
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    r"C:\Users\zulut\.claude\skills\blender\scripts\_helpers.py")
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)

NAVE_W, NAVE_L, NAVE_H = 5, 9, 4
ROOF_H = 2.0
TOWER_S, TOWER_H = 2.4, 7.0
SPIRE_H = 4.0

H.reset_scene()

grass = H.mat('Grass', (0.18, 0.42, 0.16), roughness=0.95)
wall = H.mat('Wall', (0.92, 0.88, 0.78), roughness=0.85)
roof = H.mat('Roof', (0.32, 0.18, 0.12), roughness=0.7)
stone = H.mat('Stone', (0.65, 0.62, 0.58), roughness=0.9)
wood = H.mat('Wood', (0.28, 0.16, 0.08), roughness=0.8)
glass = H.mat('Glass', (0.55, 0.7, 0.85), roughness=0.15, metallic=0.0)
gold = H.mat('Gold', (1.0, 0.82, 0.2), roughness=0.25, metallic=1.0)

ground = H.add_plane('Ground', (0, 0, 0), 60, grass)

building = H.add_cube('Building', (0, 0, NAVE_H / 2.0), (NAVE_W, NAVE_L, NAVE_H), wall)
building_roof = H.gable_roof('BuildingRoof', (0, 0, NAVE_H + ROOF_H / 2.0),
                             NAVE_W * 2, NAVE_L * 2, ROOF_H, roof)

tower_x = -(NAVE_W + TOWER_S / 2.0)
tower = H.add_cube('Tower', (tower_x, -NAVE_L + TOWER_S / 2.0, TOWER_H / 2.0),
                   (TOWER_S, TOWER_S, TOWER_H), wall)
belvedere_h = 1.6
belvedere_s = TOWER_S * 0.75
belvedere = H.add_cube('Belvedere',
                       (tower_x, -NAVE_L + TOWER_S / 2.0, TOWER_H + belvedere_h / 2.0),
                       (belvedere_s, belvedere_s, belvedere_h), stone)

spire_base_z = TOWER_H + belvedere_h
spire = H.add_cone('Spire',
                   (tower_x, -NAVE_L + TOWER_S / 2.0, spire_base_z + SPIRE_H / 2.0),
                   belvedere_s * 0.9, 0.0, SPIRE_H, roof, vertices=4)
spire.rotation_euler = (0, 0, math.radians(45))

cross_z = spire_base_z + SPIRE_H + 0.5
cross_v = H.add_cube('CrossV', (tower_x, -NAVE_L + TOWER_S / 2.0, cross_z),
                     (0.06, 0.06, 0.55), gold)
cross_h = H.add_cube('CrossH', (tower_x, -NAVE_L + TOWER_S / 2.0, cross_z + 0.1),
                     (0.06, 0.32, 0.06), gold)

door = H.add_cube('Door', (0, -NAVE_L - 0.02, 1.1), (0.7, 0.05, 1.1), wood)

rose_radius = 0.55
rose = H.add_cyl('Rose', (0, -NAVE_L - 0.02, NAVE_H - 0.6),
                 rose_radius, 0.1, glass)
rose.rotation_euler = (math.radians(90), 0, 0)

windows = []
for i, y in enumerate([-NAVE_L * 0.6, -NAVE_L * 0.2, NAVE_L * 0.2, NAVE_L * 0.6]):
    w_left = H.add_cube('WindowLeft_%d' % i, (-NAVE_W - 0.02, y, NAVE_H * 0.6),
                        (0.05, 0.4, 0.9), glass)
    w_right = H.add_cube('WindowRight_%d' % i, (NAVE_W + 0.02, y, NAVE_H * 0.6),
                         (0.05, 0.4, 0.9), glass)
    windows.extend([w_left, w_right])

steps = []
for i in range(3):
    s = H.add_cube('Step_%d' % i,
                   (0, -NAVE_L - 0.4 - i * 0.4, 0.1 + i * 0.15),
                   (1.5 + i * 0.3, 0.2, 0.15), stone)
    steps.append(s)

apse_radius = NAVE_W * 0.7
apse_h = NAVE_H
apse = H.add_cyl('Apse', (0, NAVE_L + apse_radius * 0.5, apse_h / 2.0),
                 apse_radius, apse_h, wall, vertices=24)
apse_roof = H.add_cone('ApseRoof',
                       (0, NAVE_L + apse_radius * 0.5, apse_h + 0.9),
                       apse_radius, 0.0, 1.8, roof, vertices=24)

H.set_world_sky(top=(0.55, 0.75, 0.95), strength=1.2)
key, fill, back = H.three_point_light(target=(0, 0, NAVE_H / 2.0), key_energy=4.0)
H.set_render(engine='BLENDER_EEVEE', resolution=(1280, 800), samples=64)

scene_objects = [ground, building, building_roof, tower, belvedere, spire,
                 cross_v, cross_h, door, rose, apse, apse_roof] + windows + steps
# Ground is huge by design; framing on the building only avoids zooming out to a speck.
frame_targets = [building, building_roof, tower, belvedere, spire,
                 cross_v, cross_h, apse, apse_roof] + steps
cam = H.auto_frame(frame_targets, padding=1.3, elevation_deg=20,
                   azimuth_deg=45, lens=35)

bb_min, bb_max = H.bbox_of(frame_targets)

result = {
    'objects': {
        'ground': ground.name,
        'building': building.name,
        'building_roof': building_roof.name,
        'tower': tower.name,
        'belvedere': belvedere.name,
        'spire': spire.name,
        'cross_v': cross_v.name,
        'cross_h': cross_h.name,
        'door': door.name,
        'rose': rose.name,
        'apse': apse.name,
        'apse_roof': apse_roof.name,
        'windows': [w.name for w in windows],
        'steps': [s.name for s in steps],
    },
    'camera': cam.name,
    'lights': {'key': key.name, 'fill': fill.name, 'back': back.name},
    'bbox_min': tuple(bb_min),
    'bbox_max': tuple(bb_max),
}
