# Releasing

This skill follows [SemVer](https://semver.org/):

- **Major** — breaking change to a public helper signature, removed helper, changed workflow contract.
- **Minor** — new helpers, new pitfalls, new docs, new templates. No breaking changes.
- **Patch** — bug fixes inside helpers, doc clarifications, validator improvements.

The `version:` field in `SKILL.md` frontmatter is the source of truth and must match the git tag.

## Release checklist

### 1. Pre-release sanity

```bash
python tools/validate_skill.py
python tests/test_helper_index.py
python -m py_compile tools/validate_skill.py tests/test_helper_index.py
```

All three must pass. CI will re-run them on the release commit anyway, but local-first saves a round-trip.

If you added or modified helpers, regenerate the index:

```bash
python tools/_gen_helper_index.py
```

Then re-run the validator. The validator will fail if the index is out of sync.

### 2. Update version + changelog

Edit `SKILL.md` frontmatter:

```yaml
version: 1.7.0
```

Edit `CHANGELOG.md` — add a new section at the top with the matching version and a short, user-facing description of the change. Use Keep a Changelog conventions (`Added`, `Changed`, `Fixed`, `Removed`).

Example:

```markdown
## 1.7.0

### Added
- `import_glb` helper for .glb / .gltf assets.
- 7 new pitfalls (linked-libraries, multi-user mesh, link-dedupe, EEVEE samples, Cycles GPU, modifier-apply hidden, shape-keys-after-scale).

### Fixed
- `hdri_world` now validates `image.has_data` after load.
- `bbox_of` now calls `view_layer.update()` and reads from depsgraph.
- `paving_stones` no longer creates 800 material datablocks for medium grids.
```

### 3. Commit + push

```bash
git add -A
git commit -m "release: v1.7.0"
git push origin main
```

CI must go green on this commit before tagging.

### 4. Tag + push tag

```bash
git tag -a v1.7.0 -m "v1.7.0"
git push origin v1.7.0
```

Tag format: `vX.Y.Z` (with the `v` prefix). The tag must match `SKILL.md`'s `version:` field exactly.

### 5. Cut the GitHub release

GitHub UI → Releases → **Draft a new release**:

- **Tag**: `v1.7.0` (existing tag).
- **Release title**: `v1.7.0 — short description` (e.g. `v1.7.0 — public-release polish`).
- **Body**: paste the matching `CHANGELOG.md` slice. Add an "Install" snippet and a one-line summary at the top.
- **Set as the latest release**: checked (for a stable release).
- **Set as a pre-release**: only for `-rc.N` or `-beta.N` versions.
- **Generate release notes**: optional; usually the changelog slice is better.

### 6. Verify the published release

- Tag page on GitHub shows the release notes.
- README badges still go green (CI workflow runs on the tag commit too).
- `git clone <repo> <tmp>; cd <tmp>; python tools/validate_skill.py` from a fresh clone passes.

## Hotfix flow (patch on a released tag)

1. Branch from the tag: `git checkout -b hotfix/v1.7.1 v1.7.0`
2. Land the fix, bump to `1.7.1` in SKILL.md, update CHANGELOG.
3. Open PR to `main`. Once green, merge.
4. Tag `v1.7.1` on the merge commit. Release.

Do not retag an existing version. If a release ships broken, immediately publish `vX.Y.Z+1` rather than rewriting the tag.

## Pre-release versions

For risky changes (large new helper categories, workflow contract tweaks):

- Version: `1.7.0-rc.1` (semver pre-release).
- Tag: `v1.7.0-rc.1`.
- Mark the GitHub release as **pre-release**.
- Once stable, ship `v1.7.0` (no `-rc`).

## What never goes into a release

- Personal paths, machine-specific settings (`tools/validate_skill.py` lints for these).
- Half-implemented helpers — either ship working or don't add to the index.
- Pitfalls that are speculative — only document failures actually observed.

## First public release

For the very first public release (`v1.0.0` or whatever the current `SKILL.md` version says):

- Add a `LICENSE` file at the repo root (MIT recommended; matches README).
- Update [`docs/repo-metadata.md`](repo-metadata.md) — apply description / topics / website fields in the GitHub UI.
- Optional: upload a hero render as social preview image (Settings → Social preview).
- Pin `main` branch protection: require PRs and the `validate` status check.
- Announce: link to the GitHub release plus the [`docs/quickstart.md`](quickstart.md) page.
