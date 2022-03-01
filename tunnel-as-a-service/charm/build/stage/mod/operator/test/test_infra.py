# Copyright 2020-2021 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools
import os
import re
import subprocess
import sys
import tempfile
import unittest

import ops


def get_python_filepaths(include_tests=True):
    """Helper to retrieve paths of Python files."""
    python_paths = ['setup.py']
    roots = ['ops']
    if include_tests:
        roots.append('test')
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath == 'ops':
                # Don't scan ops/_vendor directory
                dirnames[:] = [x for x in dirnames if x != '_vendor']
            for filename in filenames:
                if filename.endswith(".py"):
                    python_paths.append(os.path.join(dirpath, filename))
    return python_paths


class InfrastructureTests(unittest.TestCase):

    def test_quote_backslashes(self):
        # ensure we're not using unneeded backslash to escape strings
        issues = []
        for filepath in get_python_filepaths():
            with open(filepath, "rt", encoding="utf8") as fh:
                for idx, line in enumerate(fh, 1):
                    if (r'\"' in line or r"\'" in line) and "NOQA" not in line:
                        issues.append((filepath, idx, line.rstrip()))
        if issues:
            msgs = ["{}:{:d}:{}".format(*issue) for issue in issues]
            self.fail("Spurious backslashes found, please fix these quotings:\n" + "\n".join(msgs))

    def test_ensure_copyright(self):
        # all non-empty Python files must have a proper copyright somewhere in the first 5 lines
        issues = []
        regex = re.compile(r"# Copyright \d\d\d\d(-\d\d\d\d)? Canonical Ltd.\n")
        for filepath in get_python_filepaths():
            if os.stat(filepath).st_size == 0:
                continue

            with open(filepath, "rt", encoding="utf8") as fh:
                for line in itertools.islice(fh, 5):
                    if regex.match(line):
                        break
                else:
                    issues.append(filepath)
        if issues:
            self.fail("Please add copyright headers to the following files:\n" + "\n".join(issues))

    def _run_setup(self, *args):
        # from 3.6 we could just use encoding="utf8" here, but 3.5
        # doesn't expose that and instead defaults to the wrong thing
        proc = subprocess.run(
            (sys.executable, 'setup.py') + args,
            stdout=subprocess.PIPE,
            check=True)
        out = proc.stdout.strip().decode("utf8")
        if os.linesep != '\n':
            out = out.replace(os.linesep, '\n')
        return out

    def test_setup_version(self):
        setup_version = self._run_setup('--version')

        self.assertEqual(setup_version, ops.__version__)

    def test_setup_description(self):
        with open("README.md", "rt", encoding="utf8") as fh:
            disk_readme = fh.read().strip()

        setup_readme = self._run_setup('--long-description')

        self.assertEqual(setup_readme, disk_readme)

    def test_check(self):
        self._run_setup('check', '--strict')


class ImportersTestCase(unittest.TestCase):

    template = "from ops import {module_name}"

    def test_imports(self):
        mod_names = [
            'charm',
            'framework',
            'main',
            'model',
            'testing',
        ]

        for name in mod_names:
            with self.subTest(name=name):
                self.check(name)

    def check(self, name):
        """Helper function to run the test."""
        fd, testfile = tempfile.mkstemp()
        self.addCleanup(os.unlink, testfile)

        with open(fd, 'wt', encoding='utf8') as fh:
            fh.write(self.template.format(module_name=name))

        environ = os.environ.copy()
        if 'PYTHONPATH' in environ:
            environ['PYTHONPATH'] = os.getcwd() + os.pathsep + environ['PYTHONPATH']
        else:
            environ['PYTHONPATH'] = os.getcwd()
        proc = subprocess.run([sys.executable, testfile], env=environ)
        self.assertEqual(proc.returncode, 0)
