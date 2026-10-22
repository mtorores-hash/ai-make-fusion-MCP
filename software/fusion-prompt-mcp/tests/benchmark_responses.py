"""Reproducible response bytes/time, synthetic inventories; no MCP SDK/Fusion required."""
import ast
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from FusionPromptBridge.job_store import Store,canonical
from FusionPromptBridge import reporting


def measure():
    rows=[]
    with tempfile.TemporaryDirectory() as temporary:
        store=Store(temporary)
        for count in (10,10000):
            payload={'document_id':'synthetic-document','components':[['fixture','r1']],
                'parameters':[['dimension_'+str(i),str(i)+' mm'] for i in range(count)],
                'references':[],'file':None,'name':'Disposable','modified':False}
            times=[]
            for _ in range(10):
                begin=time.perf_counter();reply=reporting.response(store,payload);times.append(time.perf_counter()-begin)
            unchanged=reporting.response(store,payload,after_revision=reply['revision'])
            rows.append({'parameter_count':count,'full_bytes':len(canonical(payload).encode()),
                'summary_bytes':len(canonical(reply).encode()),'unchanged_bytes':len(canonical(unchanged).encode()),
                'summary_generation_median_ms':statistics.median(times)*1000,'logical_summary_calls':1,
                'logical_unchanged_poll_calls':1,'raw_detail_calls_32768_chars':(len(canonical(payload))+32767)//32768})
        tree=ast.parse((Path(__file__).resolve().parents[1]/'server.py').read_text())
        docstrings=[ast.get_docstring(n) or '' for n in tree.body if isinstance(n,ast.FunctionDef) and
                    any(isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='tool' for d in n.decorator_list)]
    return {'qualification':'Synthetic direct Python calls; not transport latency, native timing or token/billing measurement',
        'rows':rows,'tool_count':len(docstrings),'tool_description_characters':sum(map(len,docstrings)),
        'iterations_per_case':10,'validation_or_fingerprint_work_removed':False,
        'limits':'Canonical UTF-8 response sizes exclude MCP envelope; full detail is still hashed/stored. Native latency and large real design costs unmeasured.'}


if __name__=='__main__':print(json.dumps(measure(),indent=2))
