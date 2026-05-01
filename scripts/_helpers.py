"""Helpers for Blender 5.x Python snippets executed via mcp__Blender__execute_blender_code.
Self-contained: stdlib + bpy/bmesh/mathutils only. Designed for ru_RU UI locale where new
datablock names are translated by Blender, so every helper sets obj.name explicitly after
creation. Each helper is idempotent across exec calls (bpy.data persists between calls)."""

import bpy
import bmesh
import math
import mathutils


def reset_scene():
    # Clear all objects without relying on selection context (operators may fail in headless ctx).
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                 bpy.data.lights, bpy.data.curves, bpy.data.images):
        for db in list(coll):
            if db.users == 0:
                coll.remove(db)


def _set_principled_input(bsdf, names, value):
    # Different Blender versions name emission inputs differently ('Emission' vs 'Emission Color').
    for n in names:
        if n in bsdf.inputs:
            try:
                bsdf.inputs[n].default_value = value
                return True
            except Exception:
                pass
    return False


def mat(name, color, roughness=0.7, metallic=0.0, emission=None, emission_strength=1.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.name = name
    m.use_nodes = True
    nt = m.node_tree
    bsdf = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if bsdf is None:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = None
        for n in nt.nodes:
            if n.type == 'OUTPUT_MATERIAL':
                out = n
                break
        if out is None:
            out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(bsdf.outputs[0], out.inputs[0])

    rgba = (color[0], color[1], color[2], color[3] if len(color) > 3 else 1.0)
    _set_principled_input(bsdf, ['Base Color'], rgba)
    _set_principled_input(bsdf, ['Roughness'], roughness)
    _set_principled_input(bsdf, ['Metallic'], metallic)
    if emission is not None:
        e_rgba = (emission[0], emission[1], emission[2], emission[3] if len(emission) > 3 else 1.0)
        _set_principled_input(bsdf, ['Emission Color', 'Emission'], e_rgba)
        _set_principled_input(bsdf, ['Emission Strength'], emission_strength)
    return m


def _assign_material(obj, material):
    if material is None:
        return
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def _apply_scale(obj):
    # transform_apply needs the object active and selected.
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def add_cube(name, location, scale, material=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    if hasattr(scale, '__len__'):
        obj.scale = (scale[0], scale[1], scale[2])
    else:
        obj.scale = (scale, scale, scale)
    obj.name = name
    obj.data.name = name
    _apply_scale(obj)
    _assign_material(obj, material)
    return obj


def add_cyl(name, location, radius, depth, material=None, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                        depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    _apply_scale(obj)
    _assign_material(obj, material)
    return obj


def add_cone(name, location, radius1, radius2, depth, material=None, vertices=32):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2,
                                    depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    _apply_scale(obj)
    _assign_material(obj, material)
    return obj


def add_plane(name, location, size, material=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    _assign_material(obj, material)
    return obj


def add_torus(name, location, major_radius=1.0, minor_radius=0.25,
              rotation=(0.0, 0.0, 0.0), material=None,
              major_segments=48, minor_segments=12):
    bpy.ops.mesh.primitive_torus_add(location=location,
                                     major_radius=major_radius,
                                     minor_radius=minor_radius,
                                     major_segments=major_segments,
                                     minor_segments=minor_segments)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name
    obj.rotation_euler = rotation
    _assign_material(obj, material)
    return obj


def gable_roof(name, location, length, width, height, material=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.scale = (length / 2.0, width / 2.0, height / 2.0)
    obj.name = name
    obj.data.name = name
    _apply_scale(obj)

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    # Collapse top vertices toward x=0 to form a ridge along Y.
    top_z = max(v.co.z for v in bm.verts)
    eps = 1e-4
    for v in bm.verts:
        if abs(v.co.z - top_z) < eps:
            v.co.x = 0.0
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.to_mesh(me)
    bm.free()
    me.update()
    _assign_material(obj, material)
    return obj


def safe_engine():
    items = bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items
    available = {it.identifier for it in items}
    for cand in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
        if cand in available:
            return cand
    # Fallback to whatever the enum advertises first.
    return next(iter(available)) if available else 'BLENDER_EEVEE'


def set_render(engine=None, resolution=(1280, 800), samples=64):
    scene = bpy.context.scene
    r = scene.render
    r.engine = engine if engine is not None else safe_engine()
    r.resolution_x = int(resolution[0])
    r.resolution_y = int(resolution[1])
    r.resolution_percentage = 100
    # EEVEE samples live under scene.eevee or scene.eevee_next depending on version.
    for attr in ('eevee_next', 'eevee'):
        if hasattr(scene, attr):
            grp = getattr(scene, attr)
            if hasattr(grp, 'taa_render_samples'):
                try:
                    grp.taa_render_samples = int(samples)
                except Exception:
                    pass
    if hasattr(scene, 'cycles') and r.engine == 'CYCLES':
        try:
            scene.cycles.samples = int(samples)
        except Exception:
            pass
    return r


def set_world_sky(top=(0.55, 0.75, 0.95), strength=1.2):
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new('SkillWorld')
        world.name = 'SkillWorld'
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = None
    for n in nt.nodes:
        if n.type == 'BACKGROUND':
            bg = n
            break
    if bg is None:
        bg = nt.nodes.new('ShaderNodeBackground')
        out = None
        for n in nt.nodes:
            if n.type == 'OUTPUT_WORLD':
                out = n
                break
        if out is None:
            out = nt.nodes.new('ShaderNodeOutputWorld')
        nt.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs['Color'].default_value = (top[0], top[1], top[2], 1.0)
    bg.inputs['Strength'].default_value = float(strength)
    return world


def warm_key_light(target=(0, 0, 0), energy=5.0, color=(1.0, 0.78, 0.55)):
    data = bpy.data.lights.new('SkillKey', type='AREA')
    data.energy = energy * 100
    data.size = 4.0
    data.color = color
    obj = bpy.data.objects.new('SkillKey', data)
    bpy.context.scene.collection.objects.link(obj)
    tx, ty, tz = target
    obj.location = (tx + 5, ty - 5, tz + 6)
    _aim_at(obj, target)
    return obj


def studio_dark_world(strength=0.3, color=(0.02, 0.02, 0.02)):
    return set_world_sky(top=color, strength=strength)


def boolean_difference(target, cutter, apply=True, delete_cutter=True):
    # Adds a Boolean DIFFERENCE modifier to target; cutter is subtracted.
    mod = target.modifiers.new(name='SkillBoolean', type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    if apply:
        for o in bpy.context.scene.objects:
            o.select_set(False)
        target.select_set(True)
        bpy.context.view_layer.objects.active = target
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if delete_cutter:
            bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def three_point_light(target=(0, 0, 0), key_energy=4.0):
    tx, ty, tz = target

    key_data = bpy.data.lights.new('SkillKey', type='SUN')
    key_data.energy = key_energy
    key = bpy.data.objects.new('SkillKey', key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = (tx + 6, ty - 6, tz + 10)
    key.rotation_euler = (math.radians(45), math.radians(15), math.radians(45))

    fill_data = bpy.data.lights.new('SkillFill', type='AREA')
    fill_data.energy = key_energy * 80
    fill_data.size = 5.0
    fill = bpy.data.objects.new('SkillFill', fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (tx - 8, ty - 4, tz + 4)
    _aim_at(fill, target)

    back_data = bpy.data.lights.new('SkillBack', type='AREA')
    back_data.energy = key_energy * 60
    back_data.size = 4.0
    back = bpy.data.objects.new('SkillBack', back_data)
    bpy.context.scene.collection.objects.link(back)
    back.location = (tx, ty + 8, tz + 6)
    _aim_at(back, target)

    return key, fill, back


def _aim_at(obj, target):
    direction = mathutils.Vector(target) - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()


def frame_camera(target=(0, 0, 0), distance=18, elevation_deg=35, azimuth_deg=45,
                 lens=35, name='SkillCamera'):
    # Remove any prior skill cameras so repeated auto_frame calls don't pile up
    # stale frusta that bloat bbox computations on later inspection.
    for o in list(bpy.data.objects):
        if o.type == 'CAMERA' and (o.name == name or o.name.startswith(name + '.')):
            bpy.data.objects.remove(o, do_unlink=True)
    for cd in list(bpy.data.cameras):
        if cd.users == 0:
            bpy.data.cameras.remove(cd)
    cam_data = bpy.data.cameras.new(name)
    cam_data.name = name
    cam_data.lens = lens
    cam = bpy.data.objects.new(name, cam_data)
    cam.name = name
    bpy.context.scene.collection.objects.link(cam)

    el = math.radians(elevation_deg)
    az = math.radians(azimuth_deg)
    tx, ty, tz = target
    cx = tx + distance * math.cos(el) * math.cos(az)
    cy = ty + distance * math.cos(el) * math.sin(az)
    cz = tz + distance * math.sin(el)
    cam.location = (cx, cy, cz)
    _aim_at(cam, target)

    bpy.context.scene.camera = cam
    return cam


def bbox_of(objects):
    # Cameras/lights also expose bound_box but their frusta blow up the result —
    # restrict to MESH/CURVE/SURFACE/META.
    mins = [float('inf')] * 3
    maxs = [float('-inf')] * 3
    any_pt = False
    for obj in objects:
        if obj is None or not hasattr(obj, 'bound_box'):
            continue
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            continue
        mw = obj.matrix_world
        for corner in obj.bound_box:
            world = mw @ mathutils.Vector(corner)
            for i in range(3):
                if world[i] < mins[i]:
                    mins[i] = world[i]
                if world[i] > maxs[i]:
                    maxs[i] = world[i]
            any_pt = True
    if not any_pt:
        return (mathutils.Vector((0, 0, 0)), mathutils.Vector((0, 0, 0)))
    return (mathutils.Vector(mins), mathutils.Vector(maxs))


def auto_frame(objects, padding=1.2, elevation_deg=30, azimuth_deg=45, lens=35,
               name='SkillCamera'):
    bb_min, bb_max = bbox_of(objects)
    center = (bb_min + bb_max) * 0.5
    extent = (bb_max - bb_min)
    radius = max(extent.length * 0.5, 0.5)

    scene = bpy.context.scene
    aspect = scene.render.resolution_x / max(scene.render.resolution_y, 1)
    # Sensor width default 36mm; horizontal FOV from focal length.
    sensor = 36.0
    hfov = 2.0 * math.atan((sensor / 2.0) / lens)
    vfov = 2.0 * math.atan(math.tan(hfov / 2.0) / max(aspect, 1e-3))
    fov = min(hfov, vfov)
    distance = (radius * padding) / math.tan(fov / 2.0)

    return frame_camera(target=tuple(center), distance=distance,
                        elevation_deg=elevation_deg, azimuth_deg=azimuth_deg,
                        lens=lens, name=name)


# ---------------------------------------------------------------------------
# Atmosphere & color management
# ---------------------------------------------------------------------------

def set_filmic_high_contrast():
    import bpy
    vs = bpy.context.scene.view_settings
    out = {}
    try:
        vt_items = [it.identifier for it in vs.bl_rna.properties["view_transform"].enum_items]
        if "Filmic" in vt_items:
            vs.view_transform = "Filmic"
        out["view_transform"] = vs.view_transform
    except Exception:
        out["view_transform"] = getattr(vs, "view_transform", None)
    try:
        look_items = [it.identifier for it in vs.bl_rna.properties["look"].enum_items]
        for cand in ("High Contrast", "Filmic - High Contrast",
                     "Medium High Contrast", "Filmic - Medium High Contrast"):
            if cand in look_items:
                vs.look = cand
                break
        out["look"] = vs.look
    except Exception:
        out["look"] = getattr(vs, "look", None)
    return out


def add_volumetric_fog(density=0.02, color=(0.7, 0.75, 0.85), anisotropy=0.0):
    import bpy
    scene = bpy.context.scene
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    out_node = next((n for n in nt.nodes if n.type == "OUTPUT_WORLD"), None)
    if out_node is None:
        out_node = nt.nodes.new("ShaderNodeOutputWorld")
    vol_in = out_node.inputs.get("Volume")
    if vol_in is not None and not vol_in.is_linked:
        scat = nt.nodes.new("ShaderNodeVolumeScatter")
        scat.location = (out_node.location.x - 300, out_node.location.y - 200)
        nt.links.new(scat.outputs[0], vol_in)
    scat_node = None
    if vol_in is not None and vol_in.is_linked:
        scat_node = vol_in.links[0].from_node
    if scat_node is not None:
        for key, val in (("Density", density), ("Color", (color[0], color[1], color[2], 1.0)),
                         ("Anisotropy", anisotropy)):
            inp = scat_node.inputs.get(key)
            if inp is None:
                continue
            try:
                inp.default_value = val
            except Exception:
                pass
    for ev_name in ("eevee", "eevee_next"):
        ev = getattr(scene, ev_name, None)
        if ev is None:
            continue
        for attr in ("use_volumetric", "use_volumetric_shadows"):
            if hasattr(ev, attr):
                try:
                    setattr(ev, attr, True)
                except Exception:
                    pass
    return nt


def add_camera_dof(target_obj=None, focus_distance=None, fstop=2.8, camera=None):
    import bpy
    if camera is None:
        camera = bpy.context.scene.camera
    if camera is None or getattr(camera, "type", None) != "CAMERA":
        return None
    dof = camera.data.dof
    dof.use_dof = True
    if target_obj is not None:
        try:
            dof.focus_object = target_obj
        except Exception:
            pass
    elif focus_distance is not None:
        try:
            dof.focus_distance = float(focus_distance)
        except Exception:
            pass
    try:
        dof.aperture_fstop = float(fstop)
    except Exception:
        pass
    return camera


def set_sunset_world(top=(0.95, 0.65, 0.40), bottom=(0.20, 0.18, 0.30), strength=0.8):
    import bpy, math
    scene = bpy.context.scene
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out_node = nt.nodes.new("ShaderNodeOutputWorld")
    out_node.location = (600, 0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (300, 0)
    try:
        bg.inputs["Strength"].default_value = float(strength)
    except Exception:
        pass
    nt.links.new(bg.outputs["Background"], out_node.inputs["Surface"])
    sky = None
    try:
        sky = nt.nodes.new("ShaderNodeTexSky")
    except Exception:
        sky = None
    if sky is not None:
        try:
            if hasattr(sky, "sky_type"):
                sky.sky_type = "NISHITA"
            if hasattr(sky, "sun_elevation"):
                sky.sun_elevation = math.radians(5.0)
            if hasattr(sky, "sun_rotation"):
                sky.sun_rotation = math.radians(180.0)
        except Exception:
            pass
        sky.location = (0, 0)
        nt.links.new(sky.outputs[0], bg.inputs["Color"])
        return nt
    try:
        coord = nt.nodes.new("ShaderNodeTexCoord"); coord.location = (-600, 0)
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-400, 0)
        ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-150, 0)
        nt.links.new(coord.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], ramp.inputs[0])
        cr = ramp.color_ramp
        cr.elements[0].position = 0.45
        cr.elements[0].color = (bottom[0], bottom[1], bottom[2], 1.0)
        cr.elements[1].position = 0.65
        cr.elements[1].color = (top[0], top[1], top[2], 1.0)
        nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    except Exception:
        try:
            bg.inputs["Color"].default_value = (top[0], top[1], top[2], 1.0)
        except Exception:
            pass
    return nt


def enable_eevee_quality():
    import bpy
    scene = bpy.context.scene
    applied = {}
    targets = [getattr(scene, name, None) for name in ("eevee", "eevee_next")]
    targets = [t for t in targets if t is not None]
    bool_attrs = ("use_ssr", "use_ssr_refraction", "use_soft_shadows",
                  "use_bloom", "use_gtao", "use_raytracing")
    for ev in targets:
        for attr in bool_attrs:
            if hasattr(ev, attr):
                try:
                    setattr(ev, attr, True)
                    applied[attr] = True
                except Exception:
                    pass
        if hasattr(ev, "taa_render_samples"):
            try:
                if int(getattr(ev, "taa_render_samples", 0)) < 128:
                    ev.taa_render_samples = 128
                applied["taa_render_samples"] = ev.taa_render_samples
            except Exception:
                pass
        if hasattr(ev, "taa_samples"):
            try:
                if int(getattr(ev, "taa_samples", 0)) < 16:
                    ev.taa_samples = 16
                applied["taa_samples"] = ev.taa_samples
            except Exception:
                pass
    return applied


# =====================================================================
# Gothic geometry section
# Self-contained builders for pointed-arch windows, crenellations,
# flying buttresses, low-poly trees, gargoyles, chains, and banners.
# Conventions: every created object gets obj.name and obj.data.name set,
# every obj.scale assignment is followed by _apply_scale, no UI-name lookups.
# =====================================================================


def _facing_to_z_rotation(facing):
    # Profile is built in the XZ plane (normal +Y => face looks toward -Y by default).
    # Rotate around Z so that the outward normal points in `facing`.
    table = {
        '-Y': 0.0,
        '+Y': math.pi,
        '+X': math.radians(90.0),
        '-X': math.radians(-90.0),
    }
    return table.get(facing, 0.0)


def pointed_arch_window(name, location, width, height, depth, material=None,
                        facing='-Y', frame_thickness=0.15, frame_material=None):
    w = float(width)
    h = float(height)
    d = float(depth)
    h_rect = h * 0.7

    def _build_profile_obj(obj_name, scale_xy=1.0, depth_scale=1.0):
        sx = scale_xy
        verts2d = [
            (-w * 0.5 * sx, 0.0),
            (w * 0.5 * sx, 0.0),
            (w * 0.5 * sx, h_rect * sx),
            (0.0, h * sx),
            (-w * 0.5 * sx, h_rect * sx),
        ]
        me = bpy.data.meshes.new(obj_name)
        bm = bmesh.new()
        bverts = [bm.verts.new((vx, 0.0, vz)) for (vx, vz) in verts2d]
        bm.verts.ensure_lookup_table()
        face = bm.faces.new(bverts)
        ext = bmesh.ops.extrude_face_region(bm, geom=[face])
        new_verts = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
        d_local = d * depth_scale
        for v in new_verts:
            v.co.y += d_local
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.name = obj_name
        obj = bpy.data.objects.new(obj_name, me)
        bpy.context.scene.collection.objects.link(obj)
        # Center slab on its depth so location refers to mid-thickness.
        for v in obj.data.vertices:
            v.co.y -= d_local * 0.5
        obj.location = location
        obj.rotation_euler = (0.0, 0.0, _facing_to_z_rotation(facing))
        return obj

    glass_name = name
    glass = _build_profile_obj(glass_name, scale_xy=1.0, depth_scale=1.0)
    glass.name = glass_name
    glass.data.name = glass_name
    _assign_material(glass, material)

    frame_obj = None
    if frame_material is not None:
        ft = float(frame_thickness)
        frame_name = name + '_Frame'
        outer = _build_profile_obj(frame_name, scale_xy=1.15, depth_scale=1.0 + ft)
        outer.name = frame_name
        outer.data.name = frame_name
        _assign_material(outer, frame_material)
        cutter_name = name + '_FrameCut'
        cutter = _build_profile_obj(cutter_name, scale_xy=1.0, depth_scale=1.0 + ft + 0.2)
        cutter.name = cutter_name
        cutter.data.name = cutter_name
        boolean_difference(outer, cutter, apply=True, delete_cutter=True)
        frame_obj = outer

    return (glass, frame_obj)


def crenellate_line(name_prefix, p0, p1, z_top, material=None,
                    merlon_w=0.4, merlon_h=0.7, merlon_t=0.4, gap=0.4):
    p0v = mathutils.Vector((float(p0[0]), float(p0[1])))
    p1v = mathutils.Vector((float(p1[0]), float(p1[1])))
    direction = p1v - p0v
    length = direction.length
    if length < 1e-6:
        return []
    step = merlon_w + gap
    count = int(math.floor((length + gap) / step))
    if count < 1:
        return []
    span_used = count * step - gap
    margin = (length - span_used) * 0.5 + merlon_w * 0.5
    dir_unit = direction.normalized()
    yaw = math.atan2(dir_unit.y, dir_unit.x)
    created = []
    for i in range(count):
        t = margin + i * step
        cx = p0v.x + dir_unit.x * t
        cy = p0v.y + dir_unit.y * t
        cz = z_top + merlon_h * 0.5
        obj_name = '%s_%02d' % (name_prefix, i)
        obj = add_cube(obj_name,
                       location=(cx, cy, cz),
                       scale=(merlon_w * 0.5, merlon_t * 0.5, merlon_h * 0.5),
                       material=material)
        obj.rotation_euler = (0.0, 0.0, yaw)
        created.append(obj)
    return created


def flying_buttress(name, anchor_low, anchor_high, thickness=0.4, material=None,
                    segments=8):
    p_low = mathutils.Vector((float(anchor_low[0]), float(anchor_low[1]), float(anchor_low[2])))
    p_high = mathutils.Vector((float(anchor_high[0]), float(anchor_high[1]), float(anchor_high[2])))
    seg = max(int(segments), 2)
    mid = (p_low + p_high) * 0.5
    lift = max(abs(p_high.z - p_low.z) * 0.35, 0.5)
    ctrl = mathutils.Vector((mid.x, mid.y, max(p_low.z, p_high.z) + lift))

    points = []
    for i in range(seg + 1):
        t = i / float(seg)
        omt = 1.0 - t
        pt = (omt * omt) * p_low + (2.0 * omt * t) * ctrl + (t * t) * p_high
        points.append(pt)

    horiz = mathutils.Vector((p_high.x - p_low.x, p_high.y - p_low.y, 0.0))
    if horiz.length < 1e-5:
        cross = mathutils.Vector((1.0, 0.0, 0.0))
    else:
        horiz.normalize()
        cross = mathutils.Vector((-horiz.y, horiz.x, 0.0))
    half_t = thickness * 0.5

    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    left_verts = []
    right_verts = []
    for p in points:
        lv = bm.verts.new((p.x - cross.x * half_t, p.y - cross.y * half_t, p.z))
        rv = bm.verts.new((p.x + cross.x * half_t, p.y + cross.y * half_t, p.z))
        left_verts.append(lv)
        right_verts.append(rv)
    bm.verts.ensure_lookup_table()
    faces = []
    for i in range(seg):
        f = bm.faces.new((left_verts[i], right_verts[i],
                          right_verts[i + 1], left_verts[i + 1]))
        faces.append(f)
    ext = bmesh.ops.extrude_face_region(bm, geom=faces)
    new_verts = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
    for v in new_verts:
        v.co.z += thickness
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.name = name
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.name = name
    obj.data.name = name
    _assign_material(obj, material)
    return obj


def low_poly_tree(name, location, height=4.0, trunk_radius=0.18,
                  leaf_color=(0.18, 0.45, 0.20), trunk_color=(0.30, 0.18, 0.08)):
    trunk_mat = bpy.data.materials.get('TreeTrunk')
    if trunk_mat is None:
        trunk_mat = mat('TreeTrunk', (trunk_color[0], trunk_color[1], trunk_color[2], 1.0),
                        roughness=0.85)
    leaf_mat = bpy.data.materials.get('TreeLeaves')
    if leaf_mat is None:
        leaf_mat = mat('TreeLeaves', (leaf_color[0], leaf_color[1], leaf_color[2], 1.0),
                       roughness=0.8)

    h = float(height)
    lx, ly, lz = float(location[0]), float(location[1]), float(location[2])
    trunk_h = h * 0.3
    root_name = 'TreeRoot_' + name
    root = bpy.data.objects.new(root_name, None)
    root.name = root_name
    root.location = (lx, ly, lz)
    bpy.context.scene.collection.objects.link(root)

    trunk = add_cyl(name + '_Trunk', location=(lx, ly, lz + trunk_h * 0.5),
                    radius=trunk_radius, depth=trunk_h, material=trunk_mat)
    trunk.parent = root

    cone1_h = h * 0.35
    cone1_z = lz + trunk_h + cone1_h * 0.5
    cone1 = add_cone(name + '_Cone1', location=(lx, ly, cone1_z),
                     radius1=h * 0.45, radius2=h * 0.35, depth=cone1_h,
                     material=leaf_mat)
    cone1.parent = root

    cone2_h = h * 0.45
    cone2_z = lz + trunk_h + cone1_h + cone2_h * 0.5
    cone2 = add_cone(name + '_Cone2', location=(lx, ly, cone2_z),
                     radius1=h * 0.32, radius2=h * 0.10, depth=cone2_h,
                     material=leaf_mat)
    cone2.parent = root

    cone3_h = h * 0.10
    cone3_z = lz + trunk_h + cone1_h + cone2_h + cone3_h * 0.5
    cone3 = add_cone(name + '_Cone3', location=(lx, ly, cone3_z),
                     radius1=h * 0.10, radius2=0.0, depth=cone3_h,
                     material=leaf_mat)
    cone3.parent = root

    return root


def add_gargoyle(name, location, facing='+X', material=None, scale=0.5):
    # Build all children at LOCAL offsets around origin, then translate the root.
    # Doing it the other way (placing children at world coords AND parenting to a
    # root at the same world coords) doubles their position via parent transform.
    s = float(scale)
    root_name = 'GargoyleRoot_' + name
    root = bpy.data.objects.new(root_name, None)
    root.name = root_name
    bpy.context.scene.collection.objects.link(root)

    body_w, body_d, body_h = 0.6 * s, 0.4 * s, 0.3 * s
    head_w, head_d, head_h = 0.3 * s, 0.3 * s, 0.25 * s
    body_cz = body_h * 0.5

    children = []
    body = add_cube(name + '_Body', location=(0, 0, body_cz),
                    scale=(body_w * 0.5, body_d * 0.5, body_h * 0.5),
                    material=material)
    children.append(body)

    head_off_x = body_w * 0.5 + head_w * 0.5
    head_cz = body_h + head_h * 0.5
    head = add_cube(name + '_Head', location=(head_off_x, 0, head_cz),
                    scale=(head_w * 0.5, head_d * 0.5, head_h * 0.5),
                    material=material)
    children.append(head)

    ear_r = 0.06 * s
    ear_h = 0.15 * s
    ear_z = head_cz + head_h * 0.5 + ear_h * 0.5
    for i, ey in enumerate((-head_d * 0.3, head_d * 0.3)):
        ear = add_cone(name + ('_Ear%d' % i),
                       location=(head_off_x, ey, ear_z),
                       radius1=ear_r, radius2=0.0, depth=ear_h,
                       material=material)
        children.append(ear)

    tail_len = 0.5 * s
    tail_th = 0.08 * s
    tail_x = -body_w * 0.5 - tail_len * 0.4
    tail_z = body_h * 0.6
    tail = add_cube(name + '_Tail', location=(tail_x, 0, tail_z),
                    scale=(tail_len * 0.5, tail_th * 0.5, tail_th * 0.5),
                    material=material)
    tail.rotation_euler = (0.0, math.radians(-30.0), 0.0)
    children.append(tail)

    leg_w = 0.08 * s
    leg_h = body_cz
    leg_off_x = body_w * 0.35
    leg_off_y = body_d * 0.30
    for i, (sx_sign, sy_sign) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        leg = add_cube(name + ('_Leg%d' % i),
                       location=(sx_sign * leg_off_x,
                                 sy_sign * leg_off_y,
                                 -leg_h * 0.5),
                       scale=(leg_w * 0.5, leg_w * 0.5, leg_h * 0.5),
                       material=material)
        children.append(leg)

    for c in children:
        c.parent = root

    facing_map = {
        '+X': 0.0,
        '+Y': math.radians(90.0),
        '-X': math.radians(180.0),
        '-Y': math.radians(-90.0),
    }
    root.rotation_euler = (0.0, 0.0, facing_map.get(facing, 0.0))
    root.location = (float(location[0]), float(location[1]), float(location[2]))
    return root


def chain_between(name_prefix, p_start, p_end, link_count=8, link_radius=0.08,
                  material=None):
    p0 = mathutils.Vector((float(p_start[0]), float(p_start[1]), float(p_start[2])))
    p1 = mathutils.Vector((float(p_end[0]), float(p_end[1]), float(p_end[2])))
    direction = p1 - p0
    if direction.length < 1e-6:
        return []
    dir_unit = direction.normalized()
    base_quat = dir_unit.to_track_quat('Z', 'Y')
    base_euler = base_quat.to_euler()

    created = []
    major = 0.12
    for i in range(int(link_count)):
        t = (i + 0.5) / float(link_count)
        center = p0 + direction * t
        link_name = '%s_%02d' % (name_prefix, i)
        torus = add_torus(link_name, location=tuple(center),
                          major_radius=major, minor_radius=link_radius,
                          rotation=(base_euler.x, base_euler.y, base_euler.z),
                          material=material,
                          major_segments=24, minor_segments=8)
        if i % 2 == 1:
            extra_quat = mathutils.Quaternion(dir_unit, math.radians(90.0))
            combined = extra_quat @ base_quat
            torus.rotation_euler = combined.to_euler()
        created.append(torus)
    return created


def flag_banner(name, location, width=0.8, height=1.2,
                color=(0.7, 0.08, 0.08), pole_height=2.0):
    lx, ly, lz = float(location[0]), float(location[1]), float(location[2])

    pole_mat = bpy.data.materials.get('BannerPole')
    if pole_mat is None:
        pole_mat = mat('BannerPole', (0.55, 0.42, 0.18, 1.0),
                       roughness=0.45, metallic=0.85)
    banner_mat = bpy.data.materials.get('Banner_' + name)
    if banner_mat is None:
        banner_mat = mat('Banner_' + name,
                         (color[0], color[1], color[2], 1.0),
                         roughness=0.75)

    pole_name = name + '_Pole'
    pole = add_cyl(pole_name, location=(lx, ly, lz + pole_height * 0.5),
                   radius=0.04, depth=pole_height, material=pole_mat)

    w = float(width)
    h = float(height)
    th = 0.02
    banner_name = name + '_Banner'
    me = bpy.data.meshes.new(banner_name)
    bm = bmesh.new()
    top_z = lz + pole_height
    bot_z = top_z - h
    # Fishtail pentagon: top edge at top of pole, bottom V-cut.
    v_tl = bm.verts.new((0.0, 0.0, top_z))
    v_tr = bm.verts.new((w, 0.0, top_z))
    v_mr = bm.verts.new((w, 0.0, bot_z + h * 0.25))
    v_bc = bm.verts.new((w * 0.5, 0.0, bot_z))
    v_ml = bm.verts.new((0.0, 0.0, bot_z + h * 0.25))
    bm.verts.ensure_lookup_table()
    face = bm.faces.new((v_tl, v_tr, v_mr, v_bc, v_ml))
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    new_verts = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
    for v in new_verts:
        v.co.y += th
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.name = banner_name
    banner = bpy.data.objects.new(banner_name, me)
    bpy.context.scene.collection.objects.link(banner)
    banner.name = banner_name
    banner.data.name = banner_name
    banner.location = (lx + 0.04, ly - th * 0.5, 0.0)
    _assign_material(banner, banner_mat)

    return (pole, banner)


# ---------------------------------------------------------------------------
# Procedural materials
# ---------------------------------------------------------------------------
# All helpers below build node trees by `n.type` checks only (display names are
# localized under ru_RU; identifiers stay English). Each function rebuilds the
# tree on every call so a stale graph from a previous run doesn't leak through.

def _proc_init(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.name = name
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    out.location = (600, 0)
    bsdf.location = (300, 0)
    return m, nt, bsdf, out


def _proc_set(bsdf, key, value):
    if key in bsdf.inputs:
        try:
            bsdf.inputs[key].default_value = value
            return True
        except Exception:
            return False
    return False


def _proc_rgba(c):
    if len(c) >= 4:
        return (c[0], c[1], c[2], c[3])
    return (c[0], c[1], c[2], 1.0)


def procedural_stone(name, base=(0.45, 0.42, 0.38), variation=0.15,
                     bumpiness=0.3, mortar_dark=0.5):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1400, 0)

    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.voronoi_dimensions = '3D'
    vor.feature = 'F1'
    vor.distance = 'EUCLIDEAN'
    vor.inputs['Scale'].default_value = 4.0
    vor.location = (-1100, 200)
    nt.links.new(tex.outputs['Generated'], vor.inputs['Vector'])

    ramp_mortar = nt.nodes.new('ShaderNodeValToRGB')
    ramp_mortar.color_ramp.elements[0].position = 0.0
    ramp_mortar.color_ramp.elements[0].color = (mortar_dark * 0.4, mortar_dark * 0.4,
                                                 mortar_dark * 0.4, 1.0)
    ramp_mortar.color_ramp.elements[1].position = 0.08
    ramp_mortar.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    ramp_mortar.location = (-850, 200)
    nt.links.new(vor.outputs['Distance'], ramp_mortar.inputs['Fac'])

    noise_big = nt.nodes.new('ShaderNodeTexNoise')
    noise_big.inputs['Scale'].default_value = 8.0
    noise_big.location = (-1100, -100)
    nt.links.new(tex.outputs['Generated'], noise_big.inputs['Vector'])

    ramp_color = nt.nodes.new('ShaderNodeValToRGB')
    lo = (max(0.0, base[0] - variation), max(0.0, base[1] - variation),
          max(0.0, base[2] - variation), 1.0)
    hi = (min(1.0, base[0] + variation), min(1.0, base[1] + variation),
          min(1.0, base[2] + variation), 1.0)
    ramp_color.color_ramp.elements[0].color = lo
    ramp_color.color_ramp.elements[1].color = hi
    ramp_color.location = (-850, -100)
    nt.links.new(noise_big.outputs['Fac'], ramp_color.inputs['Fac'])

    mix_col = nt.nodes.new('ShaderNodeMixRGB')
    mix_col.blend_type = 'MULTIPLY'
    mix_col.inputs['Fac'].default_value = 1.0
    mix_col.location = (-550, 0)
    nt.links.new(ramp_color.outputs['Color'], mix_col.inputs['Color1'])
    nt.links.new(ramp_mortar.outputs['Color'], mix_col.inputs['Color2'])
    nt.links.new(mix_col.outputs['Color'], bsdf.inputs['Base Color'])

    noise_rough = nt.nodes.new('ShaderNodeTexNoise')
    noise_rough.inputs['Scale'].default_value = 12.0
    noise_rough.location = (-1100, -350)
    nt.links.new(tex.outputs['Generated'], noise_rough.inputs['Vector'])

    ramp_rough = nt.nodes.new('ShaderNodeValToRGB')
    ramp_rough.color_ramp.elements[0].color = (0.7, 0.7, 0.7, 1.0)
    ramp_rough.color_ramp.elements[1].color = (0.95, 0.95, 0.95, 1.0)
    ramp_rough.location = (-850, -350)
    nt.links.new(noise_rough.outputs['Fac'], ramp_rough.inputs['Fac'])
    if 'Roughness' in bsdf.inputs:
        nt.links.new(ramp_rough.outputs['Color'], bsdf.inputs['Roughness'])

    noise_bump = nt.nodes.new('ShaderNodeTexNoise')
    noise_bump.inputs['Scale'].default_value = 20.0
    noise_bump.location = (-1100, -600)
    nt.links.new(tex.outputs['Generated'], noise_bump.inputs['Vector'])

    mix_bump = nt.nodes.new('ShaderNodeMixRGB')
    mix_bump.blend_type = 'MULTIPLY'
    mix_bump.inputs['Fac'].default_value = 1.0
    mix_bump.location = (-550, -400)
    nt.links.new(ramp_mortar.outputs['Color'], mix_bump.inputs['Color1'])
    nt.links.new(noise_bump.outputs['Fac'], mix_bump.inputs['Color2'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = float(bumpiness)
    bump.inputs['Distance'].default_value = 0.2
    bump.location = (-200, -400)
    nt.links.new(mix_bump.outputs['Color'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    _proc_set(bsdf, 'Metallic', 0.0)
    return m


def procedural_slate_tiles(name, base=(0.10, 0.11, 0.15), tile_scale=8.0):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1500, 0)
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.location = (-1300, 0)
    nt.links.new(tex.outputs['Generated'], mapping.inputs['Vector'])

    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.inputs['Scale'].default_value = float(tile_scale)
    if 'Mortar Size' in brick.inputs:
        brick.inputs['Mortar Size'].default_value = 0.02
    c1 = _proc_rgba(base)
    c2 = (base[0] * 0.85, base[1] * 0.85, base[2] * 0.85, 1.0)
    brick.inputs['Color1'].default_value = c1
    brick.inputs['Color2'].default_value = c2
    if 'Mortar' in brick.inputs:
        brick.inputs['Mortar'].default_value = (0.02, 0.02, 0.02, 1.0)
    brick.location = (-900, 0)
    nt.links.new(mapping.outputs['Vector'], brick.inputs['Vector'])
    nt.links.new(brick.outputs['Color'], bsdf.inputs['Base Color'])

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 30.0
    noise.location = (-900, -300)
    nt.links.new(mapping.outputs['Vector'], noise.inputs['Vector'])

    mix_h = nt.nodes.new('ShaderNodeMixRGB')
    mix_h.blend_type = 'ADD'
    mix_h.inputs['Fac'].default_value = 0.4
    mix_h.location = (-550, -200)
    nt.links.new(brick.outputs['Fac'], mix_h.inputs['Color1'])
    nt.links.new(noise.outputs['Fac'], mix_h.inputs['Color2'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.3
    bump.location = (-200, -300)
    nt.links.new(mix_h.outputs['Color'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    _proc_set(bsdf, 'Roughness', 0.3)
    _proc_set(bsdf, 'Metallic', 0.0)
    _proc_set(bsdf, 'Specular IOR Level', 0.7)
    _proc_set(bsdf, 'Specular', 0.7)
    return m


def procedural_wood(name, base=(0.30, 0.18, 0.08), grain_scale=12.0):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1500, 0)

    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.inputs['Scale'].default_value = float(grain_scale)
    wave.inputs['Distortion'].default_value = 1.5
    wave.inputs['Detail'].default_value = 4.0
    wave.location = (-1100, 100)
    nt.links.new(tex.outputs['Generated'], wave.inputs['Vector'])

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    dark = (base[0] * 0.6, base[1] * 0.6, base[2] * 0.6, 1.0)
    light = (min(1.0, base[0] * 1.4), min(1.0, base[1] * 1.4),
             min(1.0, base[2] * 1.4), 1.0)
    ramp.color_ramp.elements[0].color = dark
    ramp.color_ramp.elements[1].color = light
    ramp.location = (-800, 100)
    nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 25.0
    noise.location = (-1100, -200)
    nt.links.new(tex.outputs['Generated'], noise.inputs['Vector'])

    mix = nt.nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Fac'].default_value = 0.3
    mix.location = (-500, 0)
    nt.links.new(ramp.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(noise.outputs['Color'], mix.inputs['Color2'])
    nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])

    mix_h = nt.nodes.new('ShaderNodeMixRGB')
    mix_h.blend_type = 'ADD'
    mix_h.inputs['Fac'].default_value = 0.3
    mix_h.location = (-500, -300)
    nt.links.new(wave.outputs['Fac'], mix_h.inputs['Color1'])
    nt.links.new(noise.outputs['Fac'], mix_h.inputs['Color2'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    bump.inputs['Distance'].default_value = 0.1
    bump.location = (-200, -300)
    nt.links.new(mix_h.outputs['Color'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    ramp_r = nt.nodes.new('ShaderNodeValToRGB')
    ramp_r.color_ramp.elements[0].color = (0.7, 0.7, 0.7, 1.0)
    ramp_r.color_ramp.elements[1].color = (0.9, 0.9, 0.9, 1.0)
    ramp_r.location = (-500, -550)
    nt.links.new(noise.outputs['Fac'], ramp_r.inputs['Fac'])
    if 'Roughness' in bsdf.inputs:
        nt.links.new(ramp_r.outputs['Color'], bsdf.inputs['Roughness'])

    _proc_set(bsdf, 'Metallic', 0.0)
    return m


def procedural_grass(name, base=(0.18, 0.34, 0.12), variation=0.10):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1500, 0)

    noise_fine = nt.nodes.new('ShaderNodeTexNoise')
    noise_fine.inputs['Scale'].default_value = 50.0
    noise_fine.location = (-1100, 100)
    nt.links.new(tex.outputs['Generated'], noise_fine.inputs['Vector'])

    noise_big = nt.nodes.new('ShaderNodeTexNoise')
    noise_big.inputs['Scale'].default_value = 5.0
    noise_big.location = (-1100, -150)
    nt.links.new(tex.outputs['Generated'], noise_big.inputs['Vector'])

    mix_n = nt.nodes.new('ShaderNodeMixRGB')
    mix_n.blend_type = 'MIX'
    mix_n.inputs['Fac'].default_value = 0.5
    mix_n.location = (-800, 0)
    nt.links.new(noise_fine.outputs['Fac'], mix_n.inputs['Color1'])
    nt.links.new(noise_big.outputs['Fac'], mix_n.inputs['Color2'])

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    lo = (max(0.0, base[0] - variation), max(0.0, base[1] - variation),
          max(0.0, base[2] - variation), 1.0)
    hi = (min(1.0, base[0] + variation), min(1.0, base[1] + variation),
          min(1.0, base[2] + variation), 1.0)
    ramp.color_ramp.elements[0].color = lo
    ramp.color_ramp.elements[1].color = hi
    ramp.location = (-500, 0)
    nt.links.new(mix_n.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.05
    bump.inputs['Distance'].default_value = 0.05
    bump.location = (-200, -300)
    nt.links.new(noise_fine.outputs['Fac'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    _proc_set(bsdf, 'Roughness', 0.95)
    _proc_set(bsdf, 'Metallic', 0.0)
    return m


def procedural_dirt_path(name, base=(0.30, 0.22, 0.14), gravel_scale=20.0):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1500, 0)

    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.voronoi_dimensions = '3D'
    vor.feature = 'F1'
    vor.distance = 'EUCLIDEAN'
    vor.inputs['Scale'].default_value = float(gravel_scale)
    vor.location = (-1100, 150)
    nt.links.new(tex.outputs['Generated'], vor.inputs['Vector'])

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 6.0
    noise.location = (-1100, -150)
    nt.links.new(tex.outputs['Generated'], noise.inputs['Vector'])

    ramp_base = nt.nodes.new('ShaderNodeValToRGB')
    dark = (base[0] * 0.7, base[1] * 0.7, base[2] * 0.7, 1.0)
    light = (min(1.0, base[0] * 1.3), min(1.0, base[1] * 1.3),
             min(1.0, base[2] * 1.3), 1.0)
    ramp_base.color_ramp.elements[0].color = dark
    ramp_base.color_ramp.elements[1].color = light
    ramp_base.location = (-800, -150)
    nt.links.new(noise.outputs['Fac'], ramp_base.inputs['Fac'])

    ramp_grav = nt.nodes.new('ShaderNodeValToRGB')
    ramp_grav.color_ramp.elements[0].color = (
        min(1.0, base[0] * 1.5), min(1.0, base[1] * 1.5), min(1.0, base[2] * 1.5), 1.0)
    ramp_grav.color_ramp.elements[1].color = dark
    ramp_grav.location = (-800, 150)
    nt.links.new(vor.outputs['Distance'], ramp_grav.inputs['Fac'])

    mix = nt.nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MIX'
    mix.inputs['Fac'].default_value = 0.5
    mix.location = (-500, 0)
    nt.links.new(ramp_base.outputs['Color'], mix.inputs['Color1'])
    nt.links.new(ramp_grav.outputs['Color'], mix.inputs['Color2'])
    nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])

    mix_h = nt.nodes.new('ShaderNodeMixRGB')
    mix_h.blend_type = 'ADD'
    mix_h.inputs['Fac'].default_value = 0.5
    mix_h.location = (-500, -350)
    nt.links.new(vor.outputs['Distance'], mix_h.inputs['Color1'])
    nt.links.new(noise.outputs['Fac'], mix_h.inputs['Color2'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.4
    bump.inputs['Distance'].default_value = 0.2
    bump.location = (-200, -350)
    nt.links.new(mix_h.outputs['Color'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    _proc_set(bsdf, 'Roughness', 0.95)
    _proc_set(bsdf, 'Metallic', 0.0)
    return m


def procedural_water(name, base=(0.02, 0.07, 0.12), wave_scale=6.0):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1500, 0)

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = float(wave_scale)
    noise.inputs['Detail'].default_value = 4.0
    noise.inputs['Distortion'].default_value = 0.5
    noise.location = (-1100, -200)
    nt.links.new(tex.outputs['Generated'], noise.inputs['Vector'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.05
    bump.inputs['Distance'].default_value = 0.05
    bump.location = (-200, -300)
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    _proc_set(bsdf, 'Base Color', _proc_rgba(base))
    _proc_set(bsdf, 'Roughness', 0.05)
    _proc_set(bsdf, 'Metallic', 0.0)
    for tk in ('Transmission Weight', 'Transmission'):
        if tk in bsdf.inputs:
            try:
                bsdf.inputs[tk].default_value = 0.8
                break
            except Exception:
                pass
    return m


def procedural_metal_aged(name, base=(0.7, 0.55, 0.25), patina=(0.18, 0.35, 0.30),
                          patina_amount=0.4):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1500, 0)

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 4.0
    noise.inputs['Detail'].default_value = 6.0
    noise.location = (-1200, 0)
    nt.links.new(tex.outputs['Generated'], noise.inputs['Vector'])

    pos = max(0.05, min(0.95, 1.0 - float(patina_amount)))

    ramp_mask = nt.nodes.new('ShaderNodeValToRGB')
    ramp_mask.color_ramp.elements[0].position = max(0.0, pos - 0.15)
    ramp_mask.color_ramp.elements[1].position = min(1.0, pos + 0.15)
    ramp_mask.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp_mask.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    ramp_mask.location = (-900, 0)
    nt.links.new(noise.outputs['Fac'], ramp_mask.inputs['Fac'])

    mix_col = nt.nodes.new('ShaderNodeMixRGB')
    mix_col.blend_type = 'MIX'
    mix_col.location = (-600, 200)
    mix_col.inputs['Color1'].default_value = _proc_rgba(base)
    mix_col.inputs['Color2'].default_value = _proc_rgba(patina)
    nt.links.new(ramp_mask.outputs['Color'], mix_col.inputs['Fac'])
    nt.links.new(mix_col.outputs['Color'], bsdf.inputs['Base Color'])

    ramp_metal = nt.nodes.new('ShaderNodeValToRGB')
    ramp_metal.color_ramp.elements[0].position = max(0.0, pos - 0.15)
    ramp_metal.color_ramp.elements[1].position = min(1.0, pos + 0.15)
    ramp_metal.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    ramp_metal.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    ramp_metal.location = (-600, -50)
    nt.links.new(noise.outputs['Fac'], ramp_metal.inputs['Fac'])
    if 'Metallic' in bsdf.inputs:
        nt.links.new(ramp_metal.outputs['Color'], bsdf.inputs['Metallic'])

    ramp_rough = nt.nodes.new('ShaderNodeValToRGB')
    ramp_rough.color_ramp.elements[0].position = max(0.0, pos - 0.15)
    ramp_rough.color_ramp.elements[1].position = min(1.0, pos + 0.15)
    ramp_rough.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1.0)
    ramp_rough.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1.0)
    ramp_rough.location = (-600, -300)
    nt.links.new(noise.outputs['Fac'], ramp_rough.inputs['Fac'])
    if 'Roughness' in bsdf.inputs:
        nt.links.new(ramp_rough.outputs['Color'], bsdf.inputs['Roughness'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    bump.inputs['Distance'].default_value = 0.05
    bump.location = (-200, -500)
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    return m


def procedural_canvas_flag(name, base=(0.7, 0.08, 0.08), wear=0.3):
    m, nt, bsdf, out = _proc_init(name)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-1500, 0)

    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.voronoi_dimensions = '3D'
    vor.feature = 'F1'
    vor.inputs['Scale'].default_value = 100.0
    vor.location = (-1100, 150)
    nt.links.new(tex.outputs['Generated'], vor.inputs['Vector'])

    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 20.0
    noise.location = (-1100, -150)
    nt.links.new(tex.outputs['Generated'], noise.inputs['Vector'])

    ramp_col = nt.nodes.new('ShaderNodeValToRGB')
    dark = (base[0] * (1.0 - wear), base[1] * (1.0 - wear),
            base[2] * (1.0 - wear), 1.0)
    light = _proc_rgba(base)
    ramp_col.color_ramp.elements[0].color = dark
    ramp_col.color_ramp.elements[1].color = light
    ramp_col.location = (-800, -150)
    nt.links.new(noise.outputs['Fac'], ramp_col.inputs['Fac'])
    nt.links.new(ramp_col.outputs['Color'], bsdf.inputs['Base Color'])

    mix_h = nt.nodes.new('ShaderNodeMixRGB')
    mix_h.blend_type = 'ADD'
    mix_h.inputs['Fac'].default_value = 0.5
    mix_h.location = (-500, 0)
    nt.links.new(vor.outputs['Distance'], mix_h.inputs['Color1'])
    nt.links.new(noise.outputs['Fac'], mix_h.inputs['Color2'])

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.05
    bump.inputs['Distance'].default_value = 0.02
    bump.location = (-200, -300)
    nt.links.new(mix_h.outputs['Color'], bump.inputs['Height'])
    if 'Normal' in bsdf.inputs:
        nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    _proc_set(bsdf, 'Roughness', 0.85)
    _proc_set(bsdf, 'Metallic', 0.0)
    return m


# =====================================================================
# Castle interior / courtyard section
# Builders for stone block bands, tower arrow-slits, paving, well, barrel,
# haybale, wall torches, market stall. All composite-helpers (root Empty)
# build their children at LOCAL offsets around (0,0,0), then translate the
# root — placing children at world coords AND parenting to a root at the
# same world coords would double their position via parent transform.
# =====================================================================


import random as _ci_random


def stone_block_band(name_prefix, p0, p1, z_bottom, z_top, block_w=0.6,
                     block_h=0.4, depth=0.15, material=None, jitter=0.05,
                     seed=0):
    """Decorative brick-like stone band laid along a wall segment as raised geometry."""
    _ci_random.seed(seed)
    p0v = mathutils.Vector((float(p0[0]), float(p0[1])))
    p1v = mathutils.Vector((float(p1[0]), float(p1[1])))
    direction = p1v - p0v
    length = direction.length
    if length < 1e-6 or z_top <= z_bottom:
        return []
    dir_unit = direction.normalized()
    yaw = math.atan2(dir_unit.y, dir_unit.x)
    normal = mathutils.Vector((-dir_unit.y, dir_unit.x))  # outward normal (perp, +90 deg)
    half_w = block_w * 0.5
    half_h = block_h * 0.5
    half_d = depth * 0.5

    rows = max(int(math.floor((z_top - z_bottom) / block_h)), 0)
    if rows < 1:
        return []
    created = []
    for r in range(rows):
        z_center = z_bottom + (r + 0.5) * block_h
        phase = (block_w * 0.5) if (r % 2 == 1) else 0.0
        # Effective span starts from -phase so neighbouring rows are offset.
        n_blocks = int(math.floor((length - phase) / block_w))
        if n_blocks < 1:
            continue
        span_used = n_blocks * block_w
        margin = phase + (length - phase - span_used) * 0.5 + half_w
        for i in range(n_blocks):
            t = margin + i * block_w
            jx = _ci_random.uniform(-jitter, jitter)
            jz = _ci_random.uniform(-jitter, jitter)
            t_eff = t + jx
            cx = p0v.x + dir_unit.x * t_eff + normal.x * (half_d + 0.005)
            cy = p0v.y + dir_unit.y * t_eff + normal.y * (half_d + 0.005)
            cz = z_center + jz
            obj_name = '%s_r%02d_b%02d' % (name_prefix, r, i)
            obj = add_cube(obj_name,
                           location=(cx, cy, cz),
                           scale=(half_w, half_d, half_h),
                           material=material)
            obj.rotation_euler = (0.0, 0.0, yaw)
            created.append(obj)
    return created


def tower_windows(name_prefix, center_xy, tower_radius, z_levels,
                  count_per_level=4, slit_w=0.18, slit_h=1.2,
                  material=None, frame_material=None):
    """Place arrow-slit windows around a round tower at given vertical levels."""
    cx = float(center_xy[0])
    cy = float(center_xy[1])
    r_out = float(tower_radius) + 0.02
    half_w = slit_w * 0.5
    half_h = slit_h * 0.5
    slit_d = 0.05
    half_d = slit_d * 0.5
    created = []
    for li, z in enumerate(z_levels):
        zc = float(z)
        for i in range(int(count_per_level)):
            ang = (2.0 * math.pi * i) / float(count_per_level)
            # Place window flush against tower at distance r_out along radial direction.
            wx = cx + math.cos(ang) * r_out
            wy = cy + math.sin(ang) * r_out
            yaw = ang + math.radians(90.0)
            obj_name = '%s_L%02d_W%02d' % (name_prefix, li, i)
            slit = add_cube(obj_name,
                            location=(wx, wy, zc),
                            scale=(half_w, half_d, half_h),
                            material=material)
            slit.rotation_euler = (0.0, 0.0, yaw)
            created.append(slit)
            if frame_material is not None:
                frame_w = slit_w + 0.10
                frame_h = slit_h + 0.10
                frame_d = slit_d + 0.04
                # Push frame slightly inward (toward tower) so slit reads as opening.
                fx = cx + math.cos(ang) * (r_out - 0.01)
                fy = cy + math.sin(ang) * (r_out - 0.01)
                frame_name = '%s_L%02d_W%02d_Frame' % (name_prefix, li, i)
                frame = add_cube(frame_name,
                                 location=(fx, fy, zc),
                                 scale=(frame_w * 0.5, frame_d * 0.5,
                                        frame_h * 0.5),
                                 material=frame_material)
                frame.rotation_euler = (0.0, 0.0, yaw)
                created.append(frame)
    return created


def paving_stones(name_prefix, area_min, area_max, tile_size=0.5,
                  height=0.05, material=None, jitter=0.04,
                  color_jitter=0.08):
    """Fill a rectangular area with slightly jittered paving tiles parented to an Empty."""
    xmin = float(area_min[0])
    ymin = float(area_min[1])
    xmax = float(area_max[0])
    ymax = float(area_max[1])
    if xmax <= xmin or ymax <= ymin:
        return None
    nx = max(int(math.floor((xmax - xmin) / tile_size)), 1)
    ny = max(int(math.floor((ymax - ymin) / tile_size)), 1)
    margin_x = (xmax - xmin - nx * tile_size) * 0.5
    margin_y = (ymax - ymin - ny * tile_size) * 0.5
    half_t = tile_size * 0.5
    half_h = max(height, 0.001) * 0.5
    z_center = half_h + 0.001  # tiny lift above ground

    root_name = 'PavingRoot_' + name_prefix
    root = bpy.data.objects.new(root_name, None)
    root.name = root_name
    bpy.context.scene.collection.objects.link(root)

    # Try to capture base color of supplied material for color_jitter clones.
    base_rgba = None
    if material is not None and color_jitter > 0.0:
        try:
            for n in material.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED' and 'Base Color' in n.inputs:
                    bc = n.inputs['Base Color'].default_value
                    base_rgba = (bc[0], bc[1], bc[2], bc[3])
                    break
        except Exception:
            base_rgba = None

    _ci_random.seed(0)
    for ix in range(nx):
        for iy in range(ny):
            cx = xmin + margin_x + (ix + 0.5) * tile_size + _ci_random.uniform(-jitter, jitter)
            cy = ymin + margin_y + (iy + 0.5) * tile_size + _ci_random.uniform(-jitter, jitter)
            tile_mat = material
            if base_rgba is not None and color_jitter > 0.0:
                dr = _ci_random.uniform(-color_jitter, color_jitter)
                dg = _ci_random.uniform(-color_jitter, color_jitter)
                db = _ci_random.uniform(-color_jitter, color_jitter)
                clone_name = '%s_TileMat_%02d_%02d' % (name_prefix, ix, iy)
                tile_mat = bpy.data.materials.get(clone_name)
                if tile_mat is None:
                    tile_mat = material.copy()
                    tile_mat.name = clone_name
                try:
                    for n in tile_mat.node_tree.nodes:
                        if n.type == 'BSDF_PRINCIPLED' and 'Base Color' in n.inputs:
                            n.inputs['Base Color'].default_value = (
                                max(0.0, min(1.0, base_rgba[0] + dr)),
                                max(0.0, min(1.0, base_rgba[1] + dg)),
                                max(0.0, min(1.0, base_rgba[2] + db)),
                                base_rgba[3])
                            break
                except Exception:
                    pass
            tile_name = '%s_T_%02d_%02d' % (name_prefix, ix, iy)
            tile = add_cube(tile_name,
                            location=(cx, cy, z_center),
                            scale=(half_t, half_t, half_h),
                            material=tile_mat)
            tile.rotation_euler = (0.0, 0.0, _ci_random.uniform(-0.05, 0.05))
            tile.parent = root
    return root


def add_well(name, location, radius=1.0, depth=0.6, well_height=1.0,
             stone_material=None, water_material=None):
    """Round stone courtyard well with water surface and a small wooden roof."""
    root_name = 'WellRoot_' + name
    root = bpy.data.objects.new(root_name, None)
    root.name = root_name
    bpy.context.scene.collection.objects.link(root)

    children = []
    # Outer rim torus on top of the wall.
    rim = add_torus(name + '_Rim',
                    location=(0.0, 0.0, well_height),
                    major_radius=radius, minor_radius=0.15,
                    rotation=(0.0, 0.0, 0.0),
                    material=stone_material,
                    major_segments=32, minor_segments=10)
    children.append(rim)

    # Stone wall cylinder: centered at well_height/2, height=well_height.
    wall = add_cyl(name + '_Wall',
                   location=(0.0, 0.0, well_height * 0.5),
                   radius=radius, depth=well_height,
                   material=stone_material, vertices=32)
    children.append(wall)

    # Water disc inside, slightly recessed.
    water_mat = water_material
    water = add_cyl(name + '_Water',
                    location=(0.0, 0.0, well_height - depth),
                    radius=radius * 0.85, depth=0.05,
                    material=water_mat, vertices=32)
    children.append(water)

    # Wood roof: 2 posts on a diameter + cone canopy.
    wood_mat = bpy.data.materials.get('WoodWell')
    if wood_mat is None:
        try:
            wood_mat = procedural_wood('WoodWell', base=(0.30, 0.18, 0.08))
        except Exception:
            wood_mat = mat('WoodWell', (0.30, 0.18, 0.08), roughness=0.85)

    post_h = 1.6
    post_r = 0.06
    post_z = well_height + post_h * 0.5
    post_off = radius * 0.85
    post_a = add_cyl(name + '_PostA',
                     location=(post_off, 0.0, post_z),
                     radius=post_r, depth=post_h,
                     material=wood_mat, vertices=12)
    children.append(post_a)
    post_b = add_cyl(name + '_PostB',
                     location=(-post_off, 0.0, post_z),
                     radius=post_r, depth=post_h,
                     material=wood_mat, vertices=12)
    children.append(post_b)

    canopy_h = 0.6
    canopy_z = well_height + post_h + canopy_h * 0.5
    canopy = add_cone(name + '_Canopy',
                      location=(0.0, 0.0, canopy_z),
                      radius1=radius * 1.15, radius2=0.0,
                      depth=canopy_h, material=wood_mat, vertices=16)
    children.append(canopy)

    for c in children:
        c.parent = root
    root.location = (float(location[0]), float(location[1]), float(location[2]))
    return root


def add_barrel(name, location, radius=0.35, height=0.85,
               wood_material=None, band_material=None):
    """Wooden barrel with two metal bands."""
    root_name = 'BarrelRoot_' + name
    root = bpy.data.objects.new(root_name, None)
    root.name = root_name
    bpy.context.scene.collection.objects.link(root)

    if band_material is None:
        band_material = bpy.data.materials.get('BarrelBand')
        if band_material is None:
            band_material = mat('BarrelBand', (0.18, 0.16, 0.14, 1.0),
                                roughness=0.55, metallic=0.7)

    body = add_cyl(name + '_Body',
                   location=(0.0, 0.0, height * 0.5),
                   radius=radius, depth=height,
                   material=wood_material, vertices=24)
    body.parent = root

    band_minor = 0.04
    for i, frac in enumerate((0.25, 0.75)):
        z = height * frac
        band = add_torus(name + ('_Band%d' % i),
                         location=(0.0, 0.0, z),
                         major_radius=radius + 0.005,
                         minor_radius=band_minor,
                         rotation=(0.0, 0.0, 0.0),
                         material=band_material,
                         major_segments=24, minor_segments=8)
        band.parent = root

    root.location = (float(location[0]), float(location[1]), float(location[2]))
    return root


def add_haybale(name, location, scale=1.0, color=(0.85, 0.72, 0.30)):
    """Rounded hay bale: cube with strong bevel, applied."""
    s = float(scale)
    hay_mat = bpy.data.materials.get('Hay')
    if hay_mat is None:
        hay_mat = mat('Hay', (color[0], color[1], color[2], 1.0),
                      roughness=0.95)
    obj = add_cube(name,
                   location=(float(location[0]), float(location[1]),
                             float(location[2])),
                   scale=(0.6 * s, 0.4 * s, 0.35 * s),
                   material=hay_mat)
    bev = obj.modifiers.new(name='HayBevel', type='BEVEL')
    bev.width = 0.15
    bev.segments = 4
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=bev.name)
    except Exception:
        pass
    return obj


def add_torch(name, location, mount_dir='+X', wood_material=None,
              flame_color=(1.0, 0.55, 0.15), flame_strength=12.0):
    """Wall torch: horizontal stick + emissive flame cone + warm point light."""
    root_name = 'TorchRoot_' + name
    root = bpy.data.objects.new(root_name, None)
    root.name = root_name
    bpy.context.scene.collection.objects.link(root)

    wood_mat = wood_material
    if wood_mat is None:
        wood_mat = bpy.data.materials.get('TorchWood')
        if wood_mat is None:
            wood_mat = mat('TorchWood', (0.25, 0.15, 0.07, 1.0),
                           roughness=0.9)

    stick_len = 0.6
    stick_r = 0.04
    # Direction unit vector for mount.
    dirs = {
        '+X': (1.0, 0.0, 0.0),
        '-X': (-1.0, 0.0, 0.0),
        '+Y': (0.0, 1.0, 0.0),
        '-Y': (0.0, -1.0, 0.0),
    }
    dx, dy, dz = dirs.get(mount_dir, (1.0, 0.0, 0.0))
    # Stick midpoint: half its length along outward direction.
    mid = (dx * stick_len * 0.5, dy * stick_len * 0.5, dz * stick_len * 0.5)
    stick = add_cyl(name + '_Stick',
                    location=mid,
                    radius=stick_r, depth=stick_len,
                    material=wood_mat, vertices=12)
    # Cylinder default axis is Z; rotate so axis aligns with mount dir.
    if mount_dir in ('+X', '-X'):
        stick.rotation_euler = (0.0, math.radians(90.0), 0.0)
    elif mount_dir in ('+Y', '-Y'):
        stick.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    stick.parent = root

    # Flame cone over far end of stick.
    flame_h = 0.30
    end = (dx * stick_len, dy * stick_len, dz * stick_len)
    flame_loc = (end[0], end[1], end[2] + flame_h * 0.5)
    flame_name = name + '_Flame'
    flame_mat = mat(flame_name + '_Mat',
                    (flame_color[0], flame_color[1], flame_color[2], 1.0),
                    roughness=0.5,
                    emission=(flame_color[0], flame_color[1], flame_color[2], 1.0),
                    emission_strength=flame_strength)
    flame = add_cone(flame_name,
                     location=flame_loc,
                     radius1=0.10, radius2=0.0, depth=flame_h,
                     material=flame_mat, vertices=12)
    flame.parent = root

    # Warm point light at flame.
    light_data = bpy.data.lights.new(name + '_Light', type='POINT')
    light_data.name = name + '_Light'
    light_data.energy = 80.0
    light_data.color = (flame_color[0], flame_color[1], flame_color[2])
    light_obj = bpy.data.objects.new(name + '_Light', light_data)
    light_obj.name = name + '_Light'
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = flame_loc
    light_obj.parent = root

    root.location = (float(location[0]), float(location[1]), float(location[2]))
    return root


def add_market_stall(name, location, width=2.5, depth=1.5, height=2.2,
                     awning_color=(0.5, 0.15, 0.10), wood_material=None):
    """Low-poly market stall: 4 posts, counter top, sloped awning, a couple of crates."""
    root_name = 'StallRoot_' + name
    root = bpy.data.objects.new(root_name, None)
    root.name = root_name
    bpy.context.scene.collection.objects.link(root)

    wood_mat = wood_material
    if wood_mat is None:
        wood_mat = bpy.data.materials.get('StallWood')
        if wood_mat is None:
            wood_mat = mat('StallWood', (0.36, 0.22, 0.10, 1.0),
                           roughness=0.85)
    awn_mat = bpy.data.materials.get('StallAwning_' + name)
    if awn_mat is None:
        awn_mat = mat('StallAwning_' + name,
                      (awning_color[0], awning_color[1], awning_color[2], 1.0),
                      roughness=0.8)

    half_w = width * 0.5
    half_d = depth * 0.5
    post_t = 0.06
    # 4 corner posts.
    for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        post = add_cube(name + ('_Post%d' % i),
                        location=(sx * (half_w - post_t),
                                  sy * (half_d - post_t),
                                  height * 0.5),
                        scale=(post_t, post_t, height * 0.5),
                        material=wood_mat)
        post.parent = root

    # Counter top at z=0.9.
    counter_z = 0.9
    counter = add_cube(name + '_Counter',
                       location=(0.0, 0.0, counter_z + 0.05),
                       scale=(half_w, half_d, 0.05),
                       material=wood_mat)
    counter.parent = root

    # Awning: thin slab at top, tilted 25 deg around Y so it slopes forward.
    awn_th = 0.025
    awn_z = height + 0.05
    awning = add_cube(name + '_Awning',
                      location=(0.0, 0.0, awn_z),
                      scale=(half_w + 0.15, half_d + 0.15, awn_th),
                      material=awn_mat)
    awning.rotation_euler = (math.radians(25.0), 0.0, 0.0)
    awning.parent = root

    # 1-2 crates on counter.
    crate_top_z = counter_z + 0.10 + 0.20
    crate1 = add_cube(name + '_Crate1',
                      location=(-half_w * 0.45, 0.0, crate_top_z),
                      scale=(0.20, 0.20, 0.20),
                      material=wood_mat)
    crate1.parent = root
    crate2 = add_cube(name + '_Crate2',
                      location=(half_w * 0.35, half_d * 0.30, crate_top_z - 0.05),
                      scale=(0.18, 0.18, 0.15),
                      material=wood_mat)
    crate2.parent = root

    root.location = (float(location[0]), float(location[1]), float(location[2]))
    return root

# =====================================================================
# Animation / cinematic helpers.
# Render via chunks: animation=True timeouts MCP for >200 frames.
# =====================================================================

import os as _anim_os


def set_animation_range(start=1, end=120, fps=24):
    scene = bpy.context.scene
    scene.frame_start = int(start)
    scene.frame_end = int(end)
    scene.render.fps = int(fps)
    scene.frame_current = int(start)
    return (int(start), int(end), int(fps))


def keyframe_camera_path(camera, keyframes, look_at_per_key=None,
                         lens_per_key=None, interpolation='BEZIER'):
    scene = bpy.context.scene
    cam = camera if camera is not None else scene.camera
    if cam is None:
        raise RuntimeError("keyframe_camera_path: no camera (pass one or set scene.camera)")

    n = len(keyframes)
    if look_at_per_key is not None and len(look_at_per_key) != n:
        raise ValueError("look_at_per_key length must match keyframes length")
    if lens_per_key is not None and len(lens_per_key) != n:
        raise ValueError("lens_per_key length must match keyframes length")

    for i, item in enumerate(keyframes):
        frame, loc = item
        scene.frame_set(int(frame))
        cam.location = (float(loc[0]), float(loc[1]), float(loc[2]))
        if look_at_per_key is not None:
            target = look_at_per_key[i]
            direction = mathutils.Vector((float(target[0]), float(target[1]), float(target[2]))) - cam.location
            rot_quat = direction.to_track_quat('-Z', 'Y')
            cam.rotation_euler = rot_quat.to_euler()
        cam.keyframe_insert(data_path='location', frame=int(frame))
        cam.keyframe_insert(data_path='rotation_euler', frame=int(frame))
        if lens_per_key is not None and hasattr(cam.data, 'lens'):
            cam.data.lens = float(lens_per_key[i])
            cam.data.keyframe_insert(data_path='lens', frame=int(frame))

    def _action_fcurves(act):
        # Blender 5.x slotted actions removed action.fcurves — fall back to layered API.
        if act is None:
            return []
        if hasattr(act, 'fcurves') and act.fcurves:
            return list(act.fcurves)
        if hasattr(act, 'slots') and act.slots:
            try:
                slot = act.slots[0]
                cb = act.layers[0].strips[0].channelbag(slot)
                return list(cb.fcurves)
            except Exception:
                return []
        return []

    if cam.animation_data:
        for fcu in _action_fcurves(cam.animation_data.action):
            for kp in fcu.keyframe_points:
                kp.interpolation = interpolation
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'
    if lens_per_key is not None and cam.data.animation_data:
        for fcu in _action_fcurves(cam.data.animation_data.action):
            for kp in fcu.keyframe_points:
                kp.interpolation = interpolation
    return cam


def render_animation_frames(output_dir, frame_start, frame_end,
                            file_prefix='frame_', resolution=None,
                            samples=None, file_format='PNG'):
    scene = bpy.context.scene
    _anim_os.makedirs(output_dir, exist_ok=True)

    if resolution is not None:
        scene.render.resolution_x = int(resolution[0])
        scene.render.resolution_y = int(resolution[1])
    if samples is not None:
        try:
            scene.eevee.taa_render_samples = int(samples)
        except Exception:
            pass
        try:
            scene.cycles.samples = int(samples)
        except Exception:
            pass
    scene.render.image_settings.file_format = file_format

    paths = []
    norm_dir = output_dir
    if not (norm_dir.endswith('/') or norm_dir.endswith(chr(92))):
        norm_dir = norm_dir + '/'

    for i in range(int(frame_start), int(frame_end) + 1):
        scene.frame_set(i)
        fname = file_prefix + ('%04d' % i)
        scene.render.filepath = norm_dir + fname
        bpy.ops.render.render(write_still=True)
        ext = '.png'
        if file_format == 'JPEG':
            ext = '.jpg'
        elif file_format == 'OPEN_EXR':
            ext = '.exr'
        elif file_format == 'TIFF':
            ext = '.tif'
        paths.append(norm_dir + fname + ext)
    return paths


def bezier_orbit_keyframes(center, radius, height, n_samples=8,
                           frame_start=1, frame_end=120, ccw=True):
    cx = float(center[0])
    cy = float(center[1])
    cz = float(center[2])
    r = float(radius)
    h = float(height)
    n = int(n_samples)
    if n < 2:
        raise ValueError("n_samples must be >= 2")

    keyframes = []
    look_at_points = []
    direction = 1.0 if ccw else -1.0
    fs = int(frame_start)
    fe = int(frame_end)
    span = fe - fs

    for i in range(n):
        t = i / float(n)
        angle = direction * 2.0 * math.pi * t
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        z = cz + h
        if n == 1:
            frame = fs
        else:
            frame = fs + int(round(span * (i / float(n - 1))))
        keyframes.append((frame, (x, y, z)))
        look_at_points.append((cx, cy, cz))
    return (keyframes, look_at_points)


# === Sky / cloud / cinematic helpers (v1.4.0) ===

def set_hosek_sky(sun_elevation_deg=20, sun_azimuth_deg=225, turbidity=2.5,
                  ground_albedo=0.30, strength=1.3):
    """Hosek-Wilkie physical sky for Blender 5.1 (Nishita is not yet available)."""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new('SkillWorld'); world.name = 'SkillWorld'
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    available = [v.identifier for v in type(sky).bl_rna.properties['sky_type'].enum_items]
    for cand in ('NISHITA', 'HOSEK_WILKIE', 'PREETHAM', 'MULTIPLE_SCATTERING'):
        if cand in available:
            sky.sky_type = cand; break
    elev = math.radians(sun_elevation_deg)
    azim = math.radians(sun_azimuth_deg)
    sun_dir = (math.cos(elev)*math.cos(azim), math.cos(elev)*math.sin(azim),
               math.sin(elev))
    if hasattr(sky, 'sun_direction'):
        sky.sun_direction = sun_dir
    if hasattr(sky, 'turbidity'): sky.turbidity = float(turbidity)
    if hasattr(sky, 'ground_albedo'): sky.ground_albedo = float(ground_albedo)
    nt.links.new(sky.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs['Strength'].default_value = float(strength)
    return sun_dir


def add_cloud_drifts(positions=None, plane_size=80, tilt_deg=15, name_prefix='Cloud'):
    """Scattered cloud sprite planes; emissive+transparent procedural noise material."""
    if positions is None:
        positions = [(60,-40,35),(70,30,38),(-65,20,40),(-55,-45,36),(0,70,42)]
    m = bpy.data.materials.get('Clouds')
    if m is None:
        m = bpy.data.materials.new('Clouds'); m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    mix = nt.nodes.new('ShaderNodeMixShader')
    trans = nt.nodes.new('ShaderNodeBsdfTransparent')
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (0.3, 0.3, 0.3)
    n1.inputs['Scale'].default_value = 1.5
    n1.inputs['Detail'].default_value = 8.0
    n1.inputs['Roughness'].default_value = 0.55
    n1.inputs['Distortion'].default_value = 1.5
    n2.inputs['Scale'].default_value = 4.5
    n2.inputs['Detail'].default_value = 6.0
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[0].color = (0,0,0,1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (1,1,1,1)
    emit.inputs['Color'].default_value = (1.0, 0.95, 0.85, 1)
    emit.inputs['Strength'].default_value = 2.0
    nt.links.new(tc.outputs['Generated'], mp.inputs[0])
    nt.links.new(mp.outputs[0], n1.inputs['Vector'])
    nt.links.new(mp.outputs[0], n2.inputs['Vector'])
    nt.links.new(n1.outputs['Fac'], mul.inputs[0])
    nt.links.new(n2.outputs['Fac'], mul.inputs[1])
    nt.links.new(mul.outputs[0], ramp.inputs[0])
    nt.links.new(trans.outputs[0], mix.inputs[1])
    nt.links.new(emit.outputs[0], mix.inputs[2])
    nt.links.new(ramp.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[0], out.inputs[0])
    if hasattr(m, 'blend_method'): m.blend_method = 'BLEND'
    if hasattr(m, 'shadow_method'): m.shadow_method = 'NONE'
    objs = []
    for i, (x,y,z) in enumerate(positions):
        bpy.ops.mesh.primitive_plane_add(size=plane_size, location=(x,y,z))
        p = bpy.context.object
        p.name = f"{name_prefix}_{i}"; p.data.name = p.name
        p.rotation_euler = (math.radians(tilt_deg), 0, math.radians(i*30))
        p.data.materials.clear(); p.data.materials.append(m)
        objs.append(p)
    return objs


def set_object_origin(obj, world_pos):
    """Move obj origin to world_pos so subsequent rotation pivots there (hinges)."""
    bpy.context.scene.cursor.location = (float(world_pos[0]),
                                         float(world_pos[1]),
                                         float(world_pos[2]))
    for o in bpy.context.scene.objects: o.select_set(False)
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return obj


def swing_door(obj, hinge_world_pos, axis='Z', closed_deg=0, open_deg=90,
               start_frame=1, swing_in_frame=150, swing_out_frame=175,
               end_frame=192):
    """Animate a hinged door: closed → swings open between swing_in..swing_out → stays open."""
    set_object_origin(obj, hinge_world_pos)
    obj.animation_data_clear() if obj.animation_data else None
    axis_idx = {'X':0, 'Y':1, 'Z':2}[axis]

    def kf(frame, deg):
        bpy.context.scene.frame_set(int(frame))
        rot = list(obj.rotation_euler)
        rot[axis_idx] = math.radians(deg)
        obj.rotation_euler = rot
        obj.keyframe_insert('rotation_euler', frame=int(frame))

    kf(start_frame, closed_deg)
    kf(swing_in_frame, closed_deg)
    kf(swing_out_frame, open_deg)
    kf(end_frame, open_deg)
    return obj


def bird_flight_keyframes(camera, plan, interpolation='BEZIER'):
    """plan = list of (frame, location, look_at, roll_deg). Sets keyframes with banking."""
    if camera is None: camera = bpy.context.scene.camera
    if camera.animation_data: camera.animation_data_clear()
    scn = bpy.context.scene
    for frame, loc, look, roll in plan:
        scn.frame_set(int(frame))
        camera.location = (float(loc[0]), float(loc[1]), float(loc[2]))
        direction = mathutils.Vector(look) - mathutils.Vector(loc)
        if direction.length < 1e-6:
            direction = mathutils.Vector((0,1,0))
        quat = direction.to_track_quat('-Z', 'Y')
        if roll:
            roll_q = mathutils.Quaternion(direction.normalized(), math.radians(float(roll)))
            quat = roll_q @ quat
        camera.rotation_euler = quat.to_euler()
        camera.keyframe_insert('location', frame=int(frame))
        camera.keyframe_insert('rotation_euler', frame=int(frame))
    # Smooth via slotted-actions API
    ad = camera.animation_data
    if ad is not None and ad.action is not None:
        a = ad.action
        fcurves = list(a.fcurves) if hasattr(a, 'fcurves') and a.fcurves else []
        if not fcurves and hasattr(a, 'slots') and a.slots:
            try:
                slot = a.slots[0]
                fcurves = list(a.layers[0].strips[0].channelbag(slot).fcurves)
            except Exception:
                fcurves = []
        for fc in fcurves:
            for kp in fc.keyframe_points:
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'
                kp.interpolation = interpolation
    return camera
