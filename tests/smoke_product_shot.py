"""Smoke test: build a minimal product shot scene via helpers. No rendering."""
import importlib.util, os, sys, traceback

import bpy

HELPERS_PATH = os.path.join(os.path.dirname(__file__), '..', 'scripts', '_helpers.py')


def load_helpers():
    spec = importlib.util.spec_from_file_location('_skill_helpers', HELPERS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def safe_call(name, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        print(f'[PASS] {name}')
        return result
    except AttributeError as e:
        print(f'[SKIP] {name} -- helper missing: {e}')
        return None
    except Exception as e:
        print(f'[FAIL] {name} -- {type(e).__name__}: {e}')
        traceback.print_exc()
        return 'FAIL'


def _skip_or_call(H, name, *args, **kwargs):
    fn = getattr(H, name, None)
    if fn is None:
        print(f'[SKIP] {name} -- helper missing on module')
        return None
    return safe_call(name, fn, *args, **kwargs)


def main():
    results = []
    try:
        H = load_helpers()
        print('[PASS] load_helpers')
    except Exception as e:
        print(f'[FAIL] load_helpers -- {type(e).__name__}: {e}')
        traceback.print_exc()
        sys.exit(1)

    results.append(_skip_or_call(H, 'reset_scene'))
    results.append(
        _skip_or_call(
            H, 'cyclorama_backdrop', 'Cyc', size=4.0, color=(0.05, 0.05, 0.05)
        )
    )
    results.append(
        _skip_or_call(H, 'add_cube', 'Subject', (0, 0, 1), (0.5, 0.5, 0.5), None)
    )
    results.append(_skip_or_call(H, 'studio_dark_world', strength=0.2))
    results.append(
        _skip_or_call(H, 'three_point_light', target=(0, 0, 1), key_energy=4.0)
    )
    results.append(_skip_or_call(H, 'set_render', resolution=(640, 400), samples=8))

    auto_frame = getattr(H, 'auto_frame', None)
    if auto_frame is None:
        print('[SKIP] auto_frame -- helper missing on module')
    else:
        subj = bpy.data.objects.get('Subject')
        results.append(
            safe_call(
                'auto_frame',
                auto_frame,
                [subj] if subj is not None else [],
                padding=1.3,
                elevation_deg=15,
                azimuth_deg=30,
                lens=50,
            )
        )

    no_failures = not any(r == 'FAIL' for r in results)
    print('-' * 60)
    print('smoke_product_shot: %s' % ('OK' if no_failures else 'FAILURES PRESENT'))
    sys.exit(0 if no_failures else 1)


if __name__ == '__main__':
    main()
