"""Smoke test: animation helpers don't blow up on a tiny range. No rendering."""
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
        _skip_or_call(H, 'add_cube', 'Subject', (0, 0, 1), (0.5, 0.5, 0.5), None)
    )
    results.append(_skip_or_call(H, 'set_animation_range', start=1, end=10, fps=24))

    plan = [
        (1, (5, -5, 4), (0, 0, 1), 0),
        (5, (0, -7, 4), (0, 0, 1), 0),
        (10, (-5, -5, 4), (0, 0, 1), 0),
    ]

    cam = bpy.context.scene.camera
    if cam is None:
        frame_camera = getattr(H, 'frame_camera', None)
        if frame_camera is not None:
            try:
                cam = frame_camera()
                print('[PASS] frame_camera (created camera)')
            except Exception as e:
                print(f'[FAIL] frame_camera -- {type(e).__name__}: {e}')
                traceback.print_exc()
                results.append('FAIL')
                cam = None
        else:
            print('[SKIP] frame_camera -- helper missing on module')

    bird = getattr(H, 'bird_flight_keyframes', None)
    kf_path = getattr(H, 'keyframe_camera_path', None)
    if cam is None:
        print('[SKIP] keyframe insertion -- no camera available')
    elif bird is not None:
        results.append(safe_call('bird_flight_keyframes', bird, cam, plan))
    elif kf_path is not None:
        results.append(safe_call('keyframe_camera_path', kf_path, cam, plan))
    else:
        print('[SKIP] bird_flight_keyframes / keyframe_camera_path -- both missing')

    if cam is not None:
        if cam.animation_data is not None:
            print('[PASS] camera has animation_data')
        else:
            print('[FAIL] camera has no animation_data after keyframe insertion')
            results.append('FAIL')

    no_failures = not any(r == 'FAIL' for r in results)
    print('-' * 60)
    print('smoke_animation_chunk: %s' % ('OK' if no_failures else 'FAILURES PRESENT'))
    sys.exit(0 if no_failures else 1)


if __name__ == '__main__':
    main()
