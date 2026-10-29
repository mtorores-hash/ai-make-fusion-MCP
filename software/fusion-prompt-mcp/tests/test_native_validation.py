"""Runtime gate controls use module doubles; these are not native Fusion tests."""
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from native_validation import inspect_runtime, require_runtime


class RuntimeGateTests(unittest.TestCase):
    def test_fresh_single_candidate_and_mixed_old_module(self):
        with tempfile.TemporaryDirectory() as home:
            candidate = Path(home) / 'candidate'
            package = candidate / 'FusionPromptBridge'
            package.mkdir(parents=True)
            bridge_path = package / 'FusionPromptBridge.py'
            bridge_path.write_text('# fixture')
            bridge = NS(__file__=str(bridge_path), ROOT=Path(home)/'queue',
                        _thread=NS(is_alive=lambda: True), _lock=NS(file=NS(closed=False)), _busy=False)
            modules = {'bridge': bridge}
            report = inspect_runtime(NS(version='double'), candidate, modules)
            require_runtime(report)
            self.assertEqual(len(report['loaded_modules']), 1)
            old = Path(home)/'old'/'FusionPromptBridge'
            old.mkdir(parents=True)
            (old/'scope.py').write_text('# old fixture')
            modules['old_scope'] = NS(__file__=str(old/'scope.py'))
            with self.assertRaisesRegex(RuntimeError, 'mixed'):
                require_runtime(inspect_runtime(NS(version='double'), candidate, modules))

    def test_inactive_busy_and_duplicate_bridge_rejected(self):
        with tempfile.TemporaryDirectory() as home:
            package=Path(home)/'FusionPromptBridge';package.mkdir()
            path=package/'FusionPromptBridge.py';path.write_text('# fixture')
            bridge=NS(__file__=str(path),_thread=None,_lock=None)
            for modules in ({}, {'bridge':bridge}):
                self.assertEqual(inspect_runtime(NS(version='double'),home,modules)['status'],'blocked')
            bridge._thread=NS(is_alive=lambda:True);bridge._lock=NS(file=NS(closed=False));bridge._busy=True
            self.assertEqual(inspect_runtime(NS(version='double'),home,{'bridge':bridge})['status'],'blocked')
            bridge._busy=False
            self.assertEqual(inspect_runtime(NS(version='double'),home,{'a':bridge,'b':bridge})['status'],'blocked')
