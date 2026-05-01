# Helper index

Total: 83 helpers across 9 categories

Auto-derived from `scripts/_helpers.py`. Run `python tools/validate_skill.py` after editing helpers.

## scene

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `enable_eevee_quality()` | value (e.g. `applied`) | side effects depend on usage | yes |  |
| `reset_scene()` | None | purges all data-blocks and resets the scene | partial | wipes orphan data; call once at start of script |
| `safe_engine()` | value (e.g. `next(iter(available)) if available else 'BLENDER_EEVEE'`) | mutates scene view-transform / engine settings | yes | falls back to CYCLES if requested engine unavailable |
| `save_blend(filepath)` | None | writes a .blend file to disk | partial | creates parent dirs; relative paths resolve to bpy cwd |
| `set_filmic_high_contrast()` | value (e.g. `out`) | mutates scene view-transform / engine settings | yes | sets view_transform=Filmic, look=High Contrast |
| `set_output_path(path, file_format='PNG')` | None | sets scene.render.filepath | yes |  |

## mesh

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `add_barrel(name, location, radius=0.35, height=0.85, wood_material=None, band_material=None)` | value (e.g. `root`) | creates one or more mesh objects in the current scene | no | wood barrel with bands |
| `add_cone(name, location, radius1, radius2, depth, material=None, vertices=32)` | the created object | creates one or more mesh objects in the current scene | no | thin wrapper over primitive_cone_add |
| `add_cube(name, location, scale, material=None)` | the created object | creates one or more mesh objects in the current scene | no | thin wrapper over mesh.primitive_cube_add |
| `add_curtain(name, location, width=1.2, height=2.4, segments_x=6, segments_y=12, material=None, wave_amplitude=0.08)` | the created object | creates one or more mesh objects in the current scene | no | subdivided drape; consider cloth |
| `add_cyl(name, location, radius, depth, material=None, vertices=32)` | the created object | creates one or more mesh objects in the current scene | no | thin wrapper over primitive_cylinder_add |
| `add_door_frame(name, location, width=0.9, height=2.1, depth=0.25, material=None)` | value (e.g. `joined`) | creates one or more mesh objects in the current scene | no | creates 3-piece frame around opening |
| `add_gargoyle(name, location, facing='+X', material=None, scale=0.5)` | value (e.g. `root`) | creates one or more mesh objects in the current scene | no | stylized low-poly creature |
| `add_haybale(name, location, scale=1.0, color=(0.85, 0.72, 0.3))` | the created object | creates one or more mesh objects in the current scene | no | low-poly hay cylinder |
| `add_market_stall(name, location, width=2.5, depth=1.5, height=2.2, awning_color=(0.5, 0.15, 0.1), wood_material=None)` | value (e.g. `root`) | creates one or more mesh objects in the current scene | no | wood frame + cloth roof |
| `add_plane(name, location, size, material=None)` | the created object | creates one or more mesh objects in the current scene | no | thin wrapper over primitive_plane_add |
| `add_rug(name, location, size_x=2.0, size_y=3.0, thickness=0.04, color=(0.6, 0.2, 0.1))` | the created object | creates one or more mesh objects in the current scene | no | flat textured plane |
| `add_torch(name, location, mount_dir='+X', wood_material=None, flame_color=(1.0, 0.55, 0.15), flame_strength=12.0)` | value (e.g. `root`) | creates one or more mesh objects in the current scene | no | torch with emissive flame |
| `add_torus(name, location, major_radius=1.0, minor_radius=0.25, rotation=(0.0, 0.0, 0.0), material=None, major_segments=48, minor_segments=12)` | the created object | creates one or more mesh objects in the current scene | no | thin wrapper over primitive_torus_add |
| `add_tree_cluster(center, count=5, radius=8.0, height_range=(3.0, 7.0), seed=0)` | value (e.g. `trees`) | creates many mesh objects in the current scene | no | low-poly trees; cap count to bound poly budget |
| `add_well(name, location, radius=1.0, depth=0.6, well_height=1.0, stone_material=None, water_material=None)` | value (e.g. `root`) | creates one or more mesh objects in the current scene | no | round stone well prop |
| `add_window_cutout(wall_obj, location, width=1.2, height=1.5)` | None | creates one or more mesh objects in the current scene | no | boolean cuts hole then frames it |
| `auto_bevel(obj, width=0.02, segments=2)` | None | adds and applies a modifier on the target | no | marks sharp edges by angle then bevels |
| `boolean_difference(target, cutter, apply=True, delete_cutter=True)` | value (e.g. `target`) | applies a boolean modifier (mutates target mesh) | no | applies modifier; target mesh must be manifold |
| `build_room_box(name_prefix, width, depth, height, wall_thickness=0.2, material=None)` | value (e.g. `{'floor': floor, 'ceiling': ceiling, 'wall_n': wall_n, 'wall`) | creates a multi-mesh enclosure / backdrop | no | interior shell with wall thickness |
| `chain_between(name_prefix, p_start, p_end, link_count=8, link_radius=0.08, material=None)` | value (e.g. `created`) | side effects depend on usage | no | torus chain between two points |
| `cleanup_materials(obj)` | value (e.g. `removed`) | mutates objects and material slots in place | partial | removes unused slots and orphan datablocks |
| `crenellate_line(name_prefix, p0, p1, z_top, material=None, merlon_w=0.4, merlon_h=0.7, merlon_t=0.4, gap=0.4)` | value (e.g. `created`) | side effects depend on usage | no | merlons along a line; cap count |
| `cyclorama_backdrop(name='Cyclorama', size=6.0, color=(0.05, 0.05, 0.05))` | value (e.g. `root`) | creates a multi-mesh enclosure / backdrop | no | curved infinity backdrop |
| `decimate_mesh(obj, ratio=0.5)` | None | adds and applies a modifier on the target | no | ratio in (0,1]; lower = fewer tris |
| `flag_banner(name, location, width=0.8, height=1.2, color=(0.7, 0.08, 0.08), pole_height=2.0)` | tuple | side effects depend on usage | no | subdivided plane; consider cloth modifier |
| `flying_buttress(name, anchor_low, anchor_high, thickness=0.4, material=None, segments=8)` | the created object | side effects depend on usage | no | arched stone support |
| `gable_roof(name, location, length, width, height, material=None)` | the created object | side effects depend on usage | no | two angled planes; symmetric pitch |
| `low_poly_tree(name, location, height=4.0, trunk_radius=0.18, leaf_color=(0.18, 0.45, 0.2), trunk_color=(0.3, 0.18, 0.08))` | value (e.g. `root`) | side effects depend on usage | no | trunk + cone foliage |
| `normalize_imported(obj)` | None | mutates objects and material slots in place | partial | recenters origin and scales to fit unit cube |
| `paving_stones(name_prefix, area_min, area_max, tile_size=0.5, height=0.05, material=None, jitter=0.04, color_jitter=0.08)` | value (e.g. `root`) | side effects depend on usage | no | tiled floor; cap count <= ~300 |
| `place_on_floor(obj, floor_z=0.0)` | None | translates the object so its base z=floor | yes | translates obj.location.z so bbox-min sits on floor |
| `pointed_arch_window(name, location, width, height, depth, material=None, facing='-Y', frame_thickness=0.15, frame_material=None)` | the created object | side effects depend on usage | no | Gothic arch profile |
| `scatter_grass_tufts(ground_obj, count=200, height_range=(0.1, 0.3), seed=0)` | the created object | creates many mesh objects in the current scene | no | cap count <= ~300 (pitfall 31) |
| `scatter_rocks(ground_obj, count=30, size_range=(0.1, 0.5), seed=42, material=None)` | value (e.g. `rocks`) | creates many mesh objects in the current scene | no | cap count <= ~300 (pitfall 31) |
| `stone_block_band(name_prefix, p0, p1, z_bottom, z_top, block_w=0.6, block_h=0.4, depth=0.15, material=None, jitter=0.05, seed=0)` | value (e.g. `created`) | side effects depend on usage | no | row of cuboids; cap count |
| `tower_windows(name_prefix, center_xy, tower_radius, z_levels, count_per_level=4, slit_w=0.18, slit_h=1.2, material=None, frame_material=None)` | value (e.g. `created`) | side effects depend on usage | no | evenly spaced openings around tower |

