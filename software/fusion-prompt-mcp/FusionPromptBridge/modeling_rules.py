"""Portable guidance readable by MCP without importing Autodesk modules."""
import hashlib
from pathlib import Path

RULES_VERSION = '1.3.2'


def get_rules(known_sha256=''):
    path=Path(__file__).resolve().parents[1] / 'modeling-rules.md'
    data=path.read_bytes()  # Fail visibly when an incomplete installation omits the rules.
    digest=hashlib.sha256(data).hexdigest()
    result={'rules_version':RULES_VERSION,'sha256':hashlib.sha256(data).hexdigest(),
            'text':data.decode('utf-8'),'scope':'native parametric authoring; explicit project exceptions',
            'enforcement':'Scoped automated checks plus caller evidence; not approval or a global save interceptor.'}
    result['unchanged']=known_sha256==digest
    if result['unchanged']:result.pop('text')
    return result
