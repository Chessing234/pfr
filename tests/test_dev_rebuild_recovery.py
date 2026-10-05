import contextlib
import io
import sys
import types
import unittest
from unittest.mock import patch

from invoke import Context, Result
from invoke.exceptions import UnexpectedExit

import tasks


class RebuildRecoveryTests(unittest.TestCase):
    def run_watcher(self, bp_failures):
        watchfiles = types.ModuleType('watchfiles')
        watchfiles.DefaultFilter = lambda **kwargs: kwargs

        def run_process(*args, callback, **kwargs):
            callback({'first edit'})
            callback({'corrected edit'})

        watchfiles.run_process = run_process
        with patch.dict(sys.modules, {'watchfiles': watchfiles}), \
                patch.object(tasks, 'bp', side_effect=bp_failures) as bp, \
                patch.object(tasks, 'web') as web, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            tasks.dev.body(Context())
            return bp.call_count, web.call_count, output.getvalue()

    def test_command_failure_allows_next_edit_to_rebuild(self):
        failure = UnexpectedExit(Result(command='xelatex', exited=1,
                                        stderr='Invalid TeX syntax'))
        bp_calls, web_calls, output = self.run_watcher([failure, None])
        self.assertEqual(bp_calls, 2)
        self.assertEqual(web_calls, 1)
        self.assertIn('xelatex', output)
        self.assertIn('waiting for another edit', output)

    def test_programming_errors_still_propagate(self):
        with self.assertRaisesRegex(RuntimeError, 'unexpected bug'):
            self.run_watcher([RuntimeError('unexpected bug')])


if __name__ == '__main__':
    unittest.main()
