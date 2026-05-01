"""Generate reference/helper-index.{json,md} from scripts/_helpers.py via AST."""
from __future__ import annotations
import ast, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts" / "_helpers.py"
OUT_JSON = ROOT / "reference" / "helper-index.json"
OUT_MD = ROOT / "reference" / "helper-index.md"

CATEGORY_ORDER = [
    "scene", "mesh", "materials", "lighting", "camera",
    "render", "animation", "import_export", "geometry_nodes",
    "utility", "other",
]

# explicit name -> category overrides (most specific first)
NAME_CATEGORY = {
    # scene / render-config
    "reset_scene": "scene",
    "set_world_background": "scene",
    "set_filmic_high_contrast": "scene",
    "enable_eevee_next": "scene",
    "safe_engine": "scene",
    "save_blend": "scene",
    "set_output_path": "scene",
    # render
    "set_render": "render",
    "set_render_resolution": "render",
    "enable_denoising": "render",
    # animation
    "set_animation_range": "animation",
    "keyframe_camera_path": "animation",
    "bezier_orbit_keyframes": "animation",
    "bird_flight_keyframes": "animation",
    "render_animation_frames": "animation",
    "swing_door": "animation",
    "set_object_origin": "animation",
    # camera
    "frame_camera": "camera",
    "auto_frame": "camera",
    "bbox_of": "camera",
    "add_camera_dof": "camera",
    "setup_turntable": "camera",
    # lighting
    "three_point_light": "lighting",
    "warm_key_light": "lighting",
    "studio_dark_world": "lighting",
    "add_area_light": "lighting",
    "add_emissive_plane": "lighting",
    "rim_light": "lighting",
    "set_world_sky": "lighting",
    "set_sunset_world": "lighting",
    "set_hosek_sky": "lighting",
    "add_cloud_drifts": "lighting",
    "hdri_world": "lighting",
    "add_volumetric_fog": "lighting",
    # materials
    "mat": "materials",
    # import/export
    "import_obj": "import_export",
    "import_fbx": "import_export",
    # mesh/geom builders (keep this list explicit)
    "add_cube": "mesh", "add_cyl": "mesh", "add_cone": "mesh",
    "add_plane": "mesh", "add_torus": "mesh",
    "gable_roof": "mesh", "pointed_arch_window": "mesh",
    "crenellate_line": "mesh", "flying_buttress": "mesh",
    "chain_between": "mesh", "flag_banner": "mesh",
    "low_poly_tree": "mesh", "add_gargoyle": "mesh",
    "stone_block_band": "mesh", "tower_windows": "mesh",
    "paving_stones": "mesh", "add_well": "mesh",
    "add_barrel": "mesh", "add_haybale": "mesh",
    "add_torch": "mesh", "add_market_stall": "mesh",
    "add_curtain": "mesh", "add_rug": "mesh",
    "build_room_box": "mesh", "add_window_cutout": "mesh",
    "add_door_frame": "mesh", "place_on_floor": "mesh",
    "cyclorama_backdrop": "mesh", "boolean_difference": "mesh",
    "decimate_mesh": "mesh", "auto_bevel": "mesh",
    "normalize_imported": "mesh", "cleanup_materials": "mesh",
    "scatter_rocks": "mesh", "scatter_grass_tufts": "mesh",
    "add_tree_cluster": "mesh",
}


def categorize(name: str) -> str:
    if name in NAME_CATEGORY:
        return NAME_CATEGORY[name]
    if name.startswith("gn_"):
        return "geometry_nodes"
    if name.startswith("procedural_"):
        return "materials"
    if name.startswith("set_render"):
        return "render"
    if name.startswith("set_world_") or name.startswith("set_filmic") or name.startswith("enable_eevee"):
        return "scene"
    if name.startswith("import_"):
        return "import_export"
    if name.startswith("add_"):
        # default "add_*" without explicit lighting/camera mapping -> mesh
        return "mesh"
    return "utility"


def signature_of(fn: ast.FunctionDef) -> str:
    a = fn.args
    parts: list[str] = []
    pos = list(a.posonlyargs) + list(a.args)
    defaults = list(a.defaults)
    n_defaults = len(defaults)
    n_pos = len(pos)
    default_offset = n_pos - n_defaults
    posonly_count = len(a.posonlyargs)
    for i, arg in enumerate(pos):
        s = arg.arg
        if arg.annotation is not None:
            try:
                s += ": " + ast.unparse(arg.annotation)
            except Exception:
                pass
        if i >= default_offset:
            d = defaults[i - default_offset]
            try:
                s += "=" + ast.unparse(d)
            except Exception:
                s += "=..."
        parts.append(s)
        if posonly_count and i == posonly_count - 1:
            parts.append("/")
    if a.vararg:
        parts.append("*" + a.vararg.arg)
    elif a.kwonlyargs:
        parts.append("*")
    for arg, default in zip(a.kwonlyargs, a.kw_defaults):
        s = arg.arg
        if arg.annotation is not None:
            try:
                s += ": " + ast.unparse(arg.annotation)
            except Exception:
                pass
        if default is not None:
            try:
                s += "=" + ast.unparse(default)
            except Exception:
                s += "=..."
        parts.append(s)
    if a.kwarg:
        parts.append("**" + a.kwarg.arg)
    sig = f"{fn.name}({', '.join(parts)})"
    if fn.returns is not None:
        try:
            sig += " -> " + ast.unparse(fn.returns)
        except Exception:
            pass
    return sig


