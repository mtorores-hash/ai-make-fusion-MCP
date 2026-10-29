"""Local, same-user file transport; no network listener or arbitrary code execution."""
import json
import os
from pathlib import Path
import time
import uuid
from FusionPromptBridge.compatibility import identity, require_match, mutates

ROOT = Path.home() / '.fusion-prompt-mcp'

def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, allow_nan=False), encoding='utf-8')
    os.replace(temp, path)

def call(operation, arguments=None, timeout=30, root=ROOT):
    if mutates(operation,arguments or {}):
        require_compatible_bridge(timeout,root)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    ident = uuid.uuid4().hex
    request = root / (ident + '.request')
    response = root / (ident + '.response')
    atomic_json(request, {'id': ident, 'operation': operation,
                          'caller':identity(),
                          'arguments': arguments or {}, 'expires': time.time() + timeout})
    deadline = time.monotonic() + timeout + 2
    while time.monotonic() < deadline:
        if response.exists():
            result = json.loads(response.read_text(encoding='utf-8'))
            response.unlink()
            if not result['ok']:
                raise RuntimeError(result['error'])
            return result['result']
        time.sleep(0.1)
    request.unlink(missing_ok=True)
    raise TimeoutError('Fusion did not respond. An operation already started may have completed. '
                       'Inspect Fusion before retrying a mutation. Check that the add-in is running '
                       'and no dialog or sketch command is open.')


def require_compatible_bridge(timeout=30,root=ROOT):
    bridge=call('runtime_identity',timeout=timeout,root=root)
    require_match(bridge)
    return bridge
