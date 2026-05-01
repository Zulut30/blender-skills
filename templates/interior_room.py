"""Interior room template — a fully furnished room with table, chairs, rug, and lights.

REPLACE / TWEAK:
- ROOM_W / ROOM_D / ROOM_H: room dimensions in metres.
- WALL_COLOR: base wall colour (linear RGB).
- Wood / chair colours: edit the procedural_wood / mat calls below.
- Window position / size: edit the H.add_window_cutout call.
- Camera framing: tweak elevation_deg / azimuth_deg / lens in the auto_frame call,
  or replace with a manual bpy.ops.object.camera_add + look-at constraint.
- Light energies: CeilingLight (practical) and SkyFill (window bounce) are the two
  primary keys. Drop CeilingLight to ~30 for a moodier evening look.
"""
import importlib.util, bpy, math
spec = importlib.util.spec_from_file_location(
    "_skill_helpers",
    r"C:\Users\zulut\.claude\skills\blender\scripts\_helpers.py")
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)

# PARAMETERS
ROOM_W = 6.0
ROOM_D = 5.0
ROOM_H = 3.0
WALL_COLOR = (0.85, 0.78, 0.68)

H.reset_scene()

# --- Walls / floor / ceiling -------------------------------------------------
room = H.build_room_box(
    'Room', ROOM_W, ROOM_D, ROOM_H,
    wall_thickness=0.18,
    material=H.procedural_stone('RoomWall', base=WALL_COLOR, variation=0.06, bumpiness=0.2),
)

# Window cut-out on the south wall (negative Y) and a door on the west wall.
H.add_window_cutout(room['wall_s'], (0.0, -ROOM_D / 2.0, 1.5), width=1.4, height=1.4)
door = H.add_door_frame('Door', (-ROOM_W / 2.0 + 0.1, 0.0, 0.0), width=0.95, height=2.1, depth=0.18)

# --- Table (cube top + 4 cylinder legs, parented under TableRoot) -----------
wood_mat = H.procedural_wood('TableWood')

table_root = bpy.data.objects.new('TableRoot', None)
bpy.context.collection.objects.link(table_root)

# Build children at origin, then translate the root.
TABLE_W, TABLE_D, TABLE_H = 1.6, 0.9, 0.04
LEG_R, LEG_H = 0.04, 0.71

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, LEG_H + TABLE_H / 2.0))
top = bpy.context.active_object
top.name = 'TableTop'
top.scale = (TABLE_W, TABLE_D, TABLE_H)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
top.data.materials.append(wood_mat)
top.parent = table_root

table_legs = []
leg_offsets = [
    (TABLE_W / 2.0 - 0.08,  TABLE_D / 2.0 - 0.08),
    (-TABLE_W / 2.0 + 0.08,  TABLE_D / 2.0 - 0.08),
    (TABLE_W / 2.0 - 0.08, -TABLE_D / 2.0 + 0.08),
    (-TABLE_W / 2.0 + 0.08, -TABLE_D / 2.0 + 0.08),
]
for i, (lx, ly) in enumerate(leg_offsets):
    bpy.ops.mesh.primitive_cylinder_add(radius=LEG_R, depth=LEG_H, location=(lx, ly, LEG_H / 2.0))
    leg = bpy.context.active_object
    leg.name = f'TableLeg_{i}'
    leg.data.materials.append(wood_mat)
    leg.parent = table_root
    table_legs.append(leg.name)

# Translate the root so the table sits centred at (0, 0, 0.75) (top surface roughly there).
table_root.location = (0.0, 0.0, 0.0)