def extract_returns(fn: ast.FunctionDef, doc: str) -> str:
    # docstring "Returns ..." line
    if doc:
        for line in doc.splitlines():
            line = line.strip()
            if line.lower().startswith("return"):
                # strip leading "Returns:" or "Return"
                cleaned = re.sub(r"^returns?:?\s*", "", line, flags=re.I)
                if cleaned:
                    return cleaned[:120]
    # inspect return statements
    has_value = False
    has_none = False
    return_objs: list[str] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Return):
            if node.value is None:
                has_none = True
            else:
                has_value = True
                try:
                    src = ast.unparse(node.value)
                    return_objs.append(src[:60])
                except Exception:
                    pass
    if not has_value:
        return "None"
    # heuristic
    if return_objs:
        first = return_objs[0]
        if "obj" in first.lower():
            return "the created object"
        if first.startswith("[") or "list" in first.lower():
            return "list of objects"
        if "tuple" in first.lower() or first.startswith("("):
            return "tuple"
        if "mat" in first.lower():
            return "the material"
        return f"value (e.g. `{first}`)"
    return "value"


def first_doc_line(doc: str) -> str:
    if not doc:
        return ""
    for line in doc.splitlines():
        s = line.strip()
        if s:
            return s
    return ""


def side_effects_for(name: str, doc: str) -> str:
    n = name
    if n == "reset_scene":
        return "purges all data-blocks and resets the scene"
    if n == "save_blend":
        return "writes a .blend file to disk"
    if n == "set_output_path":
        return "sets scene.render.filepath"
    if n.startswith("render_") or n == "render_animation_frames":
        return "writes rendered images to disk"
    if n.startswith("set_render") or n == "enable_denoising" or n == "set_animation_range":
        return "mutates scene.render / scene timeline settings"
    if n in {"set_world_background", "set_world_sky", "set_sunset_world", "set_hosek_sky", "studio_dark_world", "hdri_world"}:
        return "modifies scene.world.node_tree"
    if n == "set_filmic_high_contrast" or n == "enable_eevee_next" or n == "safe_engine":
        return "mutates scene view-transform / engine settings"
    if n == "mat":
        return "get-or-creates a material data-block"
    if n.startswith("procedural_"):
        return "creates a material data-block with shader nodes"
    if n.startswith("gn_"):
        return "creates / attaches a geometry-nodes modifier"
    if n in {"frame_camera", "auto_frame"}:
        return "creates or replaces the SkillCamera and points it at targets"
    if n == "add_camera_dof":
        return "mutates camera DOF settings"
    if n == "bbox_of":
        return "no side effects (pure)"
    if n == "setup_turntable":
        return "creates a turntable rig and inserts keyframes"
    if n.startswith("keyframe_") or "keyframes" in n or n == "swing_door":
        return "inserts keyframes on the target object"
    if n == "set_object_origin":
        return "moves object origin (mutates mesh + transform)"
    if n.startswith("import_"):
        return "imports external file and adds objects to the scene"
    if n.startswith("scatter_") or n == "add_tree_cluster":
        return "creates many mesh objects in the current scene"
    if n in {"three_point_light", "warm_key_light", "rim_light", "add_area_light", "add_emissive_plane", "add_cloud_drifts", "add_volumetric_fog"}:
        return "creates lights / emissive geometry in the scene"
    if n.startswith("add_"):
        return "creates one or more mesh objects in the current scene"
    if n in {"build_room_box", "cyclorama_backdrop"}:
        return "creates a multi-mesh enclosure / backdrop"
    if n == "boolean_difference":
        return "applies a boolean modifier (mutates target mesh)"
    if n in {"decimate_mesh", "auto_bevel"}:
        return "adds and applies a modifier on the target"
    if n in {"normalize_imported", "cleanup_materials"}:
        return "mutates objects and material slots in place"
    if n == "place_on_floor":
        return "translates the object so its base z=floor"
    if n == "add_window_cutout" or n == "add_door_frame":
        return "modifies wall mesh and creates frame geometry"
    return "side effects depend on usage"


