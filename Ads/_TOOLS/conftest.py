# -*- coding: utf-8 -*-
"""Runs every engine test script (Ads/_TOOLS/test_*.py) as one pytest item.

The scripts are script-style: some use unittest, most count failures and call
sys.exit. Several `def test_*` functions RETURN a failure count instead of
asserting, so letting pytest import them natively would report them green even
when they fail. Instead each script runs as a subprocess with the same
interpreter and passes only when it exits with code 0 -- exactly the verdict
the script gives when run by hand. No assertion is rewritten.

    python -m pytest Ads/_TOOLS            # all engine tests
    python -m pytest Ads/_TOOLS -k decidir # one script
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent
RAIZ = TOOLS.parent.parent
TIMEOUT_S = 900


def pytest_collect_file(parent, file_path):
    if file_path.parent == TOOLS and file_path.name.startswith("test_") and file_path.suffix == ".py":
        return ScriptFile.from_parent(parent, path=file_path)
    return None


class ScriptFile(pytest.File):
    def collect(self):
        yield ScriptItem.from_parent(self, name=self.path.stem)


class ScriptFailed(Exception):
    pass


class ScriptItem(pytest.Item):
    def runtest(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        proc = subprocess.run(
            [sys.executable, str(self.path)],
            cwd=RAIZ, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=TIMEOUT_S,
        )
        if proc.returncode != 0:
            raise ScriptFailed(
                "exit %d\n%s\n%s" % (proc.returncode, proc.stdout[-4000:], proc.stderr[-4000:])
            )

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, ScriptFailed):
            return str(excinfo.value)
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, None, "script: %s" % self.path.name
