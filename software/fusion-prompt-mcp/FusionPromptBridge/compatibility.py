"""Fail closed before mutations when server and native bridge builds differ."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from .modeling_rules import get_rules


@lru_cache(maxsize=1)
def identity():
    root=Path(__file__).resolve().parent.parent
    files=[root/'server.py',root/'bridge_client.py']+sorted((root/'FusionPromptBridge').glob('*.py'))
    digest=hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
    return {'runtime':'0.8.0','caller_contract':'2.0','protocol':1,
            'rules_sha256':get_rules()['sha256'],'build_sha256':digest.hexdigest()}


def require_match(caller,bridge=None):
    bridge=identity() if bridge is None else bridge
    if not isinstance(caller,dict) or any(caller.get(k)!=v for k,v in bridge.items()):
        raise ValueError('MCP_RUNTIME_MISMATCH: mutation blocked before execution. Reconnect the MCP server and restart Fusion with the same installed build; inspect runtime_identity. No edit token consumed or original job replay authorized.')


def mutates(operation,arguments):
    if operation=='document_state':return bool(arguments.get('acquire_token'))
    if operation=='reconcile_cloud_job':return bool(arguments.get('confirmation_note'))
    return operation not in {'runtime_identity','inspect','capabilities','browse_cloud','inspect_full',
        'inspect_assembly','inspect_body','read_selection','select_geometry','measure_distance',
        'check_interference','validate_model','audit_hygiene'}


# Freeze the source identity when this process imports the implementation, not at
# the first later mutation. Matching immutable installation folders still matter.
LOADED_IDENTITY=identity()
