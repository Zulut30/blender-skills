# Setting up Blender + MCP

## Requirements

- Blender 5.x (tested on 5.1.1; older 4.x may work for most helpers but Hosek-Wilkie sky and slotted-actions code paths assume 5.x)
- Blender MCP addon enabled and the MCP server started inside Blender
- Python >= 3.11 on the host (for validation tooling, not for running Blender)
- Optional: ffmpeg on PATH (for assembling rendered frame sequences into mp4)

## Installing the skill

```
git clone https://github.com/Zulut30/blender-skills.git ~/.claude/skills/blender
```

On Windows: `C:\Users\<you>\.claude\skills\blender\`. Claude Code auto-discovers skills under `~/.claude/skills/` via the `description` field in `SKILL.md`.

## Verifying MCP availability

The skill expects the following MCP tools to be present:

- `mcp__Blender__execute_blender_code`
- `mcp__Blender__render_viewport_to_path`
- `mcp__Blender__get_objects_summary`
- `mcp__Blender__get_object_detail_summary`
- `mcp__Blender__get_blendfile_summary_*`
- `mcp__Blender__search_api_docs`
- `mcp__Blender__get_python_api_docs`

Quick sanity check (run from Claude Code after enabling the Blender MCP):

```python
import bpy
result = {"version": list(bpy.app.version), "n_objects": len(bpy.data.objects)}
```

If you get `Cannot connect to Blender at localhost:9876`, start the MCP server in Blender: N-panel in 3D Viewport -> MCP tab -> Start Server.

## Minimal sanity check

Run a Blender smoke script:

```
blender -b --factory-startup --python tests/smoke_basic_scene.py
```

This exercises `reset_scene`, `add_*` primitives, and the material helper without rendering. Expected output ends with `[PASS] ...` lines and exit 0.

## Where to save renders

The skill always passes an output path to `render_viewport_to_path`, but Blender's MCP writes to a temp directory and returns the actual path in `result.filepath`. **Read that returned path, not your hint.** Recommended convention:

- Hint: `D:\renders\my_scene.png` (Windows) or `/tmp/renders/my_scene.png` (Linux/macOS)
- Real output: whatever the MCP returns; copy it elsewhere if you need to keep it.

For animation frames, set the `output_dir` argument of `render_animation_frames` to a directory you control.

## Platform path notes

- Windows: prefer raw strings or forward slashes when passing to bpy: `r"C:\renders"` or `"C:/renders"`. Backslash strings can cause silent failures (see `reference/pitfalls.md#33`).
- macOS / Linux: standard POSIX paths. `~` is NOT auto-expanded inside Blender Python -- use `os.path.expanduser`.
- Locale: helpers all set `obj.name` and `obj.data.name` explicitly because `use_translate_new_dataname=True` in some Blender installs translates default names ("Cube" -> "Куб"). The skill is locale-safe by design.
