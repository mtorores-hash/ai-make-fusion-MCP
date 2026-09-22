import concurrent.futures
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from FusionPromptBridge.job_store import Store, BridgeLock

class JobTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name)
        self.req=dict(operation_id='part-001',document_id='doc',component_token='root',units='mm',
                      script='def run(ctx):\n    return {"ok":True}',checkpoint_before=True,validate_after=True)
    def test_concurrent_duplicate_submission(self):
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            jobs=list(pool.map(lambda _:self.store.submit(self.req),range(20)))
        self.assertEqual(len({j['job_id'] for j in jobs}),1)
        self.assertEqual(len(self.store.list()),1)
    def test_changed_payload_cannot_reuse_id(self):
        self.store.submit(self.req)
        with self.assertRaises(ValueError): self.store.submit(dict(self.req,script='def run(ctx): pass'))
    def test_claim_exactly_once(self):
        self.store.submit(self.req)
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            jobs=list(pool.map(lambda _:self.store.claim('bridge'),range(4)))
        self.assertEqual(sum(j is not None for j in jobs),1)
    def test_recovery_never_replays_partial_job(self):
        job=self.store.submit(self.req); self.store.claim('old')
        self.store.partial(job['job_id'],{'checkpoints':[{'path':'before.f3d'}]})
        self.store.recover()
        self.assertEqual(self.store.status(job['job_id'])['status'],'interrupted')
        self.assertIsNone(self.store.claim('new'))
        self.assertEqual(self.store.submit(self.req)['job_id'],job['job_id'])
        self.assertEqual(self.store.result(job['job_id'])['result']['checkpoints'][0]['path'],'before.f3d')
    def test_cancel_queued_job(self):
        job=self.store.submit(self.req)
        self.assertEqual(self.store.cancel(job['job_id'])['status'],'cancelled')
        self.assertIsNone(self.store.claim('bridge'))
    def test_cancel_running_is_cooperative(self):
        job=self.store.submit(self.req); self.store.claim('bridge')
        status=self.store.cancel(job['job_id'])
        self.assertEqual(status['status'],'running'); self.assertEqual(status['cancel_requested'],1)
    def test_progress_visible_to_other_connection(self):
        job=self.store.submit(self.req); self.store.claim('bridge')
        self.store.progress(job['job_id'],0.5,'Sketches done')
        self.assertEqual(Store(self.tmp.name).status(job['job_id'])['progress'],0.5)
    def test_bridge_lock_exclusive_and_released(self):
        a=BridgeLock(self.tmp.name); b=BridgeLock(self.tmp.name)
        a.acquire()
        try:
            with self.assertRaises(RuntimeError): b.acquire()
        finally: a.close()
        b.acquire(); b.close()
    def test_bad_script_does_not_enqueue(self):
        for script in ('syntax error!', 'x=1', 'async def run(ctx): pass'):
            with self.assertRaises((ValueError,SyntaxError)):
                self.store.submit(dict(self.req,script=script))
        self.assertEqual(self.store.list(),[])
    def test_bad_target_and_units(self):
        for change in ({'component_token':''},{'document_id':''},{'units':'feet'}):
            with self.assertRaises(ValueError): self.store.submit(dict(self.req,**change))
    def test_finished_job_survives_new_store(self):
        j=self.store.submit(self.req); self.store.claim('bridge')
        self.store.finish(j['job_id'],'failed',{'traceback':'complete trace\nline 2'})
        r=Store(self.tmp.name).result(j['job_id'])
        self.assertEqual(r['result']['traceback'],'complete trace\nline 2')

if __name__=='__main__': unittest.main()