def idempotency_for(name: str, doc: str) -> str:
    n = name
    pure_setters = {
        "set_render", "set_render_resolution", "enable_denoising",
        "set_filmic_high_contrast", "enable_eevee_next", "safe_engine",
        "set_animation_range", "set_output_path",
        "set_world_background", "set_world_sky", "set_sunset_world",
        "set_hosek_sky", "studio_dark_world", "hdri_world",
        "add_camera_dof", "set_object_origin", "place_on_floor",
        "bbox_of",
    }
    if n in pure_setters:
        return "yes"
    if n == "mat":
        return "yes"  # get-or-create
    if n in {"reset_scene", "frame_camera", "auto_frame", "save_blend"}:
        return "partial"
    if n == "cleanup_materials" or n == "normalize_imported":
        return "partial"
    if n.startswith("add_") or n.startswith("scatter_") or n == "add_tree_cluster":
        return "no"
    if n.startswith("procedural_"):
        return "no"
    if n.startswith("gn_"):
        return "no"
    if n.startswith("import_"):
        return "no"
    if "keyframes" in n or n.startswith("keyframe_") or n == "swing_door" or n == "render_animation_frames":
        return "no"
    if n in {"build_room_box", "cyclorama_backdrop", "add_window_cutout", "add_door_frame"}:
        return "no"
    # explicit mesh builders without add_ prefix
    if n in {"chain_between", "crenellate_line", "flag_banner", "flying_buttress",
             "gable_roof", "pointed_arch_window", "low_poly_tree", "stone_block_band",
             "tower_windows", "paving_stones"}:
        return "no"
    if n == "enable_eevee_quality":
        return "yes"
    if n in {"boolean_difference", "decimate_mesh", "auto_bevel"}:
        return "no"
    if n in {"three_point_light", "warm_key_light", "rim_light", "add_area_light",
             "add_emissive_plane", "add_cloud_drifts", "add_volumetric_fog",
             "setup_turntable"}:
        return "no"
    return "unknown"


def notes_for(name: str, doc: str) -> str:
    n = name
    notes = {
        "reset_scene": "wipes orphan data; call once at start of script",
        "save_blend": "creates parent dirs; relative paths resolve to bpy cwd",
        "set_render": "use this rather than poking scene.render directly",
        "set_render_resolution": "resolution_percentage defaults to 100",
        "enable_denoising": "Cycles + Eevee Next compatible",
        "set_animation_range": "scene.frame_start/end inclusive",
        "set_filmic_high_contrast": "sets view_transform=Filmic, look=High Contrast",
        "enable_eevee_next": "BLENDER_EEVEE_NEXT only available in Blender 4.2+",
        "safe_engine": "falls back to CYCLES if requested engine unavailable",
        "frame_camera": "removes any existing SkillCamera before creating new one",
        "auto_frame": "wraps frame_camera with bounding-box of all visible meshes",
        "bbox_of": "pure; returns (min, max) world-space tuple",
        "add_camera_dof": "set focus object first, then aperture",
        "setup_turntable": "inserts orbit keyframes on a parent empty",
        "set_hosek_sky": "uses HOSEK_WILKIE; NISHITA missing in some 4.x builds",
        "set_sunset_world": "warm gradient via Sky Texture nodes",
        "set_world_sky": "preset entry point for sky textures",
        "studio_dark_world": "neutral dark grey world for product shots",
        "hdri_world": "loads HDRI from path; check filepath exists",
        "three_point_light": "creates Key/Fill/Rim area lights",
        "warm_key_light": "single warm key with soft falloff",
        "rim_light": "high-energy rim from behind subject",
        "add_area_light": "tweak size and energy together",
        "add_emissive_plane": "for soft cards / billboards",
        "add_cloud_drifts": "cap count to keep render time reasonable (pitfall 31)",
        "add_volumetric_fog": "uses a large cube with volume scatter shader",
        "mat": "get-or-create by name; safe to call repeatedly",
        "import_obj": "uses bpy.ops.wm.obj_import (Blender 4.x)",
        "import_fbx": "uses bpy.ops.import_scene.fbx",
        "boolean_difference": "applies modifier; target mesh must be manifold",
        "decimate_mesh": "ratio in (0,1]; lower = fewer tris",
        "auto_bevel": "marks sharp edges by angle then bevels",
        "normalize_imported": "recenters origin and scales to fit unit cube",
        "cleanup_materials": "removes unused slots and orphan datablocks",
        "scatter_rocks": "cap count <= ~300 (pitfall 31)",
        "scatter_grass_tufts": "cap count <= ~300 (pitfall 31)",
        "add_tree_cluster": "low-poly trees; cap count to bound poly budget",
        "swing_door": "sets origin to hinge before rotation keyframes",
        "keyframe_camera_path": "inserts location+rotation keyframes",
        "bezier_orbit_keyframes": "smooth orbit via bezier handles",
        "bird_flight_keyframes": "noise-driven flight path",
        "render_animation_frames": "writes PNG sequence; cap frame count",
        "set_object_origin": "moves origin without translating mesh",
        "place_on_floor": "translates obj.location.z so bbox-min sits on floor",
        "add_window_cutout": "boolean cuts hole then frames it",
        "add_door_frame": "creates 3-piece frame around opening",
        "build_room_box": "interior shell with wall thickness",
        "cyclorama_backdrop": "curved infinity backdrop",
        "gable_roof": "two angled planes; symmetric pitch",
        "pointed_arch_window": "Gothic arch profile",
        "crenellate_line": "merlons along a line; cap count",
        "flying_buttress": "arched stone support",
        "chain_between": "torus chain between two points",
        "flag_banner": "subdivided plane; consider cloth modifier",
        "low_poly_tree": "trunk + cone foliage",
        "add_gargoyle": "stylized low-poly creature",
        "stone_block_band": "row of cuboids; cap count",
        "tower_windows": "evenly spaced openings around tower",
        "paving_stones": "tiled floor; cap count <= ~300",
        "add_well": "round stone well prop",
        "add_barrel": "wood barrel with bands",
        "add_haybale": "low-poly hay cylinder",
        "add_torch": "torch with emissive flame",
        "add_market_stall": "wood frame + cloth roof",
        "add_curtain": "subdivided drape; consider cloth",
        "add_rug": "flat textured plane",
        "add_cube": "thin wrapper over mesh.primitive_cube_add",
        "add_cyl": "thin wrapper over primitive_cylinder_add",
        "add_cone": "thin wrapper over primitive_cone_add",
        "add_plane": "thin wrapper over primitive_plane_add",
        "add_torus": "thin wrapper over primitive_torus_add",
    }
    if n in notes:
        return notes[n]
    if n.startswith("procedural_"):
        return "creates new material each call; reuse via mat() if needed"
    if n.startswith("gn_"):
        return "geometry-nodes graph builder; verify node names per Blender version"
    return ""