# --- Two chairs flanking the table ------------------------------------------
def build_chair(name: str, position):
    root = bpy.data.objects.new(name + 'Root', None)
    bpy.context.collection.objects.link(root)

    SEAT_W, SEAT_D, SEAT_H = 0.45, 0.45, 0.05
    CLEG_R, CLEG_H = 0.025, 0.45
    BACK_W, BACK_D, BACK_H = 0.45, 0.05, 0.5

    # Seat
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, CLEG_H + SEAT_H / 2.0))
    seat = bpy.context.active_object
    seat.name = name + '_Seat'
    seat.scale = (SEAT_W, SEAT_D, SEAT_H)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    seat.data.materials.append(wood_mat)
    seat.parent = root

    # 4 legs
    chair_legs = []
    coffsets = [
        (SEAT_W / 2.0 - 0.04,  SEAT_D / 2.0 - 0.04),
        (-SEAT_W / 2.0 + 0.04,  SEAT_D / 2.0 - 0.04),
        (SEAT_W / 2.0 - 0.04, -SEAT_D / 2.0 + 0.04),
        (-SEAT_W / 2.0 + 0.04, -SEAT_D / 2.0 + 0.04),
    ]
    for i, (lx, ly) in enumerate(coffsets):
        bpy.ops.mesh.primitive_cylinder_add(radius=CLEG_R, depth=CLEG_H, location=(lx, ly, CLEG_H / 2.0))
        leg = bpy.context.active_object
        leg.name = f'{name}_Leg_{i}'
        leg.data.materials.append(wood_mat)
        leg.parent = root
        chair_legs.append(leg.name)

    # Backrest (rises behind the seat, +Y side)
    back_z = CLEG_H + SEAT_H + BACK_H / 2.0
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, SEAT_D / 2.0 - BACK_D / 2.0, back_z))
    back = bpy.context.active_object
    back.name = name + '_Back'
    back.scale = (BACK_W, BACK_D, BACK_H)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    back.data.materials.append(wood_mat)
    back.parent = root

    root.location = position
    return root, chair_legs

chair1_root, chair1_legs = build_chair('ChairA', (1.4, 0.0, 0.0))
chair1_root.rotation_euler = (0.0, 0.0, math.radians(-90))
chair2_root, chair2_legs = build_chair('ChairB', (-1.4, 0.0, 0.0))
chair2_root.rotation_euler = (0.0, 0.0, math.radians(90))

# --- Rug under the table -----------------------------------------------------
rug = H.add_rug('Rug', (0.0, 0.0, 0.02), size_x=2.5, size_y=1.5, color=(0.4, 0.15, 0.10))

# --- Lights ------------------------------------------------------------------
ceiling_light = H.add_area_light(
    'CeilingLight',
    (0.0, 0.0, ROOM_H - 0.05),
    (math.radians(180), 0.0, 0.0),
    energy=80,
    size=1.5,
    color=(1.0, 0.92, 0.78),
)
sky_fill = H.add_emissive_plane(
    'SkyFill',
    (0.0, -ROOM_D / 2.0 + 0.3, 1.5),
    size=1.4,
    energy=3.0,
    color=(0.7, 0.85, 1.0),
)

# Subtle ambient (walls block most of it but it lifts shadows).
H.set_world_sky(top=(0.55, 0.62, 0.75), strength=0.4)

# --- Camera ------------------------------------------------------------------
cam = H.auto_frame(
    [table_root, chair1_root, chair2_root],
    padding=1.3,
    elevation_deg=12,
    azimuth_deg=210,
    lens=35,
)

H.set_render(resolution=(1600, 1000), samples=64)

result = {
    "room": {
        "floor": room.get('floor').name if hasattr(room.get('floor'), 'name') else room.get('floor'),
        "ceiling": room.get('ceiling').name if hasattr(room.get('ceiling'), 'name') else room.get('ceiling'),
        "wall_n": room.get('wall_n').name if hasattr(room.get('wall_n'), 'name') else room.get('wall_n'),
        "wall_s": room.get('wall_s').name if hasattr(room.get('wall_s'), 'name') else room.get('wall_s'),
        "wall_e": room.get('wall_e').name if hasattr(room.get('wall_e'), 'name') else room.get('wall_e'),
        "wall_w": room.get('wall_w').name if hasattr(room.get('wall_w'), 'name') else room.get('wall_w'),
        "door": door.name if hasattr(door, 'name') else str(door),
    },
    "table": {
        "root": table_root.name,
        "top": top.name,
        "legs": table_legs,
    },
    "chairs": [
        {"root": chair1_root.name, "legs": chair1_legs},
        {"root": chair2_root.name, "legs": chair2_legs},
    ],
    "rug": rug.name if hasattr(rug, 'name') else str(rug),
    "lights": [
        ceiling_light.name if hasattr(ceiling_light, 'name') else str(ceiling_light),
        sky_fill.name if hasattr(sky_fill, 'name') else str(sky_fill),
    ],
    "camera": cam.name if hasattr(cam, 'name') else str(cam),
}
