"""Root conftest: skip integration tests unless POLARION_LIVE is set."""

import os
import pytest

# Collect integration test files only when POLARION_LIVE env var is set
collect_ignore_glob = []
if not os.environ.get('POLARION_LIVE'):
    collect_ignore_glob.append('test_polarion_*.py')
    collect_ignore_glob.append('test_junit.py')
