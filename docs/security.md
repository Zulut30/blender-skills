# Security & Safety Rules for Agents

Audience: Claude Code or any coding agent running this skill. These are rules the agent must follow when acting on behalf of the user.

## Scene preservation

- NEVER call `reset_scene()` unless: the user explicitly asked for a fresh scene, OR the scene is empty / known throwaway, OR you announced "resetting the scene" before doing so.
- For modifications to an existing user .blend: prefer additive operations. Use `boolean_difference` only on objects you created.

## File writes

- NEVER call `bpy.ops.wm.save_as_mainfile` (or the `save_blend` helper) unless the user explicitly asked to save and confirmed the path.
- Confine writes to:
  - the working directory (where Claude Code is running)
  - the user-supplied render output path
  - OS temp directory for intermediate frames
- Renders default to a project-local path; document it in the response so the user can find files.

## Shell and code execution

- NEVER pass user-supplied strings into `subprocess`, `os.system`, or `bpy.ops` arguments without sanitisation.
- For ffmpeg invocation in animation pipelines: pass arguments as a list, never as a single shell string.
- Don't `eval` / `exec` user-supplied code beyond what's already inside `execute_blender_code`.

## Network and assets

- NEVER download external assets (HDRIs, textures, models) without explicit user consent. Even one-off downloads should be announced.
- The skill ships with NO bundled binary assets. All visual richness is procedural.
- If the user provides an asset path, validate it points to a local file before loading.

## Destructive operations -- always announce

Before any of these, post a one-sentence heads-up to the user:

- Deleting > 5 objects at once
- Resetting the scene with non-empty content
- Overwriting an existing .blend file
- Running an animation render that will take > 1 minute (e.g., > 30 frames)
- Running `decimate_mesh` with `ratio < 0.2` (irreversible mesh damage)

## Render output

- Use temporary or project-relative directories by default.
- Don't write to system directories (`C:\Windows`, `/etc`, `/usr/local`).
- Animation frame sequences can be 100+ MB; mention size to the user before mass-rendering.

## Failure containment

- If MCP times out or Blender crashes mid-task, do NOT retry blindly. Re-inspect the scene state with `get_objects_summary` before continuing.
- Cap iteration loops (skill workflow already enforces 3 render+fix cycles before asking the user).

## What to refuse

The agent should refuse (with explanation) requests to:

- Run arbitrary shell commands the user hasn't already approved in their environment.
- Download assets from URLs the user hasn't approved.
- Save .blend files outside the working directory.
- Send rendered frames over the network.

Following these rules keeps the skill predictable and safe for unattended agent runs.
