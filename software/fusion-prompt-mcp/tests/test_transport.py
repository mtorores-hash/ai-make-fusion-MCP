import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge_client import atomic_json, call

class TransportTests(unittest.TestCase):
    def run_reply(self, reply):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def worker():
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    paths = list(root.glob('*.request'))
                    if paths:
                        request = paths[0]
                        payload = json.loads(request.read_text())
                        self.assertEqual(payload['operation'], 'inspect')
                        atomic_json(request.with_suffix('.response'), reply)
                        request.unlink()
                        return
                    time.sleep(0.01)
            thread = threading.Thread(target=worker)
            thread.start()
            try:
                return call('inspect', timeout=1, root=root)
            finally:
                thread.join()

    def test_response(self):
        self.assertEqual(self.run_reply({'ok': True, 'result': {'bodies': []}}), {'bodies': []})

    def test_error(self):
        with self.assertRaisesRegex(RuntimeError, 'wrong document'):
            self.run_reply({'ok': False, 'error': 'wrong document'})

    def test_timeout_removes_pending_request(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(TimeoutError):
                call('inspect', timeout=-1.9, root=root)
            self.assertEqual(list(root.glob('*.request')), [])

if __name__ == '__main__':
    unittest.main()
