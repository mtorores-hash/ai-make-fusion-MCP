"""Read-only metadata probe; does not import bridge modules, acquire locks or touch CAD."""
import json
from pathlib import Path
import sys
import tempfile
import adsk.core


def run(context):
    source=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(source))
    from native_validation import inspect_runtime
    report=inspect_runtime(adsk.core.Application.get(),source)
    output=Path(tempfile.mkdtemp(prefix='fusion-runtime-probe-'))/'runtime.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    adsk.core.Application.get().userInterface.messageBox('Read-only runtime metadata: '+str(output))
