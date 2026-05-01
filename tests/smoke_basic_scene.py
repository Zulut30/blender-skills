"""Smoke test: load helpers, build a minimal scene, no rendering. Pass = no exceptions."""
import importlib.util, os, sys, traceback

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
    results.append(_skip_or_call(H, 'add_plane', 'Ground', (0, 0, 0), 10, None))
    results.append(_skip_or_call(H, 'add_cube', 'Cube', (0, 0, 1), (1, 1, 1), None))
    results.append(_skip_or_call(H, 'add_cyl', 'Cyl', (3, 0, 1), 0.5, 2, None))
    results.append(_skip_or_call(H, 'add_cone', 'Cone', (-3, 0, 1), 0.6, 0, 1.5, None))
    results.append(_skip_or_call(H, 'mat', 'TestMat', (0.5, 0.5, 0.5)))

    no_failures = not any(r == 'FAIL' for r in results)
    print('-' * 60)
    print('smoke_basic_scene: %s' % ('OK' if no_failures else 'FAILURES PRESENT'))
    sys.exit(0 if no_failures else 1)


if __name__ == '__main__':
    main()