def main():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    helpers = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            doc = ast.get_docstring(node) or ""
            sig = signature_of(node)
            cat = categorize(node.name)
            ret = extract_returns(node, doc)
            se = side_effects_for(node.name, doc)
            idem = idempotency_for(node.name, doc)
            nts = notes_for(node.name, doc)
            if idem == "unknown" and "TODO" not in nts:
                nts = (nts + " TODO").strip() if nts else "TODO"
            helpers.append({
                "name": node.name,
                "signature": sig,
                "category": cat,
                "return": ret,
                "side_effects": se,
                "idempotency": idem,
                "notes": nts,
            })

    helpers.sort(key=lambda h: (CATEGORY_ORDER.index(h["category"]) if h["category"] in CATEGORY_ORDER else 99, h["name"]))

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(helpers, indent=2) + "\n", encoding="utf-8")

    # MD
    by_cat: dict[str, list] = {}
    for h in helpers:
        by_cat.setdefault(h["category"], []).append(h)
    cats_present = [c for c in CATEGORY_ORDER if c in by_cat]
    lines = []
    lines.append("# Helper index")
    lines.append("")
    lines.append(f"Total: {len(helpers)} helpers across {len(cats_present)} categories")
    lines.append("")
    lines.append("Auto-derived from `scripts/_helpers.py`. Run `python tools/validate_skill.py` after editing helpers.")
    lines.append("")
    for c in cats_present:
        lines.append(f"## {c}")
        lines.append("")
        lines.append("| Function | Returns | Side effects | Idempotent | Notes |")
        lines.append("|---|---|---|---|---|")
        for h in sorted(by_cat[c], key=lambda x: x["name"]):
            def esc(s: str) -> str:
                return s.replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| `{esc(h['signature'])}` | {esc(h['return'])} | {esc(h['side_effects'])} | {h['idempotency']} | {esc(h['notes'])} |"
            )
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    # validate
    json.loads(OUT_JSON.read_text(encoding="utf-8"))
    print(f"total: {len(helpers)}")
    counts: dict[str, int] = {}
    for h in helpers:
        counts[h["category"]] = counts.get(h["category"], 0) + 1
    for c in cats_present:
        print(f"  {c}: {counts[c]}")
    unknown = [h for h in helpers if h["idempotency"] == "unknown"]
    if unknown:
        print("unknown idempotency (top 5):")
        for h in unknown[:5]:
            print(f"  - {h['name']}")


if __name__ == "__main__":
    main()
