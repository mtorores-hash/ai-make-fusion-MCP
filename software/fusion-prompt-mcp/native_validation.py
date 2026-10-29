"""Read-only loaded-runtime gate for disposable native acceptance, not CAD validation."""
import hashlib
from pathlib import Path
import sys


def inspect_runtime(app, expected, modules=None):
    expected = Path(expected).resolve()
    loaded = []
    bridges = []
    for name, module in list((sys.modules if modules is None else modules).items()):
        filename = getattr(module, '__file__', None)
        if not filename:
            continue
        path = Path(filename).resolve()
        if path.parent.name != 'FusionPromptBridge' or path.suffix != '.py':
            continue
        loaded.append({'module': name, 'path': str(path),
                       'disk_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        if path.name == 'FusionPromptBridge.py':
            thread = getattr(module, '_thread', None)
            lock = getattr(module, '_lock', None)
            handle = getattr(lock, 'file', None)
            bridges.append({'path': str(path), 'queue': str(getattr(module, 'ROOT', '')),
                            'worker_alive': bool(thread and thread.is_alive()),
                            'lock_handle_open': bool(handle and not handle.closed),
                            'busy': bool(getattr(module, '_busy', False))})
    errors = []
    if not loaded or any(Path(row['path']).parent.parent != expected for row in loaded):
        errors.append('Missing candidate modules or mixed loaded source paths')
    if len(bridges) != 1 or not all(b['worker_alive'] and b['lock_handle_open'] for b in bridges):
        errors.append('Exactly one running candidate bridge with an open queue lock is required')
    if any(b['busy'] for b in bridges):
        errors.append('Bridge is busy; wait for a safe boundary')
    return {'status': 'blocked' if errors else 'pass', 'errors': errors,
            'expected_source': str(expected), 'fusion_version': app.version,
            'python_version': sys.version, 'python_executable': sys.executable,
            'loaded_modules': loaded, 'bridges': bridges,
            'limits': 'Disk hashes identify current files, not in-memory bytecode. Use a fresh Fusion process after switching source. No CAD qualification.'}


def require_runtime(report):
    if report['status'] != 'pass':
        raise RuntimeError('; '.join(report['errors']))