## materials

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `mat(name, color, roughness=0.7, metallic=0.0, emission=None, emission_strength=1.0)` | value (e.g. `m`) | get-or-creates a material data-block | yes | get-or-create by name; safe to call repeatedly |
| `procedural_canvas_flag(name, base=(0.7, 0.08, 0.08), wear=0.3)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |
| `procedural_dirt_path(name, base=(0.3, 0.22, 0.14), gravel_scale=20.0)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |
| `procedural_grass(name, base=(0.18, 0.34, 0.12), variation=0.1)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |
| `procedural_metal_aged(name, base=(0.7, 0.55, 0.25), patina=(0.18, 0.35, 0.3), patina_amount=0.4)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |
| `procedural_slate_tiles(name, base=(0.1, 0.11, 0.15), tile_scale=8.0)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |
| `procedural_stone(name, base=(0.45, 0.42, 0.38), variation=0.15, bumpiness=0.3, mortar_dark=0.5)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |
| `procedural_water(name, base=(0.02, 0.07, 0.12), wave_scale=6.0)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |
| `procedural_wood(name, base=(0.3, 0.18, 0.08), grain_scale=12.0)` | value (e.g. `m`) | creates a material data-block with shader nodes | no | creates new material each call; reuse via mat() if needed |

## lighting

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `add_area_light(name, location, rotation_euler, energy=100.0, size=1.0, color=(1, 1, 1))` | the created object | creates lights / emissive geometry in the scene | no | tweak size and energy together |
| `add_cloud_drifts(positions=None, plane_size=80, tilt_deg=15, name_prefix='Cloud')` | the created object | creates lights / emissive geometry in the scene | no | cap count to keep render time reasonable (pitfall 31) |
| `add_emissive_plane(name, location, size=1.0, energy=5.0, color=(1, 1, 1))` | the created object | creates lights / emissive geometry in the scene | no | for soft cards / billboards |
| `add_volumetric_fog(density=0.02, color=(0.7, 0.75, 0.85), anisotropy=0.0)` | value (e.g. `nt`) | creates lights / emissive geometry in the scene | no | uses a large cube with volume scatter shader |
| `hdri_world(hdri_path, strength=1.0, rotation_deg=0.0)` | None | modifies scene.world.node_tree | yes | loads HDRI from path; check filepath exists |
| `rim_light(target_obj, energy=3.0, color=(0.7, 0.85, 1.0))` | the created object | creates lights / emissive geometry in the scene | no | high-energy rim from behind subject |
| `set_hosek_sky(sun_elevation_deg=20, sun_azimuth_deg=225, turbidity=2.5, ground_albedo=0.3, strength=1.3)` | value (e.g. `sun_dir`) | modifies scene.world.node_tree | yes | uses HOSEK_WILKIE; NISHITA missing in some 4.x builds |
| `set_sunset_world(top=(0.95, 0.65, 0.4), bottom=(0.2, 0.18, 0.3), strength=0.8)` | value (e.g. `nt`) | modifies scene.world.node_tree | yes | warm gradient via Sky Texture nodes |
| `set_world_sky(top=(0.55, 0.75, 0.95), strength=1.2)` | value (e.g. `world`) | modifies scene.world.node_tree | yes | preset entry point for sky textures |
| `studio_dark_world(strength=0.3, color=(0.02, 0.02, 0.02))` | value (e.g. `set_world_sky(top=color, strength=strength)`) | modifies scene.world.node_tree | yes | neutral dark grey world for product shots |
| `three_point_light(target=(0, 0, 0), key_energy=4.0)` | tuple | creates lights / emissive geometry in the scene | no | creates Key/Fill/Rim area lights |
| `warm_key_light(target=(0, 0, 0), energy=5.0, color=(1.0, 0.78, 0.55))` | the created object | creates lights / emissive geometry in the scene | no | single warm key with soft falloff |

## camera

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `add_camera_dof(target_obj=None, focus_distance=None, fstop=2.8, camera=None)` | value (e.g. `camera`) | mutates camera DOF settings | yes | set focus object first, then aperture |
| `auto_frame(objects, padding=1.2, elevation_deg=30, azimuth_deg=45, lens=35, name='SkillCamera')` | tuple | creates or replaces the SkillCamera and points it at targets | partial | wraps frame_camera with bounding-box of all visible meshes |
| `bbox_of(objects)` | tuple | no side effects (pure) | yes | pure; returns (min, max) world-space tuple |
| `frame_camera(target=(0, 0, 0), distance=18, elevation_deg=35, azimuth_deg=45, lens=35, name='SkillCamera')` | value (e.g. `cam`) | creates or replaces the SkillCamera and points it at targets | partial | removes any existing SkillCamera before creating new one |
| `setup_turntable(subject_obj, frame_start=1, frame_end=120, radius=None, height_offset=0.3, lens=85)` | value (e.g. `cam`) | creates a turntable rig and inserts keyframes | no | inserts orbit keyframes on a parent empty |

## render

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `enable_denoising(engine='auto')` | None | mutates scene.render / scene timeline settings | yes | Cycles + Eevee Next compatible |
| `set_render(engine=None, resolution=(1280, 800), samples=64)` | value (e.g. `r`) | mutates scene.render / scene timeline settings | yes | use this rather than poking scene.render directly |
| `set_render_resolution(width=1920, height=1080, percentage=100)` | None | mutates scene.render / scene timeline settings | yes | resolution_percentage defaults to 100 |

## animation

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `bezier_orbit_keyframes(center, radius, height, n_samples=8, frame_start=1, frame_end=120, ccw=True)` | tuple | inserts keyframes on the target object | no | smooth orbit via bezier handles |
| `bird_flight_keyframes(camera, plan, interpolation='BEZIER')` | value (e.g. `camera`) | inserts keyframes on the target object | no | noise-driven flight path |
| `keyframe_camera_path(camera, keyframes, look_at_per_key=None, lens_per_key=None, interpolation='BEZIER')` | value (e.g. `cam`) | inserts keyframes on the target object | no | inserts location+rotation keyframes |
| `render_animation_frames(output_dir, frame_start, frame_end, file_prefix='frame_', resolution=None, samples=None, file_format='PNG')` | value (e.g. `paths`) | writes rendered images to disk | no | writes PNG sequence; cap frame count |
| `set_animation_range(start=1, end=120, fps=24)` | tuple | mutates scene.render / scene timeline settings | yes | scene.frame_start/end inclusive |
| `set_object_origin(obj, world_pos)` | the created object | moves object origin (mutates mesh + transform) | yes | moves origin without translating mesh |
| `swing_door(obj, hinge_world_pos, axis='Z', closed_deg=0, open_deg=90, start_frame=1, swing_in_frame=150, swing_out_frame=175, end_frame=192)` | the created object | inserts keyframes on the target object | no | sets origin to hinge before rotation keyframes |

## import_export

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `import_fbx(filepath, name=None)` | value (e.g. `tops`) | imports external file and adds objects to the scene | no | uses bpy.ops.import_scene.fbx |
| `import_obj(filepath, name=None)` | value (e.g. `joined`) | imports external file and adds objects to the scene | no | uses bpy.ops.wm.obj_import (Blender 4.x) |

## geometry_nodes

| Function | Returns | Side effects | Idempotent | Notes |
|---|---|---|---|---|
| `gn_array_along_curve(obj, curve_obj, count=10, name='GN_ArrayCurve')` | value (e.g. `container`) | creates / attaches a geometry-nodes modifier | no | geometry-nodes graph builder; verify node names per Blender version |
| `gn_random_transform(obj, loc_range=0.1, rot_range=15.0, scale_range=0.2, seed=0)` | value (e.g. `rv`) | creates / attaches a geometry-nodes modifier | no | geometry-nodes graph builder; verify node names per Blender version |
| `gn_scatter_on_surface(target_obj, instance_obj, density=5.0, seed=0, name='GN_Scatter')` | the created object | creates / attaches a geometry-nodes modifier | no | geometry-nodes graph builder; verify node names per Blender version |
