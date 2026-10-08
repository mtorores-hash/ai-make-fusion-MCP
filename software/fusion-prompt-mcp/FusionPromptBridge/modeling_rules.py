"""Portable guidance readable by MCP without importing Autodesk modules."""
import hashlib
from pathlib import Path

RULES_VERSION = '1.0.4'


def get_rules():
    path=Path(__file__).resolve().parents[1] / 'modeling-rules.md'
    data=path.read_bytes()  # Fail visibly when an incomplete installation omits the rules.
    return {'rules_version':RULES_VERSION,'sha256':hashlib.sha256(data).hexdigest(),
            'text':data.decode('utf-8'),'scope':'native parametric authoring; explicit project exceptions',
            'enforcement':'Guidance plus explicit automated-subset audit/export gate; not a global save interceptor.'}
